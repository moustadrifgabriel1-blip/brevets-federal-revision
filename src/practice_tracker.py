"""
🔧 Tracker de Pratique Terrain — Compétences Non-Quizzables
=============================================================
Suit les exercices pratiques, oraux et projets que l'utilisateur
doit réaliser EN DEHORS du système numérique.

Ces compétences ne peuvent pas être évaluées par un quiz :
- 🔧 Pratique terrain : manipulation d'outils, mesures, chantier
- 🎤 Oral : argumentation, présentation, communication
- 📐 Projet : travail de projet complet (rédaction + présentation)

Le tracker permet de :
1. Cocher les exercices réalisés
2. Ajouter des notes/observations
3. Planifier des rappels
4. Voir la progression terrain vs numérique
"""

import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import defaultdict


class PracticeTracker:
    """
    Suivi des compétences pratiques/orales/projet qui nécessitent
    un entraînement en dehors du système de quiz.
    """

    def __init__(self, data_file: str = "data/practice_tracker.json"):
        self.data_file = Path(data_file)
        self.data = self._load()

    def _load(self) -> Dict:
        if self.data_file.exists():
            with open(self.data_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            "exercises": {},          # exercise_id -> {status, notes, dates...}
            "practice_log": [],       # journal de pratique [{date, module, description, duration_min}]
            "stats": {
                "total_practice_hours": 0,
                "last_practice_date": None,
                "streak_days": 0,
            },
            "last_update": None,
        }

    def _save(self):
        self.data_file.parent.mkdir(parents=True, exist_ok=True)
        self.data["last_update"] = datetime.now().isoformat()
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)

    def mark_exercise(self, exercise_id: str, completed: bool,
                      notes: str = "", confidence: int = 3,
                      duration_min: int = 0):
        """
        Marquer un exercice pratique comme fait ou pas fait.
        
        Args:
            exercise_id: ID unique de l'exercice (module_competence)
            completed: True si l'exercice a été réalisé
            notes: Notes/observations de l'utilisateur
            confidence: Niveau de confiance 1-5 (1=pas du tout confiant, 5=maîtrisé)
            duration_min: Durée de la pratique en minutes
        """
        now = datetime.now().isoformat()

        if exercise_id not in self.data["exercises"]:
            self.data["exercises"][exercise_id] = {
                "first_attempt": now,
                "attempts": 0,
                "completed_count": 0,
                "last_attempt": None,
                "notes": [],
                "confidence_history": [],
                "best_confidence": 0,
                "total_minutes": 0,
            }

        entry = self.data["exercises"][exercise_id]
        entry["attempts"] += 1
        entry["last_attempt"] = now

        if completed:
            entry["completed_count"] += 1

        if notes:
            entry["notes"].append({
                "date": now,
                "text": notes,
                "confidence": confidence,
            })

        entry["confidence_history"].append({
            "date": now,
            "value": confidence,
        })
        entry["best_confidence"] = max(entry["best_confidence"], confidence)
        entry["total_minutes"] += duration_min

        # Mettre à jour les stats globales
        self.data["stats"]["total_practice_hours"] += duration_min / 60
        self.data["stats"]["last_practice_date"] = now[:10]

        # Streak
        today = datetime.now().date().isoformat()
        yesterday = (datetime.now().date() - timedelta(days=1)).isoformat()
        last = self.data["stats"].get("last_practice_date")
        if last == yesterday or last == today:
            if last != today:  # Nouveau jour
                self.data["stats"]["streak_days"] += 1
        else:
            self.data["stats"]["streak_days"] = 1

        self._save()

    def log_practice_session(self, module: str, description: str,
                             duration_min: int, exercises_done: List[str] = None):
        """
        Enregistrer une session de pratique terrain complète.
        
        Args:
            module: Code du module (ex: "AE02")
            description: Ce qui a été pratiqué
            duration_min: Durée en minutes
            exercises_done: Liste des IDs d'exercices complétés
        """
        session = {
            "date": datetime.now().isoformat(),
            "module": module,
            "description": description,
            "duration_min": duration_min,
            "exercises_done": exercises_done or [],
        }

        self.data["practice_log"].append(session)
        self.data["stats"]["total_practice_hours"] += duration_min / 60
        self.data["stats"]["last_practice_date"] = datetime.now().date().isoformat()

        # Marquer les exercices comme complétés
        for ex_id in (exercises_done or []):
            self.mark_exercise(ex_id, completed=True, duration_min=0)

        self._save()

    def get_exercise_status(self, exercise_id: str) -> Dict:
        """Statut d'un exercice spécifique"""
        return self.data["exercises"].get(exercise_id, {
            "attempts": 0,
            "completed_count": 0,
            "best_confidence": 0,
            "total_minutes": 0,
        })

    def get_completion_by_module(self, checklist: List[Dict]) -> Dict:
        """
        Calcule le taux de complétion par module pour la checklist pratique.
        
        Args:
            checklist: La checklist générée par ExamFocusAnalyzer.get_practice_checklist()
        """
        modules = defaultdict(lambda: {"total": 0, "completed": 0, "exercises": []})

        for item in checklist:
            module = item["module"]
            ex_id = item["id"]
            status = self.get_exercise_status(ex_id)

            is_done = status.get("completed_count", 0) > 0
            confidence = status.get("best_confidence", 0)

            modules[module]["total"] += 1
            if is_done:
                modules[module]["completed"] += 1

            modules[module]["exercises"].append({
                **item,
                "done": is_done,
                "confidence": confidence,
                "attempts": status.get("attempts", 0),
                "total_minutes": status.get("total_minutes", 0),
            })

        # Calculer les pourcentages
        result = {}
        for mod, data in modules.items():
            data["pct"] = (data["completed"] / data["total"] * 100) if data["total"] > 0 else 0
            result[mod] = data

        return dict(sorted(result.items()))

    def get_global_practice_stats(self, checklist: List[Dict]) -> Dict:
        """Statistiques globales de la pratique terrain"""
        total_exercises = len(checklist)
        completed = sum(
            1 for item in checklist
            if self.get_exercise_status(item["id"]).get("completed_count", 0) > 0
        )

        by_type = defaultdict(lambda: {"total": 0, "completed": 0})
        for item in checklist:
            ctype = item["type"]
            by_type[ctype]["total"] += 1
            if self.get_exercise_status(item["id"]).get("completed_count", 0) > 0:
                by_type[ctype]["completed"] += 1

        return {
            "total_exercises": total_exercises,
            "completed": completed,
            "completion_pct": (completed / total_exercises * 100) if total_exercises > 0 else 0,
            "by_type": dict(by_type),
            "total_practice_hours": self.data["stats"].get("total_practice_hours", 0),
            "streak_days": self.data["stats"].get("streak_days", 0),
            "last_practice": self.data["stats"].get("last_practice_date"),
            "total_sessions": len(self.data["practice_log"]),
        }

    def get_recent_practice(self, limit: int = 10) -> List[Dict]:
        """Dernières sessions de pratique"""
        return sorted(
            self.data["practice_log"],
            key=lambda x: x["date"],
            reverse=True
        )[:limit]

    def get_overdue_exercises(self, checklist: List[Dict], days_threshold: int = 14) -> List[Dict]:
        """
        Exercices jamais faits ou pas pratiqués depuis longtemps.
        Pour les compétences à haut poids d'examen, c'est un rappel important.
        """
        overdue = []
        threshold = datetime.now() - timedelta(days=days_threshold)

        for item in checklist:
            status = self.get_exercise_status(item["id"])
            last = status.get("last_attempt")

            is_overdue = False
            reason = ""

            if status.get("attempts", 0) == 0:
                is_overdue = True
                reason = "Jamais pratiqué"
            elif last:
                last_dt = datetime.fromisoformat(last)
                if last_dt < threshold:
                    is_overdue = True
                    reason = f"Pas pratiqué depuis {(datetime.now() - last_dt).days} jours"

            if is_overdue:
                overdue.append({
                    **item,
                    "reason": reason,
                    "last_attempt": last,
                    "confidence": status.get("best_confidence", 0),
                })

        # Trier par poids d'examen décroissant (les plus importants d'abord)
        overdue.sort(key=lambda x: x["exam_weight"], reverse=True)
        return overdue
