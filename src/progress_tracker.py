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
