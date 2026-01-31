"""
Cartographie des Concepts
=========================
Crée une carte visuelle des relations entre concepts
"""

import json
from typing import Dict, List, Optional, Set
from dataclasses import dataclass
from pathlib import Path

from rich.console import Console
from rich.tree import Tree
from rich.panel import Panel
from rich.table import Table

console = Console()


@dataclass 
class ConceptNode:
    """Nœud dans le graphe de concepts"""
    id: str
    name: str
    category: str
    importance: str
    exam_relevant: bool
    prerequisites: Set[str]
    dependents: Set[str]  # Concepts qui dépendent de celui-ci
    module: Optional[str]
    

class ConceptMapper:
    """Crée et gère la cartographie des concepts"""
    
    def __init__(self, config: dict):
        self.config = config
        self.nodes: Dict[str, ConceptNode] = {}
        self.categories: Dict[str, List[str]] = {}
        
    def build_from_concepts(self, concepts: list) -> None:
        """Construit le graphe à partir des concepts analysés"""
        
        # Créer les nœuds
        for concept in concepts:
            node = ConceptNode(
                id=concept.id,
                name=concept.name,
                category=concept.category,
                importance=concept.importance,
                exam_relevant=concept.exam_relevant,
                prerequisites=set(concept.prerequisites),
                dependents=set(),
                module=concept.source_module
            )
            self.nodes[concept.name.lower()] = node
            
            # Organiser par catégorie
            if concept.category not in self.categories:
                self.categories[concept.category] = []
            self.categories[concept.category].append(concept.name)
        
        # Construire les liens de dépendance inverse
        for node in self.nodes.values():
            for prereq_name in node.prerequisites:
                prereq_key = prereq_name.lower()
                if prereq_key in self.nodes:
                    self.nodes[prereq_key].dependents.add(node.name)
    
    def get_learning_order(self) -> List[str]:
        """Retourne l'ordre optimal d'apprentissage (tri topologique)"""
        
        in_degree = {name: len(node.prerequisites) for name, node in self.nodes.items()}
        queue = [name for name, degree in in_degree.items() if degree == 0]
        result = []
        
        while queue:
            # Trier par importance pour les concepts sans prérequis restants
            queue.sort(key=lambda n: {
                'critical': 0, 'high': 1, 'medium': 2, 'low': 3
            }.get(self.nodes[n].importance, 3))
            
            current = queue.pop(0)
            result.append(self.nodes[current].name)
            
            for dependent_name in self.nodes[current].dependents:
                dep_key = dependent_name.lower()
                if dep_key in in_degree:
                    in_degree[dep_key] -= 1
                    if in_degree[dep_key] == 0:
                        queue.append(dep_key)
        
        return result
    
    def get_prerequisites_chain(self, concept_name: str) -> List[str]:
        """Retourne la chaîne complète de prérequis pour un concept"""
        
        concept_key = concept_name.lower()
        if concept_key not in self.nodes:
            return []
        
        chain = []
        visited = set()
        
        def traverse(name: str):
            if name in visited:
                return
            visited.add(name)
            
            node = self.nodes.get(name.lower())
            if node:
                for prereq in node.prerequisites:
                    traverse(prereq.lower())
                chain.append(node.name)
        
        traverse(concept_key)
        return chain[:-1]  # Exclure le concept lui-même
    
    def get_impact_analysis(self, concept_name: str) -> Dict:
        """Analyse l'impact d'un concept - ce qui dépend de lui"""
        
        concept_key = concept_name.lower()
        if concept_key not in self.nodes:
            return {"error": "Concept non trouvé"}
        
        node = self.nodes[concept_key]
        
        # Trouver tous les concepts qui dépendent directement ou indirectement
        all_dependents = set()
        
        def find_dependents(name: str):
            n = self.nodes.get(name.lower())
            if n:
                for dep in n.dependents:
                    if dep not in all_dependents:
                        all_dependents.add(dep)
                        find_dependents(dep)
        
        find_dependents(concept_key)
        
        return {
            "concept": node.name,
            "direct_dependents": list(node.dependents),
            "all_dependents": list(all_dependents),
            "impact_score": len(all_dependents),
            "is_foundational": len(all_dependents) > 5
        }
    
    def display_concept_tree(self, root_concept: str = None) -> None:
        """Affiche l'arbre des concepts dans le terminal"""
        
        if root_concept:
            # Afficher l'arbre d'un concept spécifique
            tree = Tree(f"🎯 [bold]{root_concept}[/bold]")
            self._add_dependents_to_tree(root_concept, tree, set())
            console.print(tree)
        else:
            # Afficher par catégorie
            main_tree = Tree("📚 [bold]Cartographie des Concepts[/bold]")
            
            for category, concepts in self.categories.items():
                cat_branch = main_tree.add(f"📁 [cyan]{category}[/cyan]")
                for concept_name in concepts:
                    node = self.nodes.get(concept_name.lower())
                    if node:
                        importance_icon = {
                            'critical': '🔴',
                            'high': '🟠',
                            'medium': '🟡',
                            'low': '🟢'
                        }.get(node.importance, '⚪')
                        
                        exam_icon = '📝' if node.exam_relevant else ''
                        cat_branch.add(f"{importance_icon} {concept_name} {exam_icon}")
            
            console.print(main_tree)
    
    def _add_dependents_to_tree(self, concept_name: str, tree: Tree, visited: set) -> None:
        """Ajoute récursivement les dépendants à l'arbre"""
        
        if concept_name in visited:
            return
        visited.add(concept_name)
        
        node = self.nodes.get(concept_name.lower())
        if node:
            for dep in node.dependents:
                dep_node = self.nodes.get(dep.lower())
                if dep_node:
                    importance_icon = {'critical': '🔴', 'high': '🟠', 'medium': '🟡', 'low': '🟢'}.get(dep_node.importance, '⚪')
                    branch = tree.add(f"{importance_icon} {dep}")
                    self._add_dependents_to_tree(dep, branch, visited)
    
    def display_priority_table(self) -> None:
        """Affiche un tableau des concepts par priorité"""
        
        table = Table(title="📋 Concepts par Priorité")
        table.add_column("Priorité", style="bold")
        table.add_column("Concept", style="cyan")
        table.add_column("Catégorie")
        table.add_column("Prérequis", style="dim")
        table.add_column("Impact", justify="right")
        table.add_column("Examen", justify="center")
        
        # Trier par importance puis par impact
        sorted_nodes = sorted(
            self.nodes.values(),
            key=lambda n: (
                {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}.get(n.importance, 3),
                -len(n.dependents)
            )
        )
        
        priority_styles = {
            'critical': '[red]CRITIQUE[/red]',
            'high': '[orange1]HAUTE[/orange1]',
            'medium': '[yellow]MOYENNE[/yellow]',
            'low': '[green]BASSE[/green]'
        }
        
        for node in sorted_nodes[:30]:  # Limiter à 30 pour la lisibilité
            prereqs = ", ".join(list(node.prerequisites)[:3])
            if len(node.prerequisites) > 3:
                prereqs += "..."
            
            table.add_row(
                priority_styles.get(node.importance, node.importance),
                node.name,
                node.category,
                prereqs or "-",
                str(len(node.dependents)),
                "✅" if node.exam_relevant else ""
            )
        
        console.print(table)
    
    def find_knowledge_gaps(self, known_concepts: List[str]) -> List[Dict]:
        """Identifie les lacunes de connaissances"""
        
        known_set = {c.lower() for c in known_concepts}
        gaps = []
        
        for name, node in self.nodes.items():
            if name not in known_set:
                # Vérifier si c'est un prérequis pour quelque chose qu'on veut apprendre
                missing_prereqs = [p for p in node.prerequisites if p.lower() not in known_set]
                
                if node.exam_relevant or len(node.dependents) > 0:
                    gaps.append({
                        "concept": node.name,
                        "importance": node.importance,
                        "exam_relevant": node.exam_relevant,
                        "blocking_count": len(node.dependents),
                        "missing_prereqs": missing_prereqs,
                        "ready_to_learn": len(missing_prereqs) == 0
                    })
        
        # Trier par importance et par nombre de concepts bloqués
        gaps.sort(key=lambda g: (
            {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}.get(g['importance'], 3),
            -g['blocking_count']
        ))
        
        return gaps
    
    def export_to_json(self, filepath: str) -> None:
        """Exporte la cartographie en JSON"""
        
        data = {
            "nodes": [
                {
                    "id": node.id,
                    "name": node.name,
                    "category": node.category,
                    "importance": node.importance,
                    "exam_relevant": node.exam_relevant,
                    "prerequisites": list(node.prerequisites),
                    "dependents": list(node.dependents),
                    "module": node.module
                }
                for node in self.nodes.values()
            ],
            "categories": self.categories,
            "learning_order": self.get_learning_order()
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        console.print(f"[green]✅ Cartographie exportée vers {filepath}[/green]")
    
    def generate_mermaid_diagram(self) -> str:
        """Génère un diagramme Mermaid des concepts"""
        
        lines = ["graph TD"]
        
        # Ajouter les nœuds avec style selon l'importance
        for name, node in self.nodes.items():
            safe_name = name.replace(" ", "_").replace("-", "_")
            
            if node.importance == 'critical':
                lines.append(f'    {safe_name}["{node.name}"]:::critical')
            elif node.importance == 'high':
                lines.append(f'    {safe_name}["{node.name}"]:::high')
            else:
                lines.append(f'    {safe_name}["{node.name}"]')
        
        # Ajouter les liens
        for name, node in self.nodes.items():
            safe_name = name.replace(" ", "_").replace("-", "_")
            for prereq in node.prerequisites:
                safe_prereq = prereq.lower().replace(" ", "_").replace("-", "_")
                if safe_prereq in [n.replace(" ", "_").replace("-", "_") for n in self.nodes.keys()]:
                    lines.append(f'    {safe_prereq} --> {safe_name}')
        
        # Styles
        lines.append('')
        lines.append('    classDef critical fill:#ff6b6b,stroke:#c92a2a')
        lines.append('    classDef high fill:#ffa94d,stroke:#d9480f')
        
        return "\n".join(lines)


if __name__ == "__main__":
    # Test du mapper
    from dataclasses import dataclass
    
    @dataclass
    class MockConcept:
        id: str
        name: str
        category: str
        importance: str
        exam_relevant: bool
        prerequisites: list
        source_module: str = None
    
    # Créer des concepts de test
    test_concepts = [
        MockConcept("1", "Loi d'Ohm", "Électricité de base", "critical", True, []),
        MockConcept("2", "Puissance électrique", "Électricité de base", "critical", True, ["Loi d'Ohm"]),
        MockConcept("3", "Transformateur", "Équipements", "high", True, ["Puissance électrique", "Magnétisme"]),
        MockConcept("4", "Magnétisme", "Physique", "high", False, []),
        MockConcept("5", "Protection différentielle", "Sécurité", "critical", True, ["Transformateur"]),
    ]
    
    mapper = ConceptMapper({})
    mapper.build_from_concepts(test_concepts)
    
    mapper.display_concept_tree()
    mapper.display_priority_table()
    
    print("\nOrdre d'apprentissage:", mapper.get_learning_order())
    print("\nChaîne de prérequis pour 'Protection différentielle':", 
          mapper.get_prerequisites_chain("Protection différentielle"))
