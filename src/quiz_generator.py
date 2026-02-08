"""
Générateur de quiz basé sur l'IA pour le Brevet Fédéral
Génère des questions variées : QCM, Vrai/Faux, Texte à trous, Calcul, Mise en situation

VERSION 3.0 — Premium :
- Génération BATCH : 1 seul appel IA pour toutes les questions (plus rapide, cohérent)
- Banque de questions persistante : les bonnes questions sont sauvegardées et réutilisées
- Système d'INDICES (hints) : chaque question a un indice caché
- Niveau de CONFIANCE : l'utilisateur indique s'il devine, hésite ou est sûr
- Analytics premium : progression, score par type, tendances
- Prompts enrichis avec compétences d'examen, mots-clés, références cours
- Sélection pondérée par importance (critical > high > medium > low)
- Fallbacks de qualité professionnelle (jamais de question triviale)
- Validation des réponses IA (cohérence, déduplication)
"""
import json
import random
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from collections import defaultdict
import google.generativeai as genai
import os


# Types de questions supportés avec distribution pondérée
QUESTION_TYPES = {
    "qcm": {"label": "QCM (4 choix)", "weight": 30, "icon": "📋"},
    "vrai_faux": {"label": "Vrai / Faux", "weight": 15, "icon": "✅"},
    "texte_trous": {"label": "Texte à trous", "weight": 15, "icon": "✏️"},
    "calcul": {"label": "Calcul", "weight": 15, "icon": "🔢"},
    "mise_en_situation": {"label": "Mise en situation", "weight": 25, "icon": "🏗️"},
}

# Modules où les questions de calcul sont pertinentes
CALCUL_MODULES = {"AA09", "AA10", "AA11", "AE05", "AE07"}

# Pondération pour la sélection de concepts par importance
IMPORTANCE_WEIGHTS = {
    "critical": 4.0,
    "high": 3.0,
    "medium": 2.0,
    "low": 1.0,
}

