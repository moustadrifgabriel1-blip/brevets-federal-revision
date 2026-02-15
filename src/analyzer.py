"""
Analyseur IA de Contenu
=======================
Utilise l'IA pour analyser les cours et les directives d'examen
"""

import json
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import time

import google.generativeai as genai
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel

console = Console()


@dataclass
class Concept:
    """Représente un concept extrait des cours"""
    id: str
    name: str
    description: str
    category: str
    source_document: str
    source_module: Optional[str]
    importance: str  # 'critical', 'high', 'medium', 'low'
    prerequisites: List[str] = field(default_factory=list)  # IDs des concepts prérequis
    related_concepts: List[str] = field(default_factory=list)
    exam_relevant: bool = False
    exam_topics: List[str] = field(default_factory=list)  # Liens avec directives d'examen
    # Références pour retrouver le contenu facilement
    page_references: str = ""  # Ex: "p.5-8" ou "Chapitre 2" ou "Section 3.1"
    keywords: List[str] = field(default_factory=list)  # Mots-clés pour recherche rapide


@dataclass
class ExamRequirement:
    """Représente une exigence des directives d'examen"""
    id: str
    topic: str
    description: str
    competency_level: str  # Ce qu'on attend du candidat
    related_concepts: List[str] = field(default_factory=list)
    source_document: str = ""


