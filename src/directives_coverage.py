"""
Matrice de Couverture Directives d'Examen ↔ Modules/Concepts
==============================================================
Mappe les exigences des directives d'examen aux modules de formation
et évalue la couverture de chaque compétence par les concepts analysés.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple


# ============================================================
# COMPÉTENCES CLÉS PAR MODULE selon les Directives EP 01.01.2024
# Source : Directives d'examen du Brevet Fédéral Spécialiste de Réseau
# ============================================================

EXAM_REQUIREMENTS = {
    # ---- MODULES DE BASE (AA) ----
    "AA01": {
        "name": "Conduite de collaborateurs",
        "competences": [
            "Diriger une équipe de collaborateurs sur le terrain",
            "Planifier et répartir les tâches de travail",
            "Communiquer de manière efficace et constructive",
            "Gérer les conflits au sein de l'équipe",
            "Évaluer les performances des collaborateurs",
            "Motiver l'équipe et assurer un bon climat de travail",
        ],
        "poids_examen": "Épreuve écrite + orale",
    },
    "AA02": {
        "name": "Formation",
        "competences": [
            "Planifier et organiser la formation des apprentis",
            "Transmettre les compétences professionnelles",
            "Évaluer les progrès de formation",
            "Appliquer les méthodes pédagogiques adaptées",
            "Connaître le cadre légal de la formation professionnelle",
        ],
        "poids_examen": "Épreuve écrite",
    },
    "AA03": {
        "name": "Préparation du travail",
        "competences": [
            "Lire et interpréter les plans et schémas techniques",
            "Établir des listes de matériel et outillage",
            "Planifier le déroulement des travaux (logistique, délais)",
            "Évaluer les risques liés aux travaux",
            "Rédiger des rapports et de la documentation technique",
        ],
        "poids_examen": "Épreuve écrite + pratique",
    },
    "AA04": {
        "name": "Exécution de mandats",
        "competences": [
            "Gérer un mandat du début à la fin (offre → facturation)",
            "Respecter les délais et budgets",
            "Coordonner les intervenants sur un chantier",
            "Appliquer les normes et prescriptions en vigueur",
            "Documenter l'exécution des travaux",
        ],
        "poids_examen": "Épreuve écrite + pratique",
    },
    "AA05": {
        "name": "Santé et sécurité au travail",
        "competences": [
            "Appliquer les règles de sécurité au travail (MSST, SUVA)",
            "Identifier et évaluer les dangers sur un chantier",
            "Utiliser correctement les EPI (équipements de protection)",
            "Mettre en place des mesures de protection collective",
            "Réagir correctement en cas d'accident",
            "Connaître les premiers secours (BLS-AED)",
        ],
        "poids_examen": "Épreuve écrite + pratique",
    },
    "AA06": {
        "name": "Suivi des travaux",
        "competences": [
            "Contrôler la qualité des travaux exécutés",
            "Vérifier la conformité aux plans et normes",
            "Documenter les contrôles et résultats",
            "Organiser les réceptions de chantier",
            "Gérer les défauts et non-conformités",
        ],
        "poids_examen": "Épreuve écrite",
    },
    "AA07": {
        "name": "Bases de la maintenance",
        "competences": [
            "Comprendre les stratégies de maintenance (préventive, corrective, prédictive)",
            "Planifier les interventions de maintenance",
            "Utiliser les systèmes de gestion de maintenance (GMAO)",
            "Documenter les interventions et historiques",
            "Calculer les coûts de maintenance",
        ],
        "poids_examen": "Épreuve écrite",
    },
    "AA08": {
        "name": "Maintenance des équipements",
        "competences": [
            "Effectuer la maintenance des équipements de réseau",
            "Diagnostiquer les pannes et dysfonctionnements",
            "Appliquer les procédures de consignation/déconsignation",
            "Utiliser les appareils de mesure et de test",
            "Rédiger des rapports de maintenance",
        ],
        "poids_examen": "Épreuve écrite + pratique",
    },
    "AA09": {
        "name": "Électrotechnique",
        "competences": [
            "Appliquer les lois fondamentales (Ohm, Kirchhoff, etc.)",
            "Calculer en courant continu et alternatif (mono/triphasé)",
            "Comprendre les transformateurs et machines électriques",
            "Calculer les puissances (P, Q, S, cos φ)",
            "Dimensionner les conducteurs et protections",
            "Comprendre les schémas de liaison à la terre (TN, TT, IT)",
        ],
        "poids_examen": "Épreuve écrite (calculs)",
    },
    "AA10": {
        "name": "Mécanique",
        "competences": [
            "Appliquer les principes de mécanique statique",
            "Calculer les forces, moments et charges",
            "Comprendre les matériaux (acier, alu, bois, béton)",
            "Dimensionner les supports et ancrages de lignes",
        ],
        "poids_examen": "Épreuve écrite (calculs)",
    },
    "AA11": {
        "name": "Mathématique",
        "competences": [
            "Maîtriser les calculs de base (algèbre, fractions, pourcentages)",
            "Appliquer la trigonométrie aux calculs de réseau",
            "Utiliser les formules de géométrie (surfaces, volumes)",
            "Résoudre des équations liées aux réseaux électriques",
        ],
        "poids_examen": "Épreuve écrite (calculs)",
    },
    
    # ---- MODULES SPÉCIALISÉS ÉNERGIE (AE) ----
    "AE01": {
        "name": "Étude de projet",
        "competences": [
            "Réaliser une étude de projet de réseau de distribution",
            "Dimensionner un réseau (câbles, postes de transformation)",
            "Calculer les chutes de tension et courants de court-circuit",
            "Établir un devis et une planification de projet",
            "Choisir les composants adaptés (câbles, connecteurs, etc.)",
        ],
        "poids_examen": "Épreuve écrite + travail de projet",
    },
    "AE02": {
        "name": "Sécurité sur et à proximité d'IE",
        "competences": [
            "Appliquer les 5 règles de sécurité",
            "Connaître les distances de sécurité selon les niveaux de tension",
            "Effectuer les consignations et déconsignations",
            "Appliquer les prescriptions ESTI/Suva pour travaux sur IE",
            "Établir des périmètres de sécurité",
            "Gérer les situations d'urgence près d'installations électriques",
        ],
        "poids_examen": "Épreuve écrite + pratique (CRITIQUE)",
    },
    "AE03": {
        "name": "Éclairage public",
        "competences": [
            "Planifier une installation d'éclairage public",
            "Appliquer les normes EN 13201 et SLG 202",
            "Choisir les luminaires et sources (LED)",
            "Calculer l'éclairement et l'uniformité",
            "Entretenir et maintenir les installations d'éclairage",
        ],
        "poids_examen": "Épreuve écrite",
    },
    "AE04": {
        "name": "Documentation de réseaux",
        "competences": [
            "Lire et créer des schémas unifilaires de réseau",
            "Utiliser les systèmes d'information géographique (SIG/GIS)",
            "Documenter les réseaux selon les normes en vigueur",
            "Mettre à jour les plans de réseau après intervention",
            "Comprendre la symbologie normalisée",
        ],
        "poids_examen": "Épreuve écrite + pratique",
    },
    "AE05": {
        "name": "Installations de mise à terre",
        "competences": [
            "Dimensionner les installations de mise à terre",
            "Calculer la résistance de terre",
            "Connaître les types de prises de terre (piquet, ruban, fondation)",
            "Mesurer la résistance de terre et la résistivité du sol",
            "Appliquer les normes pour la protection contre la foudre",
        ],
        "poids_examen": "Épreuve écrite + pratique",
    },
    "AE06": {
        "name": "Exploitation de réseaux",
        "competences": [
            "Comprendre le fonctionnement des réseaux de distribution (MT/BT)",
            "Effectuer des manœuvres de réseau (ouverture/fermeture)",
            "Gérer les perturbations et pannes de réseau",
            "Comprendre les schémas d'exploitation (boucle, radial, maillé)",
            "Appliquer les procédures d'exploitation sécurisée",
        ],
        "poids_examen": "Épreuve écrite + pratique (CRITIQUE)",
    },
    "AE07": {
        "name": "Technique de mesure",
        "competences": [
            "Effectuer des mesures électriques sur les réseaux",
            "Utiliser les appareils de mesure (multimètre, pince, mégohmmètre)",
            "Mesurer l'isolement, la continuité, la boucle de défaut",
            "Interpréter les résultats de mesure",
            "Rédiger des rapports de mesure conformes",
        ],
        "poids_examen": "Épreuve écrite + pratique",
    },
    "AE09": {
        "name": "Technique de protection",
        "competences": [
            "Comprendre les systèmes de protection des réseaux",
            "Dimensionner les fusibles et disjoncteurs",
            "Comprendre la sélectivité des protections",
            "Calculer les courants de court-circuit",
            "Configurer les relais de protection",
            "Comprendre la coordination des protections MT/BT",
        ],
        "poids_examen": "Épreuve écrite + pratique (CRITIQUE)",
    },
    "AE10": {
        "name": "Maintenance des réseaux",
        "competences": [
            "Planifier la maintenance des réseaux de distribution",
            "Effectuer les contrôles périodiques des installations",
            "Diagnostiquer les défauts sur les câbles et lignes",
            "Utiliser les techniques de localisation de défauts",
            "Organiser les interventions d'urgence sur le réseau",
        ],
        "poids_examen": "Épreuve écrite + pratique",
    },
    "AE11": {
        "name": "Travail de projet",
        "competences": [
            "Réaliser un projet complet de réseau de A à Z",
            "Rédiger un dossier technique de projet",
            "Présenter et défendre son projet oralement",
            "Appliquer la gestion de projet (planning, budget, risques)",
            "Démontrer une approche méthodique et structurée",
        ],
        "poids_examen": "Travail de projet noté (POIDS IMPORTANT)",
    },
    "AE12": {
        "name": "Lignes souterraines",
        "competences": [
            "Choisir et dimensionner les câbles souterrains",
            "Connaître les techniques de pose (tranchée, forage dirigé, etc.)",
            "Réaliser et contrôler les jonctions et terminaisons",
            "Appliquer les normes de pose et de croisement",
            "Effectuer les essais après pose (isolement, manteau)",
        ],
        "poids_examen": "Épreuve écrite + pratique",
    },
    "AE13": {
        "name": "Lignes aériennes",
        "competences": [
            "Dimensionner les lignes aériennes (conducteurs, supports)",
            "Calculer les portées et flèches",
            "Connaître les types de supports (bois, béton, acier)",
            "Appliquer les règles de croisement et voisinage",
            "Effectuer la maintenance des lignes aériennes",
        ],
        "poids_examen": "Épreuve écrite + pratique",
    },
}


def get_all_exam_modules() -> List[str]:
    """Retourne la liste de tous les modules évalués à l'examen"""
    return sorted(EXAM_REQUIREMENTS.keys())


