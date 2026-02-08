"""
Générateur de quiz basé sur l'IA pour le Brevet Fédéral
Génère des questions variées : QCM, Vrai/Faux, Texte à trous, Calcul, Mise en situation
"""
import json
import random
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import google.generativeai as genai
import os


# Types de questions supportés avec distribution pondérée
QUESTION_TYPES = {
    "qcm": {"label": "QCM (4 choix)", "weight": 35, "icon": "📋"},
    "vrai_faux": {"label": "Vrai / Faux", "weight": 20, "icon": "✅"},
    "texte_trous": {"label": "Texte à trous", "weight": 15, "icon": "✏️"},
    "calcul": {"label": "Calcul", "weight": 15, "icon": "🔢"},
    "mise_en_situation": {"label": "Mise en situation", "weight": 15, "icon": "🏗️"},
}

# Modules où les questions de calcul sont pertinentes
CALCUL_MODULES = {"AA09", "AA10", "AA11", "AE05", "AE07"}


def evaluate_answer(question: Dict, user_answer) -> bool:
    """Évalue si la réponse de l'utilisateur est correcte, tous types confondus."""
    q_type = question.get('type', 'qcm')

    if user_answer is None:
        return False

    if q_type in ('qcm', 'mise_en_situation'):
        return user_answer == question.get('correct_answer')

    elif q_type == 'vrai_faux':
        return user_answer == question.get('correct_answer')

    elif q_type == 'texte_trous':
        acceptable = question.get('acceptable_answers', [str(question.get('correct_answer', ''))])
        user_clean = str(user_answer).strip().lower()
        return user_clean in [str(a).strip().lower() for a in acceptable]

    elif q_type == 'calcul':
        try:
            val = float(str(user_answer).replace(',', '.').strip())
            correct_val = float(question['correct_answer'])
            tolerance = question.get('tolerance', 0.02)
            if correct_val == 0:
                return abs(val) < 0.01
            return abs(val - correct_val) / abs(correct_val) <= tolerance
        except (ValueError, TypeError):
            return False

    return False