class ContentAnalyzer:
    """Analyse le contenu avec l'IA pour extraire concepts et liens"""
    
    def __init__(self, config: dict):
        self.config = config
        # Configuration de Google Gemini
        import os
        api_key = config['api'].get('gemini_api_key') or os.getenv('GOOGLE_API_KEY')
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(config['api']['model'])
        self.generation_config = genai.types.GenerationConfig(
            temperature=config['api']['temperature'],
            response_mime_type="application/json"
        )
        self.concepts: List[Concept] = []
        
        # Orientation et contexte d'examen
        self.orientation = config.get('formation', {}).get('orientation', 'Énergie')
        self.directives_loaded = False
        self.exam_context = ""
        self.exam_requirements: List[ExamRequirement] = []
    
    def load_directives_context(self, directives_content: str):
        """Charge le contexte des directives d'examen pour guider l'analyse"""
        self.exam_context = directives_content[:8000]  # Limite pour le contexte
        self.directives_loaded = True
        
    def analyze_course_document(self, content: str, filename: str, module: Optional[str] = None) -> List[Concept]:
        """Analyse un document de cours et extrait les concepts clés"""
        
        # Contexte des directives d'examen si disponible
        directives_section = ""
        if self.directives_loaded and self.exam_context:
            directives_section = f"""
CONTEXTE DIRECTIVES D'EXAMEN:
Les concepts doivent être évalués selon leur pertinence pour l'examen du Brevet Fédéral.
Orientation: {self.orientation}
Critères d'évaluation clés extraits des directives:
{self.exam_context[:3000]}
"""
        
        prompt = f"""Tu es un expert en formation professionnelle pour les spécialistes de réseaux énergétiques en Suisse.
Tu analyses des documents de cours pour le BREVET FÉDÉRAL - Spécialiste de Réseau orientation {self.orientation}.

CONTEXTE MÉTIER — Orientation Énergie :
Le spécialiste de réseau orientation Énergie travaille sur les RÉSEAUX DE DISTRIBUTION ÉLECTRIQUE :
- Réseaux moyenne tension (MT, 1-36 kV) et basse tension (BT, 230/400V)
- Lignes aériennes (supports, conducteurs ACSR, isolateurs) et câbles souterrains (pose, jonctions)
- Postes de transformation MT/BT
- Installations de mise à terre et schémas de liaison (TN, TT, IT)
- Éclairage public (LED, normes EN 13201)
- Appareillage de protection et de coupure (disjoncteurs, fusibles, DDR, sectionneurs)
- Technique de mesure (mégohmmètre, boucle de défaut, résistance de terre, réflectométrie TDR)
- Consignation/déconsignation, 5 règles de sécurité, travaux sous tension (TST)
- Normes suisses : NIBT, OIBT, OLEI, ESTI, SUVA, EN 50341, SIA 261

OBJECTIF: Extraire les concepts clés PERTINENTS pour un futur spécialiste de réseau orientation Énergie.

VOCABULAIRE TECHNIQUE à identifier en priorité :
- Termes métier : consignation, déconsignation, sectionneur de terre, DDR, mégohmmètre, réenclencheur, boucle de défaut, sélectivité, coordination des protections
- Grandeurs physiques : courant de court-circuit (Ik), chute de tension (ΔU), résistance d'isolement, impédance de boucle (Zs), cos φ
- Équipements : transformateur MT/BT, cellule MT, tableau BT, câble XPE/PVC, conducteur ACSR, isolateur composite
- Normes clés : NIBT, OIBT, OLEI, ESTI (ordonnances), EN 50341, EN 13201, SIA 261, IEC 60502

DOCUMENT: {filename}
MODULE: {module or 'Non spécifié'}
ORIENTATION: {self.orientation}
{directives_section}

CONTENU DU COURS:
{content[:12000]}

INSTRUCTIONS:
1. Identifie les concepts techniques essentiels pour l'orientation {self.orientation}
2. Priorise les concepts qui correspondent aux critères d'évaluation de l'examen
3. Extrais le VOCABULAIRE TECHNIQUE PRÉCIS (pas de termes vagues ou génériques)
4. Identifie les VALEURS NUMÉRIQUES CLÉS (seuils, distances, tensions, courants, normes)
5. Pour chaque concept, détermine:
   - Son importance (critical si mentionné dans directives, high si fondamental, medium si utile, low si secondaire)
   - Les prérequis nécessaires
   - Si le concept est susceptible d'être évalué à l'examen (exam_relevant: true/false)
   - Les mots-clés TECHNIQUES PRÉCIS (pas de mots génériques comme "important" ou "essentiel")

Réponds en JSON avec cette structure:
{{
    "concepts": [
        {{
            "name": "Nom TECHNIQUE PRÉCIS du concept (ex: 'Résistance d'isolement' et non 'Mesures')",
            "description": "Description claire avec les valeurs/seuils/normes si applicable",
            "category": "Catégorie technique parmi : Électrotechnique, Réseaux de distribution, Sécurité au travail, Normes et réglementation, Technique de mesure, Maintenance, Technique de protection, Gestion de projet, Mise à terre et liaison, Éclairage public, Documentation et plans, Formation professionnelle, Conduite d'équipe",
            "importance": "critical|high|medium|low",
            "exam_relevant": true,
            "prerequisites": ["Concept prérequis 1", "Concept prérequis 2"],
            "related_concepts": ["Concept lié 1", "Concept lié 2"],
            "key_points": ["Point clé 1 avec valeur/norme", "Point clé 2 avec valeur/norme"],
            "page_references": "Pages ou sections où trouver ce concept (ex: p.5-8, Chapitre 2, Section 3.1)",
            "keywords": ["terme-technique-1", "terme-technique-2", "NORME-applicable"]
        }}
    ]
}}

ANTI-PATTERNS à éviter :
- NE PAS créer de concepts vagues ("Introduction", "Généralités", "Bases")
- NE PAS inclure de mots-clés génériques ("important", "essentiel", "fondamental")  
- NE PAS mélanger plusieurs concepts distincts dans un seul
- Chaque concept doit être ACTIONNABLE pour la révision

Concentre-toi sur les concepts vraiment importants pour un futur spécialiste de réseaux énergétiques."""

        try:
            # Délai de 2s entre requêtes pour éviter rate limiting
            time.sleep(3)
            
            response = self.model.generate_content(
                prompt,
                generation_config=self.generation_config
            )
            
            result = json.loads(response.text)
            concepts = []
            
            for i, c in enumerate(result.get('concepts', [])):
                concept = Concept(
                    id=f"{filename}_{i}",
                    name=c['name'],
                    description=c['description'],
                    category=c.get('category', 'Général'),
                    source_document=filename,
                    source_module=module,
                    importance=c.get('importance', 'medium'),
                    prerequisites=c.get('prerequisites', []),
                    related_concepts=c.get('related_concepts', []),
                    page_references=c.get('page_references', ''),
                    keywords=c.get('keywords', [])
                )
                concepts.append(concept)
            
            return concepts
            
        except Exception as e:
            console.print(f"[red]❌ Erreur d'analyse pour {filename}: {e}[/red]")
            return []
    
    def analyze_exam_directives(self, content: str, filename: str) -> List[ExamRequirement]:
        """Analyse les directives d'examen"""
        
        prompt = f"""Tu es un expert en formation professionnelle pour les spécialistes de réseaux énergétiques en Suisse.

Analyse ces directives d'examen et extrais les exigences clés.

DOCUMENT: {filename}

CONTENU:
{content[:15000]}

INSTRUCTIONS:
1. Identifie chaque compétence ou sujet évalué
2. Pour chaque exigence, détermine:
   - Le sujet principal
   - Ce qui est attendu du candidat
   - Le niveau de compétence requis

Réponds en JSON avec cette structure:
{{
    "requirements": [
        {{
            "topic": "Sujet de l'exigence",
            "description": "Description détaillée de ce qui est attendu",
            "competency_level": "Ce que le candidat doit être capable de faire",
            "keywords": ["mot-clé 1", "mot-clé 2"]
        }}
    ]
}}

Sois précis et exhaustif - c'est crucial pour la préparation à l'examen."""

        try:
            # Délai de 2s entre requêtes pour éviter rate limiting
            time.sleep(3)
            
            response = self.model.generate_content(
                prompt,
                generation_config=self.generation_config
            )
            
            result = json.loads(response.text)
            requirements = []
            
            for i, r in enumerate(result.get('requirements', [])):
                req = ExamRequirement(
                    id=f"req_{i}",
                    topic=r['topic'],
                    description=r['description'],
                    competency_level=r.get('competency_level', ''),
                    source_document=filename
                )
                requirements.append(req)
            
            return requirements
            
        except Exception as e:
            console.print(f"[red]❌ Erreur d'analyse des directives: {e}[/red]")
            return []
    
    def map_concepts_to_requirements(self) -> Dict[str, List[str]]:
        """Fait correspondre les concepts des cours aux exigences d'examen"""
        
        if not self.concepts or not self.exam_requirements:
            return {}
        
        concepts_text = "\n".join([
            f"- {c.name}: {c.description}" for c in self.concepts
        ])
        
        requirements_text = "\n".join([
            f"- {r.topic}: {r.description}" for r in self.exam_requirements
        ])
        
        prompt = f"""Tu dois faire correspondre les concepts de cours aux exigences d'examen.

CONCEPTS DES COURS:
{concepts_text}

EXIGENCES D'EXAMEN:
{requirements_text}

Pour chaque exigence d'examen, identifie quels concepts des cours sont nécessaires.
Identifie aussi les concepts MANQUANTS (exigences non couvertes par les cours).

Réponds en JSON:
{{
    "mappings": [
        {{
            "requirement": "Nom de l'exigence",
            "required_concepts": ["Concept 1", "Concept 2"],
            "coverage": "complete|partial|missing",
            "notes": "Observations éventuelles"
        }}
    ],
    "gaps": [
        {{
            "requirement": "Exigence non couverte",
            "missing_knowledge": "Ce qui manque dans les cours"
        }}
    ],
    "priorities": [
        {{
            "concept": "Nom du concept",
            "reason": "Pourquoi c'est prioritaire",
            "urgency": "critical|high|medium|low"
        }}
    ]
}}"""

        try:
            # Délai de 2s entre requêtes pour éviter rate limiting
            time.sleep(3)
            
            response = self.model.generate_content(
                prompt,
                generation_config=self.generation_config
            )
            
            result = json.loads(response.text)
            
            # Mise à jour des concepts avec leur pertinence pour l'examen
            for mapping in result.get('mappings', []):
                for concept_name in mapping.get('required_concepts', []):
                    for concept in self.concepts:
                        if concept.name.lower() == concept_name.lower():
                            concept.exam_relevant = True
                            concept.exam_topics.append(mapping['requirement'])
            
            return result
            
        except Exception as e:
            console.print(f"[red]❌ Erreur de mapping: {e}[/red]")
            return {}
    
    def identify_learning_path(self) -> List[Dict]:
        """Identifie l'ordre optimal d'apprentissage basé sur les prérequis"""
        
        # Tri topologique des concepts basé sur les prérequis
        sorted_concepts = []
        visited = set()
        
        def get_concept_by_name(name: str) -> Optional[Concept]:
            for c in self.concepts:
                if c.name.lower() == name.lower():
                    return c
            return None
        
        def visit(concept: Concept, path: List[str] = None):
            if path is None:
                path = []
            
            if concept.id in visited:
                return
            
            if concept.id in path:
                # Cycle détecté, on ignore
                return
            
            path.append(concept.id)
            
            # Visiter d'abord les prérequis
            for prereq_name in concept.prerequisites:
                prereq = get_concept_by_name(prereq_name)
                if prereq:
                    visit(prereq, path.copy())
            
            visited.add(concept.id)
            sorted_concepts.append(concept)
        
        # Trier par importance d'abord
        priority_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
        sorted_by_importance = sorted(
            self.concepts,
            key=lambda c: priority_order.get(c.importance, 3)
        )
        
        for concept in sorted_by_importance:
            visit(concept)
        
        # Construire le chemin d'apprentissage
        learning_path = []
        for concept in sorted_concepts:
            learning_path.append({
                "concept": concept.name,
                "description": concept.description,
                "category": concept.category,
                "importance": concept.importance,
                "prerequisites": concept.prerequisites,
                "exam_relevant": concept.exam_relevant,
                "source": concept.source_document,
                "module": concept.source_module
            })
        
        return learning_path
    
    def generate_study_recommendations(self) -> str:
        """Génère des recommandations d'étude personnalisées"""
        
        if not self.concepts:
            return "Aucun concept analysé. Veuillez d'abord scanner et analyser vos cours."
        
        # Statistiques
        critical_count = len([c for c in self.concepts if c.importance == 'critical'])
        exam_relevant_count = len([c for c in self.concepts if c.exam_relevant])
        
        recommendations = []
        recommendations.append("=" * 60)
        recommendations.append("📚 RECOMMANDATIONS D'ÉTUDE PERSONNALISÉES")
        recommendations.append("=" * 60)
        
        recommendations.append(f"\n📊 STATISTIQUES:")
        recommendations.append(f"  • Concepts totaux analysés: {len(self.concepts)}")
        recommendations.append(f"  • Concepts critiques: {critical_count}")
        recommendations.append(f"  • Concepts liés aux examens: {exam_relevant_count}")
        
        recommendations.append(f"\n🎯 PRIORITÉS ABSOLUES:")
        for concept in self.concepts:
            if concept.importance == 'critical' and concept.exam_relevant:
                recommendations.append(f"  ⭐ {concept.name}")
                recommendations.append(f"     → {concept.description[:100]}...")
                if concept.prerequisites:
                    recommendations.append(f"     📋 Prérequis: {', '.join(concept.prerequisites)}")
        
        recommendations.append(f"\n⚠️  ATTENTION - Prérequis à maîtriser:")
        prereq_mentions = {}
        for concept in self.concepts:
            for prereq in concept.prerequisites:
                prereq_mentions[prereq] = prereq_mentions.get(prereq, 0) + 1
        
        sorted_prereqs = sorted(prereq_mentions.items(), key=lambda x: x[1], reverse=True)
        for prereq, count in sorted_prereqs[:10]:
            recommendations.append(f"  • {prereq} (requis par {count} concepts)")
        
        return "\n".join(recommendations)


if __name__ == "__main__":
    import yaml
    
    with open("config/config.yaml", 'r') as f:
        config = yaml.safe_load(f)
    
    analyzer = ContentAnalyzer(config)
    # Test avec du contenu exemple
    test_content = """
    Introduction aux réseaux électriques
    
    1. Les fondamentaux de l'électricité
    - Tension (V): différence de potentiel électrique
    - Courant (A): flux d'électrons
    - Puissance (W): P = U × I
    
    2. Les transformateurs
    Un transformateur permet de modifier la tension d'un réseau.
    Prérequis: comprendre la loi d'Ohm et le magnétisme.
    """
    
    concepts = analyzer.analyze_course_document(test_content, "test.pdf", "Module1")
    for c in concepts:
        print(f"Concept: {c.name} ({c.importance})")
