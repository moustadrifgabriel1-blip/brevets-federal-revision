"""
Gestionnaire de progression pour le Brevet Fédéral
Suit les sessions de révision complétées et les concepts maîtrisés
"""
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional


class ProgressTracker:
    """Gère la progression de l'utilisateur dans son plan de révision"""
    
    def __init__(self, progress_file: str = "data/progress.json"):
        self.progress_file = Path(progress_file)
        self.progress = self._load_progress()
    
    def _load_progress(self) -> Dict:
        """Charge la progression depuis le fichier JSON"""
        if self.progress_file.exists():
            with open(self.progress_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            "sessions_completed": [],
            "concepts_mastered": [],
            "last_update": None,
            "stats": {
                "total_sessions": 0,
                "completed_sessions": 0,
                "total_concepts": 0,
                "mastered_concepts": 0
            }
        }
    
    def _save_progress(self):
        """Sauvegarde la progression dans le fichier JSON"""
        self.progress_file.parent.mkdir(parents=True, exist_ok=True)
        self.progress["last_update"] = datetime.now().isoformat()
        with open(self.progress_file, 'w', encoding='utf-8') as f:
            json.dump(self.progress, f, indent=2, ensure_ascii=False)
    
    def mark_session_completed(self, session_id: str):
        """Marque une session de révision comme complétée"""
        if session_id not in self.progress["sessions_completed"]:
            self.progress["sessions_completed"].append(session_id)
            self.progress["stats"]["completed_sessions"] = len(self.progress["sessions_completed"])
            self._save_progress()
    
    def unmark_session_completed(self, session_id: str):
        """Retire une session de la liste des complétées"""
        if session_id in self.progress["sessions_completed"]:
            self.progress["sessions_completed"].remove(session_id)
            self.progress["stats"]["completed_sessions"] = len(self.progress["sessions_completed"])
            self._save_progress()
    
    def is_session_completed(self, session_id: str) -> bool:
        """Vérifie si une session est complétée"""
        return session_id in self.progress["sessions_completed"]
    
    def mark_concept_mastered(self, concept_id: str):
        """Marque un concept comme maîtrisé"""
        if concept_id not in self.progress["concepts_mastered"]:
            self.progress["concepts_mastered"].append(concept_id)
            self.progress["stats"]["mastered_concepts"] = len(self.progress["concepts_mastered"])
            self._save_progress()
    
    def unmark_concept_mastered(self, concept_id: str):
        """Retire un concept de la liste des maîtrisés"""
        if concept_id in self.progress["concepts_mastered"]:
            self.progress["concepts_mastered"].remove(concept_id)
            self.progress["stats"]["mastered_concepts"] = len(self.progress["concepts_mastered"])
            self._save_progress()
    
    def is_concept_mastered(self, concept_id: str) -> bool:
        """Vérifie si un concept est maîtrisé"""
        return concept_id in self.progress["concepts_mastered"]
    
    def get_completion_rate(self) -> float:
        """Calcule le taux de complétion des sessions"""
        total = self.progress["stats"]["total_sessions"]
        if total == 0:
            return 0.0
        return (self.progress["stats"]["completed_sessions"] / total) * 100
    
    def get_mastery_rate(self) -> float:
        """Calcule le taux de maîtrise des concepts"""
        total = self.progress["stats"]["total_concepts"]
        if total == 0:
            return 0.0
        return (self.progress["stats"]["mastered_concepts"] / total) * 100
    
    def update_totals(self, total_sessions: int, total_concepts: int):
        """Met à jour les totaux de sessions et concepts"""
        self.progress["stats"]["total_sessions"] = total_sessions
        self.progress["stats"]["total_concepts"] = total_concepts
        self._save_progress()
    
    def get_stats(self) -> Dict:
        """Retourne les statistiques de progression"""
        return {
            "total_sessions": self.progress["stats"]["total_sessions"],
            "completed_sessions": self.progress["stats"]["completed_sessions"],
            "completion_rate": self.get_completion_rate(),
            "total_concepts": self.progress["stats"]["total_concepts"],
            "mastered_concepts": self.progress["stats"]["mastered_concepts"],
            "mastery_rate": self.get_mastery_rate(),
            "last_update": self.progress["last_update"]
        }
    
    def get_recent_activity(self, limit: int = 10) -> List[Dict]:
        """Retourne l'activité récente (dernières sessions complétées)"""
        sessions = self.progress["sessions_completed"][-limit:]
        return [{"session_id": s, "completed": True} for s in reversed(sessions)]
    
    def reset_progress(self):
        """Réinitialise toute la progression"""
        self.progress = {
            "sessions_completed": [],
            "concepts_mastered": [],
            "last_update": None,
            "stats": {
                "total_sessions": 0,
                "completed_sessions": 0,
                "total_concepts": 0,
                "mastered_concepts": 0
            }
        }
        self._save_progress()

    def sync_with_calendar(self, revision_plan: dict, course_schedule_sessions: list = None, concept_map: dict = None):
        """
        Synchronise la progression avec le calendrier.
        
        - Met à jour les totaux (sessions, concepts)
        - Calcule les stats de cours (modules complétés, concepts vus)
        - NE force PAS l'auto-complétion des sessions passées
          (c'est l'utilisateur qui coche manuellement)
        
        Args:
            revision_plan: Le plan de révision (depuis revision_plan.json)
            course_schedule_sessions: Liste des sessions de cours
            concept_map: La carte des concepts (concept_map.json)
        """
        now = datetime.now()
        changed = False
        
        # 1) Mettre à jour les totaux
        sessions = revision_plan.get('sessions', [])
        total_sessions = len(sessions) if sessions else self.progress["stats"]["total_sessions"]
        total_concepts = len(concept_map.get('nodes', [])) if concept_map else self.progress["stats"]["total_concepts"]
        
        if (self.progress["stats"]["total_sessions"] != total_sessions or 
            self.progress["stats"]["total_concepts"] != total_concepts):
            self.progress["stats"]["total_sessions"] = total_sessions
            self.progress["stats"]["total_concepts"] = total_concepts
            changed = True
        
        # 2) Nettoyer les IDs obsolètes (anciens IDs avec index global)
        # Si on détecte des IDs au format ancien, les migrer
        valid_ids = set()
        for session in sessions:
            sid = session.get('id')
            if sid:
                valid_ids.add(sid)
        
        if valid_ids:
            old_completed = self.progress["sessions_completed"]
            # Garder seulement les IDs valides (format rev_YYYY-MM-DD_N)
            cleaned = [sid for sid in old_completed if sid in valid_ids]
            if len(cleaned) != len(old_completed):
                self.progress["sessions_completed"] = cleaned
                self.progress["stats"]["completed_sessions"] = len(cleaned)
                changed = True
        
        # 3) Mettre à jour le compteur
        self.progress["stats"]["completed_sessions"] = len(self.progress["sessions_completed"])
        
        # 4) Identifier les modules dont les cours sont passés
        completed_modules = set()
        if course_schedule_sessions:
            for s in course_schedule_sessions:
                if hasattr(s, 'date'):
                    s_date = s.date
                    s_module = s.module_code
                else:
                    s_date = datetime.fromisoformat(s['date']) if isinstance(s.get('date'), str) else s.get('date', now)
                    s_module = s.get('module_code', '')
                
                if s_date <= now:
                    completed_modules.add(s_module)
        
        # 5) Stats de cours
        if "course_stats" not in self.progress:
            self.progress["course_stats"] = {}
        
        if course_schedule_sessions:
            total_course_sessions = len(course_schedule_sessions)
            completed_course_sessions = len([
                s for s in course_schedule_sessions 
                if (s.date if hasattr(s, 'date') else datetime.fromisoformat(s.get('date', '2099-01-01'))) <= now
            ])
            self.progress["course_stats"] = {
                "total_course_sessions": total_course_sessions,
                "completed_course_sessions": completed_course_sessions,
                "completed_modules": sorted(list(completed_modules)),
                "modules_with_content": sorted(list(set(
                    n.get('module', '') for n in concept_map.get('nodes', []) if n.get('module')
                ))) if concept_map else [],
                "concepts_seen_in_class": len([
                    n for n in (concept_map.get('nodes', []) if concept_map else [])
                    if n.get('module', '') in completed_modules
                ])
            }
            changed = True
        
        if changed:
            self._save_progress()
        
        return {
            "sessions_synced": len(self.progress["sessions_completed"]),
            "total_sessions": total_sessions,
            "completed_modules": sorted(list(completed_modules)),
            "course_stats": self.progress.get("course_stats", {})
        }
