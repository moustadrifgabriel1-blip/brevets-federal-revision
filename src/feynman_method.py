"""
🧠 Technique Feynman — Compréhension Profonde par Explication
===============================================================
Implémente la technique de Richard Feynman :
1. Choisis un concept
2. Explique-le avec tes propres mots (comme à un enfant)
3. L'IA identifie les lacunes dans ton explication
4. Tu combles les trous et réessayes

C'est la méthode d'apprentissage la plus efficace pour la COMPRÉHENSION
(pas juste la mémorisation). Elle force le rappel actif ET l'élaboration.

Principe : si tu ne peux pas l'expliquer simplement, tu ne le comprends pas vraiment.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional


class FeynmanTracker:
    """
    Gère les sessions Feynman et l'historique de compréhension.
    Chaque concept a un score de compréhension basé sur la qualité
    des explications successives.
    """

    def __init__(self, data_file: str = "data/feynman_tracker.json"):
        self.data_file = Path(data_file)
        self.data = self._load()

    def _load(self) -> Dict:
        if self.data_file.exists():
            with open(self.data_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            "sessions": {},       # concept_id -> {attempts, best_score, history}
            "total_sessions": 0,
            "concepts_mastered": 0,  # Score >= 80
            "last_session": None,
        }

    def _save(self):
        self.data_file.parent.mkdir(parents=True, exist_ok=True)
        self.data["last_session"] = datetime.now().isoformat()
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)

    def start_session(self, concept_id: str, concept_name: str, module: str) -> Dict:
        """Démarre une session Feynman pour un concept"""
        if concept_id not in self.data["sessions"]:
            self.data["sessions"][concept_id] = {
                "concept_name": concept_name,
                "module": module,
                "attempts": 0,
                "best_score": 0,
                "history": [],
                "status": "not_started",  # not_started, in_progress, mastered
                "first_attempt": datetime.now().isoformat(),
            }
        return self.data["sessions"][concept_id]

    def record_attempt(self, concept_id: str, user_explanation: str,
                       score: int, feedback: str, gaps: List[str],
                       strengths: List[str]):
        """
        Enregistre une tentative d'explication Feynman.
        
        Args:
            concept_id: ID du concept
            user_explanation: L'explication de l'utilisateur
            score: Score de qualité 0-100 (donné par l'IA)
            feedback: Feedback détaillé de l'IA
            gaps: Lacunes identifiées
            strengths: Points forts de l'explication
        """
        if concept_id not in self.data["sessions"]:
            return

        session = self.data["sessions"][concept_id]
        session["attempts"] += 1
        session["best_score"] = max(session["best_score"], score)

        session["history"].append({
            "date": datetime.now().isoformat(),
            "explanation_length": len(user_explanation),
            "score": score,
            "feedback": feedback,
            "gaps": gaps,
            "strengths": strengths,
        })

        # Mise à jour du statut
        if score >= 80:
            session["status"] = "mastered"
        else:
            session["status"] = "in_progress"

        self.data["total_sessions"] += 1
        self.data["concepts_mastered"] = sum(
            1 for s in self.data["sessions"].values()
            if s["status"] == "mastered"
        )

        self._save()

    def get_concept_status(self, concept_id: str) -> Dict:
        """Statut d'un concept pour la technique Feynman"""
        return self.data["sessions"].get(concept_id, {
            "attempts": 0,
            "best_score": 0,
            "status": "not_started",
        })

    def get_concepts_to_review(self) -> List[Dict]:
        """Concepts qui n'ont pas encore atteint la maîtrise Feynman"""
        to_review = []
        for cid, session in self.data["sessions"].items():
            if session["status"] != "mastered":
                to_review.append({
                    "concept_id": cid,
                    **session,
                })
        return sorted(to_review, key=lambda x: x["best_score"])

    def get_stats(self) -> Dict:
        """Statistiques globales Feynman"""
        sessions = self.data["sessions"]
        total = len(sessions)
        if total == 0:
            return {
                "total_concepts": 0,
                "mastered": 0,
                "in_progress": 0,
                "not_started": 0,
                "average_score": 0,
                "total_attempts": 0,
            }

        mastered = sum(1 for s in sessions.values() if s["status"] == "mastered")
        in_progress = sum(1 for s in sessions.values() if s["status"] == "in_progress")
        scores = [s["best_score"] for s in sessions.values() if s["best_score"] > 0]

        return {
            "total_concepts": total,
            "mastered": mastered,
            "in_progress": in_progress,
            "not_started": total - mastered - in_progress,
            "average_score": sum(scores) / len(scores) if scores else 0,
            "total_attempts": self.data["total_sessions"],
            "mastery_rate": mastered / total * 100 if total > 0 else 0,
        }


def build_feynman_prompt(concept_name: str, module: str,
                         concept_description: str = "",
                         user_explanation: str = "",
                         previous_gaps: List[str] = None) -> str:
    """
    Construit le prompt pour l'IA qui évalue l'explication Feynman.
    
    L'IA doit :
    1. Évaluer si l'explication est correcte et complète
    2. Identifier les lacunes et erreurs
    3. Donner un score de compréhension 0-100
    4. Suggérer des améliorations
    """
    previous_context = ""
    if previous_gaps:
        previous_context = f"""
L'utilisateur a déjà tenté d'expliquer ce concept. Voici les lacunes identifiées précédemment :
{chr(10).join(f'- {g}' for g in previous_gaps)}

Vérifie si ces lacunes sont maintenant comblées.
"""

    return f"""Tu es un formateur expert pour le Brevet Fédéral de Spécialiste de Réseau (électricien de réseau) en Suisse.

L'utilisateur utilise la TECHNIQUE FEYNMAN pour approfondir sa compréhension d'un concept.

📚 **CONCEPT :** {concept_name}
📁 **MODULE :** {module}
{"📝 **DESCRIPTION DU COURS :** " + concept_description if concept_description else ""}

{previous_context}

L'utilisateur a donné l'explication suivante avec ses propres mots :

---
{user_explanation}
---

🎯 **TA MISSION :**
Évalue cette explication selon la technique Feynman en répondant STRICTEMENT en JSON :

```json
{{
    "score": <0-100>,
    "verdict": "<EXCELLENT|BON|MOYEN|INSUFFISANT|FAUX>",
    "feedback": "<Feedback constructif et encourageant en 2-3 phrases>",
    "strengths": ["<point fort 1>", "<point fort 2>"],
    "gaps": ["<lacune 1>", "<lacune 2>"],
    "corrections": ["<correction si erreur factuelle>"],
    "tip": "<Un conseil concret pour mieux mémoriser ce concept>",
    "simplified_explanation": "<Ta propre explication simplifiée en 2-3 phrases, comme modèle>"
}}
```

**Critères d'évaluation :**
- **90-100** : Explication parfaite, complète, avec des exemples pertinents
- **70-89** : Bonne compréhension, quelques détails manquants
- **50-69** : Compréhension partielle, lacunes significatives
- **30-49** : Compréhension superficielle, concepts clés manquants
- **0-29** : Explication incorrecte ou trop vague

**IMPORTANT :**
- Sois CONSTRUCTIF, pas décourageant
- Si l'explication est bonne mais incomplète, dis-le
- Fournis TOUJOURS ta propre explication simplifiée comme modèle
- Les corrections ne concernent que les erreurs FACTUELLES (pas le style)
- Contextualise pour le métier d'électricien de réseau en Suisse
"""


def build_feynman_concept_prompt(module: str, concepts: list) -> str:
    """
    Prompt pour choisir les concepts les plus importants 
    d'un module pour la technique Feynman.
    """
    concepts_str = "\n".join(f"- {c.get('name', 'N/A')}: {c.get('description', '')[:100]}"
                             for c in concepts[:20])

    return f"""Pour le module {module} du Brevet Fédéral Spécialiste de Réseau, 
voici les concepts identifiés :

{concepts_str}

Choisis les 5 concepts les PLUS IMPORTANTS pour l'examen qui bénéficieraient 
le plus de la technique Feynman (compréhension profonde plutôt que simple mémorisation).

Réponds en JSON :
```json
{{
    "top_concepts": [
        {{"name": "...", "reason": "Pourquoi ce concept nécessite une compréhension profonde"}}
    ]
}}
```
"""
