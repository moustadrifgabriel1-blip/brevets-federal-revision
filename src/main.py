#!/usr/bin/env python3
"""
Système de Révision Intelligent
===============================
Point d'entrée principal du système de révision pour le brevet fédéral

Auteur: Gabriel
Brevet Fédéral - Spécialiste Réseaux Énergétiques
"""

import os
import sys
import argparse
from pathlib import Path
from datetime import datetime

import yaml
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.scanner import DocumentScanner
from src.analyzer import ContentAnalyzer
from src.concept_mapper import ConceptMapper
from src.planner import RevisionPlanner

console = Console()


def load_config() -> dict:
    """Charge la configuration"""
    config_path = Path(__file__).parent.parent / "config" / "config.yaml"
    
    if not config_path.exists():
        console.print("[red]❌ Fichier de configuration non trouvé![/red]")
        console.print(f"   Créez le fichier: {config_path}")
        sys.exit(1)
    
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def display_welcome():
    """Affiche le message de bienvenue"""
    welcome_text = """
🎓 [bold blue]SYSTÈME DE RÉVISION INTELLIGENT[/bold blue]
   Brevet Fédéral - Spécialiste Réseaux Énergétiques
   
   Ce système va vous aider à:
   • Scanner et analyser vos cours
   • Identifier les concepts clés et leurs liens
   • Créer un planning de révision optimisé
   • Cibler ce qui est essentiel pour l'examen
    """
    console.print(Panel(welcome_text, border_style="blue"))


def ensure_directories(config: dict):
    """Crée les répertoires nécessaires"""
    directories = [
        config['paths']['cours'],
        config['paths']['directives'],
        config['paths']['planning'],
        config['paths']['exports'],
        Path(config['paths']['database']).parent
    ]
    
    for dir_path in directories:
        Path(dir_path).mkdir(parents=True, exist_ok=True)


def run_scan(config: dict) -> dict:
    """Exécute le scan des documents"""
    console.print("\n[bold]📂 ÉTAPE 1: Scan des documents[/bold]\n")
    
    scanner = DocumentScanner(config)
    results = scanner.scan_all()
    
    if not any(results.values()):
        console.print("[yellow]⚠️  Aucun document trouvé![/yellow]")
        console.print("\nAssurez-vous d'avoir ajouté vos fichiers dans:")
        console.print(f"  • Cours: {config['paths']['cours']}")
        console.print(f"  • Directives: {config['paths']['directives']}")
        console.print(f"  • Planning: {config['paths']['planning']}")
        return None
    
    console.print(scanner.get_summary())
    return {'scanner': scanner, 'results': results}


def run_analysis(config: dict, scan_data: dict) -> dict:
    """Exécute l'analyse IA"""
    console.print("\n[bold]🔬 ÉTAPE 2: Analyse IA des contenus[/bold]\n")
    
    if config['api']['openai_api_key'] == "VOTRE_CLE_API_ICI":
        console.print("[red]❌ Clé API OpenAI non configurée![/red]")
        console.print("   Modifiez config/config.yaml et ajoutez votre clé API")
        return None
    
    analyzer = ContentAnalyzer(config)
    scanner = scan_data['scanner']
    
    all_concepts = []
    all_requirements = []
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        
        # Analyser les cours
        cours_docs = scanner.get_documents_by_category('cours')
        if cours_docs:
            task = progress.add_task("Analyse des cours...", total=len(cours_docs))
            for doc in cours_docs:
                concepts = analyzer.analyze_course_document(
                    doc.content, 
                    doc.filename, 
                    doc.module
                )
                all_concepts.extend(concepts)
                progress.update(task, advance=1)
        
        # Analyser les directives
        directive_docs = scanner.get_documents_by_category('directive')
        if directive_docs:
            task = progress.add_task("Analyse des directives...", total=len(directive_docs))
            for doc in directive_docs:
                requirements = analyzer.analyze_exam_directives(
                    doc.content,
                    doc.filename
                )
                all_requirements.extend(requirements)
                progress.update(task, advance=1)
    
    analyzer.concepts = all_concepts
    analyzer.exam_requirements = all_requirements
    
    console.print(f"\n[green]✅ {len(all_concepts)} concepts extraits[/green]")
    console.print(f"[green]✅ {len(all_requirements)} exigences d'examen identifiées[/green]")
    
    # Mapper concepts aux exigences
    if all_concepts and all_requirements:
        console.print("\n[bold]🔗 Mapping concepts ↔ exigences d'examen...[/bold]")
        mapping = analyzer.map_concepts_to_requirements()
        
        if mapping.get('gaps'):
            console.print(f"\n[yellow]⚠️  {len(mapping['gaps'])} lacunes potentielles détectées[/yellow]")
    
    return {'analyzer': analyzer, 'concepts': all_concepts, 'requirements': all_requirements}


