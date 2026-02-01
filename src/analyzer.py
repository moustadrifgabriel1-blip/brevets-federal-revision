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
        genai.configure(api_key=config['api']['gemini_api_key'])
        self.model = genai.GenerativeModel(config['api']['model'])
        self.generation_config = genai.types.GenerationConfig(
            temperature=config['api']['temperature'],
            response_mime_type="application/json"
        )
        self.concepts: List[Concept] = []
        self.exam_requirements: List[ExamRequirement] = []
        
    def analyze_course_document(self, content: str, filename: str, module: Optional[str] = None) -> List[Concept]:
        """Analyse un document de cours et extrait les concepts clés"""
        
        prompt = f"""Tu es un expert en formation professionnelle pour les spécialistes de réseaux énergétiques en Suisse.

Analyse ce document de cours et extrais les concepts clés pour un étudiant préparant le brevet fédéral.

DOCUMENT: {filename}
MODULE: {module or 'Non spécifié'}

CONTENU:
{content[:15000]}  # Limite pour le contexte

INSTRUCTIONS:
1. Identifie les concepts techniques essentiels
2. Pour chaque concept, détermine:
   - Son importance (critical/high/medium/low)
   - Les prérequis nécessaires pour le comprendre
   - Les concepts liés

Réponds en JSON avec cette structure:
{{
    "concepts": [
        {{
            "name": "Nom du concept",
            "description": "Description claire et concise",
            "category": "Catégorie technique",
            "importance": "critical|high|medium|low",
            "prerequisites": ["Concept prérequis 1", "Concept prérequis 2"],
            "related_concepts": ["Concept lié 1", "Concept lié 2"],
            "key_points": ["Point clé 1", "Point clé 2"]
        }}
    ]
}}

Concentre-toi sur les concepts vraiment importants pour un futur spécialiste de réseaux énergétiques."""

        try:
            # Délai de 2s entre requêtes pour éviter rate limiting
            time.sleep(2)
            
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
                    related_concepts=c.get('related_concepts', [])
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
            time.sleep(2)
            
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
            time.sleep(2)
            
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
