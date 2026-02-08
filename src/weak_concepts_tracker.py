"""
Tracker de Concepts Faibles — Quiz Adaptatif
=============================================
Enregistre les concepts échoués aux quiz/examens et les priorise
pour les futures sessions de révision et quiz.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from collections import defaultdict


class WeakConceptsTracker:
    """
    Suit les concepts échoués pour alimenter :
    - Les quiz adaptatifs (prioriser les concepts faibles)
    - Le planning de révision (ajouter des sessions de rattrapage)
    - La page progression (visualiser les faiblesses)
    """

    def __init__(self, data_file: str = "data/weak_concepts.json"):
        self.data_file = Path(data_file)
        self.data = self._load()

    def _load(self) -> Dict:
        if self.data_file.exists():
            with open(self.data_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            "weak_concepts": {},  # concept_id -> {stats}
            "last_update": None,
        }

    def _save(self):
        self.data_file.parent.mkdir(parents=True, exist_ok=True)
        self.data["last_update"] = datetime.now().isoformat()
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)

    def record_quiz_results(self, question_results: List[Dict]):
        """
        Enregistre les résultats d'un quiz ou examen blanc.
        
        Args:
            question_results: Liste de dicts avec au minimum :
                - concept_id ou concept_name
                - is_correct: bool
                - module (optionnel)
        """
        now = datetime.now().isoformat()

        for result in question_results:
            concept_id = result.get('concept_id') or result.get('concept_name', 'unknown')
            if not concept_id or concept_id == 'unknown':
                continue

            concept_key = str(concept_id)

            if concept_key not in self.data["weak_concepts"]:
                self.data["weak_concepts"][concept_key] = {
                    "concept_id": concept_id,
                    "concept_name": result.get('concept_name', concept_id),
                    "module": result.get('module', ''),
                    "error_count": 0,
                    "success_count": 0,
                    "total_attempts": 0,
                    "last_error": None,
                    "last_success": None,
                    "streak": 0,  # positif = succès consécutifs, négatif = erreurs consécutives
                    "mastery_score": 50,  # 0-100, commence à 50
                }

            entry = self.data["weak_concepts"][concept_key]
            entry["total_attempts"] += 1

            # Mettre à jour le nom/module si on a plus d'info
            if result.get('concept_name'):
                entry["concept_name"] = result['concept_name']
            if result.get('module'):
                entry["module"] = result['module']

            if result.get('is_correct', False):
                entry["success_count"] += 1
                entry["last_success"] = now
                entry["streak"] = max(0, entry["streak"]) + 1
                # Augmenter le score de maîtrise (plus lent que la descente)
                entry["mastery_score"] = min(100, entry["mastery_score"] + 10)
            else:
                entry["error_count"] += 1
                entry["last_error"] = now
                entry["streak"] = min(0, entry["streak"]) - 1
                # Baisser le score de maîtrise (descend plus vite)
                entry["mastery_score"] = max(0, entry["mastery_score"] - 15)

        self._save()

    def get_weak_concepts(self, min_errors: int = 1, max_mastery: int = 60) -> List[Dict]:
        """
        Retourne les concepts faibles triés par priorité (les plus faibles en premier).
        
        Args:
            min_errors: Nombre minimum d'erreurs pour être considéré faible
            max_mastery: Score de maîtrise maximum (0-100)
        """
        weak = []
        for key, entry in self.data["weak_concepts"].items():
            if entry["error_count"] >= min_errors and entry["mastery_score"] <= max_mastery:
                # Calculer un score de priorité (plus bas = plus prioritaire)
                success_rate = entry["success_count"] / entry["total_attempts"] if entry["total_attempts"] > 0 else 0
                priority_score = entry["mastery_score"] - (entry["error_count"] * 5)
                
                weak.append({
                    **entry,
                    "success_rate": success_rate,
                    "priority_score": priority_score,
                })
        
        # Trier par score de priorité croissant (les plus faibles d'abord)
        return sorted(weak, key=lambda x: x["priority_score"])

    def get_weak_concept_ids(self, limit: int = 20) -> List[str]:
        """Retourne les IDs des concepts les plus faibles"""
        weak = self.get_weak_concepts()
        return [w["concept_id"] for w in weak[:limit]]

    def get_weak_modules(self) -> Dict[str, Dict]:
        """Agrège les faiblesses par module"""
        modules = defaultdict(lambda: {"errors": 0, "total": 0, "concepts": []})
        
        for key, entry in self.data["weak_concepts"].items():
            mod = entry.get("module", "Unknown")
            if not mod:
                mod = "Unknown"
            modules[mod]["errors"] += entry["error_count"]
            modules[mod]["total"] += entry["total_attempts"]
            if entry["mastery_score"] < 50:
                modules[mod]["concepts"].append(entry["concept_name"])
        
        # Calculer le taux d'erreur par module
        result = {}
        for mod, data in modules.items():
            error_rate = (data["errors"] / data["total"] * 100) if data["total"] > 0 else 0
            result[mod] = {
                "error_rate": error_rate,
                "errors": data["errors"],
                "total": data["total"],
                "weak_concepts": data["concepts"],
            }
        
        return dict(sorted(result.items(), key=lambda x: x[1]["error_rate"], reverse=True))

    def get_stats(self) -> Dict:
        """Statistiques globales"""
        all_concepts = self.data["weak_concepts"]
        if not all_concepts:
            return {
                "total_tracked": 0,
                "weak_count": 0,
                "strong_count": 0,
                "average_mastery": 0,
            }

        total = len(all_concepts)
        weak = sum(1 for c in all_concepts.values() if c["mastery_score"] < 50)
        strong = sum(1 for c in all_concepts.values() if c["mastery_score"] >= 70)
        avg = sum(c["mastery_score"] for c in all_concepts.values()) / total

        return {
            "total_tracked": total,
            "weak_count": weak,
            "strong_count": strong,
            "average_mastery": avg,
            "last_update": self.data.get("last_update"),
        }

    def mark_concept_reviewed(self, concept_id: str):
        """Marque un concept comme révisé (boost léger du mastery)"""
        key = str(concept_id)
        if key in self.data["weak_concepts"]:
            self.data["weak_concepts"][key]["mastery_score"] = min(
                100, self.data["weak_concepts"][key]["mastery_score"] + 5
            )
            self._save()

    def reset(self):
        """Réinitialise tout le tracking"""
        self.data = {"weak_concepts": {}, "last_update": None}
        self._save()
