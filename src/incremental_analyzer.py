"""
Analyseur Incrémental
=====================
Ne ré-analyse que les documents nouveaux ou modifiés.
Fusionne intelligemment les concepts ancien/nouveau.
"""

import json
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict

STATE_FILE = Path("data/analysis_state.json")


@dataclass
class FileState:
    """État d'un fichier lors de la dernière analyse."""
    path: str
    filename: str
    module: Optional[str]
    hash: str
    size: int
    analyzed_at: str  # ISO format
    concepts_count: int


class IncrementalAnalyzer:
    """
    Gère l'analyse incrémentale des documents.
    
    Workflow :
    1. compare_with_previous(scanned_docs) → identifie new / modified / deleted / unchanged
    2. L'appelant lance l'analyse IA uniquement sur new + modified
    3. merge_concepts(new_concepts) → fusionne avec l'existant
    4. save_state() → met à jour l'état pour la prochaine exécution
    """

    def __init__(self):
        self.state_file = STATE_FILE
        self.previous_state: Dict[str, dict] = {}
        self.current_state: Dict[str, dict] = {}
        self._load_state()

    # ── Persistence ──

    def _load_state(self):
        """Charge l'état de la dernière analyse."""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.previous_state = data.get('files', {})
            except (json.JSONDecodeError, Exception):
                self.previous_state = {}
        else:
            self.previous_state = {}

    def save_state(self):
        """Sauvegarde l'état actuel pour la prochaine exécution."""
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        data = {
            'last_analysis': datetime.now().isoformat(),
            'total_files': len(self.current_state),
            'files': self.current_state,
        }
        with open(self.state_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    # ── Hashing ──

    @staticmethod
    def _hash_content(content: str) -> str:
        """Calcule un hash SHA-256 du contenu textuel."""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()[:16]

    # ── Comparaison ──

    def compare_with_previous(self, scanned_docs: list) -> Dict[str, list]:
        """
        Compare les documents scannés avec le dernier état connu.
        
        Args:
            scanned_docs: liste d'objets DocumentInfo (depuis scanner.scan_all)
        
        Returns:
            {
                'new':       [doc, ...],   # jamais analysés
                'modified':  [doc, ...],   # contenu changé
                'unchanged': [doc, ...],   # identiques
                'deleted':   [path, ...],  # supprimés depuis la dernière analyse
            }
        """
        result = {'new': [], 'modified': [], 'unchanged': [], 'deleted': []}
        seen_paths = set()

        for doc in scanned_docs:
            path_key = doc.path
            seen_paths.add(path_key)

            current_hash = self._hash_content(doc.content)

            if path_key not in self.previous_state:
                result['new'].append(doc)
            elif self.previous_state[path_key].get('hash') != current_hash:
                result['modified'].append(doc)
            else:
                result['unchanged'].append(doc)

            # Enregistrer le hash courant
            self.current_state[path_key] = {
                'path': doc.path,
                'filename': doc.filename,
                'module': doc.module,
                'hash': current_hash,
                'size': len(doc.content),
                'analyzed_at': datetime.now().isoformat(),
                'concepts_count': 0,  # sera mis à jour après analyse
            }

        # Fichiers supprimés depuis la dernière analyse
        for path_key in self.previous_state:
            if path_key not in seen_paths:
                result['deleted'].append(path_key)

        return result

    # ── Fusion de concepts ──

    def merge_concepts(
        self,
        existing_concept_map: Dict,
        new_concepts: list,
        docs_to_reanalyze: list,
        deleted_paths: list,
    ) -> Dict:
        """
        Fusionne les nouveaux concepts avec la carte existante.
        
        Stratégie :
        - Supprimer les concepts des documents supprimés ou ré-analysés
        - Ajouter les concepts issus de la nouvelle analyse
        - Conserver intacts les concepts des documents inchangés
        
        Args:
            existing_concept_map: concept_map.json actuel
            new_concepts: liste de Concept (dataclass de analyzer.py)
            docs_to_reanalyze: docs (new + modified) qui ont été ré-analysés
            deleted_paths: chemins des fichiers supprimés
        
        Returns:
            concept_map mis à jour (dict prêt pour export JSON)
        """
        if not existing_concept_map or 'nodes' not in existing_concept_map:
            # Pas de données existantes, on part de zéro
            return None  # signal que le mapper doit reconstruire

        existing_nodes = existing_concept_map.get('nodes', [])

        # Ensemble des source_document à supprimer (ré-analysés + supprimés)
        docs_to_remove = set()
        for doc in docs_to_reanalyze:
            docs_to_remove.add(doc.filename)
        for path in deleted_paths:
            docs_to_remove.add(Path(path).name)

        # Garder les concepts des documents inchangés
        kept_nodes = [
            n for n in existing_nodes
            if n.get('source_document', '') not in docs_to_remove
        ]

        # Convertir les nouveaux concepts en format node (comme concept_mapper le fait)
        new_nodes = []
        for concept in new_concepts:
            node = {
                'id': concept.id,
                'name': concept.name,
                'description': concept.description,
                'category': getattr(concept, 'category', 'Général'),
                'importance': getattr(concept, 'importance', 'medium'),
                'exam_relevant': getattr(concept, 'exam_relevant', False),
                'prerequisites': list(getattr(concept, 'prerequisites', [])),
                'dependents': [],
                'related_concepts': list(getattr(concept, 'related_concepts', [])),
                'module': getattr(concept, 'source_module', None),
                'source_document': getattr(concept, 'source_document', ''),
                'page_references': getattr(concept, 'page_references', ''),
                'keywords': list(getattr(concept, 'keywords', [])),
            }
            new_nodes.append(node)

        merged_nodes = kept_nodes + new_nodes

        # Dédupliquer par nom (garder le plus récent = new)
        seen_names = {}
        deduped = []
        for node in reversed(merged_nodes):
            name_key = node.get('name', '').lower().strip()
            if name_key and name_key not in seen_names:
                seen_names[name_key] = True
                deduped.append(node)
        deduped.reverse()

        # Mettre à jour les compteurs dans current_state
        for node in new_nodes:
            src = node.get('source_document', '')
            for path_key, state in self.current_state.items():
                if state.get('filename') == src:
                    state['concepts_count'] = state.get('concepts_count', 0) + 1

        # Reconstruire la structure
        merged_map = dict(existing_concept_map)
        merged_map['nodes'] = deduped
        merged_map['metadata'] = merged_map.get('metadata', {})
        merged_map['metadata']['last_updated'] = datetime.now().isoformat()
        merged_map['metadata']['total_concepts'] = len(deduped)
        merged_map['metadata']['incremental'] = True

        return merged_map

    # ── Résumé ──

    def get_comparison_summary(self, comparison: Dict) -> Dict:
        """Retourne un résumé lisible de la comparaison."""
        return {
            'new_count': len(comparison['new']),
            'modified_count': len(comparison['modified']),
            'unchanged_count': len(comparison['unchanged']),
            'deleted_count': len(comparison['deleted']),
            'total_to_analyze': len(comparison['new']) + len(comparison['modified']),
            'new_files': [d.filename for d in comparison['new']],
            'modified_files': [d.filename for d in comparison['modified']],
            'deleted_files': [Path(p).name for p in comparison['deleted']],
            'savings_pct': (
                round(len(comparison['unchanged']) / 
                      max(1, len(comparison['new']) + len(comparison['modified']) + len(comparison['unchanged'])) * 100)
            ),
        }

    def has_previous_analysis(self) -> bool:
        """Vérifie si une analyse précédente existe."""
        return len(self.previous_state) > 0

    def get_last_analysis_info(self) -> Optional[Dict]:
        """Retourne les infos de la dernière analyse."""
        if not self.state_file.exists():
            return None
        try:
            with open(self.state_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return {
                'date': data.get('last_analysis', 'Inconnue'),
                'total_files': data.get('total_files', 0),
            }
        except Exception:
            return None
