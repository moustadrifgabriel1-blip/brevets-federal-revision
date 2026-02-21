"""
Générateur de Planning de Révision Automatique
"""
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict, field


@dataclass
class RevisionSession:
    date: str
    day_name: str
    duration_minutes: int
    concepts: List[str]
    category: str
    priority: str
    session_type: str = "new_learning"
    module: Optional[str] = None
    completed: bool = False
    objectives: List[str] = field(default_factory=list)
    id: Optional[str] = None


class RevisionPlannerAuto:
    def __init__(self, config: dict):
        self.config = config
        self.weekday_minutes = config.get("planning", {}).get("weekday_minutes", 30)
        self.weekend_hours = config.get("planning", {}).get("weekend_hours", 8)
        exam_date_str = config.get("user", {}).get("exam_date", "2027-03-22")
        if isinstance(exam_date_str, datetime):
            self.exam_date = exam_date_str
        else:
            self.exam_date = datetime.strptime(str(exam_date_str)[:10], "%Y-%m-%d")
        self.nodes = []
        self.concepts = []
        self.categories = []
        self.learning_order = []
        self.sessions = []
        self.course_dates = set()
        self.milestones = []
        
    def load_concepts(self, concept_map_path: str = "exports/concept_map.json"):
        # Chercher dans exports/ puis cloud_data/ pour Streamlit Cloud
        path = Path(concept_map_path)
        if not path.exists():
            alt_path = Path("cloud_data") / Path(concept_map_path).name
            if alt_path.exists():
                path = alt_path
            else:
                raise FileNotFoundError(f"Fichier {concept_map_path} non trouve")
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.nodes = data.get("nodes", [])
        self.categories = data.get("categories", [])
        self.learning_order = data.get("learning_order", [])
        self.concepts = []
        for node in self.nodes:
            if isinstance(node, dict):
                self.concepts.append({
                    "id": node.get("id", node.get("name", "Unknown")),
                    "name": node.get("name", node.get("id", "Unknown")),
                    "category": node.get("category", "General"),
                    "importance": node.get("importance", "medium"),
                    "module": node.get("module"),
                    "exam_relevant": node.get("exam_relevant", False),
                })
            elif isinstance(node, str):
                self.concepts.append({"id": node, "name": node, "category": "General", "importance": "medium", "module": None, "exam_relevant": False})
        return len(self.concepts)
    
    def load_course_schedule(self, schedule_path: str = "data/course_schedule.json"):
        path = Path(schedule_path)
        if not path.exists():
            # Chercher dans cloud_data/ pour Streamlit Cloud
            alt_path = Path("cloud_data") / Path(schedule_path).name
            if alt_path.exists():
                path = alt_path
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.course_dates = set()
            for session in data.get("sessions", []):
                date_str = session.get("date", "")
                if date_str:
                    self.course_dates.add(date_str[:10])
    
    def _translate_day(self, day: str) -> str:
        return {"Monday": "Lundi", "Tuesday": "Mardi", "Wednesday": "Mercredi", "Thursday": "Jeudi", "Friday": "Vendredi", "Saturday": "Samedi", "Sunday": "Dimanche"}.get(day, day)
    
    def generate_planning(self, start_date: Optional[datetime] = None):
        if not self.concepts:
            self.load_concepts()
        self.load_course_schedule()
        if start_date is None:
            # Utiliser formation_start de la config si disponible et dans le passé
            formation_start_str = self.config.get("user", {}).get("formation_start", "")
            if formation_start_str:
                try:
                    formation_start = datetime.strptime(str(formation_start_str)[:10], "%Y-%m-%d")
                    # Commencer au plus tôt à la date de début de formation
                    start_date = formation_start
                except (ValueError, TypeError):
                    start_date = datetime.now()
            else:
                start_date = datetime.now()
        concepts_by_priority = {"critical": [], "high": [], "medium": [], "low": []}
        for c in self.concepts:
            imp = c.get("importance", "medium").lower()
            if imp not in concepts_by_priority:
                imp = "medium"
            concepts_by_priority[imp].append(c)
        ordered = concepts_by_priority["critical"] + concepts_by_priority["high"] + concepts_by_priority["medium"] + concepts_by_priority["low"]
        if self.learning_order:
            priority = []
            for name in self.learning_order:
                for c in ordered:
                    if c["name"] == name or c["id"] == name:
                        if c not in priority:
                            priority.append(c)
                        break
            remaining = [c for c in ordered if c not in priority]
            ordered = priority + remaining
        self.sessions = []
        current_date = start_date
        concept_index = 0
        total = len(ordered)
        
        # Configuration réaliste : temps par concept selon la difficulté
        # Concept simple: 10-15 min, Concept complexe: 20-30 min
        # En moyenne: ~15-20 min par concept nouveau
        MINUTES_PER_NEW_CONCEPT = 15
        
        while current_date < self.exam_date and concept_index < total:
            date_str = current_date.strftime("%Y-%m-%d")
            if date_str in self.course_dates:
                current_date += timedelta(days=1)
                continue
            is_weekend = current_date.weekday() >= 5
            duration = self.weekend_hours * 60 if is_weekend else self.weekday_minutes
            
            # Calculer le nombre réaliste de concepts pour cette session
            # 30 min = 2 concepts max, 60 min = 4 concepts max, etc.
            per_session = max(1, min(6, duration // MINUTES_PER_NEW_CONCEPT))
            
            session_concepts = []
            cats = set()
            prio = "medium"
            for i in range(per_session):
                if concept_index + i < total:
                    c = ordered[concept_index + i]
                    session_concepts.append(c["name"])
                    cats.add(c["category"])
                    if c["importance"] in ["critical", "high"]:
                        prio = "high"
            if session_concepts:
                # Générer des objectifs concrets basés sur les concepts
                objectives = []
                for sc in session_concepts[:3]:
                    # Objectifs plus précis que "Comprendre X"
                    if any(c.get("importance") in ["critical", "high"] for c in ordered[concept_index:concept_index+len(session_concepts)] if c["name"] == sc):
                        objectives.append(f"Maîtriser {sc} (concept prioritaire pour l'examen)")
                    else:
                        objectives.append(f"Comprendre et retenir {sc}")
                
                if is_weekend:
                    objectives.append("Faire un quiz de contrôle sur les concepts de la semaine")
                
                self.sessions.append(RevisionSession(
                    date=date_str,
                    day_name=self._translate_day(current_date.strftime("%A")),
                    duration_minutes=duration,
                    concepts=session_concepts,
                    category=list(cats)[0] if cats else "General",
                    priority=prio,
                    session_type="new_learning",
                    module=ordered[concept_index].get("module") or "General",
                    completed=False,
                    objectives=objectives
                ))
                concept_index += len(session_concepts)
            current_date += timedelta(days=1)
        self._add_spaced_repetition()
        # Assigner des IDs stables à toutes les sessions
        self.sessions.sort(key=lambda s: s.date)
        for i, s in enumerate(self.sessions):
            s.id = f"rev_{s.date}_{i}"
        self._create_milestones()
        return self.sessions
    
    def _add_spaced_repetition(self):
        """Ajoute des révisions espacées de manière réaliste"""
        important = [c for c in self.concepts if c.get("importance") in ["critical", "high"] or c.get("exam_relevant")][:20]
        
        # Distribuer les révisions sur différents jours pour éviter la surcharge
        review_schedule = {}  # date -> liste de concepts
        
        for i, concept in enumerate(important):
            # Décaler les intervalles pour bien répartir (éviter la surcharge)
            base_offset = i % 7  # Décaler de 0-6 jours
            for interval in [7, 21, 45]:  # Révisions moins fréquentes mais plus espacées
                actual_interval = interval + base_offset
                review_date = datetime.now() + timedelta(days=actual_interval)
                if review_date < self.exam_date:
                    date_str = review_date.strftime("%Y-%m-%d")
                    if date_str not in review_schedule:
                        review_schedule[date_str] = []
                    review_schedule[date_str].append(concept)
        
        # Ne pas surcharger les sessions courtes (30 min)
        MAX_TOTAL_CONCEPTS_SHORT = 2  # Max pour session 30 min
        MAX_TOTAL_CONCEPTS_LONG = 8   # Max pour session longue (weekend)
        
        for date_str, concepts_to_review in review_schedule.items():
            existing = [s for s in self.sessions if s.date == date_str]
            
            if existing:
                session = existing[0]
                current_total = len(session.concepts)
                is_short_session = session.duration_minutes <= 45
                max_concepts = MAX_TOTAL_CONCEPTS_SHORT if is_short_session else MAX_TOTAL_CONCEPTS_LONG
                
                # Ne pas ajouter de révisions si la session est déjà chargée
                if current_total >= max_concepts:
                    continue
                
                # Ajouter max 1 révision aux sessions courtes, 2 aux longues
                available_slots = max(0, max_concepts - current_total)
                max_reviews = 1 if is_short_session else 2
                
                for concept in concepts_to_review[:min(available_slots, max_reviews)]:
                    review_name = f"Reviser: {concept['name']}"
                    if review_name not in session.concepts:
                        session.concepts.append(review_name)
            else:
                # Créer une nouvelle session de révision (seulement si 2+ concepts)
                if len(concepts_to_review) >= 2:
                    review_date = datetime.strptime(date_str, "%Y-%m-%d")
                    limited = concepts_to_review[:3]
                    self.sessions.append(RevisionSession(
                        date=date_str,
                        day_name=self._translate_day(review_date.strftime("%A")),
                        duration_minutes=len(limited) * 15,  # 15 min par révision
                        concepts=[f"Reviser: {c['name']}" for c in limited],
                        category=limited[0].get("category", "Revision") if limited else "Revision",
                        priority="medium",
                        session_type="revision",
                        module=next((c.get("module") for c in limited if c.get("module")), "Revision"),
                        completed=False,
                        objectives=[f"Consolider les acquis"]
                    ))
        self.sessions.sort(key=lambda s: s.date)
    
    def _create_milestones(self):
        total_days = (self.exam_date - datetime.now()).days
        if total_days > 0:
            self.milestones = [
                {"date": (datetime.now() + timedelta(days=total_days * 0.25)).strftime("%Y-%m-%d"), "name": "Premier Quart", "objective": "Bases essentielles", "progress": 25},
                {"date": (datetime.now() + timedelta(days=total_days * 0.5)).strftime("%Y-%m-%d"), "name": "Mi-parcours", "objective": "Concepts avances", "progress": 50},
                {"date": (datetime.now() + timedelta(days=total_days * 0.75)).strftime("%Y-%m-%d"), "name": "Dernier Sprint", "objective": "Revisions intensives", "progress": 75},
                {"date": (self.exam_date - timedelta(days=7)).strftime("%Y-%m-%d"), "name": "Revision Finale", "objective": "Consolidation", "progress": 95}
            ]
    
    def _calculate_stats(self) -> Dict:
        total_min = sum(s.duration_minutes for s in self.sessions)
        by_prio = {"high": 0, "medium": 0, "low": 0}
        by_type = {"new_learning": 0, "revision": 0, "practice": 0}
        for s in self.sessions:
            by_prio[s.priority] = by_prio.get(s.priority, 0) + 1
            by_type[s.session_type] = by_type.get(s.session_type, 0) + 1
        return {
            "total_revision_hours": round(total_min / 60, 1),
            "sessions_by_priority": by_prio,
            "sessions_by_type": by_type,
            "average_concepts_per_session": round(sum(len(s.concepts) for s in self.sessions) / max(1, len(self.sessions)), 1),
            "days_until_exam": (self.exam_date - datetime.now()).days
        }
    
    def export_planning(self, output_path: str = "exports/revision_plan.json"):
        if not self.sessions:
            self.generate_planning()
        stats = self._calculate_stats()
        data = {
            "generated_at": datetime.now().isoformat(),
            "exam_date": self.exam_date.strftime("%Y-%m-%d"),
            "total_sessions": len(self.sessions),
            "total_concepts": len(self.concepts),
            "total_hours": stats["total_revision_hours"],
            "weekday_minutes": self.weekday_minutes,
            "weekend_hours": self.weekend_hours,
            "concepts_covered": [c["name"] for c in self.concepts],
            "categories": self.categories,
            "milestones": self.milestones,
            "sessions": [asdict(s) for s in self.sessions],
            "statistics": stats
        }
        # Écrire dans exports/ ET cloud_data/ pour Streamlit Cloud
        for path_str in [output_path, str(Path("cloud_data") / Path(output_path).name)]:
            Path(path_str).parent.mkdir(parents=True, exist_ok=True)
            with open(path_str, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        return output_path
    
    def export_to_markdown(self, output_path: str = "exports/revision_plan.md"):
        if not self.sessions:
            self.generate_planning()
        lines = ["# Planning de Revision Personnalise", "", f"Genere le: {datetime.now().strftime('%d/%m/%Y')}", f"Examen: {self.exam_date.strftime('%d/%m/%Y')}", f"Jours restants: {(self.exam_date - datetime.now()).days}", "", "## Jalons", ""]
        for m in self.milestones:
            lines.append(f"- **{m['date']}** - {m['name']}: {m['objective']}")
        lines.extend(["", "## Sessions de la semaine", ""])
        for s in self.sessions[:14]:
            lines.append(f"- **{s.day_name} {s.date}** ({s.duration_minutes}min): {', '.join(s.concepts[:3])}")
        content = "\n".join(lines)
        # Écrire dans exports/ ET cloud_data/
        for path_str in [output_path, str(Path("cloud_data") / Path(output_path).name)]:
            Path(path_str).parent.mkdir(parents=True, exist_ok=True)
            with open(path_str, "w", encoding="utf-8") as f:
                f.write(content)
        return output_path


def auto_generate_planning(config: dict) -> dict:
    """
    Genere automatiquement le planning de revision.
    Appele apres l'analyse des documents.
    """
    planner = RevisionPlannerAuto(config)
    try:
        num_concepts = planner.load_concepts()
        planner.generate_planning()
        json_path = planner.export_planning("exports/revision_plan.json")
        md_path = planner.export_to_markdown("exports/revision_plan.md")
        stats = planner._calculate_stats()
        return {
            "success": True,
            "json_path": json_path,
            "md_path": md_path,
            "total_concepts": num_concepts,
            "total_sessions": len(planner.sessions),
            "total_hours": stats["total_revision_hours"],
            "days_until_exam": stats["days_until_exam"],
            "milestones": planner.milestones
        }
    except Exception as e:
        return {"success": False, "error": str(e)}
