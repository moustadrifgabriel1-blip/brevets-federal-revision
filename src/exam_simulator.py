"""
Mode Examen Blanc - Brevet Fédéral Spécialiste de Réseau
=========================================================
Simule les conditions réelles de l'examen avec :
- Questions réparties par modules (AA + AE)
- Timer global
- Score par module pour identifier les faiblesses
- Historique des examens blancs
"""

import json
import random
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from collections import defaultdict

import google.generativeai as genai
import os


# Structure de l'examen selon les directives EP 01.01.2024
EXAM_STRUCTURE = {
    "duree_minutes": 120,  # 2 heures
    "total_questions": 42,
    "repartition": {
        # Modules de base (AA) — ~50% des questions
        "AA01": {"questions": 2, "label": "Conduite de collaborateurs"},
        "AA02": {"questions": 1, "label": "Formation"},
        "AA03": {"questions": 2, "label": "Préparation du travail"},
        "AA04": {"questions": 2, "label": "Exécution de mandats"},
        "AA05": {"questions": 3, "label": "Santé et sécurité au travail"},
        "AA06": {"questions": 1, "label": "Suivi des travaux"},
        "AA07": {"questions": 1, "label": "Bases de la maintenance"},
        "AA08": {"questions": 2, "label": "Maintenance des équipements"},
        "AA09": {"questions": 3, "label": "Électrotechnique"},
        "AA10": {"questions": 1, "label": "Mécanique"},
        "AA11": {"questions": 2, "label": "Mathématique"},
        # Modules spécialisés (AE) — ~50% des questions
        "AE01": {"questions": 2, "label": "Étude de projet"},
        "AE02": {"questions": 3, "label": "Sécurité sur et à prox. d'IE"},
        "AE03": {"questions": 2, "label": "Éclairage public"},
        "AE04": {"questions": 1, "label": "Documentation de réseaux"},
        "AE05": {"questions": 2, "label": "Installations mise à terre"},
        "AE06": {"questions": 2, "label": "Exploitation de réseaux"},
        "AE07": {"questions": 2, "label": "Technique de mesure"},
        "AE09": {"questions": 2, "label": "Technique de protection"},
        "AE10": {"questions": 1, "label": "Maintenance des réseaux"},
        "AE11": {"questions": 2, "label": "Travail de projet"},
        "AE12": {"questions": 2, "label": "Lignes souterraines"},
        "AE13": {"questions": 1, "label": "Lignes aériennes"},
    }
}


