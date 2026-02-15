"""
🎯 Focus Examen — Système de Priorisation Intelligente
========================================================
Classe chaque compétence par TYPE d'apprentissage (théorie, calcul, pratique terrain, oral)
et calcule une priorité Pareto (impact × lacune) pour cibler ce qui rapporte le plus de points.

Principes pédagogiques appliqués :
- Pareto 80/20 : cibler les 20% de concepts qui couvrent 80% des points
- Taxonomie de Bloom : identifier le NIVEAU requis (mémoriser → appliquer → analyser)
- Active Recall : tout ce qui est quizzable passe par quiz/flashcards
- Pratique délibérée : ce qui ne l'est PAS est listé comme exercice terrain
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from collections import defaultdict


# ============================================================
# CLASSIFICATION DES COMPÉTENCES PAR TYPE D'APPRENTISSAGE
# ============================================================
# Pour chaque module, on classe chaque compétence selon :
# - "theorie"   → Mémorisable par flashcards/quiz (définitions, normes, valeurs)
# - "calcul"    → Praticable par quiz calcul (formules, dimensionnement)
# - "pratique"  → Nécessite manipulation physique sur le terrain
# - "oral"      → Argumentation, présentation, communication
# - "projet"    → Travail de projet complet (rapport + présentation)

COMPETENCE_TYPES = {
    "AA01": {
        "Diriger une équipe de collaborateurs sur le terrain": "pratique",
        "Planifier et répartir les tâches de travail": "theorie",
        "Communiquer de manière efficace et constructive": "oral",
        "Gérer les conflits au sein de l'équipe": "oral",
        "Évaluer les performances des collaborateurs": "theorie",
        "Motiver l'équipe et assurer un bon climat de travail": "oral",
    },
    "AA02": {
        "Planifier et organiser la formation des apprentis": "theorie",
        "Transmettre les compétences professionnelles": "oral",
        "Évaluer les progrès de formation": "theorie",
        "Appliquer les méthodes pédagogiques adaptées": "theorie",
        "Connaître le cadre légal de la formation professionnelle": "theorie",
    },
    "AA03": {
        "Lire et interpréter les plans et schémas techniques": "pratique",
        "Établir des listes de matériel et outillage": "theorie",
        "Planifier le déroulement des travaux (logistique, délais)": "theorie",
        "Évaluer les risques liés aux travaux": "theorie",
        "Rédiger des rapports et de la documentation technique": "pratique",
    },
    "AA04": {
        "Gérer un mandat du début à la fin (offre → facturation)": "theorie",
        "Respecter les délais et budgets": "theorie",
        "Coordonner les intervenants sur un chantier": "pratique",
        "Appliquer les normes et prescriptions en vigueur": "theorie",
        "Documenter l'exécution des travaux": "pratique",
    },
    "AA05": {
        "Appliquer les règles de sécurité au travail (MSST, SUVA)": "theorie",
        "Identifier et évaluer les dangers sur un chantier": "pratique",
        "Utiliser correctement les EPI (équipements de protection)": "pratique",
        "Mettre en place des mesures de protection collective": "pratique",
        "Réagir correctement en cas d'accident": "pratique",
        "Connaître les premiers secours (BLS-AED)": "theorie",
    },
    "AA06": {
        "Contrôler la qualité des travaux exécutés": "pratique",
        "Vérifier la conformité aux plans et normes": "theorie",
        "Documenter les contrôles et résultats": "pratique",
        "Organiser les réceptions de chantier": "theorie",
        "Gérer les défauts et non-conformités": "theorie",
    },
    "AA07": {
        "Comprendre les stratégies de maintenance (préventive, corrective, prédictive)": "theorie",
        "Planifier les interventions de maintenance": "theorie",
        "Utiliser les systèmes de gestion de maintenance (GMAO)": "pratique",
        "Documenter les interventions et historiques": "theorie",
        "Calculer les coûts de maintenance": "calcul",
    },
    "AA08": {
        "Effectuer la maintenance des équipements de réseau": "pratique",
        "Diagnostiquer les pannes et dysfonctionnements": "pratique",
        "Appliquer les procédures de consignation/déconsignation": "pratique",
        "Utiliser les appareils de mesure et de test": "pratique",
        "Rédiger des rapports de maintenance": "pratique",
    },
    "AA09": {
        "Appliquer les lois fondamentales (Ohm, Kirchhoff, etc.)": "calcul",
        "Calculer en courant continu et alternatif (mono/triphasé)": "calcul",
        "Comprendre les transformateurs et machines électriques": "theorie",
        "Calculer les puissances (P, Q, S, cos φ)": "calcul",
        "Dimensionner les conducteurs et protections": "calcul",
        "Comprendre les schémas de liaison à la terre (TN, TT, IT)": "theorie",
    },
    "AA10": {
        "Appliquer les principes de mécanique statique": "calcul",
        "Calculer les forces, moments et charges": "calcul",
        "Comprendre les matériaux (acier, alu, bois, béton)": "theorie",
        "Dimensionner les supports et ancrages de lignes": "calcul",
    },
    "AA11": {
        "Maîtriser les calculs de base (algèbre, fractions, pourcentages)": "calcul",
        "Appliquer la trigonométrie aux calculs de réseau": "calcul",
        "Utiliser les formules de géométrie (surfaces, volumes)": "calcul",
        "Résoudre des équations liées aux réseaux électriques": "calcul",
    },
    "AE01": {
        "Réaliser une étude de projet de réseau de distribution": "projet",
        "Dimensionner un réseau (câbles, postes de transformation)": "calcul",
        "Calculer les chutes de tension et courants de court-circuit": "calcul",
        "Établir un devis et une planification de projet": "theorie",
        "Choisir les composants adaptés (câbles, connecteurs, etc.)": "theorie",
    },
    "AE02": {
        "Appliquer les 5 règles de sécurité": "theorie",
        "Connaître les distances de sécurité selon les niveaux de tension": "theorie",
        "Effectuer les consignations et déconsignations": "pratique",
        "Appliquer les prescriptions ESTI/Suva pour travaux sur IE": "theorie",
        "Établir des périmètres de sécurité": "pratique",
        "Gérer les situations d'urgence près d'installations électriques": "pratique",
    },
    "AE03": {
        "Planifier une installation d'éclairage public": "theorie",
        "Appliquer les normes EN 13201 et SLG 202": "theorie",
        "Choisir les luminaires et sources (LED)": "theorie",
        "Calculer l'éclairement et l'uniformité": "calcul",
        "Entretenir et maintenir les installations d'éclairage": "pratique",
    },
    "AE04": {
        "Lire et créer des schémas unifilaires de réseau": "pratique",
        "Utiliser les systèmes d'information géographique (SIG/GIS)": "pratique",
        "Documenter les réseaux selon les normes en vigueur": "theorie",
        "Mettre à jour les plans de réseau après intervention": "pratique",
        "Comprendre la symbologie normalisée": "theorie",
    },
    "AE05": {
        "Dimensionner les installations de mise à terre": "calcul",
        "Calculer la résistance de terre": "calcul",
        "Connaître les types de prises de terre (piquet, ruban, fondation)": "theorie",
        "Mesurer la résistance de terre et la résistivité du sol": "pratique",
        "Appliquer les normes pour la protection contre la foudre": "theorie",
    },
    "AE06": {
        "Comprendre le fonctionnement des réseaux de distribution (MT/BT)": "theorie",
        "Effectuer des manœuvres de réseau (ouverture/fermeture)": "pratique",
        "Gérer les perturbations et pannes de réseau": "pratique",
        "Comprendre les schémas d'exploitation (boucle, radial, maillé)": "theorie",
        "Appliquer les procédures d'exploitation sécurisée": "pratique",
    },
    "AE07": {
        "Effectuer des mesures électriques sur les réseaux": "pratique",
        "Utiliser les appareils de mesure (multimètre, pince, mégohmmètre)": "pratique",
        "Mesurer l'isolement, la continuité, la boucle de défaut": "pratique",
        "Interpréter les résultats de mesure": "calcul",
        "Rédiger des rapports de mesure conformes": "pratique",
    },
    "AE09": {
        "Comprendre les systèmes de protection des réseaux": "theorie",
        "Dimensionner les fusibles et disjoncteurs": "calcul",
        "Comprendre la sélectivité des protections": "theorie",
        "Calculer les courants de court-circuit": "calcul",
        "Configurer les relais de protection": "pratique",
        "Comprendre la coordination des protections MT/BT": "theorie",
    },
    "AE10": {
        "Planifier la maintenance des réseaux de distribution": "theorie",
        "Effectuer les contrôles périodiques des installations": "pratique",
        "Diagnostiquer les défauts sur les câbles et lignes": "pratique",
        "Utiliser les techniques de localisation de défauts": "pratique",
        "Organiser les interventions d'urgence sur le réseau": "pratique",
    },
    "AE11": {
        "Réaliser un projet complet de réseau de A à Z": "projet",
        "Rédiger un dossier technique de projet": "projet",
        "Présenter et défendre son projet oralement": "oral",
        "Appliquer la gestion de projet (planning, budget, risques)": "theorie",
        "Démontrer une approche méthodique et structurée": "projet",
    },
    "AE12": {
        "Choisir et dimensionner les câbles souterrains": "calcul",
        "Connaître les techniques de pose (tranchée, forage dirigé, etc.)": "theorie",
        "Réaliser et contrôler les jonctions et terminaisons": "pratique",
        "Appliquer les normes de pose et de croisement": "theorie",
        "Effectuer les essais après pose (isolement, manteau)": "pratique",
    },
    "AE13": {
        "Dimensionner les lignes aériennes (conducteurs, supports)": "calcul",
        "Calculer les portées et flèches": "calcul",
        "Connaître les types de supports (bois, béton, acier)": "theorie",
        "Appliquer les règles de croisement et voisinage": "theorie",
        "Effectuer la maintenance des lignes aériennes": "pratique",
    },
}

# ============================================================
# POIDS D'EXAMEN PAR MODULE (nombre de questions dans l'examen blanc)
# Plus le poids est élevé, plus le module rapporte de points
# ============================================================
EXAM_WEIGHT = {
    "AA01": 2, "AA02": 1, "AA03": 2, "AA04": 2, "AA05": 3,
    "AA06": 1, "AA07": 1, "AA08": 2, "AA09": 3, "AA10": 1, "AA11": 2,
    "AE01": 2, "AE02": 3, "AE03": 2, "AE04": 1, "AE05": 2,
    "AE06": 2, "AE07": 2, "AE09": 2, "AE10": 1, "AE11": 2,
    "AE12": 2, "AE13": 1,
}

# Types en badges pour l'UI
TYPE_LABELS = {
    "theorie": {"icon": "📖", "label": "Théorie", "color": "#2196F3", "quizzable": True,
                "description": "Mémorisable par flashcards et quiz (définitions, normes, valeurs, concepts)"},
    "calcul": {"icon": "🧮", "label": "Calcul", "color": "#FF9800", "quizzable": True,
               "description": "Praticable par quiz calcul (formules, dimensionnement, équations)"},
    "pratique": {"icon": "🔧", "label": "Pratique terrain", "color": "#4CAF50", "quizzable": False,
                 "description": "Manipulation physique, gestes techniques, utilisation d'outils — à pratiquer sur le terrain ou en atelier"},
    "oral": {"icon": "🎤", "label": "Oral / Communication", "color": "#9C27B0", "quizzable": False,
             "description": "Argumentation, présentation, gestion d'équipe — s'entraîner à voix haute ou en simulation"},
    "projet": {"icon": "📐", "label": "Travail de projet", "color": "#E91E63", "quizzable": False,
               "description": "Rédaction de dossier technique + présentation — nécessite un exercice complet de A à Z"},
}


class ExamFocusAnalyzer:
    """
    Analyse Pareto pour cibler les efforts de révision.
    Combine le poids d'examen avec le taux de maîtrise pour calculer
    un score de PRIORITÉ qui maximise les points gagnables à l'examen.
    """

    def __init__(self, weak_tracker=None, concept_map=None, config=None):
        self.weak_tracker = weak_tracker
        self.concept_map = concept_map or {}
        self.config = config or {}

    def get_competence_type(self, module: str, competence: str) -> str:
        """Retourne le type d'apprentissage d'une compétence"""
        module_types = COMPETENCE_TYPES.get(module, {})
        return module_types.get(competence, "theorie")

    def get_module_breakdown(self, module: str) -> Dict:
        """
        Décompose un module par type d'apprentissage.
        Retourne le % de théorie, calcul, pratique, oral, projet.
        """
        module_types = COMPETENCE_TYPES.get(module, {})
        if not module_types:
            return {}

        counts = defaultdict(int)
        for comp, ctype in module_types.items():
            counts[ctype] += 1

        total = len(module_types)
        return {
            "total_competences": total,
            "breakdown": {
                ctype: {
                    "count": counts.get(ctype, 0),
                    "pct": (counts.get(ctype, 0) / total * 100) if total > 0 else 0,
                    "competences": [c for c, t in module_types.items() if t == ctype],
                }
                for ctype in TYPE_LABELS.keys()
            },
            "quizzable_pct": sum(counts.get(t, 0) for t in ("theorie", "calcul")) / total * 100 if total > 0 else 0,
            "non_quizzable_pct": sum(counts.get(t, 0) for t in ("pratique", "oral", "projet")) / total * 100 if total > 0 else 0,
        }

    def get_all_modules_breakdown(self) -> Dict:
        """Décomposition de TOUS les modules"""
        return {mod: self.get_module_breakdown(mod) for mod in COMPETENCE_TYPES}

    def get_priority_ranking(self) -> List[Dict]:
        """
        Classement Pareto des modules par PRIORITÉ de révision.
        
        Score = poids_examen × (1 - taux_maîtrise)
        
        Les modules avec un haut poids d'examen ET un faible taux de maîtrise
        sont en haut de la liste = là où tu gagnes le plus de points.
        """
        weak_modules = {}
        if self.weak_tracker:
            weak_modules = self.weak_tracker.get_weak_modules()

        ranking = []
        for module, weight in EXAM_WEIGHT.items():
            # Taux de maîtrise du module (0-100)
            module_data = weak_modules.get(module, {})
            error_rate = module_data.get("error_rate", 50)  # 50% par défaut si pas de données
            mastery = 100 - error_rate

            # Score de priorité : plus c'est élevé, plus c'est urgent
            # On normalise le poids (max = 3 questions)
            normalized_weight = weight / 3.0
            gap = (100 - mastery) / 100.0
            priority_score = normalized_weight * gap * 100

            # Décomposition par type
            breakdown = self.get_module_breakdown(module)

            from src.directives_coverage import EXAM_REQUIREMENTS
            module_info = EXAM_REQUIREMENTS.get(module, {})

            ranking.append({
                "module": module,
                "name": module_info.get("name", module),
                "exam_weight": weight,
                "exam_questions": weight,
                "poids_examen": module_info.get("poids_examen", ""),
                "mastery_pct": mastery,
                "error_rate": error_rate,
                "priority_score": priority_score,
                "breakdown": breakdown,
                "quizzable_pct": breakdown.get("quizzable_pct", 0),
                "practice_needed": breakdown.get("non_quizzable_pct", 0) > 40,
                "weak_concepts": module_data.get("weak_concepts", []),
            })

        # Trier par priorité décroissante
        ranking.sort(key=lambda x: x["priority_score"], reverse=True)
        return ranking

    def get_study_plan_by_type(self) -> Dict:
        """
        Regroupe TOUTES les compétences de l'examen par type d'apprentissage.
        Permet de voir d'un coup :
        - Ce que tu peux faire en quiz/flashcards
        - Ce que tu DOIS pratiquer sur le terrain
        - Ce que tu dois préparer pour l'oral
        """
        plan = {ctype: [] for ctype in TYPE_LABELS}

        for module, competences in COMPETENCE_TYPES.items():
            from src.directives_coverage import EXAM_REQUIREMENTS
            module_info = EXAM_REQUIREMENTS.get(module, {})
            module_name = module_info.get("name", module)
            weight = EXAM_WEIGHT.get(module, 1)

            for comp, ctype in competences.items():
                plan[ctype].append({
                    "competence": comp,
                    "module": module,
                    "module_name": module_name,
                    "exam_weight": weight,
                })

        # Trier chaque liste par poids d'examen décroissant
        for ctype in plan:
            plan[ctype].sort(key=lambda x: x["exam_weight"], reverse=True)

        return plan

    def get_practice_checklist(self) -> List[Dict]:
        """
        Génère une checklist de compétences pratiques/orales/projet
        qui ne sont PAS testables par quiz.
        
        C'est ici que l'utilisateur voit ce qu'il DOIT pratiquer
        en dehors du système numérique.
        """
        checklist = []

        for module, competences in COMPETENCE_TYPES.items():
            from src.directives_coverage import EXAM_REQUIREMENTS
            module_info = EXAM_REQUIREMENTS.get(module, {})
            module_name = module_info.get("name", module)
            weight = EXAM_WEIGHT.get(module, 1)

            for comp, ctype in competences.items():
                if ctype in ("pratique", "oral", "projet"):
                    checklist.append({
                        "id": f"{module}_{comp[:30].replace(' ', '_')}",
                        "competence": comp,
                        "type": ctype,
                        "module": module,
                        "module_name": module_name,
                        "exam_weight": weight,
                        "suggestion": self._get_practice_suggestion(comp, ctype, module),
                    })

        checklist.sort(key=lambda x: x["exam_weight"], reverse=True)
        return checklist

    def _get_practice_suggestion(self, competence: str, ctype: str, module: str) -> str:
        """Génère une suggestion concrète d'exercice pour une compétence non-quizzable"""
        suggestions = {
            # PRATIQUE
            "Diriger une équipe de collaborateurs sur le terrain":
                "Prendre le lead lors d'un chantier réel. Observer un chef d'équipe et noter ses techniques.",
            "Lire et interpréter les plans et schémas techniques":
                "Prendre 5 plans de réseau différents et les interpréter sans aide. Comparer avec un collègue.",
            "Identifier et évaluer les dangers sur un chantier":
                "Faire un tour de chantier et rédiger une liste de risques. Utiliser la checklist SUVA.",
            "Utiliser correctement les EPI (équipements de protection)":
                "S'entraîner à enfiler les EPI complets en chrono. Connaître l'inspection avant usage.",
            "Mettre en place des mesures de protection collective":
                "Exercice : monter un balisage de chantier complet (panneaux, barrières, signalisation).",
            "Réagir correctement en cas d'accident":
                "Réviser le schéma d'alerte SUVA. Pratiquer BLS-AED sur mannequin.",
            "Effectuer les consignations et déconsignations":
                "Simuler une procédure de consignation complète (5 règles de sécurité). Pratiquer avec le formulaire officiel.",
            "Établir des périmètres de sécurité":
                "Exercice terrain : matérialiser un périmètre de sécurité pour travaux HT. Photo et vérification.",
            "Effectuer des mesures électriques sur les réseaux":
                "Pratiquer 10 mesures différentes avec multimètre et pince. Noter les résultats et interpréter.",
            "Utiliser les appareils de mesure (multimètre, pince, mégohmmètre)":
                "Prendre chaque appareil et faire une mesure réelle. S'entraîner au raccordement correct.",
            "Mesurer l'isolement, la continuité, la boucle de défaut":
                "Effectuer les 3 types de mesure sur une installation réelle. Comparer aux valeurs normatives.",
            "Effectuer des manœuvres de réseau (ouverture/fermeture)":
                "Observer et participer à des manœuvres réseau MT/BT. Noter la séquence exacte.",
            "Diagnostiquer les pannes et dysfonctionnements":
                "S'exercer avec des cas de pannes simulées. Pratiquer l'arbre de décision diagnostic.",
            "Réaliser et contrôler les jonctions et terminaisons":
                "Faire au moins 3 jonctions de câble + 3 terminaisons en atelier. Vérifier la qualité.",
            "Effectuer les essais après pose (isolement, manteau)":
                "Réaliser un protocole d'essais complet après pose de câble. Remplir le rapport type.",
            "Configurer les relais de protection":
                "S'exercer sur un relais de protection en laboratoire ou simulateur. Comprendre les réglages.",
            "Lire et créer des schémas unifilaires de réseau":
                "Dessiner 3 schémas unifilaires de réseau MT/BT à la main. Comparer avec un modèle correct.",
            # ORAL
            "Communiquer de manière efficace et constructive":
                "S'entraîner à faire un briefing de 5 min devant quelqu'un. Demander un feedback.",
            "Gérer les conflits au sein de l'équipe":
                "Préparer 3 scénarios de conflit et pratiquer les réponses à voix haute.",
            "Motiver l'équipe et assurer un bon climat de travail":
                "Préparer un discours de motivation de 2 min. S'enregistrer et réécouter.",
            "Transmettre les compétences professionnelles":
                "Expliquer un concept technique à un non-spécialiste. Tester la technique Feynman.",
            "Présenter et défendre son projet oralement":
                "Préparer une présentation de 10 min d'un projet réseau. Présenter devant quelqu'un.",
            # PROJET
            "Réaliser une étude de projet de réseau de distribution":
                "Prendre un cas concret et rédiger une étude de projet complète (objectif → solution → devis).",
            "Réaliser un projet complet de réseau de A à Z":
                "Choisir un projet type (nouveau raccordement) et le traiter entièrement sur papier.",
            "Rédiger un dossier technique de projet":
                "Rédiger un dossier technique avec : contexte, solution, plans, matériel, planning, budget.",
            "Démontrer une approche méthodique et structurée":
                "Utiliser un template de gestion de projet (étapes, jalons, risques) et le remplir pour un cas.",
        }

        # Suggestion générique si pas dans le dictionnaire
        if competence in suggestions:
            return suggestions[competence]

        if ctype == "pratique":
            return f"S'exercer concrètement sur : {competence}. Chercher une situation réelle pour pratiquer."
        elif ctype == "oral":
            return f"Préparer et présenter à voix haute : {competence}. S'enregistrer ou pratiquer avec un collègue."
        elif ctype == "projet":
            return f"Réaliser un exercice complet de type projet : {competence}. Rédiger un dossier et le défendre."
        return ""

    def get_global_stats(self) -> Dict:
        """Statistiques globales de la classification"""
        all_comps = []
        for module, competences in COMPETENCE_TYPES.items():
            for comp, ctype in competences.items():
                all_comps.append(ctype)

        total = len(all_comps)
        counts = defaultdict(int)
        for c in all_comps:
            counts[c] += 1

        quizzable = counts.get("theorie", 0) + counts.get("calcul", 0)
        non_quizzable = counts.get("pratique", 0) + counts.get("oral", 0) + counts.get("projet", 0)

        return {
            "total_competences": total,
            "by_type": {
                ctype: {
                    "count": counts.get(ctype, 0),
                    "pct": counts.get(ctype, 0) / total * 100 if total > 0 else 0,
                }
                for ctype in TYPE_LABELS
            },
            "quizzable": quizzable,
            "quizzable_pct": quizzable / total * 100 if total > 0 else 0,
            "non_quizzable": non_quizzable,
            "non_quizzable_pct": non_quizzable / total * 100 if total > 0 else 0,
            "total_exam_questions": sum(EXAM_WEIGHT.values()),
        }

    def get_top_priority_concepts(self, limit: int = 15) -> List[Dict]:
        """
        Top N concepts à réviser en priorité pour maximiser le score d'examen.
        Combine : poids d'examen × faiblesse × type quizzable.
        """
        if not self.weak_tracker:
            return []

        weak_concepts = self.weak_tracker.get_weak_concepts(min_errors=0, max_mastery=100)
        
        enriched = []
        for wc in weak_concepts:
            module = wc.get("module", "")
            weight = EXAM_WEIGHT.get(module, 1)
            mastery = wc.get("mastery_score", 50)
            
            # Score combiné : poids examen × lacune
            exam_impact = weight * (100 - mastery) / 100
            
            enriched.append({
                **wc,
                "exam_weight": weight,
                "exam_impact": exam_impact,
            })

        enriched.sort(key=lambda x: x["exam_impact"], reverse=True)
        return enriched[:limit]