def run_mapping(config: dict, analysis_data: dict) -> dict:
    """Crée la cartographie des concepts"""
    console.print("\n[bold]🗺️  ÉTAPE 3: Cartographie des concepts[/bold]\n")
    
    mapper = ConceptMapper(config)
    mapper.build_from_concepts(analysis_data['concepts'])
    
    # Afficher l'arbre des concepts
    mapper.display_concept_tree()
    
    # Afficher le tableau des priorités
    console.print()
    mapper.display_priority_table()
    
    # Obtenir l'ordre d'apprentissage
    learning_order = mapper.get_learning_order()
    console.print(f"\n[green]✅ Ordre d'apprentissage optimisé pour {len(learning_order)} concepts[/green]")
    
    # Exporter la cartographie
    export_path = Path(config['paths']['exports']) / "concept_map.json"
    mapper.export_to_json(str(export_path))
    
    return {'mapper': mapper, 'learning_order': learning_order}


def run_planning(config: dict, analysis_data: dict, mapping_data: dict) -> dict:
    """Génère le planning de révision"""
    console.print("\n[bold]📅 ÉTAPE 4: Génération du planning[/bold]\n")
    
    planner = RevisionPlanner(config)
    
    # Demander les informations de planning
    exam_date_str = config['user'].get('exam_date', '2026-06-15')
    exam_date = datetime.strptime(exam_date_str, '%Y-%m-%d')
    
    hours_per_week = Prompt.ask(
        "Heures de révision disponibles par semaine",
        default="10"
    )
    
    plan = planner.create_plan(
        concepts=analysis_data['concepts'],
        learning_order=mapping_data['learning_order'],
        course_schedule={},
        exam_date=exam_date,
        available_hours_per_week=float(hours_per_week)
    )
    
    if plan:
        # Afficher le résumé
        planner.display_summary()
        
        # Afficher la première semaine
        console.print("\n[bold]📆 Planning de cette semaine:[/bold]")
        planner.display_weekly_plan(0)
        
        # Exporter les plans
        export_dir = Path(config['paths']['exports'])
        planner.export_plan(str(export_dir / "revision_plan.json"))
        planner.export_to_markdown(str(export_dir / "revision_plan.md"))
    
    return {'planner': planner, 'plan': plan}


def run_full_workflow(config: dict):
    """Exécute le workflow complet"""
    
    # Étape 1: Scan
    scan_data = run_scan(config)
    if not scan_data:
        return
    
    # Étape 2: Analyse
    analysis_data = run_analysis(config, scan_data)
    if not analysis_data:
        return
    
    # Étape 3: Mapping
    mapping_data = run_mapping(config, analysis_data)
    
    # Étape 4: Planning
    planning_data = run_planning(config, analysis_data, mapping_data)
    
    # Résumé final
    console.print("\n" + "=" * 60)
    console.print("[bold green]✅ SYSTÈME DE RÉVISION CONFIGURÉ![/bold green]")
    console.print("=" * 60)
    console.print(f"""
📁 Fichiers générés dans {config['paths']['exports']}:
   • concept_map.json - Cartographie des concepts
   • revision_plan.json - Planning en JSON
   • revision_plan.md - Planning lisible en Markdown

📋 Prochaines étapes:
   1. Consultez revision_plan.md pour votre planning
   2. Suivez l'ordre d'apprentissage recommandé
   3. Cochez les sessions complétées
   4. Relancez l'analyse si vous ajoutez de nouveaux cours
    """)