class QuizGenerator:
    """Génère des quiz interactifs basés sur les concepts du Brevet Fédéral"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-3-pro-preview"):
        self.api_key = api_key or os.getenv('GOOGLE_API_KEY')
        self.model_name = model
        self.history_file = Path("data/quiz_history.json")
        self.model = None
        
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel(self.model_name)
    
    def generate_quiz(self, concepts: List[Dict], module: str = None, 
                     num_questions: int = 10, difficulty: str = "moyen",
                     weak_concept_ids: List[str] = None,
                     question_types: List[str] = None) -> Dict:
        """
        Génère un quiz à partir des concepts
        
        Args:
            concepts: Liste des concepts à tester
            module: Module spécifique (ex: "AA01") ou None pour mélangé
            num_questions: Nombre de questions à générer
            difficulty: Niveau de difficulté (facile, moyen, difficile)
            weak_concept_ids: IDs des concepts faibles à prioriser (quiz adaptatif)
            question_types: Types de questions à inclure (liste parmi QUESTION_TYPES.keys())
        
        Returns:
            Dict avec les questions et métadonnées
        """
        # Filtrer par module si spécifié
        filtered_concepts = concepts
        if module:
            filtered_concepts = [c for c in concepts if c.get('module') == module]
        
        if not filtered_concepts:
            return {"error": "Aucun concept trouvé pour ce module"}
        
        # --- QUIZ ADAPTATIF : prioriser les concepts faibles ---
        if weak_concept_ids:
            weak_set = set(weak_concept_ids)
            weak_concepts = [c for c in filtered_concepts if c.get('id') in weak_set or c.get('name') in weak_set]
            other_concepts = [c for c in filtered_concepts if c.get('id') not in weak_set and c.get('name') not in weak_set]
            
            # Prendre ~60% des questions sur les concepts faibles
            num_weak = min(len(weak_concepts), int(num_questions * 0.6))
            num_other = min(len(other_concepts), num_questions - num_weak)
            
            selected_weak = random.sample(weak_concepts, num_weak) if weak_concepts else []
            selected_other = random.sample(other_concepts, num_other) if other_concepts else []
            selected = selected_weak + selected_other
            random.shuffle(selected)
        else:
            # Sélection aléatoire classique
            selected = random.sample(filtered_concepts, min(num_questions, len(filtered_concepts)))
        
        # Générer les questions avec l'IA (types variés)
        questions = []
        for i, concept in enumerate(selected, 1):
            question = self._generate_question(
                concept, difficulty, i,
                question_types=question_types,
                module=module
            )
            if question:
                questions.append(question)
        
        quiz = {
            "id": f"quiz_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "module": module or "Tous modules",
            "difficulty": difficulty,
            "num_questions": len(questions),
            "questions": questions,
            "created_at": datetime.now().isoformat()
        }
        
        return quiz
    
    def _generate_question(self, concept: Dict, difficulty: str, question_num: int,
                           question_types: List[str] = None, module: str = None) -> Optional[Dict]:
        """Dispatche vers le bon générateur selon le type de question choisi."""
        available_types = list(question_types) if question_types else list(QUESTION_TYPES.keys())

        # Calcul seulement pour modules techniques
        if module and module not in CALCUL_MODULES:
            available_types = [t for t in available_types if t != "calcul"]
        if not available_types:
            available_types = ["qcm"]

        # Choix pondéré du type
        weights = [QUESTION_TYPES[t]["weight"] for t in available_types]
        chosen_type = random.choices(available_types, weights=weights, k=1)[0]

        generators = {
            "qcm": self._generate_qcm,
            "vrai_faux": self._generate_vrai_faux,
            "texte_trous": self._generate_texte_trous,
            "calcul": self._generate_calcul,
            "mise_en_situation": self._generate_mise_en_situation,
        }

        generator = generators.get(chosen_type, self._generate_qcm)
        question = generator(concept, difficulty, question_num)

        if question:
            question["type"] = chosen_type
        return question

    # --- Utilitaires internes ---

    def _parse_ai_response(self, response) -> Dict:
        """Parse et nettoie la réponse JSON de l'IA."""
        text = response.text.strip()
        if text.startswith("```json"):
            text = text.replace("```json", "").replace("```", "").strip()
        elif text.startswith("```"):
            text = text.replace("```", "").strip()
        return json.loads(text)

    def _add_metadata(self, data: Dict, concept: Dict, question_num: int) -> Dict:
        """Ajoute les métadonnées du concept."""
        data["concept_id"] = concept.get('id')
        data["concept_name"] = concept.get('name')
        data["question_num"] = question_num
        return data

    # --- Générateurs par type ---

    def _generate_qcm(self, concept: Dict, difficulty: str, question_num: int) -> Optional[Dict]:
        """Génère une question QCM classique (4 choix)."""
        try:
            prompt = f"""Génère une question à choix multiples (QCM) pour le Brevet Fédéral.

**Concept :** {concept.get('name', 'N/A')}
**Description :** {concept.get('description', 'N/A')}
**Difficulté :** {difficulty}

Réponds en JSON strict :
{{
  "question": "Question claire et précise",
  "options": ["Option A", "Option B", "Option C", "Option D"],
  "correct_answer": 0,
  "explanation": "Explication détaillée"
}}

IMPORTANT : correct_answer = INDEX (0-3). En français. Distracteurs plausibles."""

            response = self.model.generate_content(prompt)
            data = self._parse_ai_response(response)
            return self._add_metadata(data, concept, question_num)
        except Exception as e:
            print(f"Erreur QCM: {e}")
            return self._generate_fallback(concept, question_num, "qcm")

    def _generate_vrai_faux(self, concept: Dict, difficulty: str, question_num: int) -> Optional[Dict]:
        """Génère une question Vrai/Faux."""
        try:
            prompt = f"""Génère une affirmation VRAI ou FAUX pour le Brevet Fédéral.

**Concept :** {concept.get('name', 'N/A')}
**Description :** {concept.get('description', 'N/A')}
**Difficulté :** {difficulty}

Réponds en JSON strict :
{{
  "question": "Affirmation complète à évaluer comme vraie ou fausse",
  "correct_answer": true,
  "explanation": "Explication détaillée de pourquoi c'est vrai/faux"
}}

IMPORTANT : correct_answer est un booléen (true ou false). L'affirmation doit être technique et précise. En français."""

            response = self.model.generate_content(prompt)
            data = self._parse_ai_response(response)
            # S'assurer que correct_answer est bien un bool
            data['correct_answer'] = bool(data['correct_answer'])
            return self._add_metadata(data, concept, question_num)
        except Exception as e:
            print(f"Erreur Vrai/Faux: {e}")
            return self._generate_fallback(concept, question_num, "vrai_faux")

    def _generate_texte_trous(self, concept: Dict, difficulty: str, question_num: int) -> Optional[Dict]:
        """Génère une question à texte à trous."""
        try:
            prompt = f"""Génère une question à TEXTE À TROUS pour le Brevet Fédéral.

**Concept :** {concept.get('name', 'N/A')}
**Description :** {concept.get('description', 'N/A')}
**Difficulté :** {difficulty}

Réponds en JSON strict :
{{
  "question": "Phrase avec un _____ à compléter (un seul trou)",
  "correct_answer": "mot ou expression correcte",
  "acceptable_answers": ["réponse1", "réponse2", "variante3"],
  "explanation": "Explication détaillée"
}}

IMPORTANT :
- Le trou est marqué par _____ dans la question
- correct_answer = la réponse principale (un mot ou courte expression)
- acceptable_answers = liste de toutes les réponses acceptables (synonymes, variantes)
- Le mot à trouver doit être un terme technique important. En français."""

            response = self.model.generate_content(prompt)
            data = self._parse_ai_response(response)
            # S'assurer que acceptable_answers contient aussi correct_answer
            if data.get('correct_answer') not in data.get('acceptable_answers', []):
                data.setdefault('acceptable_answers', []).append(data['correct_answer'])
            return self._add_metadata(data, concept, question_num)
        except Exception as e:
            print(f"Erreur texte à trous: {e}")
            return self._generate_fallback(concept, question_num, "texte_trous")

    def _generate_calcul(self, concept: Dict, difficulty: str, question_num: int) -> Optional[Dict]:
        """Génère une question de calcul (modules techniques : électro, méca, math)."""
        try:
            prompt = f"""Génère une question de CALCUL pour le Brevet Fédéral (électrotechnique/mécanique/mathématique).

**Concept :** {concept.get('name', 'N/A')}
**Description :** {concept.get('description', 'N/A')}
**Difficulté :** {difficulty}

Réponds en JSON strict :
{{
  "question": "Énoncé du problème avec toutes les données numériques",
  "correct_answer": 42.5,
  "tolerance": 0.02,
  "unit": "Ω",
  "explanation": "Développement complet du calcul étape par étape"
}}

IMPORTANT :
- correct_answer = valeur numérique (nombre, pas de texte)
- tolerance = marge d'erreur relative acceptée (0.02 = 2%)
- unit = unité de mesure (V, A, Ω, W, m, kg, N, etc.)
- La question doit inclure toutes les données nécessaires au calcul
- L'explication doit montrer CHAQUE ÉTAPE du calcul. En français."""

            response = self.model.generate_content(prompt)
            data = self._parse_ai_response(response)
            # S'assurer que correct_answer est numérique
            data['correct_answer'] = float(data['correct_answer'])
            data.setdefault('tolerance', 0.02)
            data.setdefault('unit', '')
            return self._add_metadata(data, concept, question_num)
        except Exception as e:
            print(f"Erreur calcul: {e}")
            return self._generate_fallback(concept, question_num, "calcul")

    def _generate_mise_en_situation(self, concept: Dict, difficulty: str, question_num: int) -> Optional[Dict]:
        """Génère une question de mise en situation professionnelle (QCM avec scénario)."""
        try:
            prompt = f"""Génère une question de MISE EN SITUATION pour le Brevet Fédéral Spécialiste de Réseau.

**Concept :** {concept.get('name', 'N/A')}
**Description :** {concept.get('description', 'N/A')}
**Difficulté :** {difficulty}

Réponds en JSON strict :
{{
  "scenario": "Description détaillée d'une situation professionnelle réelle (2-3 phrases)",
  "question": "Question concrète liée au scénario",
  "options": ["Action A", "Action B", "Action C", "Action D"],
  "correct_answer": 0,
  "explanation": "Explication détaillée avec référence aux normes/bonnes pratiques"
}}

IMPORTANT :
- Le scénario décrit une situation de terrain (chantier, maintenance, incident...)
- correct_answer = INDEX (0-3) de la bonne réponse
- Les options sont des ACTIONS concrètes que le professionnel pourrait entreprendre
- En français."""

            response = self.model.generate_content(prompt)
            data = self._parse_ai_response(response)
            return self._add_metadata(data, concept, question_num)
        except Exception as e:
            print(f"Erreur mise en situation: {e}")
            return self._generate_fallback(concept, question_num, "mise_en_situation")

    # --- Fallback ---

    def _generate_fallback(self, concept: Dict, question_num: int, q_type: str = "qcm") -> Dict:
        """Génère une question de secours si l'IA échoue, adaptée au type demandé."""
        name = concept.get('name', 'inconnu')
        desc = concept.get('description', 'Description du concept')[:100]

        if q_type == "vrai_faux":
            return self._add_metadata({
                "question": f"Le concept '{name}' est fondamental pour le Brevet Fédéral.",
                "correct_answer": True,
                "explanation": f"'{name}' fait partie des compétences requises.",
                "fallback": True,
            }, concept, question_num)

        elif q_type == "texte_trous":
            return self._add_metadata({
                "question": f"Le concept _____ se définit comme : {desc}.",
                "correct_answer": name,
                "acceptable_answers": [name, name.lower()],
                "explanation": f"La réponse est '{name}'.",
                "fallback": True,
            }, concept, question_num)

        elif q_type == "calcul":
            return self._add_metadata({
                "question": f"Si R1 = 10 Ω et R2 = 20 Ω sont en série, quelle est la résistance totale ?",
                "correct_answer": 30.0,
                "tolerance": 0.01,
                "unit": "Ω",
                "explanation": "En série : Rtotal = R1 + R2 = 10 + 20 = 30 Ω",
                "fallback": True,
            }, concept, question_num)

        elif q_type == "mise_en_situation":
            return self._add_metadata({
                "scenario": f"Vous êtes responsable d'un chantier impliquant '{name}'.",
                "question": f"Quelle est la première action à entreprendre concernant '{name}' ?",
                "options": [
                    f"Vérifier les normes relatives à {name}",
                    "Commencer les travaux immédiatement",
                    "Déléguer sans vérification",
                    "Reporter l'intervention",
                ],
                "correct_answer": 0,
                "explanation": f"La vérification des normes est toujours la première étape pour {name}.",
                "fallback": True,
            }, concept, question_num)

        else:  # qcm par défaut
            return self._add_metadata({
                "question": f"Que représente le concept '{name}' ?",
                "options": [desc, "Une autre définition non liée", "Un concept différent", "Aucune de ces réponses"],
                "correct_answer": 0,
                "explanation": f"La bonne réponse décrit correctement {name}.",
                "fallback": True,
            }, concept, question_num)
    
    def save_quiz_result(self, quiz_id: str, score: int, total: int, 
                        time_spent: int, answers: List[Dict]):
        """Sauvegarde le résultat d'un quiz dans l'historique"""
        history = self._load_history()
        
        result = {
            "quiz_id": quiz_id,
            "score": score,
            "total": total,
            "percentage": (score / total * 100) if total > 0 else 0,
            "time_spent": time_spent,
            "answers": answers,
            "completed_at": datetime.now().isoformat()
        }
        
        history.append(result)
        self._save_history(history)
    
    def _load_history(self) -> List[Dict]:
        """Charge l'historique des quiz"""
        if self.history_file.exists():
            with open(self.history_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    
    def _save_history(self, history: List[Dict]):
        """Sauvegarde l'historique des quiz"""
        self.history_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.history_file, 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
    
    def get_history(self, limit: int = 10) -> List[Dict]:
        """Retourne l'historique des derniers quiz"""
        history = self._load_history()
        return sorted(history, key=lambda x: x['completed_at'], reverse=True)[:limit]
    
    def get_stats(self) -> Dict:
        """Calcule les statistiques globales des quiz"""
        history = self._load_history()
        
        if not history:
            return {
                "total_quizzes": 0,
                "average_score": 0,
                "best_score": 0,
                "total_time": 0,
                "total_questions": 0
            }
        
        return {
            "total_quizzes": len(history),
            "average_score": sum(q['percentage'] for q in history) / len(history),
            "best_score": max(q['percentage'] for q in history),
            "total_time": sum(q.get('time_spent', 0) for q in history),
            "total_questions": sum(q['total'] for q in history)
        }