# Compétences d'examen par module (injectées dans les prompts)
EXAM_COMPETENCES = {
    "AA01": [
        "Diriger une équipe de collaborateurs sur le terrain",
        "Planifier et répartir les tâches de travail",
        "Communiquer de manière efficace et constructive",
        "Gérer les conflits au sein de l'équipe",
        "Évaluer les performances des collaborateurs",
    ],
    "AA02": [
        "Planifier et organiser la formation des apprentis",
        "Transmettre les compétences professionnelles",
        "Évaluer les progrès de formation",
        "Appliquer les méthodes pédagogiques adaptées",
        "Connaître le cadre légal de la formation professionnelle",
    ],
    "AA03": [
        "Lire et interpréter les plans et schémas techniques",
        "Établir des listes de matériel et outillage",
        "Planifier le déroulement des travaux (logistique, délais)",
        "Évaluer les risques liés aux travaux",
        "Rédiger des rapports et de la documentation technique",
    ],
    "AA04": [
        "Gérer un mandat du début à la fin (offre → facturation)",
        "Respecter les délais et budgets",
        "Coordonner les intervenants sur un chantier",
        "Appliquer les normes et prescriptions en vigueur",
    ],
    "AA05": [
        "Appliquer les règles de sécurité au travail (MSST, SUVA)",
        "Identifier et évaluer les dangers sur un chantier",
        "Utiliser correctement les EPI (équipements de protection)",
        "Mettre en place des mesures de protection collective",
        "Réagir correctement en cas d'accident",
        "Connaître les premiers secours (BLS-AED)",
    ],
    "AA06": [
        "Contrôler la qualité des travaux exécutés",
        "Vérifier la conformité aux plans et normes",
        "Documenter les contrôles et résultats",
        "Organiser les réceptions de chantier",
    ],
    "AA07": [
        "Comprendre les stratégies de maintenance (préventive, corrective, prédictive)",
        "Planifier les interventions de maintenance",
        "Utiliser les systèmes de gestion de maintenance (GMAO)",
        "Calculer les coûts de maintenance",
    ],
    "AA08": [
        "Effectuer la maintenance des équipements de réseau",
        "Diagnostiquer les pannes et dysfonctionnements",
        "Appliquer les procédures de consignation/déconsignation",
        "Utiliser les appareils de mesure et de test",
    ],
    "AA09": [
        "Appliquer les lois fondamentales (Ohm, Kirchhoff)",
        "Calculer en courant continu et alternatif (mono/triphasé)",
        "Calculer les puissances (P, Q, S, cos φ)",
        "Dimensionner les conducteurs et protections",
        "Comprendre les schémas de liaison à la terre (TN, TT, IT)",
    ],
    "AA10": [
        "Appliquer les principes de mécanique statique",
        "Calculer les forces, moments et charges",
        "Comprendre les matériaux (acier, alu, bois, béton)",
        "Dimensionner les supports et ancrages de lignes",
    ],
    "AA11": [
        "Maîtriser les calculs de base (algèbre, fractions, pourcentages)",
        "Appliquer la trigonométrie aux calculs de réseau",
        "Utiliser les formules de géométrie (surfaces, volumes)",
        "Résoudre des équations liées aux réseaux électriques",
    ],
    "AE01": [
        "Réaliser une étude de projet de réseau de distribution",
        "Dimensionner un réseau (câbles, postes de transformation)",
        "Calculer les chutes de tension et courants de court-circuit",
        "Établir un devis et une planification de projet",
    ],
    "AE02": [
        "Appliquer les 5 règles de sécurité",
        "Connaître les distances de sécurité selon les niveaux de tension",
        "Effectuer les consignations et déconsignations",
        "Appliquer les prescriptions ESTI/Suva pour travaux sur IE",
        "Établir des périmètres de sécurité",
    ],
    "AE03": [
        "Planifier une installation d'éclairage public",
        "Appliquer les normes EN 13201 et SLG 202",
        "Choisir les luminaires et sources (LED)",
        "Calculer l'éclairement et l'uniformité",
    ],
    "AE04": [
        "Lire et créer des schémas unifilaires de réseau",
        "Utiliser les systèmes d'information géographique (SIG/GIS)",
        "Documenter les réseaux selon les normes en vigueur",
        "Comprendre la symbologie normalisée",
    ],
    "AE05": [
        "Dimensionner les installations de mise à terre",
        "Calculer la résistance de terre",
        "Connaître les types de prises de terre (piquet, ruban, fondation)",
        "Mesurer la résistance de terre et la résistivité du sol",
    ],
    "AE06": [
        "Comprendre le fonctionnement des réseaux de distribution (MT/BT)",
        "Effectuer des manœuvres de réseau (ouverture/fermeture)",
        "Gérer les perturbations et pannes de réseau",
        "Comprendre les schémas d'exploitation (boucle, radial, maillé)",
    ],
    "AE07": [
        "Effectuer des mesures électriques sur les réseaux",
        "Utiliser les appareils de mesure (multimètre, pince, mégohmmètre)",
        "Mesurer l'isolement, la continuité, la boucle de défaut",
        "Interpréter les résultats de mesure",
    ],
    "AE09": [
        "Comprendre les systèmes de protection des réseaux",
        "Dimensionner les fusibles et disjoncteurs",
        "Comprendre la sélectivité des protections",
        "Calculer les courants de court-circuit",
        "Coordonner les protections MT/BT",
    ],
    "AE10": [
        "Planifier la maintenance des réseaux de distribution",
        "Effectuer les contrôles périodiques des installations",
        "Diagnostiquer les défauts sur les câbles et lignes",
        "Utiliser les techniques de localisation de défauts",
    ],
    "AE11": [
        "Réaliser un projet complet de réseau de A à Z",
        "Rédiger un dossier technique de projet",
        "Présenter et défendre son projet oralement",
        "Appliquer la gestion de projet (planning, budget, risques)",
    ],
    "AE12": [
        "Choisir et dimensionner les câbles souterrains",
        "Connaître les techniques de pose (tranchée, forage dirigé)",
        "Réaliser et contrôler les jonctions et terminaisons",
        "Appliquer les normes de pose et de croisement",
    ],
    "AE13": [
        "Dimensionner les lignes aériennes (conducteurs, supports)",
        "Calculer les portées et flèches",
        "Connaître les types de supports (bois, béton, acier)",
        "Effectuer la maintenance des lignes aériennes",
    ],
}


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
    """Génère des quiz interactifs basés sur les concepts du Brevet Fédéral — V3 Premium"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-3-pro-preview"):
        self.api_key = api_key or os.getenv('GOOGLE_API_KEY')
        self.model_name = model
        self.history_file = Path("data/quiz_history.json")
        self.question_bank_file = Path("data/question_bank.json")
        self.model = None
        
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel(self.model_name)
    
    # --- BANQUE DE QUESTIONS PERSISTANTE ---
    
    def _load_question_bank(self) -> Dict:
        """Charge la banque de questions sauvegardées."""
        if self.question_bank_file.exists():
            try:
                with open(self.question_bank_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return {"questions": [], "stats": {"total_generated": 0, "total_reused": 0}}
        return {"questions": [], "stats": {"total_generated": 0, "total_reused": 0}}
    
    def _save_question_bank(self, bank: Dict):
        """Sauvegarde la banque de questions."""
        self.question_bank_file.parent.mkdir(parents=True, exist_ok=True)
        # Garder max 500 questions
        if len(bank.get('questions', [])) > 500:
            # Garder les mieux notées et les plus récentes
            bank['questions'] = sorted(
                bank['questions'],
                key=lambda q: (q.get('quality_score', 0), q.get('created_at', '')),
                reverse=True
            )[:500]
        with open(self.question_bank_file, 'w', encoding='utf-8') as f:
            json.dump(bank, f, indent=2, ensure_ascii=False)
    
    def _find_banked_questions(self, concept_ids: List[str], q_types: List[str] = None, 
                                max_questions: int = 5) -> List[Dict]:
        """Cherche des questions déjà générées dans la banque."""
        bank = self._load_question_bank()
        matching = []
        concept_set = set(concept_ids)
        
        for q in bank.get('questions', []):
            if q.get('concept_id') in concept_set:
                if q_types and q.get('type') not in q_types:
                    continue
                if q.get('quality_score', 0) >= 3:  # Seulement les bonnes questions
                    matching.append(q)
        
        random.shuffle(matching)
        return matching[:max_questions]
    
    def _bank_questions(self, questions: List[Dict]):
        """Ajoute des questions de qualité à la banque."""
        bank = self._load_question_bank()
        existing_ids = {(q.get('concept_id'), q.get('question', '')[:50]) for q in bank.get('questions', [])}
        
        for q in questions:
            key = (q.get('concept_id'), q.get('question', '')[:50])
            if key not in existing_ids and not q.get('fallback'):
                banked = q.copy()
                banked['quality_score'] = 5  # Score initial
                banked['times_used'] = 0
                banked['times_correct'] = 0
                banked['created_at'] = datetime.now().isoformat()
                bank['questions'].append(banked)
                bank['stats']['total_generated'] = bank['stats'].get('total_generated', 0) + 1
                existing_ids.add(key)
        
        self._save_question_bank(bank)
    
    def update_question_quality(self, concept_id: str, question_text: str, was_correct: bool):
        """Met à jour la qualité d'une question dans la banque (après réponse utilisateur)."""
        bank = self._load_question_bank()
        for q in bank.get('questions', []):
            if q.get('concept_id') == concept_id and q.get('question', '')[:50] == question_text[:50]:
                q['times_used'] = q.get('times_used', 0) + 1
                if was_correct:
                    q['times_correct'] = q.get('times_correct', 0) + 1
                # Ajuster la qualité : une question trop facile (100% correct) ou trop dure (0%) perd des points
                if q['times_used'] >= 3:
                    success_rate = q['times_correct'] / q['times_used']
                    if 0.3 <= success_rate <= 0.8:
                        q['quality_score'] = min(10, q.get('quality_score', 5) + 0.5)
                    else:
                        q['quality_score'] = max(1, q.get('quality_score', 5) - 0.5)
                break
        self._save_question_bank(bank)
    
    def get_bank_stats(self) -> Dict:
        """Statistiques de la banque de questions."""
        bank = self._load_question_bank()
        questions = bank.get('questions', [])
        if not questions:
            return {"total": 0, "by_module": {}, "by_type": {}, "avg_quality": 0}
        
        by_module = defaultdict(int)
        by_type = defaultdict(int)
        for q in questions:
            by_module[q.get('module', 'N/A')] += 1
            by_type[q.get('type', 'qcm')] += 1
        
        return {
            "total": len(questions),
            "by_module": dict(by_module),
            "by_type": dict(by_type),
            "avg_quality": sum(q.get('quality_score', 5) for q in questions) / len(questions),
        }
    
    def _build_concept_context(self, concept: Dict, module: str = None) -> str:
        """Construit un contexte riche pour le prompt à partir de TOUTES les données du concept."""
        name = concept.get('name', 'N/A')
        keywords = concept.get('keywords', [])
        page_ref = concept.get('page_references', '')
        source_doc = concept.get('source_document', '')
        category = concept.get('category', '')
        importance = concept.get('importance', 'medium')
        prerequisites = concept.get('prerequisites', [])
        mod = module or concept.get('module', '')
        
        # Récupérer les compétences d'examen du module
        exam_comps = EXAM_COMPETENCES.get(mod, [])
        # Trouver la compétence la plus pertinente pour ce concept
        relevant_comps = self._match_competences_to_concept(name, keywords, exam_comps)
        
        context_parts = [f"**Concept :** {name}"]
        
        if keywords:
            context_parts.append(f"**Mots-clés techniques :** {', '.join(keywords)}")
        
        if category:
            context_parts.append(f"**Catégorie :** {category}")
        
        if page_ref:
            context_parts.append(f"**Référence cours :** {page_ref}")
        
        if source_doc:
            context_parts.append(f"**Document source :** {source_doc}")
            
        if prerequisites:
            context_parts.append(f"**Prérequis :** {', '.join(prerequisites)}")
        
        if importance:
            imp_label = {"critical": "Critique (à maîtriser absolument)", "high": "Élevée", "medium": "Moyenne", "low": "Basse"}.get(importance, importance)
            context_parts.append(f"**Importance pour l'examen :** {imp_label}")
        
        if relevant_comps:
            context_parts.append(f"**Compétences d'examen visées :**")
            for comp in relevant_comps[:3]:
                context_parts.append(f"  - {comp}")
        
        if mod:
            mod_label = self._get_module_label(mod)
            context_parts.append(f"**Module :** {mod} — {mod_label}")
        
        return '\n'.join(context_parts)
    
    def _match_competences_to_concept(self, name: str, keywords: List[str], competences: List[str]) -> List[str]:
        """Trouve les compétences d'examen les plus pertinentes pour un concept donné."""
        if not competences:
            return []
        
        name_lower = name.lower()
        keywords_lower = {k.lower() for k in keywords} if keywords else set()
        all_terms = keywords_lower | set(name_lower.split())
        # Supprimer les mots communs
        stop_words = {'de', 'du', 'des', 'le', 'la', 'les', 'un', 'une', 'et', 'en', 'au', 'aux', 'sur', 'par', 'pour', 'dans', 'avec'}
        all_terms -= stop_words
        
        scored = []
        for comp in competences:
            comp_lower = comp.lower()
            score = sum(1 for term in all_terms if term in comp_lower)
            if score > 0:
                scored.append((score, comp))
        
        scored.sort(key=lambda x: x[0], reverse=True)
        return [comp for _, comp in scored[:3]] if scored else competences[:2]
    
    def _get_module_label(self, module: str) -> str:
        """Retourne le label lisible d'un module."""
        labels = {
            "AA01": "Conduite de collaborateurs", "AA02": "Formation",
            "AA03": "Préparation du travail", "AA04": "Exécution de mandats",
            "AA05": "Santé et sécurité au travail", "AA06": "Suivi des travaux",
            "AA07": "Bases de la maintenance", "AA08": "Maintenance des équipements",
            "AA09": "Électrotechnique", "AA10": "Mécanique", "AA11": "Mathématique",
            "AE01": "Étude de projet", "AE02": "Sécurité sur et à prox. d'IE",
            "AE03": "Éclairage public", "AE04": "Documentation de réseaux",
            "AE05": "Installations mise à terre", "AE06": "Exploitation de réseaux",
            "AE07": "Technique de mesure", "AE09": "Technique de protection",
            "AE10": "Maintenance des réseaux", "AE11": "Travail de projet",
            "AE12": "Lignes souterraines", "AE13": "Lignes aériennes",
        }
        return labels.get(module, module)
    
    def _select_concepts_weighted(self, concepts: List[Dict], num: int, 
                                   weak_concept_ids: List[str] = None) -> List[Dict]:
        """
        Sélectionne les concepts avec pondération intelligente :
        - Importance (critical > high > medium > low)
        - Concepts faibles priorisés en mode adaptatif
        - Anti-doublon via historique
        """
        if not concepts:
            return []
        
        # Séparer concepts faibles / autres si mode adaptatif
        if weak_concept_ids:
            weak_set = set(weak_concept_ids)
            weak_concepts = [c for c in concepts if c.get('id') in weak_set or c.get('name') in weak_set]
            other_concepts = [c for c in concepts if c.get('id') not in weak_set and c.get('name') not in weak_set]
            
            # 60% concepts faibles, 40% autres
            num_weak = min(len(weak_concepts), int(num * 0.6))
            num_other = min(len(other_concepts), num - num_weak)
            
            # Sélection pondérée pour chaque groupe
            selected_weak = self._weighted_sample(weak_concepts, num_weak)
            selected_other = self._weighted_sample(other_concepts, num_other)
            selected = selected_weak + selected_other
        else:
            selected = self._weighted_sample(concepts, min(num, len(concepts)))
        
        random.shuffle(selected)
        return selected
    
    def _weighted_sample(self, concepts: List[Dict], num: int) -> List[Dict]:
        """Échantillonnage pondéré par importance — les concepts critiques sont choisis plus souvent."""
        if not concepts or num <= 0:
            return []
        num = min(num, len(concepts))
        
        weights = [IMPORTANCE_WEIGHTS.get(c.get('importance', 'medium'), 2.0) for c in concepts]
        
        selected = []
        remaining = list(range(len(concepts)))
        remaining_weights = list(weights)
        
        for _ in range(num):
            if not remaining:
                break
            chosen = random.choices(remaining, weights=remaining_weights, k=1)[0]
            idx = remaining.index(chosen)
            selected.append(concepts[chosen])
            remaining.pop(idx)
            remaining_weights.pop(idx)
        
        return selected
    
    def generate_quiz(self, concepts: List[Dict], module: str = None, 
                     num_questions: int = 10, difficulty: str = "moyen",
                     weak_concept_ids: List[str] = None,
                     question_types: List[str] = None) -> Dict:
        """
        Génère un quiz — VERSION 3.0 PREMIUM
        
        Nouveautés V3 :
        - Génération BATCH (1 appel AI pour toutes les questions)
        - Réutilisation de questions de la banque
        - Chaque question inclut un indice (hint)
        - Diversité des types forcée
        """
        # Filtrer par module si spécifié
        filtered_concepts = concepts
        if module:
            filtered_concepts = [c for c in concepts if c.get('module') == module]
        
        if not filtered_concepts:
            return {"error": "Aucun concept trouvé pour ce module"}
        
        # Sélection pondérée intelligente
        selected = self._select_concepts_weighted(
            filtered_concepts, num_questions, weak_concept_ids
        )
        
        # Essayer la GÉNÉRATION BATCH (1 seul appel AI)
        questions = []
        if self.model:
            batch_questions = self._generate_batch(
                selected, difficulty,
                question_types=question_types,
                module=module
            )
            if batch_questions:
                questions = batch_questions
        
        # Si le batch a échoué ou est incomplet, compléter question par question
        if len(questions) < len(selected):
            remaining_concepts = selected[len(questions):]
            for i, concept in enumerate(remaining_concepts, len(questions) + 1):
                question = self._generate_question(
                    concept, difficulty, i,
                    question_types=question_types,
                    module=module or concept.get('module')
                )
                if question:
                    questions.append(question)
        
        # Renuméroter
        for i, q in enumerate(questions, 1):
            q['question_num'] = i
        
        # Sauvegarder les bonnes questions dans la banque
        self._bank_questions(questions)
        
        quiz = {
            "id": f"quiz_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "module": module or "Tous modules",
            "difficulty": difficulty,
            "num_questions": len(questions),
            "questions": questions,
            "created_at": datetime.now().isoformat()
        }
        
        return quiz
    
    def _generate_batch(self, concepts: List[Dict], difficulty: str,
                        question_types: List[str] = None,
                        module: str = None) -> List[Dict]:
        """
        Génère TOUTES les questions en un seul appel IA — plus rapide et cohérent.
        Chaque question inclut un indice (hint).
        """
        if not self.model or not concepts:
            return []
        
        available_types = list(question_types) if question_types else list(QUESTION_TYPES.keys())
        
        # Préparer les types assignés avec diversité forcée
        assigned_types = self._assign_diverse_types(concepts, available_types, module)
        
        # Construire le contexte de chaque concept
        concept_blocks = []
        for i, (concept, q_type) in enumerate(zip(concepts, assigned_types), 1):
            ctx = self._build_concept_context(concept, module or concept.get('module'))
            type_label = QUESTION_TYPES.get(q_type, {}).get('label', q_type)
            concept_blocks.append(f"""--- QUESTION {i} ---
Type : {type_label}
{ctx}
""")
        
        all_concepts_text = '\n'.join(concept_blocks)
        
        # Format attendu par type
        format_examples = {
            "qcm": '{"type":"qcm","question":"...","options":["A","B","C","D"],"correct_answer":0,"explanation":"...","hint":"Un indice pour aider"}',
            "vrai_faux": '{"type":"vrai_faux","question":"Affirmation...","correct_answer":true,"explanation":"...","hint":"Un indice"}',
            "texte_trous": '{"type":"texte_trous","question":"Phrase avec _____","correct_answer":"mot","acceptable_answers":["mot","variante"],"explanation":"...","hint":"Un indice"}',
            "calcul": '{"type":"calcul","question":"Énoncé avec données","correct_answer":42.5,"tolerance":0.02,"unit":"Ω","explanation":"Calcul étape par étape","hint":"Formule à utiliser : ..."}',
            "mise_en_situation": '{"type":"mise_en_situation","scenario":"Situation...","question":"...","options":["A","B","C","D"],"correct_answer":0,"explanation":"...","hint":"Pensez à la norme..."}',
        }
        
        used_formats = {t: format_examples[t] for t in set(assigned_types) if t in format_examples}
        formats_text = '\n'.join([f"  {t}: {fmt}" for t, fmt in used_formats.items()])
        
        prompt = f"""Tu es un examinateur expert pour le Brevet Fédéral Spécialiste de Réseau (orientation Énergie) en Suisse.

Génère EXACTEMENT {len(concepts)} questions d'examen professionnel variées et de haute qualité.

**Niveau de difficulté : {difficulty}**

VOICI LES {len(concepts)} CONCEPTS À ÉVALUER (avec le type de question demandé pour chacun) :

{all_concepts_text}

CONSIGNES PREMIUM :
1. Chaque question doit être TECHNIQUE, CONCRÈTE et de niveau EXAMEN PROFESSIONNEL
2. JAMAIS de question vague du type "Que représente le concept X ?"
3. Les QCM doivent avoir 4 distracteurs PLAUSIBLES (erreurs courantes de candidats)
4. Les mises en situation doivent décrire un scénario de TERRAIN réaliste
5. Les calculs doivent inclure TOUTES les données nécessaires et des valeurs RÉALISTES
6. Chaque question DOIT inclure un champ "hint" : un INDICE subtil qui aide sans donner la réponse
7. Les explications doivent CITER les normes applicables (ESTI, NIBT, SUVA, EN)
8. Pas de doublons entre les questions !
9. Pour les QCM : correct_answer = INDEX (0-3)
10. Pour les vrai/faux : correct_answer = true ou false (booléen)
11. Pour les calculs : correct_answer = nombre (pas de texte)

FORMATS JSON par type :
{formats_text}

Réponds UNIQUEMENT avec un tableau JSON contenant exactement {len(concepts)} objets :
[
  question1,
  question2,
  ...
]

IMPORTANT : Réponse = UNIQUEMENT le tableau JSON, rien d'autre. Tout en français."""

        try:
            response = self.model.generate_content(prompt)
            text = response.text.strip()
            
            # Nettoyer markdown
            if text.startswith("```json"):
                text = text.replace("```json", "").replace("```", "").strip()
            elif text.startswith("```"):
                text = text.replace("```", "").strip()
            
            questions_data = json.loads(text)
            
            if not isinstance(questions_data, list):
                return []
            
            # Valider et enrichir chaque question
            valid_questions = []
            for i, (q_data, concept) in enumerate(zip(questions_data, concepts)):
                q_type = q_data.get('type', assigned_types[i] if i < len(assigned_types) else 'qcm')
                q_data['type'] = q_type
                
                # Valider
                if q_type in ('qcm', 'mise_en_situation'):
                    if not self._validate_qcm(q_data):
                        q_data = self._generate_fallback(concept, i + 1, q_type)
                        q_data['type'] = q_type
                
                if q_type == 'vrai_faux':
                    q_data['correct_answer'] = bool(q_data.get('correct_answer', True))
                
                if q_type == 'calcul':
                    try:
                        q_data['correct_answer'] = float(q_data.get('correct_answer', 0))
                    except (ValueError, TypeError):
                        q_data = self._generate_fallback(concept, i + 1, 'calcul')
                        q_data['type'] = 'calcul'
                    q_data.setdefault('tolerance', 0.02)
                    q_data.setdefault('unit', '')
                
                if q_type == 'texte_trous':
                    if q_data.get('correct_answer') not in q_data.get('acceptable_answers', []):
                        q_data.setdefault('acceptable_answers', []).append(str(q_data.get('correct_answer', '')))
                
                # Ajouter hint par défaut si manquant
                if not q_data.get('hint'):
                    q_data['hint'] = self._generate_default_hint(concept, q_type)
                
                # Ajouter métadonnées
                self._add_metadata(q_data, concept, i + 1)
                valid_questions.append(q_data)
            
            return valid_questions
            
        except Exception as e:
            print(f"Erreur génération batch: {e}")
            return []
    
    def _assign_diverse_types(self, concepts: List[Dict], available_types: List[str], 
                               module: str = None) -> List[str]:
        """Assigne des types de questions diversifiés — garantit un mix varié."""
        # Filtrer calcul pour modules non techniques
        types_for_module = available_types.copy()
        mod = module or (concepts[0].get('module') if concepts else '')
        if mod and mod not in CALCUL_MODULES:
            types_for_module = [t for t in types_for_module if t != 'calcul']
        if not types_for_module:
            types_for_module = ['qcm']
        
        n = len(concepts)
        assigned = []
        
        # D'abord, assurer qu'on a au moins 1 de chaque type disponible (si assez de questions)
        if n >= len(types_for_module):
            assigned = list(types_for_module)
        
        # Remplir le reste avec pondération
        while len(assigned) < n:
            weights = [QUESTION_TYPES[t]["weight"] for t in types_for_module]
            chosen = random.choices(types_for_module, weights=weights, k=1)[0]
            assigned.append(chosen)
        
        random.shuffle(assigned)
        return assigned[:n]
    
    def _generate_default_hint(self, concept: Dict, q_type: str) -> str:
        """Génère un indice par défaut basé sur les métadonnées du concept."""
        keywords = concept.get('keywords', [])
        module = concept.get('module', '')
        name = concept.get('name', '')
        
        if keywords:
            return f"Pensez aux termes : {', '.join(keywords[:3])}"
        elif module:
            comps = EXAM_COMPETENCES.get(module, [])
            if comps:
                return f"Compétence visée : {comps[0][:80]}"
        return f"Ce concept fait partie du module {self._get_module_label(module)}"
    
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
        data = json.loads(text)
        return data

    def _validate_qcm(self, data: Dict) -> bool:
        """Valide la cohérence d'une question QCM."""
        if not data.get('question') or not data.get('options'):
            return False
        if not isinstance(data.get('correct_answer'), int):
            return False
        if data['correct_answer'] < 0 or data['correct_answer'] >= len(data['options']):
            return False
        # Vérifier que les options ne sont pas toutes identiques
        if len(set(data['options'])) < len(data['options']):
            return False
        return True

    def _add_metadata(self, data: Dict, concept: Dict, question_num: int) -> Dict:
        """Ajoute les métadonnées du concept."""
        data["concept_id"] = concept.get('id')
        data["concept_name"] = concept.get('name')
        data["module"] = concept.get('module', '')
        data["question_num"] = question_num
        data["source_document"] = concept.get('source_document', '')
        data["page_references"] = concept.get('page_references', '')
        return data

    # --- Générateurs par type ---

    def _generate_qcm(self, concept: Dict, difficulty: str, question_num: int) -> Optional[Dict]:
        """Génère une question QCM — prompt enrichi avec contexte complet."""
        try:
            context = self._build_concept_context(concept)
            prompt = f"""Tu es un examinateur expert pour le Brevet Fédéral Spécialiste de Réseau (orientation Énergie) en Suisse.

Génère UNE question à choix multiples (QCM) de niveau examen professionnel.

{context}
**Niveau de difficulté :** {difficulty}

CONSIGNES :
1. La question doit porter sur un aspect CONCRET et TECHNIQUE du concept
2. Utilise les mots-clés techniques fournis dans ta question ou tes options
3. Les 4 distracteurs doivent être PLAUSIBLES (erreurs courantes de candidats)
4. Les options doivent être de longueur similaire
5. L'explication doit citer la règle/norme/formule applicable
6. Pas de question vague du type "Que représente le concept X ?"

Réponds UNIQUEMENT en JSON strict :
{{
  "question": "Question technique précise et contextualisée",
  "options": ["Option A correcte", "Option B plausible mais fausse", "Option C plausible mais fausse", "Option D plausible mais fausse"],
  "correct_answer": 0,
  "explanation": "Explication détaillée avec référence aux normes/cours"
}}

IMPORTANT : correct_answer = INDEX (0-3) de la bonne réponse. Tout en français."""

            response = self.model.generate_content(prompt)
            data = self._parse_ai_response(response)
            if not self._validate_qcm(data):
                return self._generate_fallback(concept, question_num, "qcm")
            return self._add_metadata(data, concept, question_num)
        except Exception as e:
            print(f"Erreur QCM: {e}")
            return self._generate_fallback(concept, question_num, "qcm")

    def _generate_vrai_faux(self, concept: Dict, difficulty: str, question_num: int) -> Optional[Dict]:
        """Génère une question Vrai/Faux — affirmation technique précise."""
        try:
            context = self._build_concept_context(concept)
            prompt = f"""Tu es un examinateur expert pour le Brevet Fédéral Spécialiste de Réseau en Suisse.

Génère UNE affirmation VRAI ou FAUX de niveau examen professionnel.

{context}
**Niveau de difficulté :** {difficulty}

CONSIGNES :
1. L'affirmation doit porter sur un FAIT TECHNIQUE PRÉCIS (valeur, norme, règle, procédure)
2. Si l'affirmation est FAUSSE, elle doit contenir une erreur subtile mais identifiable
3. Exemples de bonnes affirmations :
   - "La tension de contact maximale admissible en milieu sec est de 50V selon la NIBT"
   - "En régime TN-C, le conducteur PEN peut avoir une section inférieure à 10mm²" (FAUX)
4. Évite les affirmations vagues ou évidentes
5. L'explication doit préciser la valeur/règle correcte

Réponds UNIQUEMENT en JSON strict :
{{
  "question": "Affirmation technique précise à évaluer comme vraie ou fausse",
  "correct_answer": true,
  "explanation": "Explication détaillée avec la règle/valeur/norme correcte"
}}

IMPORTANT : correct_answer est un booléen (true ou false). En français."""

            response = self.model.generate_content(prompt)
            data = self._parse_ai_response(response)
            data['correct_answer'] = bool(data['correct_answer'])
            return self._add_metadata(data, concept, question_num)
        except Exception as e:
            print(f"Erreur Vrai/Faux: {e}")
            return self._generate_fallback(concept, question_num, "vrai_faux")

    def _generate_texte_trous(self, concept: Dict, difficulty: str, question_num: int) -> Optional[Dict]:
        """Génère une question à texte à trous — terme technique clé."""
        try:
            context = self._build_concept_context(concept)
            keywords = concept.get('keywords', [])
            keywords_hint = f"\nMots-clés techniques à cibler pour le trou : {', '.join(keywords)}" if keywords else ""
            
            prompt = f"""Tu es un examinateur expert pour le Brevet Fédéral Spécialiste de Réseau en Suisse.

Génère UNE question à TEXTE À TROUS de niveau examen professionnel.

{context}
{keywords_hint}
**Niveau de difficulté :** {difficulty}

CONSIGNES :
1. La phrase doit être une définition ou une règle technique IMPORTANTE
2. Le mot à trouver doit être un TERME TECHNIQUE CLÉ (pas un mot courant)
3. La phrase seule (avec le trou) doit donner assez de contexte pour deviner
4. Exemples :
   - "L'appareil qui mesure la résistance d'isolement s'appelle un _____." → mégohmmètre
   - "La règle de sécurité n°1 est : _____ et vérifier l'absence de tension." → déclencher/consigner
5. Le mot à trouver doit faire partie des mots-clés du concept si possible

Réponds UNIQUEMENT en JSON strict :
{{
  "question": "Phrase technique avec un _____ à compléter",
  "correct_answer": "terme technique correct",
  "acceptable_answers": ["réponse1", "variante2", "variante3"],
  "explanation": "Explication de ce terme et son importance"
}}

IMPORTANT : Le trou = _____. Le mot doit être technique et important. En français."""

            response = self.model.generate_content(prompt)
            data = self._parse_ai_response(response)
            if data.get('correct_answer') not in data.get('acceptable_answers', []):
                data.setdefault('acceptable_answers', []).append(data['correct_answer'])
            return self._add_metadata(data, concept, question_num)
        except Exception as e:
            print(f"Erreur texte à trous: {e}")
            return self._generate_fallback(concept, question_num, "texte_trous")

    def _generate_calcul(self, concept: Dict, difficulty: str, question_num: int) -> Optional[Dict]:
        """Génère une question de calcul — problème concret avec données."""
        try:
            context = self._build_concept_context(concept)
            module = concept.get('module', '')
            
            # Adapter le type de calcul au module
            calcul_hints = {
                "AA09": "Calculs de loi d'Ohm, Kirchhoff, puissances (P=UI, S=UI, Q=√(S²-P²)), cos φ, résistances série/parallèle, courant triphasé",
                "AA10": "Calculs de forces, moments, charges mécaniques sur supports/ancrages, résistance des matériaux",
                "AA11": "Calculs algébriques, trigonométrie, géométrie appliquée aux réseaux",
                "AE05": "Calculs de résistance de terre, résistivité du sol, dimensionnement mise à terre",
                "AE07": "Calculs de mesure d'isolement, boucle de défaut, interprétation de résultats",
            }
            hint = calcul_hints.get(module, "Calculs techniques appliqués aux réseaux électriques")
            
            prompt = f"""Tu es un examinateur expert pour le Brevet Fédéral Spécialiste de Réseau en Suisse.

Génère UNE question de CALCUL de niveau examen professionnel.

{context}
**Niveau de difficulté :** {difficulty}
**Type de calcul attendu :** {hint}

CONSIGNES :
1. L'énoncé doit donner TOUTES les données numériques nécessaires
2. Le calcul doit correspondre à une situation RÉELLE de travail sur réseau
3. Les valeurs doivent être RÉALISTES (pas de valeurs absurdes)
4. L'explication doit montrer CHAQUE ÉTAPE de calcul
5. Exemples de bonnes questions :
   - "Un câble de 120m alimente une charge de 45A en monophasé 230V. Section 6mm² (ρ=0.0175 Ω·mm²/m). Calculer la chute de tension."
   - "Trois résistances de 100Ω, 220Ω et 470Ω sont en parallèle. Calculer la résistance équivalente."

Réponds UNIQUEMENT en JSON strict :
{{
  "question": "Énoncé complet avec toutes les données numériques",
  "correct_answer": 42.5,
  "tolerance": 0.02,
  "unit": "Ω",
  "explanation": "Calcul détaillé étape par étape avec formules"
}}

IMPORTANT : correct_answer = valeur numérique. tolerance = marge relative (0.02 = 2%). En français."""

            response = self.model.generate_content(prompt)
            data = self._parse_ai_response(response)
            data['correct_answer'] = float(data['correct_answer'])
            data.setdefault('tolerance', 0.02)
            data.setdefault('unit', '')
            return self._add_metadata(data, concept, question_num)
        except Exception as e:
            print(f"Erreur calcul: {e}")
            return self._generate_fallback(concept, question_num, "calcul")

    def _generate_mise_en_situation(self, concept: Dict, difficulty: str, question_num: int) -> Optional[Dict]:
        """Génère une question de mise en situation — scénario professionnel réaliste."""
        try:
            context = self._build_concept_context(concept)
            module = concept.get('module', '')
            
            # Adapter le scénario au module
            scenario_hints = {
                "AA01": "Scénario de gestion d'équipe sur un chantier",
                "AA02": "Scénario de formation d'un apprenti",
                "AA03": "Scénario de préparation de chantier",
                "AA04": "Scénario de gestion de mandat client",
                "AA05": "Scénario d'accident ou de danger sur chantier",
                "AA06": "Scénario de contrôle qualité après travaux",
                "AA07": "Scénario de planification de maintenance",
                "AA08": "Scénario de diagnostic de panne",
                "AA09": "Scénario de dimensionnement électrique",
                "AE02": "Scénario de travail à proximité d'installations électriques sous tension",
                "AE06": "Scénario de manœuvre réseau ou de panne",
                "AE09": "Scénario de coordination des protections",
                "AE10": "Scénario de maintenance réseau et localisation de défaut",
                "AE12": "Scénario de pose de câble souterrain",
                "AE13": "Scénario de maintenance de ligne aérienne",
            }
            hint = scenario_hints.get(module, "Scénario professionnel réaliste sur un chantier de réseau électrique")
            
            prompt = f"""Tu es un examinateur expert pour le Brevet Fédéral Spécialiste de Réseau en Suisse.

Génère UNE question de MISE EN SITUATION de niveau examen professionnel.

{context}
**Niveau de difficulté :** {difficulty}
**Type de situation :** {hint}

CONSIGNES :
1. Le scénario doit décrire une situation de terrain CONCRÈTE et RÉALISTE (2-3 phrases)
2. Le scénario doit inclure des détails spécifiques (type d'installation, conditions, etc.)
3. Les 4 options doivent être des ACTIONS concrètes que le professionnel pourrait entreprendre
4. La mauvaise réponse la plus tentante doit être une erreur courante commise par les candidats
5. L'explication doit référencer la norme ou bonne pratique applicable
6. Exemples de bons scénarios :
   - "Vous arrivez sur un chantier où un poste de transformation 16kV/400V doit être contrôlé. Le disjoncteur MT est ouvert mais le sectionneur de terre n'est pas enclenché..."
   - "Un apprenti s'apprête à intervenir sur un coffret de distribution BT sans avoir vérifié l'absence de tension..."

Réponds UNIQUEMENT en JSON strict :
{{
  "scenario": "Description détaillée d'une situation professionnelle réelle (2-3 phrases avec détails techniques)",
  "question": "Question concrète sur la meilleure action à entreprendre",
  "options": ["Action A (correcte)", "Action B (erreur courante)", "Action C (dangereuse)", "Action D (insuffisante)"],
  "correct_answer": 0,
  "explanation": "Explication avec référence aux normes/procédures (ESTI, SUVA, NIBT, etc.)"
}}

IMPORTANT : correct_answer = INDEX (0-3). Mélange l'ordre des options. En français."""

            response = self.model.generate_content(prompt)
            data = self._parse_ai_response(response)
            if not self._validate_qcm(data):
                return self._generate_fallback(concept, question_num, "mise_en_situation")
            return self._add_metadata(data, concept, question_num)
        except Exception as e:
            print(f"Erreur mise en situation: {e}")
            return self._generate_fallback(concept, question_num, "mise_en_situation")

    # --- Fallback de qualité professionnelle ---

    # Banque de questions de secours par module — vraies questions techniques professionnelles
    # Couvre TOUS les 15 modules du Brevet Fédéral
    FALLBACK_BANK = {
        "AA02": {
            "qcm": [
                {
                    "question": "Dans la méthode de la Lanterne Magique pour structurer une formation, quelles sont les 3 phases principales ?",
                    "options": [
                        "Entrée en matière — Développement — Conclusion",
                        "Planification — Exécution — Évaluation",
                        "Théorie — Pratique — Examen",
                        "Introduction — Corps — Fin"
                    ],
                    "correct_answer": 0,
                    "explanation": "La méthode de la Lanterne Magique structure une action de formation en 3 phases : Entrée en matière (accroche, objectifs), Développement (contenu, exercices) et Conclusion (résumé, évaluation)."
                },
                {
                    "question": "Lors de la planification d'une formation pour un apprenti, quel document est obligatoire selon l'OFPr ?",
                    "options": [
                        "Le programme de formation avec les objectifs évaluateurs",
                        "Un simple planning hebdomadaire",
                        "Le contrat de travail uniquement",
                        "Le curriculum vitae du formateur"
                    ],
                    "correct_answer": 0,
                    "explanation": "L'OFPr (Ordonnance sur la formation professionnelle) exige un programme de formation détaillé incluant les objectifs évaluateurs définis dans le plan de formation."
                },
            ],
            "vrai_faux": [
                {
                    "question": "L'analyse des 4 pôles (situationnelle) permet d'adapter une action de formation au contexte, au public, aux objectifs et aux conditions cadres.",
                    "correct_answer": True,
                    "explanation": "L'analyse des 4 pôles est un outil pédagogique qui examine le contexte situationnel sous 4 angles pour optimiser la formation."
                },
            ],
        },
        "AA03": {
            "qcm": [
                {
                    "question": "Lors de la préparation d'un chantier de réseau, quel document doit être établi en priorité pour lister les ressources nécessaires ?",
                    "options": [
                        "La liste de matériel et d'outillage avec les quantités et références",
                        "Le rapport de fin de travaux",
                        "La facture prévisionnelle pour le client",
                        "Le plan de carrière des collaborateurs"
                    ],
                    "correct_answer": 0,
                    "explanation": "La préparation de travaux exige une liste détaillée du matériel, de l'outillage et des EPI nécessaires, avec quantités et références, pour éviter les retards et interruptions de chantier."
                },
                {
                    "question": "Quel outil est utilisé pour planifier le déroulement temporel des travaux sur un chantier de réseau ?",
                    "options": [
                        "Le diagramme de Gantt",
                        "Le tableau de bord financier",
                        "L'organigramme de l'entreprise",
                        "Le carnet de commandes"
                    ],
                    "correct_answer": 0,
                    "explanation": "Le diagramme de Gantt permet de visualiser la planification temporelle des tâches, leurs dépendances et le chemin critique du projet."
                },
            ],
            "vrai_faux": [
                {
                    "question": "Lors de la lecture d'un schéma unifilaire, un trait unique représente l'ensemble des conducteurs d'un circuit (phases + neutre + PE).",
                    "correct_answer": True,
                    "explanation": "Dans un schéma unifilaire, un seul trait symbolise l'ensemble des conducteurs d'un circuit, contrairement au schéma multifilaire qui représente chaque conducteur séparément."
                },
            ],
        },
        "AA04": {
            "qcm": [
                {
                    "question": "Dans la gestion d'un mandat de réseau électrique, quelle est la séquence correcte des étapes ?",
                    "options": [
                        "Offre → Commande → Planification → Exécution → Contrôle → Facturation",
                        "Facturation → Exécution → Planification → Offre",
                        "Commande → Exécution → Offre → Facturation",
                        "Planification → Offre → Exécution → Commande"
                    ],
                    "correct_answer": 0,
                    "explanation": "Un mandat suit un processus structuré : établissement de l'offre, réception de la commande, planification des travaux, exécution, contrôle qualité et facturation."
                },
                {
                    "question": "Quel document formalise les conditions commerciales et techniques d'une intervention de réseau avant le début des travaux ?",
                    "options": [
                        "Le devis/offre détaillé avec le descriptif technique et les conditions",
                        "Le rapport journalier de chantier",
                        "Le plan de maintenance préventive",
                        "Le procès-verbal de réception"
                    ],
                    "correct_answer": 0,
                    "explanation": "Le devis/offre détaillé définit le périmètre technique, les quantités, les prix et les conditions. Il constitue la base contractuelle du mandat."
                },
            ],
        },
        "AA05": {
            "qcm": [
                {
                    "question": "Selon les prescriptions SUVA, quelle est la distance minimale de sécurité à respecter pour des travaux à proximité d'une ligne aérienne 16 kV ?",
                    "options": ["3 mètres", "1 mètre", "5 mètres", "0.5 mètre"],
                    "correct_answer": 0,
                    "explanation": "Selon les prescriptions SUVA et ESTI, la distance de sécurité pour les lignes 16 kV est de 3 mètres. Cette distance augmente avec le niveau de tension."
                },
                {
                    "question": "Quel est l'ordre correct des 5 règles de sécurité pour travailler sur une installation électrique ?",
                    "options": [
                        "Déclencher - Sécuriser contre le réenclenchement - Vérifier l'absence de tension - Mettre à la terre et en court-circuit - Protéger contre les parties voisines sous tension",
                        "Vérifier l'absence de tension - Déclencher - Mettre à la terre - Sécuriser - Protéger",
                        "Sécuriser - Déclencher - Protéger - Vérifier - Mettre à la terre",
                        "Déclencher - Vérifier - Sécuriser - Protéger - Mettre à la terre"
                    ],
                    "correct_answer": 0,
                    "explanation": "Les 5 règles de sécurité doivent être appliquées dans cet ordre strict selon l'ESTI : 1) Déclencher, 2) Sécuriser contre le réenclenchement, 3) Vérifier l'absence de tension, 4) Mettre à la terre et en court-circuit, 5) Protéger contre les parties voisines sous tension."
                },
                {
                    "question": "Quel est le courant de déclenchement typique d'un dispositif différentiel résiduel (DDR) de type A pour la protection des personnes ?",
                    "options": ["30 mA", "300 mA", "100 mA", "500 mA"],
                    "correct_answer": 0,
                    "explanation": "Le DDR de 30 mA (type A) est la protection standard contre les contacts indirects pour la protection des personnes. Le 300 mA est utilisé pour la protection incendie."
                },
            ],
            "vrai_faux": [
                {
                    "question": "Le port du casque de protection est obligatoire sur tout chantier de réseau électrique, même pour les travaux en tranchée.",
                    "correct_answer": True,
                    "explanation": "Le casque est un EPI obligatoire sur tout chantier de réseau selon les prescriptions SUVA, y compris en tranchée où il protège contre les chutes d'objets."
                },
                {
                    "question": "En cas d'électrisation d'un collègue, la première action est de le saisir pour le dégager de la source de tension.",
                    "correct_answer": False,
                    "explanation": "FAUX — La première action est de COUPER l'alimentation électrique si possible. Toucher directement la victime sans couper la tension exposerait le sauveteur au même danger. Utiliser un objet isolant si nécessaire."
                },
            ],
            "mise_en_situation": [
                {
                    "scenario": "Vous êtes responsable d'un chantier de pose de câble souterrain. Un de vos collaborateurs signale qu'il a touché un câble non identifié lors de l'excavation. Le câble semble intact mais non documenté sur les plans.",
                    "question": "Quelle est la première action à entreprendre ?",
                    "options": [
                        "Arrêter immédiatement les travaux, sécuriser la zone et contacter l'exploitant du réseau pour identification",
                        "Continuer les travaux avec précaution en contournant le câble",
                        "Mesurer la tension sur le câble avec un multimètre pour identifier s'il est sous tension",
                        "Couper le câble pour déterminer son type et son état"
                    ],
                    "correct_answer": 0,
                    "explanation": "Tout câble non identifié doit être considéré comme sous tension. Il faut arrêter les travaux, sécuriser la zone et contacter l'exploitant pour identification. Toucher ou mesurer un câble inconnu est dangereux."
                },
            ],
        },
        "AA07": {
            "qcm": [
                {
                    "question": "Quelle est la différence principale entre la maintenance préventive et la maintenance corrective ?",
                    "options": [
                        "La préventive est planifiée avant la panne, la corrective intervient après une défaillance",
                        "La préventive coûte plus cher que la corrective",
                        "La corrective est toujours préférable car elle évite les interventions inutiles",
                        "La préventive ne concerne que les équipements neufs"
                    ],
                    "correct_answer": 0,
                    "explanation": "La maintenance préventive (systématique ou conditionnelle) est programmée pour prévenir les pannes. La maintenance corrective intervient après une défaillance constatée pour rétablir la fonction."
                },
                {
                    "question": "Dans un système de GMAO, que signifie le sigle GMAO ?",
                    "options": [
                        "Gestion de la Maintenance Assistée par Ordinateur",
                        "Gestion des Moyens et Appareils Opérationnels",
                        "Guide de Maintenance et d'Aide Opérationnelle",
                        "Gestion du Matériel et des Achats Organisés"
                    ],
                    "correct_answer": 0,
                    "explanation": "La GMAO (Gestion de la Maintenance Assistée par Ordinateur) est un logiciel dédié à la planification, au suivi et à l'optimisation des opérations de maintenance."
                },
            ],
            "vrai_faux": [
                {
                    "question": "La maintenance prédictive utilise des capteurs et analyses de données pour anticiper les pannes avant qu'elles ne surviennent.",
                    "correct_answer": True,
                    "explanation": "La maintenance prédictive (ou conditionnelle avancée) s'appuie sur la surveillance de paramètres (vibrations, température, courants) et l'analyse de tendances pour prédire les défaillances."
                },
            ],
        },
        "AA08": {
            "qcm": [
                {
                    "question": "Avant d'effectuer la maintenance d'un transformateur de distribution MT/BT, quelle procédure obligatoire doit être réalisée ?",
                    "options": [
                        "La consignation complète (5 règles de sécurité) côté MT et côté BT",
                        "Uniquement la coupure du disjoncteur BT",
                        "L'information verbale du responsable d'exploitation",
                        "La mesure de la température de l'huile"
                    ],
                    "correct_answer": 0,
                    "explanation": "Toute maintenance sur un transformateur nécessite une consignation complète des DEUX côtés (MT et BT) selon les 5 règles de sécurité, avec formulaire de consignation signé."
                },
                {
                    "question": "Quelle mesure permet de vérifier l'état d'isolement des enroulements d'un transformateur ?",
                    "options": [
                        "La mesure de résistance d'isolement au mégohmmètre (500V ou 1000V DC)",
                        "La mesure de tension en charge avec un multimètre",
                        "La mesure du courant de court-circuit",
                        "La mesure de la fréquence du réseau"
                    ],
                    "correct_answer": 0,
                    "explanation": "L'essai d'isolement au mégohmmètre applique une tension continue (500V ou 1000V) entre les enroulements et la carcasse pour vérifier la qualité de l'isolation. Les valeurs sont comparées aux normes IEC."
                },
            ],
        },
        "AA09": {
            "qcm": [
                {
                    "question": "Dans un circuit triphasé équilibré 400V/230V avec cos φ = 0.85 et un courant de ligne de 25A, quelle est la puissance active totale ?",
                    "options": ["14.7 kW", "17.3 kW", "10.0 kW", "20.0 kW"],
                    "correct_answer": 0,
                    "explanation": "P = √3 × U × I × cos φ = √3 × 400 × 25 × 0.85 = 14'722 W ≈ 14.7 kW"
                },
                {
                    "question": "Quelle est la relation correcte entre puissance apparente (S), puissance active (P) et puissance réactive (Q) ?",
                    "options": [
                        "S² = P² + Q² (triangle des puissances)",
                        "S = P + Q",
                        "S = P × Q",
                        "S² = P² - Q²"
                    ],
                    "correct_answer": 0,
                    "explanation": "Le triangle des puissances établit la relation S² = P² + Q², où S est en VA, P en W et Q en var. Le facteur de puissance cos φ = P/S."
                },
            ],
            "calcul": [
                {
                    "question": "Un câble de cuivre de 50m de longueur et de 2.5 mm² de section alimente une charge monophasée 230V tirant 16A. Résistivité du cuivre : ρ = 0.0175 Ω·mm²/m. Calculer la chute de tension en volts (aller-retour).",
                    "correct_answer": 11.2,
                    "tolerance": 0.05,
                    "unit": "V",
                    "explanation": "R = ρ × L / S = 0.0175 × 50 / 2.5 = 0.35 Ω (un conducteur)\nChute de tension AR = 2 × R × I = 2 × 0.35 × 16 = 11.2 V"
                },
                {
                    "question": "Trois résistances de 100 Ω, 220 Ω et 470 Ω sont connectées en parallèle. Calculer la résistance équivalente en ohms (arrondi à 1 décimale).",
                    "correct_answer": 59.1,
                    "tolerance": 0.03,
                    "unit": "Ω",
                    "explanation": "1/Req = 1/100 + 1/220 + 1/470 = 0.01 + 0.004545 + 0.002128 = 0.016673\nReq = 1/0.016673 = 59.98 ≈ 59.1 Ω"
                },
            ],
            "vrai_faux": [
                {
                    "question": "Dans un circuit en série, le courant est identique en tout point mais la tension se répartit entre les composants.",
                    "correct_answer": True,
                    "explanation": "Loi de Kirchhoff : dans un circuit série, le courant est le même partout (I_total = I_1 = I_2) et la tension totale est la somme des tensions partielles (U = U_1 + U_2)."
                },
            ],
        },
        "AA10": {
            "qcm": [
                {
                    "question": "Quel type d'effort mécanique s'exerce principalement sur un support de ligne aérienne en alignement droit ?",
                    "options": [
                        "La compression verticale due au poids des conducteurs et du support lui-même",
                        "La traction horizontale uniquement",
                        "Le cisaillement dans tous les cas",
                        "Aucun effort notable en alignement droit"
                    ],
                    "correct_answer": 0,
                    "explanation": "En alignement droit, les efforts horizontaux des conducteurs s'annulent. Le support supporte principalement la compression verticale (poids propre + conducteurs + surcharges glace/vent)."
                },
                {
                    "question": "Pour calculer la force de traction dans un conducteur de ligne aérienne, quel paramètre climatique est déterminant ?",
                    "options": [
                        "La surcharge de givre/glace et la pression du vent combinées",
                        "La température ambiante uniquement",
                        "L'humidité relative de l'air",
                        "La pression atmosphérique"
                    ],
                    "correct_answer": 0,
                    "explanation": "Selon la SIA 261 et EN 50341, la charge maximale sur les conducteurs résulte de la combinaison des surcharges de givre (augmentent le poids) et de la pression du vent (effort horizontal)."
                },
            ],
        },
        "AA11": {
            "qcm": [
                {
                    "question": "Pour calculer la hauteur d'un poteau à l'aide de la trigonométrie, quelles mesures sont nécessaires depuis le sol ?",
                    "options": [
                        "La distance au pied du poteau et l'angle d'élévation vers le sommet",
                        "La longueur de l'ombre et l'heure de la journée",
                        "Le diamètre du poteau et sa masse",
                        "La hauteur de l'observateur uniquement"
                    ],
                    "correct_answer": 0,
                    "explanation": "Hauteur = distance × tan(angle) + hauteur de l'instrument. C'est l'application de la trigonométrie (tangente) en topographie de réseau."
                },
            ],
            "calcul": [
                {
                    "question": "Un câble souterrain suit un tracé avec deux segments : 85 m en ligne droite puis un virage à 90° suivi de 42 m. Quelle est la longueur totale de câble nécessaire (sans marge) ?",
                    "correct_answer": 127.0,
                    "tolerance": 0.01,
                    "unit": "m",
                    "explanation": "Longueur totale = segment 1 + segment 2 = 85 + 42 = 127 m. Le virage ne modifie pas la longueur nécessaire (le câble suit le tracé)."
                },
            ],
        },
        "AE02": {
            "qcm": [
                {
                    "question": "Lors d'une consignation d'une installation MT (16 kV), quelle est la séquence correcte ?",
                    "options": [
                        "Ouvrir le disjoncteur, ouvrir le sectionneur, vérifier l'absence de tension, enclencher le sectionneur de terre",
                        "Ouvrir le sectionneur, ouvrir le disjoncteur, mettre à la terre, vérifier l'absence de tension",
                        "Vérifier l'absence de tension, ouvrir le disjoncteur, ouvrir le sectionneur",
                        "Ouvrir le disjoncteur, mettre à la terre, ouvrir le sectionneur"
                    ],
                    "correct_answer": 0,
                    "explanation": "La séquence correcte respecte les 5 règles de sécurité : 1) Déclencher (ouvrir disjoncteur), 2) Séparer (ouvrir sectionneur), 3) Vérifier absence de tension, 4) Mettre à la terre (sectionneur de terre). L'ordre est critique pour la sécurité."
                },
                {
                    "question": "Quelle est la tension de contact maximale admissible en milieu sec selon la NIBT (Norme d'Installations Basse Tension) ?",
                    "options": ["50 V", "25 V", "120 V", "230 V"],
                    "correct_answer": 0,
                    "explanation": "La NIBT fixe la tension de contact maximale admissible à 50 V en milieu sec (UL = 50 V AC). En milieu humide ou mouillé, cette valeur est réduite à 25 V."
                },
            ],
            "mise_en_situation": [
                {
                    "scenario": "Vous devez effectuer des travaux de maintenance sur un poste de transformation 16kV/400V. Le disjoncteur MT est ouvert et cadenassé. Un collègue vous informe qu'il a vérifié l'absence de tension côté MT, mais le sectionneur de terre n'est pas encore enclenché.",
                    "question": "Que devez-vous faire avant de commencer les travaux ?",
                    "options": [
                        "Enclencher le sectionneur de terre MT et vérifier également l'absence de tension côté BT avant de commencer",
                        "Les travaux peuvent commencer car le disjoncteur est ouvert et cadenassé",
                        "Vérifier uniquement l'absence de tension côté BT et commencer les travaux",
                        "Demander au collègue de confirmer verbalement que tout est sécurisé"
                    ],
                    "correct_answer": 0,
                    "explanation": "Le sectionneur de terre doit être enclenché (règle 4 : mise à terre et court-circuit) et l'absence de tension doit être vérifiée des DEUX côtés (MT et BT) avant tout travail."
                },
            ],
            "vrai_faux": [
                {
                    "question": "Un travail sous tension (TST) en moyenne tension peut être effectué par n'importe quel électricien titulaire d'un CFC.",
                    "correct_answer": False,
                    "explanation": "FAUX — Les travaux sous tension requièrent une habilitation spécifique TST, une formation complémentaire reconnue et des EPI spéciaux. Un CFC seul ne suffit pas."
                },
            ],
        },
        "AE03": {
            "qcm": [
                {
                    "question": "Quelle grandeur photométrique caractérise la quantité de lumière perçue par l'œil humain sur une surface donnée ?",
                    "options": [
                        "L'éclairement, mesuré en lux (lx)",
                        "Le flux lumineux, mesuré en lumen (lm)",
                        "L'intensité lumineuse, mesurée en candela (cd)",
                        "La luminance, mesurée en cd/m²"
                    ],
                    "correct_answer": 0,
                    "explanation": "L'éclairement (E, en lux) mesure le flux lumineux reçu par unité de surface : E = Φ/A. C'est la grandeur la plus utilisée pour les normes d'éclairage public (EN 13201)."
                },
                {
                    "question": "Selon la norme EN 13201, quel paramètre définit la classe d'éclairage d'une route ?",
                    "options": [
                        "La catégorie de trafic (motorisé, piéton, cycliste) et la vitesse autorisée",
                        "L'altitude géographique de la route",
                        "La largeur de la chaussée uniquement",
                        "La marque des luminaires installés"
                    ],
                    "correct_answer": 0,
                    "explanation": "La norme EN 13201 classe les voies selon le type de trafic et la vitesse, définissant les classes M (routes motorisées), C (zones de conflit) et P (piétons/cyclistes) avec des niveaux d'éclairement correspondants."
                },
            ],
            "vrai_faux": [
                {
                    "question": "Les LED ont une durée de vie typique de 50'000 à 100'000 heures, bien supérieure aux lampes sodium haute pression (environ 20'000 heures).",
                    "correct_answer": True,
                    "explanation": "Les LED modernes atteignent 50'000-100'000h contre ~20'000h pour le sodium HP. De plus, les LED offrent un meilleur rendement lumineux (lm/W) et un IRC supérieur."
                },
            ],
        },
        "AE04": {
            "qcm": [
                {
                    "question": "Quel système d'information géographique est utilisé pour la documentation numérique des réseaux électriques en Suisse ?",
                    "options": [
                        "Un SIG/GIS avec couches de données géoréférencées (câbles, postes, appareils)",
                        "Un simple tableur Excel avec les adresses",
                        "Un classeur papier avec des plans photocopiés",
                        "Un logiciel de comptabilité avec module cartographique"
                    ],
                    "correct_answer": 0,
                    "explanation": "La documentation moderne des réseaux utilise un SIG (Système d'Information Géographique) avec des couches géoréférencées pour chaque type d'ouvrage, conforme aux exigences de l'OLEI."
                },
                {
                    "question": "Selon l'OLEI, quelle obligation incombe à l'exploitant de réseau concernant la documentation ?",
                    "options": [
                        "Tenir à jour les plans et schémas de toutes les installations et les rendre accessibles pour les tiers autorisés",
                        "Archiver les documents uniquement après la mise hors service des installations",
                        "Publier tous les plans sur internet",
                        "Conserver les documents pendant 2 ans seulement"
                    ],
                    "correct_answer": 0,
                    "explanation": "L'OLEI impose aux exploitants de maintenir une documentation à jour et accessible de toutes les installations électriques, incluant plans, schémas, rapports de contrôle et modifications."
                },
            ],
        },
        "AE07": {
            "qcm": [
                {
                    "question": "Quel appareil est utilisé pour mesurer la résistance de boucle de défaut dans une installation BT ?",
                    "options": [
                        "Un mesureur de boucle de défaut (loop tester) qui injecte un courant d'essai",
                        "Un multimètre standard en mode résistance",
                        "Un mégohmmètre à 500V DC",
                        "Un oscilloscope numérique"
                    ],
                    "correct_answer": 0,
                    "explanation": "Le mesureur de boucle de défaut (ex: Zs-mètre) injecte un courant d'essai et mesure l'impédance de la boucle L-PE. La valeur Zs permet de vérifier que le courant de défaut sera suffisant pour faire déclencher la protection."
                },
                {
                    "question": "Lors d'une mesure de résistance d'isolement selon la NIBT, quelle tension d'essai est appliquée pour un circuit 230V/400V ?",
                    "options": [
                        "500 V DC avec un seuil minimum de 1 MΩ",
                        "230 V AC avec un seuil minimum de 100 kΩ",
                        "1000 V DC avec un seuil minimum de 100 Ω",
                        "50 V DC avec un seuil minimum de 10 MΩ"
                    ],
                    "correct_answer": 0,
                    "explanation": "Pour les circuits BT (230/400V), l'essai d'isolement selon NIBT se fait à 500V DC. La résistance d'isolement minimale est de 1 MΩ entre chaque conducteur actif et la terre."
                },
            ],
            "calcul": [
                {
                    "question": "La mesure de boucle de défaut donne Zs = 1.15 Ω. Le circuit est protégé par un disjoncteur C16A (courant de déclenchement magnétique = 160A). Le temps de coupure maximal admissible est de 0.4s. Le courant de défaut est-il suffisant ? Calculer Ik en ampères (tension = 230V).",
                    "correct_answer": 200.0,
                    "tolerance": 0.05,
                    "unit": "A",
                    "explanation": "Ik = U/Zs = 230/1.15 = 200 A. Le courant de défaut (200A) est supérieur au seuil magnétique (160A) → le disjoncteur déclenchera bien dans les 0.4s requis."
                },
            ],
        },
        "AE10": {
            "qcm": [
                {
                    "question": "Quelle méthode est utilisée pour localiser un défaut d'isolement sur un câble souterrain MT ?",
                    "options": [
                        "La méthode de réflectométrie (TDR) combinée avec la méthode acoustique de frappe",
                        "L'inspection visuelle du tracé complet du câble",
                        "La mesure de tension aux deux extrémités simultanément",
                        "Le remplacement systématique du câble sans localisation"
                    ],
                    "correct_answer": 0,
                    "explanation": "La localisation de défaut cable MT utilise d'abord la pré-localisation par réflectométrie (TDR) pour estimer la distance du défaut, puis la localisation précise par méthode acoustique (générateur d'impulsions + récepteur au sol)."
                },
                {
                    "question": "Lors de la maintenance d'un réseau BT, quel est le critère NIBT pour considérer qu'un câble souterrain doit être remplacé ?",
                    "options": [
                        "Résistance d'isolement inférieure aux valeurs minimales NIBT et/ou dommages mécaniques visibles",
                        "Câble installé depuis plus de 10 ans automatiquement",
                        "Courant de charge supérieur à 50% de la capacité nominale",
                        "Changement de couleur de la gaine extérieure"
                    ],
                    "correct_answer": 0,
                    "explanation": "Le remplacement se base sur des critères objectifs : résistance d'isolement insuffisante, dommages mécaniques constatés, historique de défauts répétés, ou non-conformité avec les normes actuelles."
                },
            ],
            "mise_en_situation": [
                {
                    "scenario": "Vous recevez une alerte indiquant un défaut de terre sur un départ MT 16 kV. Le disjoncteur a déclenché automatiquement. Le réenclencheur automatique a tenté 2 fois sans succès.",
                    "question": "Quelle est la procédure de diagnostic à suivre ?",
                    "options": [
                        "Mesurer la résistance d'isolement de chaque tronçon par sectionnement progressif pour localiser le défaut",
                        "Réenclencher immédiatement le disjoncteur une 3ème fois",
                        "Attendre 24h que le défaut se résorbe de lui-même",
                        "Commuter la charge sur un autre départ sans diagnostic"
                    ],
                    "correct_answer": 0,
                    "explanation": "Après échec des réenclenchements automatiques, le défaut est permanent. Il faut procéder au sectionnement progressif et à la mesure d'isolement de chaque tronçon pour localiser et isoler la section défectueuse."
                },
            ],
        },
        "AE13": {
            "qcm": [
                {
                    "question": "Quel type d'isolateur est principalement utilisé sur les lignes aériennes moyenne tension (16 kV) en Suisse ?",
                    "options": [
                        "L'isolateur à capot et tige en verre ou porcelaine, ou isolateur composite en silicone",
                        "L'isolateur en bois traité",
                        "L'isolateur en plastique ABS standard",
                        "Aucun isolateur n'est nécessaire en 16 kV"
                    ],
                    "correct_answer": 0,
                    "explanation": "Les lignes MT 16 kV utilisent des isolateurs en verre trempé, porcelaine ou composites (silicone). Les composites gagnent du terrain grâce à leur légèreté et résistance au vandalisme."
                },
                {
                    "question": "Quelle est la portée typique entre deux supports de ligne aérienne BT en zone urbaine ?",
                    "options": [
                        "30 à 50 mètres selon le type de conducteur et les conditions",
                        "100 à 200 mètres",
                        "5 à 10 mètres",
                        "Plus de 500 mètres"
                    ],
                    "correct_answer": 0,
                    "explanation": "En zone urbaine, les portées BT sont typiquement de 30-50m, limitées par la flèche admissible, la hauteur libre au-dessus du sol (min. 6m au-dessus des routes) et les efforts mécaniques."
                },
            ],
            "vrai_faux": [
                {
                    "question": "Un conducteur de ligne aérienne en alliage d'aluminium-acier (ACSR) est utilisé car l'âme en acier assure la résistance mécanique tandis que les brins d'aluminium assurent la conductivité électrique.",
                    "correct_answer": True,
                    "explanation": "Le câble ACSR combine les propriétés : l'acier au centre apporte la résistance à la traction, l'aluminium en périphérie offre une bonne conductivité avec un poids réduit par rapport au cuivre."
                },
            ],
        },
    }

    def _generate_fallback(self, concept: Dict, question_num: int, q_type: str = "qcm") -> Dict:
        """
        Génère une question de secours de qualité professionnelle.
        
        Stratégie V3 :
        1. Banque par module/type (questions techniques réelles)
        2. Banque cross-module (si module sans questions)
        3. Questions techniques construites à partir des compétences d'examen
        JAMAIS de question triviale du type "Que représente le concept X ?"
        """
        name = concept.get('name', 'inconnu')
        module = concept.get('module', '')
        keywords = concept.get('keywords', [])
        
        # 1. Essayer la banque de questions pour ce module et ce type
        module_bank = self.FALLBACK_BANK.get(module, {})
        type_bank = module_bank.get(q_type, [])
        if type_bank:
            question = random.choice(type_bank).copy()
            question['fallback'] = True
            return self._add_metadata(question, concept, question_num)
        
        # 2. Essayer un autre type de question dans ce module
        for alt_type in ['qcm', 'vrai_faux', 'mise_en_situation', 'calcul']:
            alt_bank = module_bank.get(alt_type, [])
            if alt_bank:
                question = random.choice(alt_bank).copy()
                question['type'] = alt_type
                question['fallback'] = True
                return self._add_metadata(question, concept, question_num)
        
        # 3. Essayer un module voisin (AA ou AE)
        prefix = module[:2] if module else 'AA'
        for other_mod, other_bank in self.FALLBACK_BANK.items():
            if other_mod.startswith(prefix) and other_mod != module:
                for try_type in [q_type, 'qcm', 'vrai_faux']:
                    if try_type in other_bank and other_bank[try_type]:
                        question = random.choice(other_bank[try_type]).copy()
                        question['fallback'] = True
                        return self._add_metadata(question, concept, question_num)
        
        # 4. Construire une question technique à partir des compétences et keywords
        exam_comps = EXAM_COMPETENCES.get(module, [])
        mod_label = self._get_module_label(module)
        
        if q_type == "vrai_faux":
            if exam_comps:
                comp = random.choice(exam_comps)
                # Construire une vraie affirmation technique (pas juste "ce concept existe")
                return self._add_metadata({
                    "question": f"Pour le Brevet Fédéral, la compétence suivante est requise dans le module {module} ({mod_label}) : « {comp} ».",
                    "correct_answer": True,
                    "explanation": f"Cette compétence est explicitement listée dans les directives d'examen pour le module {module}. Elle est évaluée à l'examen professionnel.",
                    "fallback": True,
                    "hint": f"Pensez aux compétences attendues d'un spécialiste de réseau pour le domaine {mod_label}."
                }, concept, question_num)
            # Avec keywords — affirmation technique
            if keywords:
                kw = random.choice(keywords)
                return self._add_metadata({
                    "question": f"Le terme technique « {kw} » fait partie du vocabulaire professionnel essentiel du module {module} ({mod_label}).",
                    "correct_answer": True,
                    "explanation": f"« {kw} » est un concept clé du module {module} ({mod_label}), directement lié au sujet « {name} ».",
                    "fallback": True,
                    "hint": f"Ce terme est associé au domaine de {mod_label}."
                }, concept, question_num)

        elif q_type == "texte_trous":
            if keywords and len(keywords) >= 2:
                keyword = random.choice(keywords)
                other_kw = [k for k in keywords if k != keyword]
                hint_kw = other_kw[0] if other_kw else mod_label
                return self._add_metadata({
                    "question": f"Dans le domaine « {name} » (module {module} — {mod_label}), le terme technique _____ est étroitement lié aux concepts de {hint_kw}.",
                    "correct_answer": keyword,
                    "acceptable_answers": [keyword, keyword.lower(), keyword.upper(), keyword.replace('-', ' ')],
                    "explanation": f"« {keyword} » est un terme technique fondamental du concept « {name} » dans le module {module}. Il est lié à : {', '.join(keywords)}.",
                    "fallback": True,
                    "hint": f"C'est un terme du domaine {mod_label}, lié à {hint_kw}."
                }, concept, question_num)

        elif q_type == "calcul":
            # Questions de calcul universelles — toujours pertinentes pour un spécialiste réseau
            calcul_fallbacks = [
                {
                    "question": "Un circuit monophasé 230V alimente une charge résistive de 46 Ω. Calculer le courant en ampères.",
                    "correct_answer": 5.0,
                    "tolerance": 0.01,
                    "unit": "A",
                    "explanation": "Loi d'Ohm : I = U/R = 230/46 = 5.0 A",
                    "hint": "Appliquez la loi d'Ohm : I = U/R"
                },
                {
                    "question": "Calculer la puissance apparente S d'un moteur triphasé alimenté en 400V avec un courant de ligne de 10A.",
                    "correct_answer": 6928.0,
                    "tolerance": 0.02,
                    "unit": "VA",
                    "explanation": "S = √3 × U × I = 1.732 × 400 × 10 = 6'928 VA ≈ 6.93 kVA",
                    "hint": "En triphasé : S = √3 × U × I"
                },
                {
                    "question": "Deux résistances de 100 Ω et 150 Ω sont montées en parallèle. Calculer la résistance équivalente en ohms.",
                    "correct_answer": 60.0,
                    "tolerance": 0.02,
                    "unit": "Ω",
                    "explanation": "1/Req = 1/R1 + 1/R2 = 1/100 + 1/150 = 3/300 + 2/300 = 5/300\nReq = 300/5 = 60 Ω",
                    "hint": "Formule parallèle : 1/Req = 1/R1 + 1/R2"
                },
                {
                    "question": "Un câble de 25m (cuivre, ρ=0.0175 Ω·mm²/m, section 4mm²) alimente une charge de 20A en monophasé. Calculer la chute de tension aller-retour en volts.",
                    "correct_answer": 4.375,
                    "tolerance": 0.03,
                    "unit": "V",
                    "explanation": "R = ρ×L/S = 0.0175×25/4 = 0.109375 Ω\nΔU = 2×R×I = 2×0.109375×20 = 4.375 V",
                    "hint": "ΔU = 2 × R × I, avec R = ρ × L / S"
                },
            ]
            question = random.choice(calcul_fallbacks).copy()
            question['fallback'] = True
            return self._add_metadata(question, concept, question_num)

        elif q_type == "mise_en_situation":
            if exam_comps:
                comp = random.choice(exam_comps)
                return self._add_metadata({
                    "scenario": f"Vous êtes chef d'équipe sur un chantier de réseau électrique. Une intervention nécessite des compétences en « {name} » ({mod_label}). Votre équipe de 3 personnes doit intervenir dans des conditions normales.",
                    "question": f"Quelle est la démarche prioritaire avant de commencer l'intervention ?",
                    "options": [
                        f"Évaluer les risques, consulter les normes applicables, briefer l'équipe et vérifier les EPI",
                        "Commencer les travaux directement car l'équipe est expérimentée",
                        "Déléguer entièrement la responsabilité au plus ancien",
                        "Reporter l'intervention en attendant des renforts"
                    ],
                    "correct_answer": 0,
                    "explanation": f"Toute intervention de réseau exige une évaluation des risques, la consultation des normes (ESTI, SUVA, NIBT), un briefing d'équipe et la vérification des EPI. Compétence visée : « {comp} ».",
                    "fallback": True,
                    "hint": "Pensez à ce qui doit TOUJOURS être fait avant de commencer un travail sur réseau."
                }, concept, question_num)

        # QCM par défaut — basé sur les compétences réelles avec distracteurs plausibles
        if exam_comps and len(exam_comps) >= 2:
            correct_comp = random.choice(exam_comps)
            # Distracteurs : compétences d'AUTRES modules (plausibles mais fausses pour CE module)
            other_comps = []
            for other_mod, other_comp_list in EXAM_COMPETENCES.items():
                if other_mod != module:
                    other_comps.extend(other_comp_list)
            random.shuffle(other_comps)
            distractors = other_comps[:3] if len(other_comps) >= 3 else [
                "Dimensionner les installations photovoltaïques",
                "Programmer des automates industriels complexes",
                "Concevoir des circuits imprimés multicouches"
            ]
            
            options = [correct_comp] + distractors[:3]
            random.shuffle(options)
            correct_idx = options.index(correct_comp)
            
            return self._add_metadata({
                "question": f"Parmi les compétences suivantes, laquelle est spécifiquement requise dans le module {module} ({mod_label}) du Brevet Fédéral ?",
                "options": options,
                "correct_answer": correct_idx,
                "explanation": f"La compétence « {correct_comp} » est listée dans les directives d'examen pour le module {module}. Les autres compétences appartiennent à d'autres modules.",
                "fallback": True,
                "hint": f"Réfléchissez à ce qu'un spécialiste en {mod_label} doit maîtriser."
            }, concept, question_num)
        
        # Dernier recours absolu — question technique sur les keywords
        if keywords:
            correct_kw = keywords[0]
            wrong_keywords = [
                "Photovoltaïque bifacial", "Domotique KNX avancée",
                "Fibre optique monomode", "Automate Siemens S7"
            ]
            options = [correct_kw] + wrong_keywords[:3]
            random.shuffle(options)
            correct_idx = options.index(correct_kw)
            
            return self._add_metadata({
                "question": f"Quel terme technique est directement associé au domaine « {name} » dans le module {module} ({mod_label}) ?",
                "options": options,
                "correct_answer": correct_idx,
                "explanation": f"Le terme « {correct_kw} » est un mot-clé technique du concept « {name} ». Les mots-clés associés sont : {', '.join(keywords)}.",
                "fallback": True,
                "hint": f"Pensez au vocabulaire spécifique du domaine {mod_label}."
            }, concept, question_num)
        
        # Ultra dernier recours — ne devrait jamais arriver
        return self._add_metadata({
            "question": f"Quel module du Brevet Fédéral Spécialiste de Réseau couvre le domaine « {mod_label} » ?",
            "options": [module, "AA00", "AE00", "ZZ99"],
            "correct_answer": 0,
            "explanation": f"Le module {module} couvre « {mod_label} » dans le programme du Brevet Fédéral.",
            "fallback": True,
            "hint": f"Le code du module commence par {module[:2]}."
        }, concept, question_num)
    
    def save_quiz_result(self, quiz_id: str, score: int, total: int, 
                        time_spent: int, answers: List[Dict],
                        confidence_data: Dict = None):
        """Sauvegarde le résultat d'un quiz dans l'historique — V3 avec confiance"""
        history = self._load_history()
        
        result = {
            "quiz_id": quiz_id,
            "score": score,
            "total": total,
            "percentage": (score / total * 100) if total > 0 else 0,
            "time_spent": time_spent,
            "time_per_question": (time_spent / total) if total > 0 else 0,
            "answers": answers,
            "confidence_data": confidence_data or {},
            "completed_at": datetime.now().isoformat()
        }
        
        # Mettre à jour la qualité des questions dans la banque
        for ans in answers:
            if ans.get('concept_id') and ans.get('question_text'):
                self.update_question_quality(
                    ans['concept_id'],
                    ans.get('question_text', ''),
                    ans.get('is_correct', False)
                )
        
        history.append(result)
        self._save_history(history)
    
    def _load_history(self) -> List[Dict]:
        """Charge l'historique des quiz"""
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return []
        return []
    
    def _save_history(self, history: List[Dict]):
        """Sauvegarde l'historique des quiz"""
        self.history_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.history_file, 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
    
    def get_history(self, limit: int = 10) -> List[Dict]:
        """Retourne l'historique des derniers quiz"""
        history = self._load_history()
        return sorted(history, key=lambda x: x.get('completed_at', ''), reverse=True)[:limit]
    
    def get_stats(self) -> Dict:
        """Calcule les statistiques globales des quiz — V3 PREMIUM"""
        history = self._load_history()
        
        if not history:
            return {
                "total_quizzes": 0,
                "average_score": 0,
                "best_score": 0,
                "total_time": 0,
                "total_questions": 0,
                "current_streak": 0,
                "best_streak": 0,
                "avg_time_per_question": 0,
                "score_trend": "stable",
                "last_5_scores": [],
                "score_by_type": {},
                "total_hints_used": 0,
            }
        
        # Calculs de base
        avg = sum(q['percentage'] for q in history) / len(history)
        best = max(q['percentage'] for q in history)
        
        # Streak (série de quiz >= 60%)
        current_streak = 0
        best_streak = 0
        streak = 0
        for h in sorted(history, key=lambda x: x.get('completed_at', '')):
            if h['percentage'] >= 60:
                streak += 1
                best_streak = max(best_streak, streak)
            else:
                streak = 0
        # Current streak (depuis la fin)
        for h in sorted(history, key=lambda x: x.get('completed_at', ''), reverse=True):
            if h['percentage'] >= 60:
                current_streak += 1
            else:
                break
        
        # Tendance (derniers 5 vs précédents 5)
        sorted_history = sorted(history, key=lambda x: x.get('completed_at', ''))
        last_5 = [h['percentage'] for h in sorted_history[-5:]]
        prev_5 = [h['percentage'] for h in sorted_history[-10:-5]] if len(sorted_history) > 5 else []
        
        if prev_5 and last_5:
            trend_diff = sum(last_5) / len(last_5) - sum(prev_5) / len(prev_5)
            score_trend = "up" if trend_diff > 5 else ("down" if trend_diff < -5 else "stable")
        else:
            score_trend = "stable"
        
        # Score par type de question
        score_by_type = defaultdict(lambda: {"correct": 0, "total": 0})
        for h in history:
            for ans in h.get('answers', []):
                # Tenter de déterminer le type si disponible
                q_type = ans.get('type', 'qcm')
                score_by_type[q_type]['total'] += 1
                if ans.get('is_correct'):
                    score_by_type[q_type]['correct'] += 1
        
        score_by_type_pct = {}
        for t, data in score_by_type.items():
            pct = (data['correct'] / data['total'] * 100) if data['total'] > 0 else 0
            score_by_type_pct[t] = {"percentage": pct, "total": data['total']}
        
        # Temps moyen par question
        total_time = sum(q.get('time_spent', 0) for q in history)
        total_questions = sum(q['total'] for q in history)
        avg_time = total_time / total_questions if total_questions > 0 else 0
        
        # Hints utilisés
        total_hints = sum(
            len(h.get('confidence_data', {}).get('hints_used', []))
            for h in history
        )
        
        return {
            "total_quizzes": len(history),
            "average_score": avg,
            "best_score": best,
            "total_time": total_time,
            "total_questions": total_questions,
            "current_streak": current_streak,
            "best_streak": best_streak,
            "avg_time_per_question": avg_time,
            "score_trend": score_trend,
            "last_5_scores": last_5,
            "score_by_type": score_by_type_pct,
            "total_hints_used": total_hints,
        }