def get_module_coverage(concept_map: dict, config: dict) -> Dict[str, dict]:
    """
    Calcule la couverture de chaque module d'examen.
    
    Returns:
        Dict[module_code] -> {
            "name": str,
            "has_content": bool,        # Cours importés ?
            "num_concepts": int,         # Concepts analysés
            "competences": list,         # Compétences requises (directives)
            "poids_examen": str,
            "coverage_score": float,     # 0.0 à 1.0
            "status": str,              # "complet", "partiel", "manquant"
            "matched_concepts": list,    # Concepts qui couvrent les compétences
            "gaps": list,               # Compétences non couvertes
        }
    """
    nodes = concept_map.get('nodes', []) if concept_map else []
    modules_config = config.get('modules', {}) if config else {}
    
    # Regrouper les concepts par module
    concepts_by_module = {}
    for node in nodes:
        mod = node.get('module')
        if mod:
            if mod not in concepts_by_module:
                concepts_by_module[mod] = []
            concepts_by_module[mod].append(node)
    
    coverage = {}
    
    for module_code, req in EXAM_REQUIREMENTS.items():
        module_config = modules_config.get(module_code, {})
        has_content = module_config.get('has_content', False) if isinstance(module_config, dict) else False
        module_concepts = concepts_by_module.get(module_code, [])
        num_concepts = len(module_concepts)
        
        # Évaluer la couverture de chaque compétence
        competences = req['competences']
        matched_concepts = []
        gaps = []
        
        for comp in competences:
            # Chercher des concepts qui couvrent cette compétence
            comp_lower = comp.lower()
            comp_keywords = set(comp_lower.split())
            # Supprimer les mots courants
            stop_words = {'les', 'des', 'une', 'sur', 'par', 'pour', 'dans', 'avec',
                         'aux', 'est', 'sont', 'être', 'avoir', 'qui', 'que',
                         'son', 'ses', 'leur', 'du', 'de', 'la', 'le', 'un', 'et',
                         'en', 'au', 'ce', 'se', 'ou', 'd\'un', 'd\'une'}
            comp_keywords -= stop_words
            
            found = False
            for concept in module_concepts:
                concept_text = (
                    concept.get('name', '').lower() + ' ' +
                    concept.get('category', '').lower() + ' ' +
                    ' '.join(concept.get('keywords', []))
                ).lower()
                
                # Score de correspondance basé sur les mots-clés communs
                concept_words = set(concept_text.split())
                common = comp_keywords & concept_words
                
                if len(common) >= 2 or (len(comp_keywords) <= 3 and len(common) >= 1):
                    matched_concepts.append({
                        "competence": comp,
                        "concept": concept.get('name'),
                        "concept_id": concept.get('id'),
                    })
                    found = True
                    break
            
            if not found:
                gaps.append(comp)
        
        # Calculer le score de couverture
        total_comp = len(competences)
        covered = total_comp - len(gaps)
        coverage_score = covered / total_comp if total_comp > 0 else 0
        
        # Déterminer le statut
        if not has_content and num_concepts == 0:
            status = "manquant"
        elif coverage_score >= 0.7:
            status = "complet"
        elif coverage_score >= 0.3:
            status = "partiel"
        else:
            status = "insuffisant"
        
        coverage[module_code] = {
            "name": req['name'],
            "has_content": has_content,
            "num_concepts": num_concepts,
            "competences": competences,
            "poids_examen": req.get('poids_examen', ''),
            "coverage_score": coverage_score,
            "status": status,
            "matched_concepts": matched_concepts,
            "gaps": gaps,
        }
    
    return coverage


