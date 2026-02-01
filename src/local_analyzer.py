"""
Analyseur Local de Contenu (sans API)
=====================================
Extrait les concepts des cours sans utiliser d'API externe
"""

import re
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from pathlib import Path
from collections import Counter
import json


@dataclass
class LocalConcept:
    """Représente un concept extrait localement"""
    id: str
    name: str
    description: str
    category: str
    source_document: str
    source_module: Optional[str]
    importance: str  # 'critical', 'high', 'medium', 'low'
    keywords: List[str] = field(default_factory=list)
    frequency: int = 1


class LocalContentAnalyzer:
    """Analyse le contenu localement sans API"""
    
    # Mots-clés techniques par catégorie
    TECHNICAL_KEYWORDS = {
        'Électrotechnique': [
            'tension', 'courant', 'résistance', 'puissance', 'ohm', 'volt', 'ampère', 
            'watt', 'transformateur', 'condensateur', 'inductance', 'circuit', 
            'triphasé', 'monophasé', 'alternatif', 'continu', 'fréquence', 'impédance',
            'réactance', 'cos phi', 'facteur de puissance', 'court-circuit'
        ],
        'Réseaux de distribution': [
            'réseau', 'distribution', 'transport', 'poste', 'station', 'ligne',
            'câble', 'conducteur', 'pylône', 'isolateur', 'raccordement', 'branchement',
            'moyenne tension', 'basse tension', 'haute tension', 'mt', 'bt', 'ht',
            'souterrain', 'aérien', 'armoire', 'coffret'
        ],
        'Sécurité': [
            'sécurité', 'protection', 'risque', 'danger', 'epi', 'consignation',
            'habilitation', 'travaux', 'intervention', 'manœuvre', 'vérification',
            'accident', 'prévention', 'incendie', 'électrocution', 'arc électrique',
            'règle des 5', 'mise à terre', 'équipotentielle'
        ],
        'Réglementation': [
            'norme', 'ordonnance', 'loi', 'oibt', 'nibt', 'esti', 'suva', 'cfst',
            'directive', 'règlement', 'prescription', 'conformité', 'contrôle',
            'inspection', 'certification', 'homologation'
        ],
        'Mesures et contrôles': [
            'mesure', 'multimètre', 'pince', 'ohmmètre', 'mégohmmètre', 'test',
            'vérification', 'contrôle', 'calibrage', 'étalonnage', 'précision',
            'isolement', 'continuité', 'terre', 'boucle'
        ],
        'Maintenance': [
            'maintenance', 'entretien', 'réparation', 'dépannage', 'diagnostic',
            'préventif', 'correctif', 'planification', 'intervention', 'rapport',
            'historique', 'suivi', 'inspection', 'révision'
        ],
        'Éclairage': [
            'éclairage', 'lampe', 'luminaire', 'led', 'sodium', 'mercure',
            'candela', 'lumen', 'lux', 'photométrie', 'public', 'routier'
        ],
        'Mécanique': [
            'force', 'couple', 'moment', 'pression', 'levier', 'poulie',
            'engrenage', 'friction', 'résistance mécanique', 'traction', 'compression'
        ],
        'Mathématiques': [
            'calcul', 'formule', 'équation', 'trigonométrie', 'pythagore',
            'pourcentage', 'proportion', 'vecteur', 'phaseur', 'complexe'
        ]
    }
    
    # Mots à ignorer
    STOP_WORDS = {
        'le', 'la', 'les', 'un', 'une', 'des', 'de', 'du', 'et', 'ou', 'en', 'à',
        'pour', 'par', 'sur', 'avec', 'dans', 'ce', 'cette', 'ces', 'son', 'sa',
        'ses', 'leur', 'leurs', 'qui', 'que', 'quoi', 'dont', 'où', 'est', 'sont',
        'être', 'avoir', 'faire', 'peut', 'doit', 'faut', 'plus', 'moins', 'très',
        'aussi', 'donc', 'mais', 'car', 'si', 'ne', 'pas', 'tout', 'tous', 'toute',
        'page', 'figure', 'tableau', 'exemple', 'exercice', 'solution', 'chapitre'
    }
    
    def __init__(self, config: dict):
        self.config = config
        self.concepts: List[LocalConcept] = []
        self.concept_counter = Counter()
        
    def analyze_course_document(self, content: str, filename: str, module: Optional[str] = None) -> List[LocalConcept]:
        """Analyse un document et extrait les concepts sans API"""
        
        concepts = []
        
        # Nettoyer le contenu
        content_lower = content.lower()
        
        # Extraire les mots significatifs
        words = re.findall(r'\b[a-zàâäéèêëïîôùûüç]{4,}\b', content_lower)
        word_freq = Counter(words)
        
        # Détecter les concepts par catégorie
        for category, keywords in self.TECHNICAL_KEYWORDS.items():
            found_keywords = []
            total_freq = 0
            
            for keyword in keywords:
                # Chercher le mot-clé dans le contenu
                count = content_lower.count(keyword.lower())
                if count > 0:
                    found_keywords.append(keyword)
                    total_freq += count
            
            if found_keywords:
                # Créer un concept pour cette catégorie dans ce document
                importance = self._calculate_importance(total_freq, len(found_keywords))
                
                concept = LocalConcept(
                    id=f"{module or 'DOC'}_{category}_{len(self.concepts)+1}",
                    name=f"{category} - {module or filename[:20]}",
                    description=f"Concepts de {category.lower()} identifiés dans {filename}",
                    category=category,
                    source_document=filename,
                    source_module=module,
                    importance=importance,
                    keywords=found_keywords[:10],  # Top 10 mots-clés
                    frequency=total_freq
                )
                concepts.append(concept)
                self.concept_counter[category] += total_freq
        
        # Extraire aussi les titres (lignes courtes en majuscules ou avec numérotation)
        title_patterns = [
            r'^[0-9]+[\.\)]\s*([A-ZÀÂÄÉÈÊËÏÎÔÙÛÜÇ][A-Za-zàâäéèêëïîôùûüç\s\-]{5,50})$',
            r'^([A-ZÀÂÄÉÈÊËÏÎÔÙÛÜÇ][A-ZÀÂÄÉÈÊËÏÎÔÙÛÜÇ\s\-]{5,40})$',
        ]
        
        for line in content.split('\n'):
            line = line.strip()
            for pattern in title_patterns:
                match = re.match(pattern, line)
                if match:
                    title = match.group(1).strip()
                    if len(title) > 5 and title.lower() not in self.STOP_WORDS:
                        # C'est probablement un titre de section
                        category = self._guess_category(title)
                        concept = LocalConcept(
                            id=f"{module or 'DOC'}_TITLE_{len(self.concepts)+1}",
                            name=title.title(),
                            description=f"Section: {title}",
                            category=category,
                            source_document=filename,
                            source_module=module,
                            importance='medium',
                            keywords=[title.lower()],
                            frequency=1
                        )
                        concepts.append(concept)
                    break
        
        self.concepts.extend(concepts)
        return concepts
    
    def _calculate_importance(self, frequency: int, keyword_count: int) -> str:
        """Calcule l'importance basée sur la fréquence"""
        score = frequency * (1 + keyword_count * 0.1)
        
        if score > 50:
            return 'critical'
        elif score > 20:
            return 'high'
        elif score > 10:
            return 'medium'
        else:
            return 'low'
    
    def _guess_category(self, text: str) -> str:
        """Devine la catégorie d'un texte"""
        text_lower = text.lower()
        
        for category, keywords in self.TECHNICAL_KEYWORDS.items():
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    return category
        
        return 'Général'
    
    def get_summary(self) -> Dict:
        """Retourne un résumé de l'analyse"""
        return {
            'total_concepts': len(self.concepts),
            'by_category': dict(self.concept_counter),
            'by_importance': {
                'critical': len([c for c in self.concepts if c.importance == 'critical']),
                'high': len([c for c in self.concepts if c.importance == 'high']),
                'medium': len([c for c in self.concepts if c.importance == 'medium']),
                'low': len([c for c in self.concepts if c.importance == 'low']),
            },
            'modules': list(set(c.source_module for c in self.concepts if c.source_module))
        }
    
    def export_concepts(self, filepath: str):
        """Exporte les concepts en JSON"""
        data = {
            'concepts': [
                {
                    'id': c.id,
                    'name': c.name,
                    'description': c.description,
                    'category': c.category,
                    'source_document': c.source_document,
                    'source_module': c.source_module,
                    'importance': c.importance,
                    'keywords': c.keywords,
                    'frequency': c.frequency
                }
                for c in self.concepts
            ],
            'summary': self.get_summary()
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return filepath
