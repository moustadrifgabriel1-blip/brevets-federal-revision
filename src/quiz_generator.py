"""
Générateur de quiz basé sur l'IA pour le Brevet Fédéral
Crée des QCM à partir des concepts analysés
"""
import json
import random
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import google.generativeai as genai
import os


class QuizGenerator:
    """Génère des quiz interactifs basés sur les concepts du Brevet Fédéral"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-3-pro-preview"):
        self.api_key = api_key or os.getenv('GOOGLE_API_KEY')
        self.model_name = model
        self.history_file = Path("data/quiz_history.json")
        
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel(self.model_name)
    
    def generate_quiz(self, concepts: List[Dict], module: str = None, 
                     num_questions: int = 10, difficulty: str = "moyen") -> Dict:
        """
        Génère un quiz à partir des concepts
        
        Args:
            concepts: Liste des concepts à tester
            module: Module spécifique (ex: "AA01") ou None pour mélangé
            num_questions: Nombre de questions à générer
            difficulty: Niveau de difficulté (facile, moyen, difficile)
        
        Returns:
            Dict avec les questions et métadonnées
        """
        # Filtrer par module si spécifié
        filtered_concepts = concepts
        if module:
            filtered_concepts = [c for c in concepts if c.get('module') == module]
        
        if not filtered_concepts:
            return {"error": "Aucun concept trouvé pour ce module"}
        
        # Sélectionner aléatoirement les concepts
        selected = random.sample(filtered_concepts, min(num_questions, len(filtered_concepts)))
        
        # Générer les questions avec l'IA
        questions = []
        for i, concept in enumerate(selected, 1):
            question = self._generate_question(concept, difficulty, i)
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
    
    def _generate_question(self, concept: Dict, difficulty: str, question_num: int) -> Optional[Dict]:
        """Génère une question QCM pour un concept donné"""
        try:
            prompt = f"""
Génère une question à choix multiples (QCM) pour tester la compréhension de ce concept :

**Concept :** {concept.get('name', 'N/A')}
**Description :** {concept.get('description', 'N/A')}
**Importance :** {concept.get('importance', 3)}/5
**Difficulté souhaitée :** {difficulty}

Format de réponse (JSON strict) :
{{
  "question": "Texte de la question claire et précise",
  "options": [
    "Option A - première réponse",
    "Option B - deuxième réponse",
    "Option C - troisième réponse",
    "Option D - quatrième réponse"
  ],
  "correct_answer": 0,
  "explanation": "Explication détaillée de la bonne réponse et pourquoi les autres sont incorrectes"
}}

IMPORTANT :
- correct_answer est l'INDEX (0-3) de la bonne réponse dans options
- La question doit être en français
- Les distracteurs (mauvaises réponses) doivent être plausibles
- L'explication doit être pédagogique
"""
            
            response = self.model.generate_content(prompt)
            
            # Parser la réponse JSON
            text = response.text.strip()
            # Nettoyer le markdown si présent
            if text.startswith("```json"):
                text = text.replace("```json", "").replace("```", "").strip()
            elif text.startswith("```"):
                text = text.replace("```", "").strip()
            
            question_data = json.loads(text)
            
            # Ajouter les métadonnées
            question_data["concept_id"] = concept.get('id')
            question_data["concept_name"] = concept.get('name')
            question_data["question_num"] = question_num
            
            return question_data
            
        except Exception as e:
            print(f"Erreur génération question: {e}")
            # Générer une question fallback simple
            return self._generate_fallback_question(concept, question_num)
    
    def _generate_fallback_question(self, concept: Dict, question_num: int) -> Dict:
        """Génère une question simple si l'IA échoue"""
        return {
            "question": f"Que représente le concept '{concept.get('name', 'inconnu')}' ?",
            "options": [
                concept.get('description', 'Description du concept')[:100],
                "Une autre définition non liée",
                "Un concept différent",
                "Aucune de ces réponses"
            ],
            "correct_answer": 0,
            "explanation": f"La bonne réponse est la première car elle décrit correctement {concept.get('name')}.",
            "concept_id": concept.get('id'),
            "concept_name": concept.get('name'),
            "question_num": question_num,
            "fallback": True
        }
    
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