class ExamGenerator:
    """Génère un examen blanc complet simulant les conditions réelles"""

    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-3-pro-preview"):
        self.api_key = api_key or os.getenv('GOOGLE_API_KEY')
        self.model_name = model
        self.history_file = Path("data/exam_history.json")
        self.model = None

        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel(self.model_name)

    def generate_exam(self, concepts: List[Dict], directives_coverage: Dict = None) -> Dict:
        """
        Génère un examen blanc complet avec questions réparties par module.
        
        Args:
            concepts: Liste de tous les concepts analysés
            directives_coverage: Couverture des directives (pour cibler les lacunes)
        
        Returns:
            Dict complet de l'examen
        """
        all_questions = []
        question_num = 0

        # Regrouper les concepts par module
        concepts_by_module = defaultdict(list)
        for c in concepts:
            mod = c.get('module')
            if mod:
                concepts_by_module[mod].append(c)

        for module_code, module_info in EXAM_STRUCTURE['repartition'].items():
            nb_questions = module_info['questions']
            module_concepts = concepts_by_module.get(module_code, [])

            for _ in range(nb_questions):
                question_num += 1
                question = self._generate_exam_question(
                    module_code=module_code,
                    module_label=module_info['label'],
                    concepts=module_concepts,
                    question_num=question_num,
                    directives_coverage=directives_coverage
                )
                if question:
                    all_questions.append(question)

        # Mélanger les questions pour simuler l'examen réel
        random.shuffle(all_questions)
        # Renuméroter
        for i, q in enumerate(all_questions, 1):
            q['question_num'] = i

        exam = {
            "id": f"exam_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "type": "examen_blanc",
            "duree_minutes": EXAM_STRUCTURE['duree_minutes'],
            "total_questions": len(all_questions),
            "questions": all_questions,
            "created_at": datetime.now().isoformat(),
            "modules_tested": list(EXAM_STRUCTURE['repartition'].keys()),
        }

        return exam

    def _generate_exam_question(self, module_code: str, module_label: str,
                                 concepts: List[Dict], question_num: int,
                                 directives_coverage: Dict = None) -> Optional[Dict]:
        """Génère une question d'examen pour un module donné — V2 enrichie"""
        
        # Si on a des concepts pour ce module, en choisir un (pondéré par importance)
        if concepts:
            # Sélection pondérée par importance
            importance_weights = {"critical": 4, "high": 3, "medium": 2, "low": 1}
            weights = [importance_weights.get(c.get('importance', 'medium'), 2) for c in concepts]
            concept = random.choices(concepts, weights=weights, k=1)[0]
            
            concept_name = concept.get('name', 'N/A')
            concept_keywords = ', '.join(concept.get('keywords', []))
            concept_page_ref = concept.get('page_references', '')
            concept_source = concept.get('source_document', '')
            concept_category = concept.get('category', '')
            concept_prerequisites = ', '.join(concept.get('prerequisites', []))
        else:
            concept = None
            concept_name = module_label
            concept_keywords = module_label
            concept_page_ref = ''
            concept_source = ''
            concept_category = ''
            concept_prerequisites = ''

        # Enrichir avec les compétences des directives d'examen
        from src.directives_coverage import EXAM_REQUIREMENTS
        exam_req = EXAM_REQUIREMENTS.get(module_code, {})
        exam_competences = exam_req.get('competences', [])
        poids_examen = exam_req.get('poids_examen', '')
        
        # Enrichir avec les lacunes détectées
        concept_desc = f"Compétences du module {module_code} - {module_label}"
        if directives_coverage and module_code in directives_coverage:
            gaps = directives_coverage[module_code].get('gaps', [])
            competences = directives_coverage[module_code].get('competences', [])
            if gaps:
                concept_desc = f"Compétence requise (lacune détectée) : {random.choice(gaps)}"
            elif competences:
                concept_desc = f"Compétence requise : {random.choice(competences)}"

        try:
            # Construction du contexte enrichi
            context_parts = [
                f"**Module :** {module_code} — {module_label}",
                f"**Thème/Concept :** {concept_name}",
            ]
            if concept_keywords:
                context_parts.append(f"**Mots-clés techniques :** {concept_keywords}")
            if concept_category:
                context_parts.append(f"**Catégorie :** {concept_category}")
            if concept_page_ref:
                context_parts.append(f"**Référence cours :** {concept_page_ref}")
            if concept_source:
                context_parts.append(f"**Document source :** {concept_source}")
            if concept_prerequisites:
                context_parts.append(f"**Prérequis :** {concept_prerequisites}")
            if exam_competences:
                relevant_comps = random.sample(exam_competences, min(3, len(exam_competences)))
                context_parts.append(f"**Compétences d'examen à évaluer :**")
                for comp in relevant_comps:
                    context_parts.append(f"  - {comp}")
            if poids_examen:
                context_parts.append(f"**Format d'évaluation :** {poids_examen}")
            context_parts.append(f"**Contexte additionnel :** {concept_desc}")
            
            context_block = '\n'.join(context_parts)

            prompt = f"""Tu es un examinateur expert pour le Brevet Fédéral Spécialiste de Réseau orientation Énergie en Suisse.

Génère UNE question d'examen de niveau professionnel fédéral.

{context_block}

CONSIGNES STRICTES :
1. La question doit correspondre au niveau d'un examen professionnel fédéral (pas trop facile)
2. La question doit être CONCRÈTE et TECHNIQUE — utilise les mots-clés techniques fournis
3. Privilégie les mises en situation professionnelles réalistes (chantier, maintenance, diagnostic)
4. Les 4 options doivent être PLAUSIBLES et de longueur similaire
5. L'explication doit être détaillée et PÉDAGOGIQUE avec référence aux normes (ESTI, NIBT, SUVA, EN)
6. Ne génère JAMAIS de question vague du type "Que représente le concept X ?"
7. La question doit tester une COMPÉTENCE RÉELLE du professionnel

Réponds UNIQUEMENT en JSON strict :
{{
  "question": "Question technique précise en contexte professionnel",
  "options": [
    "Option A",
    "Option B",
    "Option C",
    "Option D"
  ],
  "correct_answer": 0,
  "explanation": "Explication détaillée avec la règle/norme/calcul applicable",
  "difficulty": "examen",
  "topic": "{module_label}"
}}

correct_answer = INDEX (0-3) de la bonne réponse. Tout en français."""

            response = self.model.generate_content(prompt)
            text = response.text.strip()

            # Nettoyer markdown
            if text.startswith("```json"):
                text = text.replace("```json", "").replace("```", "").strip()
            elif text.startswith("```"):
                text = text.replace("```", "").strip()

            question_data = json.loads(text)
            question_data["module"] = module_code
            question_data["module_label"] = module_label
            question_data["concept_name"] = concept_name
            question_data["question_num"] = question_num
            question_data["type"] = "qcm"

            return question_data

        except Exception as e:
            print(f"Erreur génération question examen {module_code}: {e}")
            return self._generate_fallback_exam_question(module_code, module_label, concept_name, question_num)

    def _generate_fallback_exam_question(self, module_code: str, module_label: str,
                                          concept_name: str, question_num: int) -> Dict:
        """Question de secours de qualité professionnelle si l'IA échoue"""
        
        # Utiliser les compétences d'examen pour générer des questions pertinentes
        from src.directives_coverage import EXAM_REQUIREMENTS
        exam_req = EXAM_REQUIREMENTS.get(module_code, {})
        competences = exam_req.get('competences', [])
        
        if competences:
            comp = random.choice(competences)
            # Générer une question basée sur la compétence d'examen
            return {
                "question": f"Dans le cadre du module {module_code} ({module_label}), quelle action est correcte concernant la compétence : '{comp}' ?",
                "options": [
                    f"Appliquer les procédures normalisées et les normes suisses en vigueur (ESTI, NIBT, SUVA)",
                    "Procéder selon son expérience personnelle sans consulter les prescriptions",
                    "Déléguer systématiquement cette tâche sans supervision",
                    "Cette compétence n'est pas requise pour le Brevet Fédéral"
                ],
                "correct_answer": 0,
                "explanation": f"Pour le module {module_code} ({module_label}), la compétence '{comp}' doit toujours être exercée conformément aux normes et prescriptions suisses. C'est une exigence des directives d'examen du Brevet Fédéral.",
                "module": module_code,
                "module_label": module_label,
                "concept_name": concept_name,
                "question_num": question_num,
                "difficulty": "examen",
                "type": "qcm",
                "fallback": True,
            }
        
        return {
            "question": f"Pour le module {module_code} ({module_label}), quelle approche est recommandée pour maîtriser '{concept_name}' en vue de l'examen ?",
            "options": [
                "Étudier la théorie ET pratiquer sur le terrain en respectant les normes suisses",
                "Se concentrer uniquement sur la théorie sans pratique",
                "Se fier uniquement à l'expérience de terrain sans formation théorique",
                "Ce sujet n'est jamais évalué à l'examen du Brevet Fédéral"
            ],
            "correct_answer": 0,
            "explanation": f"Le Brevet Fédéral évalue à la fois les connaissances théoriques et les compétences pratiques. Le module {module_code} ({module_label}) requiert une maîtrise complète de '{concept_name}'.",
            "module": module_code,
            "module_label": module_label,
            "concept_name": concept_name,
            "question_num": question_num,
            "difficulty": "examen",
            "type": "qcm",
            "fallback": True,
        }

    def evaluate_exam(self, exam: Dict, answers: Dict[int, any]) -> Dict:
        """
        Évalue un examen blanc et calcule les scores par module.
        Supporte tous les types de questions (QCM, vrai/faux, calcul, etc.)
        
        Args:
            exam: L'examen généré
            answers: {question_num: réponse_utilisateur}
        
        Returns:
            Résultats détaillés avec score par module
        """
        from src.quiz_generator import evaluate_answer
        
        total_correct = 0
        total_questions = len(exam['questions'])
        results_by_module = defaultdict(lambda: {"correct": 0, "total": 0, "questions": []})
        question_results = []

        for question in exam['questions']:
            q_num = question['question_num']
            user_answer = answers.get(q_num, -1)
            correct_answer = question['correct_answer']
            
            is_correct = evaluate_answer(question, user_answer)

            if is_correct:
                total_correct += 1

            module = question.get('module', 'Unknown')
            results_by_module[module]['total'] += 1
            if is_correct:
                results_by_module[module]['correct'] += 1

            q_result = {
                "question_num": q_num,
                "module": module,
                "module_label": question.get('module_label', ''),
                "concept_name": question.get('concept_name', ''),
                "user_answer": user_answer,
                "correct_answer": correct_answer,
                "is_correct": is_correct,
            }
            question_results.append(q_result)
            results_by_module[module]['questions'].append(q_result)

        # Calculer les pourcentages par module
        module_scores = {}
        for mod, data in results_by_module.items():
            pct = (data['correct'] / data['total'] * 100) if data['total'] > 0 else 0
            label = EXAM_STRUCTURE['repartition'].get(mod, {}).get('label', mod)
            module_scores[mod] = {
                "label": label,
                "correct": data['correct'],
                "total": data['total'],
                "percentage": pct,
                "status": "réussi" if pct >= 50 else "échoué",
                "questions": data['questions'],
            }

        # Score global
        global_pct = (total_correct / total_questions * 100) if total_questions > 0 else 0

        # Identifier les modules faibles
        weak_modules = sorted(
            [m for m, s in module_scores.items() if s['percentage'] < 50],
            key=lambda m: module_scores[m]['percentage']
        )
        strong_modules = sorted(
            [m for m, s in module_scores.items() if s['percentage'] >= 70],
            key=lambda m: module_scores[m]['percentage'],
            reverse=True
        )

        return {
            "exam_id": exam['id'],
            "total_correct": total_correct,
            "total_questions": total_questions,
            "global_percentage": global_pct,
            "passed": global_pct >= 50,
            "module_scores": module_scores,
            "weak_modules": weak_modules,
            "strong_modules": strong_modules,
            "question_results": question_results,
        }

    def save_exam_result(self, results: Dict, time_spent: int):
        """Sauvegarde les résultats d'un examen blanc"""
        history = self._load_history()

        entry = {
            "exam_id": results['exam_id'],
            "global_percentage": results['global_percentage'],
            "total_correct": results['total_correct'],
            "total_questions": results['total_questions'],
            "passed": results['passed'],
            "module_scores": {
                mod: {"correct": s['correct'], "total": s['total'], "percentage": s['percentage']}
                for mod, s in results['module_scores'].items()
            },
            "weak_modules": results['weak_modules'],
            "time_spent": time_spent,
            "completed_at": datetime.now().isoformat(),
        }

        history.append(entry)
        self._save_history(history)

    def _load_history(self) -> List[Dict]:
        if self.history_file.exists():
            with open(self.history_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []

    def _save_history(self, history: List[Dict]):
        self.history_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.history_file, 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=2, ensure_ascii=False)

    def get_history(self, limit: int = 10) -> List[Dict]:
        history = self._load_history()
        return sorted(history, key=lambda x: x['completed_at'], reverse=True)[:limit]

    def get_stats(self) -> Dict:
        history = self._load_history()
        if not history:
            return {
                "total_exams": 0,
                "average_score": 0,
                "best_score": 0,
                "pass_rate": 0,
                "weakest_modules": [],
            }

        avg = sum(h['global_percentage'] for h in history) / len(history)
        best = max(h['global_percentage'] for h in history)
        passed = sum(1 for h in history if h['passed'])

        # Modules les plus faibles sur tous les examens
        module_totals = defaultdict(lambda: {"correct": 0, "total": 0})
        for h in history:
            for mod, scores in h.get('module_scores', {}).items():
                module_totals[mod]['correct'] += scores['correct']
                module_totals[mod]['total'] += scores['total']

        weakest = sorted(
            module_totals.items(),
            key=lambda x: (x[1]['correct'] / x[1]['total'] * 100) if x[1]['total'] > 0 else 0
        )[:5]

        return {
            "total_exams": len(history),
            "average_score": avg,
            "best_score": best,
            "pass_rate": (passed / len(history) * 100) if history else 0,
            "weakest_modules": [
                {"module": m, "percentage": (d['correct']/d['total']*100) if d['total'] > 0 else 0}
                for m, d in weakest
            ],
        }