def get_coverage_summary(coverage: Dict[str, dict]) -> dict:
    """Résumé global de la couverture"""
    total_modules = len(coverage)
    total_competences = sum(len(c['competences']) for c in coverage.values())
    total_gaps = sum(len(c['gaps']) for c in coverage.values())
    covered_competences = total_competences - total_gaps
    
    modules_complet = sum(1 for c in coverage.values() if c['status'] == 'complet')
    modules_partiel = sum(1 for c in coverage.values() if c['status'] == 'partiel')
    modules_insuffisant = sum(1 for c in coverage.values() if c['status'] == 'insuffisant')
    modules_manquant = sum(1 for c in coverage.values() if c['status'] == 'manquant')
    
    # Modules critiques manquants
    critical_gaps = []
    for code, cov in coverage.items():
        if cov['status'] in ('manquant', 'insuffisant'):
            critical_gaps.append({
                'module': code,
                'name': cov['name'],
                'poids_examen': cov['poids_examen'],
                'gaps': cov['gaps'],
            })
    
    return {
        "total_modules": total_modules,
        "total_competences": total_competences,
        "covered_competences": covered_competences,
        "total_gaps": total_gaps,
        "coverage_rate": covered_competences / total_competences if total_competences > 0 else 0,
        "modules_complet": modules_complet,
        "modules_partiel": modules_partiel,
        "modules_insuffisant": modules_insuffisant,
        "modules_manquant": modules_manquant,
        "critical_gaps": critical_gaps,
    }