def interactive_menu(config: dict):
    """Menu interactif"""
    
    while True:
        console.print("\n[bold]📋 MENU PRINCIPAL[/bold]\n")
        console.print("1. 🔄 Exécuter le workflow complet")
        console.print("2. 📂 Scanner les documents uniquement")
        console.print("3. 🔬 Analyser les contenus")
        console.print("4. 🗺️  Voir la cartographie des concepts")
        console.print("5. 📅 Générer un nouveau planning")
        console.print("6. 📊 Voir le planning actuel")
        console.print("7. ⚙️  Configuration")
        console.print("8. ❌ Quitter")
        
        choice = Prompt.ask("\nVotre choix", choices=["1", "2", "3", "4", "5", "6", "7", "8"])
        
        if choice == "1":
            run_full_workflow(config)
        elif choice == "2":
            run_scan(config)
        elif choice == "3":
            console.print("[yellow]Lancez d'abord le scan (option 1 ou 2)[/yellow]")
        elif choice == "4":
            export_path = Path(config['paths']['exports']) / "concept_map.json"
            if export_path.exists():
                import json
                with open(export_path) as f:
                    data = json.load(f)
                console.print(f"\n📊 {len(data.get('nodes', []))} concepts cartographiés")
                console.print(f"📚 Catégories: {list(data.get('categories', {}).keys())}")
            else:
                console.print("[yellow]Aucune cartographie. Lancez l'analyse d'abord.[/yellow]")
        elif choice == "5":
            console.print("[yellow]Lancez d'abord le workflow complet (option 1)[/yellow]")
        elif choice == "6":
            plan_path = Path(config['paths']['exports']) / "revision_plan.md"
            if plan_path.exists():
                console.print(f"\n📄 Ouvrez {plan_path} pour voir votre planning")
            else:
                console.print("[yellow]Aucun planning. Lancez le workflow complet.[/yellow]")
        elif choice == "7":
            console.print(f"\n⚙️  Configuration actuelle:")
            console.print(f"   • API Model: {config['api']['model']}")
            console.print(f"   • Cours: {config['paths']['cours']}")
            console.print(f"   • Directives: {config['paths']['directives']}")
            console.print(f"   • Date examen: {config['user'].get('exam_date', 'Non définie')}")
        elif choice == "8":
            console.print("\n[bold blue]Au revoir et bon courage pour vos révisions! 📚[/bold blue]\n")
            break


def main():
    """Point d'entrée principal"""
    
    parser = argparse.ArgumentParser(
        description="Système de Révision Intelligent - Brevet Fédéral"
    )
    parser.add_argument('--scan', action='store_true', help='Scanner les documents uniquement')
    parser.add_argument('--analyze', action='store_true', help='Analyser les contenus')
    parser.add_argument('--plan', action='store_true', help='Générer le planning')
    parser.add_argument('--full', action='store_true', help='Exécuter le workflow complet')
    
    args = parser.parse_args()
    
    # Charger la configuration
    config = load_config()
    
    # S'assurer que les répertoires existent
    ensure_directories(config)
    
    # Afficher le message de bienvenue
    display_welcome()
    
    # Exécuter selon les arguments
    if args.scan:
        run_scan(config)
    elif args.analyze:
        console.print("[yellow]Utilisez --full pour l'analyse complète[/yellow]")
    elif args.plan:
        console.print("[yellow]Utilisez --full pour générer le planning[/yellow]")
    elif args.full:
        run_full_workflow(config)
    else:
        # Mode interactif
        interactive_menu(config)


if __name__ == "__main__":
    main()
