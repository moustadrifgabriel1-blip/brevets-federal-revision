"""
Générateur de Planning de Révision
==================================
Crée un planning de révision optimisé basé sur les analyses
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from pathlib import Path

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress

console = Console()


@dataclass
class StudySession:
    """Représente une session d'étude planifiée"""
    date: datetime
    duration_minutes: int
    concepts: List[str]
    objectives: List[str]
    session_type: str  # 'new_learning', 'revision', 'practice'
    priority: str
    module: Optional[str] = None
    completed: bool = False
    notes: str = ""


@dataclass
class StudyPlan:
    """Plan d'étude complet"""
    created_at: datetime
    exam_date: datetime
    sessions: List[StudySession] = field(default_factory=list)
    total_hours: float = 0
    concepts_covered: List[str] = field(default_factory=list)
    milestones: List[Dict] = field(default_factory=list)


class RevisionPlanner:
    """Génère des plannings de révision intelligents"""
    
    def __init__(self, config: dict):
        self.config = config
        self.plan: Optional[StudyPlan] = None
        
    def create_plan(
        self,
        concepts: list,
        learning_order: List[str],
        course_schedule: Dict[str, datetime],
        exam_date: datetime,
        available_hours_per_week: float = 10,
        course_schedule_manager = None
    ) -> StudyPlan:
        """
        Crée un plan d'étude complet en tenant compte du planning de cours
        
        Args:
            concepts: Liste des concepts extraits
            learning_order: Ordre d'apprentissage recommandé
            course_schedule: Dictionnaire module -> date de cours
            exam_date: Date de l'examen
            available_hours_per_week: Heures disponibles par semaine pour révisions
            course_schedule_manager: Gestionnaire du planning de cours
        """
        
        today = datetime.now()
        days_until_exam = (exam_date - today).days
        
        if days_until_exam <= 0:
            console.print("[red]⚠️  La date d'examen est passée ou aujourd'hui![/red]")
            return None
        
        console.print(Panel(
            f"📅 Création du planning de révision\n"
            f"   Jours restants: {days_until_exam}\n"
            f"   Concepts à couvrir: {len(learning_order)}\n"
            f"   Heures/semaine: {available_hours_per_week}",
            title="🎯 Planification"
        ))
        
        self.plan = StudyPlan(
            created_at=today,
            exam_date=exam_date
        )
        
        # Filtrer les concepts selon le planning de cours
        if course_schedule_manager:
            concepts = self._filter_concepts_by_course_schedule(concepts, course_schedule_manager)
            console.print(f"   ℹ️  {len(concepts)} concepts prêts à réviser (cours déjà vus)")
        
        # Calculer le temps disponible
        weeks_available = days_until_exam / 7
        total_hours = weeks_available * available_hours_per_week
        
        # Diviser le temps: 60% apprentissage, 30% révision, 10% pratique
        learning_hours = total_hours * 0.60
        revision_hours = total_hours * 0.30
        practice_hours = total_hours * 0.10
        
        # Créer les sessions d'apprentissage
        self._create_learning_sessions(
            concepts, 
            learning_order, 
            learning_hours, 
            today, 
            exam_date,
            course_schedule_manager
        )
        
        # Ajouter les sessions de révision (répétition espacée)
        self._add_spaced_repetition(revision_hours)
        
        # Ajouter les sessions de pratique avant l'examen
        self._add_practice_sessions(practice_hours, exam_date)
        
        # Créer les jalons
        self._create_milestones(exam_date)
        
        # Calculer les statistiques
        self.plan.total_hours = sum(s.duration_minutes / 60 for s in self.plan.sessions)
        self.plan.concepts_covered = learning_order
        
        return self.plan
    
    def _filter_concepts_by_course_schedule(self, concepts: list, course_schedule_manager) -> list:
        """
        Filtre les concepts selon ce qui a déjà été vu en cours
        Retourne uniquement les concepts des modules déjà commencés
        """
        if not course_schedule_manager:
            return concepts
        
        now = datetime.now()
        filtered = []
        skipped = []
        
        for concept in concepts:
            module = concept.source_module
            
            if not module:
                # Pas de module associé, on garde le concept
                filtered.append(concept)
                continue
            
            # Vérifier si le module a commencé
            if course_schedule_manager.is_module_started(module, now):
                filtered.append(concept)
            else:
                skipped.append((concept, module))
        
        if skipped:
            console.print(f"\n   ℹ️  {len(skipped)} concepts ignorés (modules pas encore vus en cours):")
            modules_skipped = set(m for _, m in skipped)
            for module in sorted(modules_skipped):
                console.print(f"      • {module}")
        
        return filtered
    
    def _create_learning_sessions(
        self,
        concepts: list,
        learning_order: List[str],
        total_hours: float,
        start_date: datetime,
        end_date: datetime,
        course_schedule_manager = None
    ) -> None:
        """Crée les sessions d'apprentissage initial en tenant compte du planning de cours"""
        
        # Temps moyen par concept (ajusté par importance)
        concept_dict = {c.name: c for c in concepts}
        
        time_weights = {'critical': 2.0, 'high': 1.5, 'medium': 1.0, 'low': 0.5}
        
        total_weight = 0
        for name in learning_order:
            if name in concept_dict:
                importance = concept_dict[name].importance
                total_weight += time_weights.get(importance, 1.0)
        
        minutes_per_weight = (total_hours * 60) / total_weight if total_weight > 0 else 30
        
        current_date = start_date
        days_available = (end_date - start_date).days - 7  # Garder la dernière semaine pour révisions finales
        
        concepts_per_day = max(1, len(learning_order) // max(1, days_available))
        
        for i, concept_name in enumerate(learning_order):
            concept = concept_dict.get(concept_name)
            if not concept:
                continue
            
            # Calculer la durée de la session
            weight = time_weights.get(concept.importance, 1.0)
            duration = int(minutes_per_weight * weight)
            duration = max(30, min(120, duration))  # Entre 30 min et 2h
            
            # Déterminer la date minimale de révision
            min_revision_date = start_date
            if course_schedule_manager and concept.source_module:
                # Ne pas réviser avant que le module soit vu en cours
                module_sessions = course_schedule_manager.get_sessions_by_module(concept.source_module)
                if module_sessions:
                    # Commencer les révisions après la première session du module
                    first_session_date = min(s.date for s in module_sessions)
                    # Attendre J+2 après le cours pour commencer les révisions
                    min_revision_date = max(min_revision_date, first_session_date + timedelta(days=2))
            
            # Déterminer la date
            day_offset = i // concepts_per_day
            session_date = max(min_revision_date, current_date + timedelta(days=day_offset))
            
            # Ne pas dépasser la date limite
            if session_date >= end_date - timedelta(days=7):
                session_date = end_date - timedelta(days=7)
            
            # Créer les objectifs
            objectives = [f"Comprendre: {concept_name}"]
            if concept.prerequisites:
                objectives.append(f"Prérequis maîtrisés: {', '.join(concept.prerequisites[:3])}")
            if concept.exam_relevant:
                objectives.append("⚠️ Important pour l'examen")
            
            session = StudySession(
                date=session_date,
                duration_minutes=duration,
                concepts=[concept_name],
                objectives=objectives,
                session_type='new_learning',
                priority=concept.importance,
                module=concept.source_module
            )
            
            self.plan.sessions.append(session)
    
    def _add_spaced_repetition(self, total_hours: float) -> None:
        """Ajoute des sessions de révision avec répétition espacée"""
        
        intervals = self.config['planning']['spaced_repetition_intervals']
        
        # Pour chaque session d'apprentissage, planifier des révisions
        learning_sessions = [s for s in self.plan.sessions if s.session_type == 'new_learning']
        
        revision_time_per_session = (total_hours * 60) / (len(learning_sessions) * len(intervals))
        revision_time_per_session = max(15, min(30, revision_time_per_session))
        
        for session in learning_sessions:
            for interval in intervals:
                revision_date = session.date + timedelta(days=interval)
                
                # Ne pas dépasser la date d'examen
                if revision_date >= self.plan.exam_date:
                    continue
                
                revision = StudySession(
                    date=revision_date,
                    duration_minutes=int(revision_time_per_session),
                    concepts=session.concepts,
                    objectives=[f"Révision: {c}" for c in session.concepts],
                    session_type='revision',
                    priority='medium',
                    module=session.module
                )
                
                self.plan.sessions.append(revision)
    
    def _add_practice_sessions(self, total_hours: float, exam_date: datetime) -> None:
        """Ajoute des sessions de pratique/exercices"""
        
        # Sessions de pratique dans les 2 dernières semaines
        start_practice = exam_date - timedelta(days=14)
        
        num_sessions = int(total_hours / 1.5)  # Sessions de 1h30
        
        for i in range(num_sessions):
            practice_date = start_practice + timedelta(days=i)
            
            if practice_date >= exam_date:
                break
            
            session = StudySession(
                date=practice_date,
                duration_minutes=90,
                concepts=["Exercices pratiques", "Révision générale"],
                objectives=[
                    "Faire des exercices type examen",
                    "Identifier les points faibles",
                    "Renforcer la compréhension"
                ],
                session_type='practice',
                priority='critical'
            )
            
            self.plan.sessions.append(session)
    
    def _create_milestones(self, exam_date: datetime) -> None:
        """Crée des jalons de progression"""
        
        today = datetime.now()
        total_days = (exam_date - today).days
        
        milestones = [
            {
                "date": today + timedelta(days=total_days // 4),
                "name": "📍 25% - Premier quart",
                "objective": "Concepts fondamentaux maîtrisés"
            },
            {
                "date": today + timedelta(days=total_days // 2),
                "name": "📍 50% - Mi-parcours",
                "objective": "Tous les concepts vus au moins une fois"
            },
            {
                "date": today + timedelta(days=3 * total_days // 4),
                "name": "📍 75% - Trois quarts",
                "objective": "Révisions en cours, exercices pratiques"
            },
            {
                "date": exam_date - timedelta(days=7),
                "name": "📍 Dernière semaine",
                "objective": "Révisions finales et repos"
            }
        ]
        
        self.plan.milestones = milestones
    
    def display_weekly_plan(self, week_offset: int = 0) -> None:
        """Affiche le planning d'une semaine"""
        
        if not self.plan:
            console.print("[red]Aucun plan créé. Utilisez create_plan() d'abord.[/red]")
            return
        
        start_of_week = datetime.now() + timedelta(weeks=week_offset)
        start_of_week = start_of_week - timedelta(days=start_of_week.weekday())
        end_of_week = start_of_week + timedelta(days=7)
        
        week_sessions = [
            s for s in self.plan.sessions
            if start_of_week <= s.date < end_of_week
        ]
        
        table = Table(title=f"📅 Semaine du {start_of_week.strftime('%d/%m/%Y')}")
        table.add_column("Jour", style="bold")
        table.add_column("Durée", justify="right")
        table.add_column("Type", style="cyan")
        table.add_column("Concepts")
        table.add_column("Objectifs")
        
        days = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche']
        
        for day_num in range(7):
            day_date = start_of_week + timedelta(days=day_num)
            day_sessions = [s for s in week_sessions if s.date.date() == day_date.date()]
            
            if day_sessions:
                for session in day_sessions:
                    type_icons = {
                        'new_learning': '📚 Apprentissage',
                        'revision': '🔄 Révision',
                        'practice': '✏️ Pratique'
                    }
                    
                    priority_style = {
                        'critical': '[red]',
                        'high': '[orange1]',
                        'medium': '[yellow]',
                        'low': '[green]'
                    }.get(session.priority, '')
                    
                    table.add_row(
                        f"{days[day_num]}\n{day_date.strftime('%d/%m')}",
                        f"{session.duration_minutes} min",
                        type_icons.get(session.session_type, session.session_type),
                        f"{priority_style}{', '.join(session.concepts[:2])}[/]",
                        "\n".join(session.objectives[:2])
                    )
            else:
                table.add_row(
                    f"{days[day_num]}\n{day_date.strftime('%d/%m')}",
                    "-",
                    "🌴 Repos",
                    "-",
                    "-"
                )
        
        console.print(table)
    
    def display_summary(self) -> None:
        """Affiche un résumé du plan"""
        
        if not self.plan:
            console.print("[red]Aucun plan créé.[/red]")
            return
        
        # Statistiques par type
        by_type = {}
        for session in self.plan.sessions:
            if session.session_type not in by_type:
                by_type[session.session_type] = {'count': 0, 'minutes': 0}
            by_type[session.session_type]['count'] += 1
            by_type[session.session_type]['minutes'] += session.duration_minutes
        
        summary = []
        summary.append("=" * 60)
        summary.append("📊 RÉSUMÉ DU PLAN DE RÉVISION")
        summary.append("=" * 60)
        summary.append(f"\n📅 Date de création: {self.plan.created_at.strftime('%d/%m/%Y')}")
        summary.append(f"📅 Date d'examen: {self.plan.exam_date.strftime('%d/%m/%Y')}")
        summary.append(f"⏱️  Temps total planifié: {self.plan.total_hours:.1f} heures")
        summary.append(f"📚 Concepts à couvrir: {len(self.plan.concepts_covered)}")
        
        summary.append(f"\n📈 RÉPARTITION:")
        for session_type, data in by_type.items():
            hours = data['minutes'] / 60
            type_names = {
                'new_learning': 'Apprentissage',
                'revision': 'Révision',
                'practice': 'Pratique'
            }
            summary.append(f"  • {type_names.get(session_type, session_type)}: {data['count']} sessions ({hours:.1f}h)")
        
        summary.append(f"\n🏁 JALONS:")
        for milestone in self.plan.milestones:
            summary.append(f"  • {milestone['date'].strftime('%d/%m/%Y')}: {milestone['name']}")
            summary.append(f"    Objectif: {milestone['objective']}")
        
        console.print("\n".join(summary))
    
    def export_plan(self, filepath: str) -> None:
        """Exporte le plan en JSON"""
        
        if not self.plan:
            console.print("[red]Aucun plan à exporter.[/red]")
            return
        
        data = {
            "created_at": self.plan.created_at.isoformat(),
            "exam_date": self.plan.exam_date.isoformat(),
            "total_hours": self.plan.total_hours,
            "concepts_covered": self.plan.concepts_covered,
            "milestones": [
                {
                    "date": m['date'].isoformat(),
                    "name": m['name'],
                    "objective": m['objective']
                }
                for m in self.plan.milestones
            ],
            "sessions": [
                {
                    "date": s.date.isoformat(),
                    "duration_minutes": s.duration_minutes,
                    "concepts": s.concepts,
                    "objectives": s.objectives,
                    "session_type": s.session_type,
                    "priority": s.priority,
                    "module": s.module,
                    "completed": s.completed
                }
                for s in sorted(self.plan.sessions, key=lambda x: x.date)
            ]
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        console.print(f"[green]✅ Plan exporté vers {filepath}[/green]")
    
    def export_to_markdown(self, filepath: str) -> None:
        """Exporte le plan en format Markdown lisible"""
        
        if not self.plan:
            return
        
        lines = []
        lines.append("# 📚 Plan de Révision - Brevet Fédéral")
        lines.append(f"\n> Créé le {self.plan.created_at.strftime('%d/%m/%Y')}")
        lines.append(f"> Examen le {self.plan.exam_date.strftime('%d/%m/%Y')}")
        lines.append(f"> Temps total: {self.plan.total_hours:.1f} heures")
        
        lines.append("\n## 🏁 Jalons")
        for m in self.plan.milestones:
            lines.append(f"- **{m['date'].strftime('%d/%m/%Y')}** - {m['name']}")
            lines.append(f"  - {m['objective']}")
        
        lines.append("\n## 📅 Sessions planifiées")
        
        # Grouper par semaine
        sessions_by_week = {}
        for session in sorted(self.plan.sessions, key=lambda x: x.date):
            week_start = session.date - timedelta(days=session.date.weekday())
            week_key = week_start.strftime('%d/%m/%Y')
            if week_key not in sessions_by_week:
                sessions_by_week[week_key] = []
            sessions_by_week[week_key].append(session)
        
        for week, sessions in sessions_by_week.items():
            lines.append(f"\n### Semaine du {week}")
            lines.append("")
            lines.append("| Jour | Durée | Type | Concepts | Objectifs |")
            lines.append("|------|-------|------|----------|-----------|")
            
            for s in sessions:
                type_emoji = {'new_learning': '📚', 'revision': '🔄', 'practice': '✏️'}.get(s.session_type, '')
                concepts = ', '.join(s.concepts[:2])
                objectives = ' / '.join(s.objectives[:2])
                lines.append(f"| {s.date.strftime('%a %d/%m')} | {s.duration_minutes}min | {type_emoji} | {concepts} | {objectives} |")
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        
        console.print(f"[green]✅ Plan Markdown exporté vers {filepath}[/green]")


if __name__ == "__main__":
    import yaml
    from datetime import datetime
    
    with open("config/config.yaml", 'r') as f:
        config = yaml.safe_load(f)
    
    # Test du planner
    planner = RevisionPlanner(config)
    
    # Créer des concepts de test
    from dataclasses import dataclass
    
    @dataclass
    class MockConcept:
        name: str
        importance: str
        exam_relevant: bool
        prerequisites: list
        source_module: str = None
    
    test_concepts = [
        MockConcept("Loi d'Ohm", "critical", True, [], "M1"),
        MockConcept("Puissance", "critical", True, ["Loi d'Ohm"], "M1"),
        MockConcept("Transformateur", "high", True, ["Puissance"], "M2"),
    ]
    
    learning_order = ["Loi d'Ohm", "Puissance", "Transformateur"]
    
    plan = planner.create_plan(
        concepts=test_concepts,
        learning_order=learning_order,
        course_schedule={},
        exam_date=datetime(2026, 6, 15),
        available_hours_per_week=10
    )
    
    planner.display_summary()
    planner.display_weekly_plan(0)
