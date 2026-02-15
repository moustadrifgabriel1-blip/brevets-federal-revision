"""
🎓 Coach Expert IA — Chaque compétence classée par NIVEAU DE MAÎTRISE REQUIS
==============================================================================
Un vrai formateur CIFER te dirait :
  « Ça, faut le DRILLER jusqu'à ce que ça soit automatique »
  « Ça, il faut le MAÎTRISER, tu dois pouvoir l'appliquer dans n'importe quelle situation »
  « Ça, tu dois le CONNAÎTRE, comprendre le principe mais pas besoin de tout savoir par cœur »
  « Ça, tu dois juste SAVOIR QUE ÇA EXISTE, être capable de le reconnaître si ça tombe »

Ce module classe les 118 compétences d'examen en 4 niveaux d'exigence
et fournit des prompts IA spécialisés par domaine pour agir comme un 
vrai coach expert de chaque domaine technique.
"""

from typing import Dict, List
from collections import defaultdict


# ============================================================
# NIVEAUX DE MAÎTRISE REQUIS — Taxonomie de Bloom adaptée
# ============================================================
# 🔴 DRILL    = Automatisme. Doit pouvoir répondre en 3 secondes. Drill quotidien.
#               Quiz intensif, flashcards quotidiennes, exercices répétés.
#               → «Si tu te trompes là-dessus à l'examen, tu perds des points bêtement»
#
# 🟠 MAÎTRISER = Compréhension profonde + application. Feynman + exercices variés.
#               Tu dois pouvoir l'expliquer ET l'appliquer dans un contexte nouveau.
#               → «On te posera un cas pratique, faut que tu saches quoi faire»
#
# 🟡 CONNAÎTRE = Comprendre le concept, le reconnaître, savoir le principe. 
#               Flashcards + lecture suffit. Pas besoin de drill intensif.
#               → «Faut le savoir mais pas besoin de le maîtriser à fond»
#
# 🟢 RECONNAÎTRE = Savoir que ça existe, identifier si c'est pertinent.
#               Lecture seule suffit. Pas de quiz nécessaire.
#               → «Si ça tombe à l'examen, ça sera un QCM facile, juste reconnaître»

MASTERY_LEVELS = {
    "drill": {
        "icon": "🔴",
        "label": "DRILL — Automatisme",
        "color": "#e53935",
        "description": "Réponse immédiate en 3 secondes. Drill quotidien obligatoire.",
        "study_method": "Quiz intensif + flashcards quotidiennes + exercices chronométrés",
        "frequency": "Tous les jours, 2-3x par jour si possible",
        "exam_risk": "Si tu te trompes là-dessus, tu perds des points faciles",
    },
    "maitriser": {
        "icon": "🟠",
        "label": "MAÎTRISER — Appliquer",
        "color": "#ff6f00",
        "description": "Comprendre en profondeur ET appliquer dans un cas nouveau.",
        "study_method": "Technique Feynman + quiz adaptatif + exercices de cas pratiques",
        "frequency": "3-4x par semaine, sessions de 20-30 min",
        "exam_risk": "Questions de mise en situation — faut pouvoir raisonner",
    },
    "connaitre": {
        "icon": "🟡",
        "label": "CONNAÎTRE — Comprendre",
        "color": "#fdd835",
        "description": "Comprendre le principe, savoir l'expliquer, reconnaître.",
        "study_method": "Flashcards + lecture active + résumés personnels",
        "frequency": "2x par semaine, révision espacée",
        "exam_risk": "Des QCM de compréhension, pas de piège",
    },
    "reconnaitre": {
        "icon": "🟢",
        "label": "RECONNAÎTRE — Identifier",
        "color": "#43a047",
        "description": "Savoir que ça existe, identifier dans un contexte donné.",
        "study_method": "Lecture seule + 1 passage en flashcards",
        "frequency": "1x par mois suffit",
        "exam_risk": "Rarement demandé directement, surtout du contexte",
    },
}


# ============================================================
# CLASSIFICATION EXHAUSTIVE — Chaque compétence, son niveau requis
# ============================================================
# Classé comme un vrai formateur CIFER le ferait, en pensant
# à ce qui tombe VRAIMENT à l'examen et combien ça pèse.

COMPETENCE_MASTERY = {
    # ============ AA01 — Conduite de collaborateurs ============
    "AA01": {
        "module_coach_profile": "Expert en management et leadership d'équipe technique",
        "module_focus": "L'examen teste ta capacité à diriger une équipe sur le terrain. Les questions sont souvent des mises en situation.",
        "competences": {
            "Diriger une équipe de collaborateurs sur le terrain": {
                "level": "maitriser",
                "coach_note": "Tu auras des mises en situation : « un collaborateur refuse une tâche, que fais-tu ? ». Prépare 5-6 scénarios types.",
                "exam_tip": "Pense toujours SÉCURITÉ D'ABORD dans tes réponses de conduite d'équipe.",
                "key_points": ["Styles de leadership", "Délégation", "Briefing sécurité", "Feedback constructif"],
            },
            "Planifier et répartir les tâches de travail": {
                "level": "maitriser",
                "coach_note": "Savoir faire un planning de chantier avec répartition des rôles. On te demandera de planifier un cas concret.",
                "exam_tip": "Utilise toujours la structure : Objectif → Ressources → Planning → Contrôle",
                "key_points": ["Diagramme de Gantt simplifié", "Matrice RACI", "Check-list préparation"],
            },
            "Communiquer de manière efficace et constructive": {
                "level": "connaitre",
                "coach_note": "Connaître les principes de communication. Pas besoin de drill, mais savoir les nommer.",
                "exam_tip": "Mots-clés : écoute active, reformulation, feedback sandwich, communication non-violente.",
                "key_points": ["4 règles de la communication", "Feedback constructif", "Rapport de chantier"],
            },
            "Gérer les conflits au sein de l'équipe": {
                "level": "connaitre",
                "coach_note": "Connaître 2-3 méthodes de résolution de conflits. C'est du QCM, pas un oral poussé.",
                "exam_tip": "Retiens : Écouter les deux parties → Trouver un terrain d'entente → Fixer des règles → Suivre",
                "key_points": ["Méthode DESC", "Médiation", "Escalade hiérarchique quand nécessaire"],
            },
            "Évaluer les performances des collaborateurs": {
                "level": "connaitre",
                "coach_note": "Savoir ce qu'est un entretien d'évaluation et ses étapes. Rarement une question complète dessus.",
                "exam_tip": "Retiens les 3 étapes : Préparation → Entretien → Suivi (objectifs SMART)",
                "key_points": ["Objectifs SMART", "Entretien annuel", "Plan de développement"],
            },
            "Motiver l'équipe et assurer un bon climat de travail": {
                "level": "reconnaitre",
                "coach_note": "Juste savoir que c'est important et connaître 2-3 leviers de motivation. Pas de drill nécessaire.",
                "exam_tip": "Si ça tombe : reconnaissance, responsabilisation, conditions de travail sûres.",
                "key_points": ["Théorie de Maslow", "Reconnaissance", "Implication dans les décisions"],
            },
        },
    },

    # ============ AA02 — Formation ============
    "AA02": {
        "module_coach_profile": "Expert en pédagogie et formation professionnelle CFC/AFP",
        "module_focus": "Module à faible poids (1 question). Connaître les bases de la formation des apprentis suffit.",
        "competences": {
            "Planifier et organiser la formation des apprentis": {
                "level": "connaitre",
                "coach_note": "Savoir utiliser un plan de formation et le programme de formation CFC Monteur-électricien.",
                "exam_tip": "Retiens : Plan de formation → Programme semestriel → Contrôle des compétences",
                "key_points": ["Plan de formation entreprise", "OrFo", "Compétences opérationnelles"],
            },
            "Transmettre les compétences professionnelles": {
                "level": "connaitre",
                "coach_note": "Connaître la méthode en 4 étapes (montrer, expliquer, faire faire, contrôler).",
                "exam_tip": "La méthode PADS : Préparer, Annoncer, Démontrer, S'exercer",
                "key_points": ["Méthode des 4 étapes", "Apprentissage par la pratique", "Instructions de travail"],
            },
            "Évaluer les progrès de formation": {
                "level": "reconnaitre",
                "coach_note": "Savoir que ça existe : contrôle de compétences, rapport de formation. Pas de drill.",
                "exam_tip": "Dossier de formation, évaluations semestrielles, rapport de stage.",
                "key_points": ["Dossier de formation", "Évaluation formative vs sommative"],
            },
            "Appliquer les méthodes pédagogiques adaptées": {
                "level": "reconnaitre",
                "coach_note": "Juste connaître que différentes méthodes existent. 1 question QCM max.",
                "exam_tip": "Méthodes : démonstration, instruction, projet guidé, auto-apprentissage.",
                "key_points": ["Pédagogie active", "Adaptation au niveau de l'apprenant"],
            },
            "Connaître le cadre légal de la formation professionnelle": {
                "level": "connaitre",
                "coach_note": "La LFPr (Loi sur la formation professionnelle) et les droits/devoirs du formateur.",
                "exam_tip": "Mots-clés : LFPr, OrFo, SEFRI, contrat d'apprentissage, durée, formation obligatoire formateur.",
                "key_points": ["LFPr", "OrFo", "Cours interentreprise (CI)", "Contrat d'apprentissage"],
            },
        },
    },

    # ============ AA03 — Préparation du travail ============
    "AA03": {
        "module_coach_profile": "Chef de chantier expérimenté en réseau électrique",
        "module_focus": "Préparer un chantier correctement. Questions de planification et lecture de plans.",
        "competences": {
            "Lire et interpréter les plans et schémas techniques": {
                "level": "drill",
                "coach_note": "C'EST FONDAMENTAL. Tu dois reconnaître INSTANTANÉMENT chaque symbole, chaque type de plan. Drill quotidien avec des plans réels.",
                "exam_tip": "On te montrera un plan et tu devras identifier des éléments. Zéro hésitation permise.",
                "key_points": ["Symboles normalisés", "Plans unifilaires", "Plans de situation", "Coupes de tranchée", "Schémas de câblage"],
            },
            "Établir des listes de matériel et outillage": {
                "level": "connaitre",
                "coach_note": "Savoir quoi mettre dans une liste de matériel pour un chantier type. Pas de drill.",
                "exam_tip": "Pense catégories : câbles, accessoires, outillage, EPI, signalisation, matériel de mesure.",
                "key_points": ["Check-list chantier", "Références techniques câbles", "Normes d'outillage"],
            },
            "Planifier le déroulement des travaux (logistique, délais)": {
                "level": "maitriser",
                "coach_note": "Tu devras planifier un mini-chantier en situation d'examen. Maîtrise la méthode.",
                "exam_tip": "Structure : Permis → Préparation → Exécution → Contrôle → Remise en état → Documentation",
                "key_points": ["Phases de chantier", "Planning journalier", "Coordination intervenants"],
            },
            "Évaluer les risques liés aux travaux": {
                "level": "maitriser",
                "coach_note": "L'évaluation des risques est TOUJOURS demandée en lien avec la sécurité. Maîtrise la matrice de risque.",
                "exam_tip": "Matrice probabilité × gravité. TOUJOURS lier au module AA05 (sécurité).",
                "key_points": ["Analyse de risque", "Matrice de risque", "Mesures de prévention", "SUVA"],
            },
            "Rédiger des rapports et de la documentation technique": {
                "level": "connaitre",
                "coach_note": "Savoir ce qu'on met dans un rapport de chantier. Pas de drill, mais connaître la structure.",
                "exam_tip": "Structure rapport : lieu, date, description, mesures prises, résultats, suite à donner.",
                "key_points": ["Rapport de chantier", "PV de réception", "Documentation as-built"],
            },
        },
    },

    # ============ AA04 — Exécution de mandats ============
    "AA04": {
        "module_coach_profile": "Responsable de projets en entreprise de réseau",
        "module_focus": "Gestion complète d'un mandat. Questions sur le processus offre → facturation.",
        "competences": {
            "Gérer un mandat du début à la fin (offre → facturation)": {
                "level": "maitriser",
                "coach_note": "Tu dois connaître CHAQUE étape du flux : Demande → Offre → Commande → Exécution → Rapport → Facture. C'est un classique d'examen.",
                "exam_tip": "Dessine le flux complet sur papier de tête. Si tu peux le faire = tu es prêt.",
                "key_points": ["Flow complet du mandat", "Offre", "Bon de commande", "Facturation", "PV de réception"],
            },
            "Respecter les délais et budgets": {
                "level": "connaitre",
                "coach_note": "Connaître les outils de suivi (planning, budget). Pas de drill, c'est du bon sens + méthode.",
                "exam_tip": "Outils : planning des tâches, suivi des coûts, rapport d'avancement.",
                "key_points": ["Suivi budgétaire", "Reporting", "Écarts planning"],
            },
            "Coordonner les intervenants sur un chantier": {
                "level": "connaitre",
                "coach_note": "Savoir qui fait quoi sur un chantier multi-corps. Pas besoin de drill mais de compréhension.",
                "exam_tip": "Intervenants types : maître d'ouvrage, ingénieur, entreprise, sous-traitant, commune, GRD.",
                "key_points": ["Organigramme chantier", "Séances de coordination", "Interfaces"],
            },
            "Appliquer les normes et prescriptions en vigueur": {
                "level": "drill",
                "coach_note": "Tu DOIS connaître les normes principales par cœur : NIBT, OIBT, ESTI, LIE, OLT, Suva. Ça tombe TOUJOURS.",
                "exam_tip": "Fais des flashcards par norme : nom complet, numéro, contenu principal, quand l'appliquer.",
                "key_points": ["NIBT (NIN)", "OIBT (NIV)", "ESTI", "LIE", "OLT 3+4", "Ordonnances Suva", "EN/IEC"],
            },
            "Documenter l'exécution des travaux": {
                "level": "connaitre",
                "coach_note": "Savoir quels documents produire après un chantier. C'est de la culture métier.",
                "exam_tip": "Documents : rapport journalier, plans as-built, PV de mesure, certificat de conformité.",
                "key_points": ["Plans conformes à l'exécution", "Dossier de fin de travaux", "Archivage"],
            },
        },
    },

    # ============ AA05 — Santé et sécurité au travail ============
    "AA05": {
        "module_coach_profile": "Responsable sécurité certifié MSST / Chargé de sécurité Suva",
        "module_focus": "3 QUESTIONS À L'EXAMEN. Module CRITIQUE. Sécurité = jamais d'erreur permise, dans la vie comme à l'examen.",
        "competences": {
            "Appliquer les règles de sécurité au travail (MSST, SUVA)": {
                "level": "drill",
                "coach_note": "MSST, les 10 règles vitales Suva, la directive CFST 6508 — DRILL QUOTIDIEN. C'est 3 questions à l'examen !!",
                "exam_tip": "Les 10 règles vitales de la Suva doivent être récitées PAR CŒUR. Aucune excuse.",
                "key_points": ["10 règles vitales Suva", "Directive CFST 6508", "MSST", "Concept de sécurité", "Plan de sécurité"],
            },
            "Identifier et évaluer les dangers sur un chantier": {
                "level": "drill",
                "coach_note": "Identifier les dangers = RÉFLEXE. Tu dois pouvoir scanner un chantier et lister les dangers en 30 secondes.",
                "exam_tip": "Catégories de dangers : électrique, mécanique, chute, ensevelissement, chimique, circulation, tiers.",
                "key_points": ["Analyse de risques", "Check-list dangers", "Évaluation probabilité/gravité", "Stop-travail"],
            },
            "Utiliser correctement les EPI (équipements de protection)": {
                "level": "drill",
                "coach_note": "Chaque EPI, quand l'utiliser, comment l'inspecter. AUTOMATISME. À l'examen pratique, pas d'hésitation.",
                "exam_tip": "Connaître par cœur : casque, lunettes, gants (isolants + mécanique), chaussures S3, harnais, ARI.",
                "key_points": ["Types d'EPI par risque", "Inspection avant usage", "Normes EPI (EN)", "Durée de vie", "Traçabilité"],
            },
            "Mettre en place des mesures de protection collective": {
                "level": "maitriser",
                "coach_note": "Les mesures collectives AVANT les EPI individuels. Maîtrise la hiérarchie STOP.",
                "exam_tip": "STOP : Substituer → Technique → Organisationnel → Personnel. Toujours dans cet ordre !",
                "key_points": ["Hiérarchie STOP", "Balisage", "Signalisation", "Protection anti-chute", "Blindage tranchées"],
            },
            "Réagir correctement en cas d'accident": {
                "level": "drill",
                "coach_note": "Le schéma d'alerte = AUTOMATISME. Tu dois pouvoir le dérouler les yeux fermés.",
                "exam_tip": "1. Protéger 2. Alerter (144/112) 3. Secourir. BLS-AED obligatoire.",
                "key_points": ["Schéma d'alerte", "Numéros d'urgence (144, 118, 117, 112, 145)", "BLS-AED", "Position latérale", "Protocole accident électrique"],
            },
            "Connaître les premiers secours (BLS-AED)": {
                "level": "drill",
                "coach_note": "PAS NÉGOCIABLE. Un électricien qui ne sait pas réanimer = dangereux. Drill le protocole.",
                "exam_tip": "30 compressions : 2 insufflations. Rythme 100-120/min. AED dès que possible. Ne jamais arrêter.",
                "key_points": ["Chaîne de survie", "30:2", "AED automatique", "Accident électrique (ne pas toucher avant mise hors tension)"],
            },
        },
    },

    # ============ AA06 — Suivi des travaux ============
    "AA06": {
        "module_coach_profile": "Responsable qualité et contrôle de chantier",
        "module_focus": "1 seule question à l'examen. Connaître les principes de contrôle qualité suffit.",
        "competences": {
            "Contrôler la qualité des travaux exécutés": {
                "level": "connaitre",
                "coach_note": "Savoir quels sont les points de contrôle sur un chantier de réseau. Pas de drill nécessaire.",
                "exam_tip": "Points de contrôle types : profondeur tranchée, lit de pose, distance croisements, essais câbles.",
                "key_points": ["Check-list qualité", "Points d'arrêt", "Contrôle visuel"],
            },
            "Vérifier la conformité aux plans et normes": {
                "level": "connaitre",
                "coach_note": "Comparer ce qui est fait avec ce qui était prévu. Documenter les écarts.",
                "exam_tip": "Plans as-built = obligatoire. Tout écart doit être documenté et validé.",
                "key_points": ["Conformité as-built", "Non-conformité", "Dérogation"],
            },
            "Documenter les contrôles et résultats": {
                "level": "reconnaitre",
                "coach_note": "Savoir que ça doit se faire. Un rapport type suffit. Pas de drill.",
                "exam_tip": "PV de contrôle avec : date, lieu, participants, résultats, suivi.",
                "key_points": ["PV de contrôle", "Traçabilité", "Archivage"],
            },
            "Organiser les réceptions de chantier": {
                "level": "reconnaitre",
                "coach_note": "Savoir ce qu'est une réception (provisoire vs définitive). C'est 1 QCM maximum.",
                "exam_tip": "Réception provisoire → Période de garantie → Réception définitive.",
                "key_points": ["Réception provisoire", "Réception définitive", "Période de garantie", "Réserves"],
            },
            "Gérer les défauts et non-conformités": {
                "level": "reconnaitre",
                "coach_note": "Savoir qu'il faut documenter et corriger. Pas plus que ça pour l'examen.",
                "exam_tip": "Processus : Constater → Documenter → Corriger → Vérifier → Clôturer.",
                "key_points": ["Fiche de non-conformité", "Action corrective"],
            },
        },
    },

    # ============ AA07 — Bases de la maintenance ============
    "AA07": {
        "module_coach_profile": "Ingénieur maintenance réseau de distribution",
        "module_focus": "1 question. Connaître les types de maintenance et la logique. Pas de drill.",
        "competences": {
            "Comprendre les stratégies de maintenance (préventive, corrective, prédictive)": {
                "level": "drill",
                "coach_note": "Les 3 types de maintenance = AUTOMATISME. Ça tombe quasiment à chaque examen en QCM.",
                "exam_tip": "Préventive (planifiée), Corrective (après panne), Prédictive (selon état). Exemple pour chaque.",
                "key_points": ["Maintenance préventive systématique", "Maintenance corrective", "Maintenance prédictive (conditionnelle)", "MTBF", "MTTR"],
            },
            "Planifier les interventions de maintenance": {
                "level": "connaitre",
                "coach_note": "Savoir faire un planning de maintenance périodique. Pas de drill mais comprendre.",
                "exam_tip": "Fréquences types : contrôle visuel annuel, essais périodiques, remplacement préventif.",
                "key_points": ["Planning périodique", "Gamme de maintenance", "Priorités d'intervention"],
            },
            "Utiliser les systèmes de gestion de maintenance (GMAO)": {
                "level": "reconnaitre",
                "coach_note": "Savoir que ça existe. Tu n'auras pas de question technique dessus.",
                "exam_tip": "GMAO = logiciel de gestion de maintenance assistée par ordinateur. Just know it exists.",
                "key_points": ["GMAO", "Historique des interventions", "Suivi des équipements"],
            },
            "Documenter les interventions et historiques": {
                "level": "reconnaitre",
                "coach_note": "Bon sens professionnel. Savoir qu'on documente toute intervention.",
                "exam_tip": "Rapport d'intervention : date, installation, constat, action, résultat, suite.",
                "key_points": ["Rapport d'intervention", "Historique équipement", "Base de données technique"],
            },
            "Calculer les coûts de maintenance": {
                "level": "connaitre",
                "coach_note": "Comprendre le concept coût maintenance vs coût remplacement. Pas de calcul complexe.",
                "exam_tip": "Coût total = main d'œuvre + matériel + indisponibilité. Quand remplacer vs réparer ?",
                "key_points": ["Coût de maintenance", "Analyse coût/bénéfice", "Durée de vie économique"],
            },
        },
    },

    # ============ AA08 — Maintenance des équipements ============
    "AA08": {
        "module_coach_profile": "Technicien senior en maintenance d'installations électriques",
        "module_focus": "2 questions. Accent sur les procédures de consignation et le diagnostic.",
        "competences": {
            "Effectuer la maintenance des équipements de réseau": {
                "level": "connaitre",
                "coach_note": "Connaître les types d'équipements (transformateurs, cellules, câbles) et leur maintenance type.",
                "exam_tip": "Pour chaque équipement : fréquence de contrôle, points de vérification, critères de remplacement.",
                "key_points": ["Transformateurs", "Cellules MT", "Coffrets BT", "Câbles", "Postes de transformation"],
            },
            "Diagnostiquer les pannes et dysfonctionnements": {
                "level": "maitriser",
                "coach_note": "On te donnera un cas de panne à l'examen. Tu dois savoir dérouler la méthode de diagnostic.",
                "exam_tip": "Méthode : Symptôme → Hypothèses → Tests → Diagnostic → Réparation → Vérification",
                "key_points": ["Arbre de décision", "Méthode de diagnostic", "Défauts courants", "Mesures de vérification"],
            },
            "Appliquer les procédures de consignation/déconsignation": {
                "level": "drill",
                "coach_note": "LES 5 RÈGLES DE SÉCURITÉ = RÉFLEXE ABSOLU. Tu dois les réciter dans l'ordre PAR CŒUR.",
                "exam_tip": "1. Déclencher/Sectionner 2. Sécuriser contre le réenclenchement 3. Vérifier l'absence de tension 4. Mettre à la terre et en court-circuit 5. Protéger contre les parties voisines sous tension",
                "key_points": ["5 règles de sécurité", "Formulaire de consignation", "Responsabilités (chargé de consignation, chargé de travaux)", "Déconsignation"],
            },
            "Utiliser les appareils de mesure et de test": {
                "level": "maitriser",
                "coach_note": "Savoir QUEL appareil pour QUELLE mesure et COMMENT l'utiliser correctement.",
                "exam_tip": "Multimètre (U, I, R), Pince ampèremétrique, Mégohmmètre (isolement), Terre (Chauvin Arnoux), Boucle de défaut.",
                "key_points": ["Multimètre", "Pince ampèremétrique", "Mégohmmètre", "Mesureur de terre", "Localisateur de câbles"],
            },
            "Rédiger des rapports de maintenance": {
                "level": "reconnaitre",
                "coach_note": "Savoir qu'un rapport est obligatoire et connaître sa structure. Pas de drill.",
                "exam_tip": "Structure : Identification installation → Constat → Mesures → Actions → Résultat → Recommandations",
                "key_points": ["Rapport type", "Traçabilité", "Recommandations"],
            },
        },
    },

    # ============ AA09 — Électrotechnique ============
    "AA09": {
        "module_coach_profile": "Professeur d'électrotechnique spécialisé réseaux de distribution",
        "module_focus": "3 QUESTIONS — Module CRITIQUE de CALCUL. Les formules doivent sortir automatiquement.",
        "competences": {
            "Appliquer les lois fondamentales (Ohm, Kirchhoff, etc.)": {
                "level": "drill",
                "coach_note": "U=R×I, P=U×I, lois de Kirchhoff = AUTOMATISME. Tu dois pouvoir les appliquer en 10 secondes.",
                "exam_tip": "Attention aux pièges : unités (kV, mA, MΩ), facteur √3 en triphasé, signe des courants.",
                "key_points": ["U=R×I", "P=U×I", "1ère loi Kirchhoff (nœuds)", "2ème loi Kirchhoff (mailles)", "Résistances série/parallèle"],
            },
            "Calculer en courant continu et alternatif (mono/triphasé)": {
                "level": "drill",
                "coach_note": "Formules triphasé = le nerf de la guerre. P=√3×U×I×cosφ doit être un réflexe.",
                "exam_tip": "Mono : P=U×I×cosφ | Tri : P=√3×U×I×cosφ | Ne jamais confondre tension phase et tension composée !",
                "key_points": ["P=U×I×cosφ (mono)", "P=√3×U×I×cosφ (tri)", "U_composée = √3 × U_phase", "Diagramme de Fresnel", "Impédance Z=√(R²+X²)"],
            },
            "Comprendre les transformateurs et machines électriques": {
                "level": "maitriser",
                "coach_note": "Le rapport de transformation et les couplages (Dyn11, Yyn0) doivent être maîtrisés, pas juste connus.",
                "exam_tip": "U1/U2 = N1/N2. Couplage Dyn11 = le plus courant en distribution. Savoir pourquoi.",
                "key_points": ["Rapport de transformation", "Couplages (Dyn11, Yyn0)", "Pertes fer/cuivre", "Rendement", "Plaque signalétique"],
            },
            "Calculer les puissances (P, Q, S, cos φ)": {
                "level": "drill",
                "coach_note": "Triangle des puissances = AUTOMATISME. S² = P² + Q², cosφ = P/S. DRILL QUOTIDIEN.",
                "exam_tip": "P (active, W), Q (réactive, var), S (apparente, VA). Compensation du cosφ = question classique.",
                "key_points": ["Triangle des puissances", "S² = P² + Q²", "cos φ = P/S", "Compensation réactive", "Batterie de condensateurs"],
            },
            "Dimensionner les conducteurs et protections": {
                "level": "drill",
                "coach_note": "Choisir la section du câble selon le courant, la chute de tension et la protection. Questions SYSTÉMATIQUES.",
                "exam_tip": "Étapes : 1. Courant nominal 2. Facteurs de correction 3. Iz admissible 4. Vérification Δu ≤ 3-5% 5. Choix protection",
                "key_points": ["Tableaux de courant admissible", "Facteurs de correction (température, groupement)", "Chute de tension Δu", "Sélectivité", "Coordination câble/protection"],
            },
            "Comprendre les schémas de liaison à la terre (TN, TT, IT)": {
                "level": "drill",
                "coach_note": "TN-C, TN-S, TT, IT = SAVOIR PAR CŒUR avec les schémas. Ça tombe à chaque examen.",
                "exam_tip": "TN-S = le plus courant en Suisse (NIBT). Dessine les 4 schémas de mémoire = tu es prêt.",
                "key_points": ["TN-S (neutre + PE séparés)", "TN-C (PEN combiné)", "TT (terre séparée)", "IT (neutre isolé)", "Conditions de coupure pour chaque"],
            },
        },
    },

    # ============ AA10 — Mécanique ============
    "AA10": {
        "module_coach_profile": "Ingénieur mécanique spécialisé en lignes aériennes et supports",
        "module_focus": "1 question. Calculs mécaniques simples (forces, moments). Pas le plus dur.",
        "competences": {
            "Appliquer les principes de mécanique statique": {
                "level": "connaitre",
                "coach_note": "Équilibre des forces, moments. Comprendre le concept mais pas besoin de calculs complexes.",
                "exam_tip": "ΣF=0, ΣM=0. Savoir décomposer une force en composantes. Dessiner un diagramme des forces.",
                "key_points": ["Équilibre statique", "Décomposition de forces", "Moment d'une force"],
            },
            "Calculer les forces, moments et charges": {
                "level": "maitriser",
                "coach_note": "Savoir calculer des efforts sur un support de ligne aérienne. Questions de calcul simples.",
                "exam_tip": "Charge du vent, poids du câble, résultante. Toujours faire un schéma avant de calculer !",
                "key_points": ["Charge de vent", "Poids propre", "Résultante des forces", "Coefficient de sécurité"],
            },
            "Comprendre les matériaux (acier, alu, bois, béton)": {
                "level": "connaitre",
                "coach_note": "Propriétés principales de chaque matériau. QCM simple sur avantages/inconvénients.",
                "exam_tip": "Acier = résistant mais corrosion. Alu = léger. Bois = isolant naturel. Béton = supports.",
                "key_points": ["Résistance mécanique", "Résistance à la corrosion", "Conductivité", "Utilisation en réseau"],
            },
            "Dimensionner les supports et ancrages de lignes": {
                "level": "connaitre",
                "coach_note": "Comprendre le principe mais les calculs détaillés sont rares à l'examen.",
                "exam_tip": "Types de supports : d'alignement, d'angle, d'ancrage, d'arrêt. Fondation adaptée au sol.",
                "key_points": ["Types de supports", "Fondations", "Efforts au sol", "Haubanage"],
            },
        },
    },

    # ============ AA11 — Mathématique ============
    "AA11": {
        "module_coach_profile": "Prof de maths appliquées à l'électrotechnique",
        "module_focus": "2 questions. Les maths sont un OUTIL pour les autres modules. Drill les formules appliquées.",
        "competences": {
            "Maîtriser les calculs de base (algèbre, fractions, pourcentages)": {
                "level": "drill",
                "coach_note": "Si tu galères en algèbre et pourcentages, tu galères PARTOUT. Drill quotidien.",
                "exam_tip": "Règles de priorité, fractions, pourcentages, conversion d'unités (kV↔V, kW↔W, mm²).",
                "key_points": ["Conversion d'unités", "Pourcentages", "Fractions", "Puissances de 10", "Règle de trois"],
            },
            "Appliquer la trigonométrie aux calculs de réseau": {
                "level": "maitriser",
                "coach_note": "sin, cos, tan pour les diagrammes de Fresnel et calculs de flèches. Pas optionnel.",
                "exam_tip": "SOH-CAH-TOA. Théorème de Pythagore. Application : diagramme des puissances, cosφ.",
                "key_points": ["sin, cos, tan", "Pythagore", "Diagramme de Fresnel", "Résolution de triangles"],
            },
            "Utiliser les formules de géométrie (surfaces, volumes)": {
                "level": "connaitre",
                "coach_note": "Surfaces de tranchées, volumes de béton. Calculs simples, pas de drill nécessaire.",
                "exam_tip": "Rectangle, triangle, cercle, trapèze. Volume = surface × longueur.",
                "key_points": ["Surfaces simples", "Volumes", "Section de câble (A = π×d²/4)"],
            },
            "Résoudre des équations liées aux réseaux électriques": {
                "level": "maitriser",
                "coach_note": "Résoudre U=R×I pour trouver I, résoudre Δu=... pour trouver la section. Applications concrètes.",
                "exam_tip": "Isoler l'inconnue. Vérifier l'unité du résultat. Arrondir à la section commerciale supérieure.",
                "key_points": ["Isolation de variable", "Vérification dimensionnelle", "Arrondi commercial"],
            },
        },
    },

    # ============ AE01 — Étude de projet ============
    "AE01": {
        "module_coach_profile": "Ingénieur planificateur réseau de distribution",
        "module_focus": "2 questions + poids important dans le travail de projet. Raisonnement technique complet.",
        "competences": {
            "Réaliser une étude de projet de réseau de distribution": {
                "level": "maitriser",
                "coach_note": "C'est le cœur du travail de projet à l'examen. Tu dois savoir structurer une étude complète.",
                "exam_tip": "Analyse des besoins → Variantes → Calculs → Choix → Devis → Planning",
                "key_points": ["Analyse des besoins", "Variantes de solution", "Critères de choix", "Rapport technique"],
            },
            "Dimensionner un réseau (câbles, postes de transformation)": {
                "level": "drill",
                "coach_note": "Choisir la bonne section de câble, le bon transfo. C'est LE calcul que tu feras à l'examen.",
                "exam_tip": "Section câble : Iz ≥ In (avec facteurs) + Δu ≤ limite. Transfo : Sn ≥ P/cosφ × facteur.",
                "key_points": ["Dimensionnement câbles MT/BT", "Choix transformateur", "Calcul de charge", "Facteur de simultanéité"],
            },
            "Calculer les chutes de tension et courants de court-circuit": {
                "level": "drill",
                "coach_note": "ΔU et Icc = les 2 calculs les plus importants de l'examen. DRILL QUOTIDIEN avec des exemples variés.",
                "exam_tip": "Δu(%) = (b × ρ × L × I × cosφ) / (S × Un) × 100. Icc = Un / (√3 × Zcc). FORMULES PAR CŒUR.",
                "key_points": ["Formule Δu mono et tri", "Limites NIBT (3% et 5%)", "Calcul Icc", "Impédance de boucle", "Pouvoir de coupure"],
            },
            "Établir un devis et une planification de projet": {
                "level": "connaitre",
                "coach_note": "Savoir structurer un devis et un planning. Pas de drill mais comprendre la logique.",
                "exam_tip": "Devis : matériel + main d'œuvre + frais généraux + marge. Planning : phases + durées + jalons.",
                "key_points": ["Structure de devis", "Estimation des coûts", "Planning de projet", "Diagramme de Gantt"],
            },
            "Choisir les composants adaptés (câbles, connecteurs, etc.)": {
                "level": "maitriser",
                "coach_note": "Savoir quel câble pour quelle application (XLPE, PVC, MT, BT), quels connecteurs.",
                "exam_tip": "Câbles BT: VKF, TKF. Câbles MT: NA2XS(F)2Y. Connaître les critères de choix.",
                "key_points": ["Types de câbles BT", "Types de câbles MT", "Connecteurs de dérivation", "Terminaisons", "Normes de désignation"],
            },
        },
    },

    # ============ AE02 — Sécurité sur et à prox. d'IE ============
    "AE02": {
        "module_coach_profile": "Chargé de sécurité ESTI / Responsable travaux sous tension",
        "module_focus": "3 QUESTIONS — Module CRITIQUE. La sécurité près d'installations électriques = zéro erreur.",
        "competences": {
            "Appliquer les 5 règles de sécurité": {
                "level": "drill",
                "coach_note": "LES 5 RÈGLES DE SÉCURITÉ DANS L'ORDRE = C'EST LA VIE. Tu dois les réciter en dormant.",
                "exam_tip": "1. Déclencher/sectionner 2. Sécuriser contre réenclenchement 3. Vérifier absence de tension 4. MAT+CC 5. Protéger parties voisines",
                "key_points": ["Les 5 règles dans l'ordre EXACT", "Qui fait quoi (chargé de consignation/travaux)", "Formulaire de consignation", "Déconsignation"],
            },
            "Connaître les distances de sécurité selon les niveaux de tension": {
                "level": "drill",
                "coach_note": "Les distances DL et DV pour chaque niveau de tension = AUTOMATISME. Ça tombe systématiquement.",
                "exam_tip": "BT: DL=0.3m, DV=0.3m | 1-36kV: DL=0.3m, DV=0.6m | 36-110kV: DL=0.6m, DV=1.0m | 110-220kV: DL=1.0m, DV=1.5m",
                "key_points": ["DL (distance limite)", "DV (distance de voisinage)", "Zone de danger", "Zone de voisinage", "Tableau des distances par tension"],
            },
            "Effectuer les consignations et déconsignations": {
                "level": "drill",
                "coach_note": "La procédure complète de consignation dans l'ordre. DRILL avec le formulaire officiel.",
                "exam_tip": "Qui a le droit de consigner ? Le chargé de consignation autorisé. Documenter TOUT.",
                "key_points": ["Procédure de consignation", "Rôles", "Formulaire", "Vérificateur d'absence de tension (VAT)", "Déconsignation inverse"],
            },
            "Appliquer les prescriptions ESTI/Suva pour travaux sur IE": {
                "level": "maitriser",
                "coach_note": "Connaître les 3 catégories de travaux : hors tension, au voisinage, sous tension. Quand quelle méthode.",
                "exam_tip": "Travaux hors tension = LA RÈGLE. Travaux au voisinage = avec mesures. Sous tension = personnel qualifié + procédure spéciale.",
                "key_points": ["Travaux hors tension", "Travaux au voisinage", "Travaux sous tension (TST)", "Ordonnance sur les installations à basse tension (OIBT)", "Ordonnance sur les installations à courant fort (OICF)"],
            },
            "Établir des périmètres de sécurité": {
                "level": "maitriser",
                "coach_note": "Savoir matérialiser les zones de danger et de voisinage sur le terrain.",
                "exam_tip": "Balisage physique (rubans, panneaux). Signalisation des dangers. Contrôle d'accès.",
                "key_points": ["Zone de danger", "Zone de voisinage", "Matérialisation", "Signalisation", "Surveillance"],
            },
            "Gérer les situations d'urgence près d'installations électriques": {
                "level": "maitriser",
                "coach_note": "Que faire si quelqu'un est électrocuté ? Procédure spéciale accident électrique.",
                "exam_tip": "NE PAS TOUCHER avant mise hors tension ! Couper le courant → Éloigner la victime → Alerter 144 → BLS si nécessaire",
                "key_points": ["Accident électrique", "Mise hors tension prioritaire", "Électrisation vs électrocution", "Brûlures électriques", "Protocole d'urgence"],
            },
        },
    },

    # ============ AE03 — Éclairage public ============
    "AE03": {
        "module_coach_profile": "Spécialiste éclairage public et normes SLG",
        "module_focus": "2 questions. Connaître les normes et principes de base de l'éclairage.",
        "competences": {
            "Planifier une installation d'éclairage public": {
                "level": "connaitre",
                "coach_note": "Les étapes de planification d'un éclairage public. Pas de drill mais comprendre la logique.",
                "exam_tip": "Analyse des besoins → Classification voie → Choix luminaire → Implantation → Calcul.",
                "key_points": ["Classification des voies (M, C, P)", "Interdistance", "Hauteur de feu", "Implantation unilatérale/bilatérale"],
            },
            "Appliquer les normes EN 13201 et SLG 202": {
                "level": "maitriser",
                "coach_note": "Les classes d'éclairage et les valeurs limites. C'est le cœur des questions sur ce module.",
                "exam_tip": "EN 13201 = norme européenne (luminance/éclairement). SLG 202 = recommandation suisse. Classes M, C, P.",
                "key_points": ["EN 13201 (classes M, C, P)", "SLG 202", "Luminance (cd/m²)", "Éclairement (lux)", "Uniformité"],
            },
            "Choisir les luminaires et sources (LED)": {
                "level": "connaitre",
                "coach_note": "LED = la norme aujourd'hui. Savoir comparer les luminaires (flux, efficacité, température de couleur).",
                "exam_tip": "LED : efficacité >120 lm/W, durée de vie >50'000h, température 3000-4000K pour routes.",
                "key_points": ["Efficacité lumineuse (lm/W)", "Température de couleur (K)", "Durée de vie", "IRC (indice rendu des couleurs)"],
            },
            "Calculer l'éclairement et l'uniformité": {
                "level": "maitriser",
                "coach_note": "Calcul d'éclairement moyen et uniformité. Questions de calcul simples mais à maîtriser.",
                "exam_tip": "E = Φ × Fu × Fm / (e × l). Uniformité U0 = Emin/Emoy ≥ 0.4 typique.",
                "key_points": ["Formule d'éclairement", "Facteur d'utilisation (Fu)", "Facteur de maintenance (Fm)", "Uniformité U0"],
            },
            "Entretenir et maintenir les installations d'éclairage": {
                "level": "reconnaitre",
                "coach_note": "Savoir que les luminaires doivent être entretenus (nettoyage, remplacement). Pas de drill.",
                "exam_tip": "Maintenance préventive : nettoyage, contrôle câblage, remplacement drivers LED défectueux.",
                "key_points": ["Plan de maintenance EP", "Facteur de maintenance", "Remplacement LED"],
            },
        },
    },

    # ============ AE04 — Documentation de réseaux ============
    "AE04": {
        "module_coach_profile": "Responsable documentation technique et SIG/GIS",
        "module_focus": "1 question. Connaître la symbologie et les systèmes de documentation.",
        "competences": {
            "Lire et créer des schémas unifilaires de réseau": {
                "level": "drill",
                "coach_note": "Les schémas unifilaires = langage de base du métier. Tu dois les lire comme tu lis du texte.",
                "exam_tip": "Transformateur, disjoncteur, sectionneur, fusible, jeu de barres = reconnaître INSTANTANÉMENT.",
                "key_points": ["Symboles normalisés", "Schéma unifilaire BT et MT", "Jeu de barres", "Arrivée/départ"],
            },
            "Utiliser les systèmes d'information géographique (SIG/GIS)": {
                "level": "reconnaitre",
                "coach_note": "Savoir ce qu'est un SIG et à quoi il sert dans la gestion de réseau. Pas de drill.",
                "exam_tip": "SIG = cartographie numérique du réseau. Couches : câbles, postes, raccordements, terrain.",
                "key_points": ["SIG/GIS", "Couches d'information", "Mise à jour des plans"],
            },
            "Documenter les réseaux selon les normes en vigueur": {
                "level": "connaitre",
                "coach_note": "Savoir quels documents sont obligatoires et comment les tenir à jour.",
                "exam_tip": "Plans de réseau, schémas unifilaires, documentation de poste, plans de câbles.",
                "key_points": ["Documentation obligatoire", "Mise à jour", "Archivage", "Accès d'urgence"],
            },
            "Mettre à jour les plans de réseau après intervention": {
                "level": "connaitre",
                "coach_note": "Les plans as-built doivent être mis à jour après CHAQUE intervention. C'est une obligation.",
                "exam_tip": "Relevé terrain → Correction des plans → Validation → Transmission au GRD.",
                "key_points": ["Plans as-built", "Relevé de position", "Transmission au SIG"],
            },
            "Comprendre la symbologie normalisée": {
                "level": "drill",
                "coach_note": "La symbologie des plans = AUTOMATISME. Tu dois reconnaître chaque symbole sans réfléchir.",
                "exam_tip": "Apprends les symboles par thème : protection, commutation, câbles, transformateurs, mise à terre.",
                "key_points": ["Symboles IEC/EN", "Symboles spécifiques réseau", "Légende des plans"],
            },
        },
    },

    # ============ AE05 — Installations de mise à terre ============
    "AE05": {
        "module_coach_profile": "Expert en mise à terre et protection foudre",
        "module_focus": "2 questions. Calculs de résistance de terre et dimensionnement.",
        "competences": {
            "Dimensionner les installations de mise à terre": {
                "level": "maitriser",
                "coach_note": "Savoir dimensionner une prise de terre pour atteindre la résistance cible. Calculs nécessaires.",
                "exam_tip": "RA ≤ 50V / Ia (courant de défaut). Nombre de piquets, longueur, profondeur selon résistivité.",
                "key_points": ["Résistance de terre cible", "Types de prise de terre", "Dimensionnement", "Normes NIBT"],
            },
            "Calculer la résistance de terre": {
                "level": "drill",
                "coach_note": "Formules de résistance de terre = DRILL. RA = ρ/(2πL) pour un piquet. Questions classiques.",
                "exam_tip": "Piquet : RA = ρ/(2πL). Boucle : RA = ρ/(4r). Combinaison piquets parallèles. Facteur de correction.",
                "key_points": ["Formule piquet vertical", "Formule boucle", "Piquets en parallèle", "Influence de la résistivité du sol"],
            },
            "Connaître les types de prises de terre (piquet, ruban, fondation)": {
                "level": "maitriser",
                "coach_note": "Avantages/inconvénients de chaque type et quand les utiliser. Questions QCM + calcul.",
                "exam_tip": "Piquet (facile, profond), Ruban (surface, tranchée), Fondation (béton, nouveau bâtiment), Anneau.",
                "key_points": ["Piquet de terre", "Conducteur en boucle", "Prise de terre de fondation", "Ruban de terre"],
            },
            "Mesurer la résistance de terre et la résistivité du sol": {
                "level": "maitriser",
                "coach_note": "Méthode des 3 piquets (62%) et méthode de Wenner. Savoir interpréter les résultats.",
                "exam_tip": "Méthode 62% : distance piquet auxiliaire = 62% de la distance du piquet de référence.",
                "key_points": ["Méthode des 3 piquets (62%)", "Méthode de Wenner", "Mesureur de terre", "Interprétation des résultats"],
            },
            "Appliquer les normes pour la protection contre la foudre": {
                "level": "connaitre",
                "coach_note": "Connaître les bases de la protection parafoudre. Pas de calcul complexe.",
                "exam_tip": "SPD Type 1 (capteurs foudre), Type 2 (tableau principal), Type 3 (prises). Classe de protection.",
                "key_points": ["SPD Type 1, 2, 3", "Norme SN EN 62305", "Classe de protection", "Zone de protection foudre"],
            },
        },
    },

    # ============ AE06 — Exploitation de réseaux ============
    "AE06": {
        "module_coach_profile": "Dispatcheur réseau de distribution / Chef d'exploitation",
        "module_focus": "2 questions. Comprendre les manœuvres réseau et la gestion des perturbations.",
        "competences": {
            "Comprendre le fonctionnement des réseaux de distribution (MT/BT)": {
                "level": "maitriser",
                "coach_note": "La structure du réseau depuis le poste source jusqu'au client. Fondamental pour tout le module AE.",
                "exam_tip": "HTB (transport) → HTA/MT (distribution) → BT (distribution finale). Niveaux de tension suisses.",
                "key_points": ["Niveaux de tension (BT/MT/HT)", "Poste de transformation MT/BT", "Réseau radial vs bouclé", "Poste source"],
            },
            "Effectuer des manœuvres de réseau (ouverture/fermeture)": {
                "level": "drill",
                "coach_note": "L'ordre des manœuvres est CRITIQUE pour la sécurité. DRILL la séquence exacte.",
                "exam_tip": "Ouverture : charge → sectionneur → vérification. Fermeture : inverse. TOUJOURS sous charge = disjoncteur !",
                "key_points": ["Séquence de manœuvre", "Disjoncteur vs sectionneur", "Manœuvre en charge interdite pour sectionneur", "Verrouillages"],
            },
            "Gérer les perturbations et pannes de réseau": {
                "level": "maitriser",
                "coach_note": "Cas pratiques classiques à l'examen : une panne survient, que fais-tu ? Méthode systématique.",
                "exam_tip": "1. Localiser le défaut 2. Isoler le tronçon 3. Réalimenter les clients 4. Réparer 5. Rétablir la configuration normale",
                "key_points": ["Localisation de défaut", "Réalimentation par contre-alimentation", "Coupure sélective", "Gestion de crise"],
            },
            "Comprendre les schémas d'exploitation (boucle, radial, maillé)": {
                "level": "maitriser",
                "coach_note": "Avantages/inconvénients de chaque topologie. Questions de compréhension + mise en situation.",
                "exam_tip": "Radial = simple, pas de redondance. Bouclé = redondance, réalimentation possible. Maillé = complexe mais fiable.",
                "key_points": ["Réseau radial", "Réseau bouclé (anneau)", "Réseau maillé", "Redondance", "Disponibilité"],
            },
            "Appliquer les procédures d'exploitation sécurisée": {
                "level": "maitriser",
                "coach_note": "Les procédures de manœuvre sécurisée avec communication formelle entre dispatcheur et équipe terrain.",
                "exam_tip": "Communication codifiée : répétition du message, confirmation, identification. JAMAIS de manœuvre sans ordre écrit/verbal confirmé.",
                "key_points": ["Communication opérationnelle", "Ordre de manœuvre", "Confirmation", "Registre des manœuvres"],
            },
        },
    },

    # ============ AE07 — Technique de mesure ============
    "AE07": {
        "module_coach_profile": "Technicien de mesure certifié en installations électriques",
        "module_focus": "2 questions. Savoir faire TOUTES les mesures normatives et interpréter les résultats.",
        "competences": {
            "Effectuer des mesures électriques sur les réseaux": {
                "level": "maitriser",
                "coach_note": "Toutes les mesures du protocole de mise en service. Maîtrise la procédure complète.",
                "exam_tip": "Ordre des mesures : 1. Continuité PE 2. Isolement 3. Boucle de défaut 4. Temps de déclenchement 5. Tension de contact",
                "key_points": ["Protocole de mesure complet", "Ordre des mesures", "Conditions de mesure", "Sécurité pendant les mesures"],
            },
            "Utiliser les appareils de mesure (multimètre, pince, mégohmmètre)": {
                "level": "drill",
                "coach_note": "QUEL appareil pour QUELLE mesure = doit être AUTOMATIQUE. Pas d'hésitation possible.",
                "exam_tip": "Multimètre (U, I, R), Pince (I sans coupure), Mégohmmètre (isolement), Mesureur de boucle (Zs), Mesureur de terre.",
                "key_points": ["Choix de l'appareil", "Raccordement correct", "Précautions", "Vérification de l'appareil avant mesure"],
            },
            "Mesurer l'isolement, la continuité, la boucle de défaut": {
                "level": "drill",
                "coach_note": "Les 3 mesures fondamentales = AUTOMATISME. Valeurs normatives PAR CŒUR.",
                "exam_tip": "Isolement ≥ 1MΩ (500V DC). Continuité PE ≤ 1Ω. Boucle Zs : Ia × Zs ≤ U0 → temps de coupure OK.",
                "key_points": ["Isolement ≥ 1MΩ", "Continuité ≤ 1Ω", "Boucle de défaut Zs", "Tension de mesure isolement (500V DC)", "Valeurs NIBT"],
            },
            "Interpréter les résultats de mesure": {
                "level": "maitriser",
                "coach_note": "Pas juste mesurer, mais COMPRENDRE si c'est OK ou pas. Que faire si la valeur est mauvaise ?",
                "exam_tip": "Valeur hors norme → identifier la cause → corriger → re-mesurer. Toujours documenter.",
                "key_points": ["Valeurs normatives NIBT", "Causes de résultats anormaux", "Actions correctives", "Documentation"],
            },
            "Rédiger des rapports de mesure conformes": {
                "level": "connaitre",
                "coach_note": "Savoir ce qui doit figurer dans un rapport de mesure. Pas de drill.",
                "exam_tip": "Installation, date, appareil utilisé, résultats, conformité, signature.",
                "key_points": ["Formulaire ESTI", "Rapport de sécurité (OIBT)", "Archivage"],
            },
        },
    },

    # ============ AE09 — Technique de protection ============
    "AE09": {
        "module_coach_profile": "Ingénieur protection réseau spécialisé sélectivité et coordination",
        "module_focus": "2 questions. Comprendre la sélectivité et le dimensionnement des protections.",
        "competences": {
            "Comprendre les systèmes de protection des réseaux": {
                "level": "maitriser",
                "coach_note": "La philosophie de la protection : détecter le défaut et couper AU BON ENDROIT. Fondamental.",
                "exam_tip": "Protection = Détection (capteur) + Décision (relais) + Action (disjoncteur). Temps de coupure.",
                "key_points": ["Capteur de courant/tension", "Relais de protection", "Disjoncteur", "Temps de coupure"],
            },
            "Dimensionner les fusibles et disjoncteurs": {
                "level": "drill",
                "coach_note": "Choix de la protection selon le courant et le pouvoir de coupure. Question CLASSIQUE de calcul.",
                "exam_tip": "In ≥ Ib (courant d'emploi). In ≤ Iz (courant admissible câble). PdC ≥ Icc. Courbe B, C, D.",
                "key_points": ["Calibre nominal In", "Pouvoir de coupure", "Courbes de déclenchement (B, C, D)", "Coordination câble/protection", "Fusible HPC/NH"],
            },
            "Comprendre la sélectivité des protections": {
                "level": "drill",
                "coach_note": "La sélectivité = SEUL le disjoncteur le plus proche du défaut déclenche. FONDAMENTAL pour l'examen.",
                "exam_tip": "Sélectivité ampèremétrique (calibres) et chronométrique (temporisation). Vérifier les courbes de déclenchement.",
                "key_points": ["Sélectivité ampèremétrique", "Sélectivité chronométrique", "Sélectivité logique", "Tables de sélectivité constructeur"],
            },
            "Calculer les courants de court-circuit": {
                "level": "drill",
                "coach_note": "Icc = Un / (√3 × Zcc). C'est LE calcul technique le plus demandé à l'examen. DRILL QUOTIDIEN.",
                "exam_tip": "Icc_max (triphasé) et Icc_min (phase-PE). Les deux sont nécessaires pour le dimensionnement.",
                "key_points": ["Icc = Un / (√3 × Zcc)", "Impédance totale (réseau + transfo + câble)", "Icc max et Icc min", "Contribution du réseau amont"],
            },
            "Configurer les relais de protection": {
                "level": "connaitre",
                "coach_note": "Connaître les types de relais et leurs réglages de base. Pas de drill complexe.",
                "exam_tip": "Relais à maximum de courant (50/51), relais terre (50N/51N). Seuils et temporisations.",
                "key_points": ["Protection à maximum de courant", "Protection homopolaire", "Réglages de seuil", "Temporisation"],
            },
            "Comprendre la coordination des protections MT/BT": {
                "level": "maitriser",
                "coach_note": "Comment les protections MT et BT se coordonnent. Le fusible HPC du transfo vs disjoncteur BT.",
                "exam_tip": "Le fusible HPC MT protège le transfo. Le disjoncteur BT protège les départs. Sélectivité entre les deux.",
                "key_points": ["Fusible HPC MT", "Disjoncteur BT", "Coordination MT/BT", "Courbes de fusion/déclenchement"],
            },
        },
    },

    # ============ AE10 — Maintenance des réseaux ============
    "AE10": {
        "module_coach_profile": "Responsable maintenance réseau de distribution",
        "module_focus": "1 question. Planification et diagnostic de défauts sur les réseaux.",
        "competences": {
            "Planifier la maintenance des réseaux de distribution": {
                "level": "connaitre",
                "coach_note": "Fréquences de contrôle types pour les équipements de réseau. Connaissance suffit.",
                "exam_tip": "Postes de transformation : contrôle annuel. Câbles : mesures périodiques. Lignes aériennes : contrôle visuel + grimpeur.",
                "key_points": ["Fréquences de contrôle", "Types d'inspection", "Priorités d'intervention"],
            },
            "Effectuer les contrôles périodiques des installations": {
                "level": "connaitre",
                "coach_note": "Check-lists de contrôle pour les postes de transformation et les réseaux.",
                "exam_tip": "Contrôle visuel, thermographie, mesure d'isolement, vérification protections mécaniques.",
                "key_points": ["Check-list de contrôle", "Thermographie", "Mesure d'isolement", "État des câbles/accessoires"],
            },
            "Diagnostiquer les défauts sur les câbles et lignes": {
                "level": "maitriser",
                "coach_note": "Localiser un défaut de câble = exercice classique. Méthode de diagnostic structurée.",
                "exam_tip": "Types de défauts : court-circuit, rupture, défaut d'isolement. Méthodes : TDR (écho), pont de Murray, injection.",
                "key_points": ["Réflectométrie (TDR)", "Pont de Murray", "Injection de tension", "Types de défauts câbles"],
            },
            "Utiliser les techniques de localisation de défauts": {
                "level": "connaitre",
                "coach_note": "Connaître les méthodes de localisation. Pas besoin de drill mais de compréhension.",
                "exam_tip": "Pré-localisation (TDR, pont) puis localisation précise (détection acoustique ou injection DC).",
                "key_points": ["Pré-localisation", "Localisation acoustique", "Détection de tracé", "Marqueur de défaut"],
            },
            "Organiser les interventions d'urgence sur le réseau": {
                "level": "connaitre",
                "coach_note": "La procédure en cas de panne majeure. Logique et priorités.",
                "exam_tip": "Sécuriser → Évaluer → Réalimenter (boucle) → Réparer → Documenter.",
                "key_points": ["Procédure d'urgence", "Réalimentation par secours", "Communication de crise", "Retour d'expérience"],
            },
        },
    },

    # ============ AE11 — Travail de projet ============
    "AE11": {
        "module_coach_profile": "Directeur de projet en génie électrique réseau",
        "module_focus": "2 questions + TRAVAIL DE PROJET NOTÉ. C'est une des épreuves les plus lourdes de l'examen.",
        "competences": {
            "Réaliser un projet complet de réseau de A à Z": {
                "level": "maitriser",
                "coach_note": "Le travail de projet est une épreuve COMPLÈTE. Tu reçois un cas et tu dois tout traiter. PRÉPARE-TOI avec des cas réels.",
                "exam_tip": "Analyse → Variantes → Calculs → Choix → Plans → Devis → Planning → Rapport. TOUT dans le temps imparti.",
                "key_points": ["Méthodologie de projet", "Structure du rapport", "Gestion du temps à l'examen", "Présentation orale"],
            },
            "Rédiger un dossier technique de projet": {
                "level": "maitriser",
                "coach_note": "Le dossier sera NOTÉ. Structure claire, calculs justes, plans propres, conclusions argumentées.",
                "exam_tip": "Introduction → Analyse situation → Solution technique → Calculs → Plans → Devis → Conclusion",
                "key_points": ["Structure du dossier", "Rédaction technique", "Justification des choix", "Présentation soignée"],
            },
            "Présenter et défendre son projet oralement": {
                "level": "maitriser",
                "coach_note": "La présentation orale est NOTÉE. Prépare-toi à être challengé par les experts.",
                "exam_tip": "Structure en 10 min : intro (1min) → problème (2min) → solution (4min) → conclusion (2min) → questions (1min+)",
                "key_points": ["Présentation structurée", "Défense technique", "Répondre aux questions", "Gestion du temps"],
            },
            "Appliquer la gestion de projet (planning, budget, risques)": {
                "level": "connaitre",
                "coach_note": "Connaître les bases de la gestion de projet appliquée au réseau. Pas de certification PMP nécessaire.",
                "exam_tip": "Planning (Gantt), Budget (estimation paramétrée), Risques (matrice simple).",
                "key_points": ["Diagramme de Gantt", "Estimation des coûts", "Analyse de risques", "Jalons"],
            },
            "Démontrer une approche méthodique et structurée": {
                "level": "maitriser",
                "coach_note": "Les experts évaluent ta MÉTHODE autant que le résultat. Montre que tu es structuré.",
                "exam_tip": "Toujours : 1. Comprendre le problème 2. Analyser les données 3. Proposer des solutions 4. Comparer 5. Choisir et justifier",
                "key_points": ["Méthode de travail", "Justification des choix", "Esprit critique", "Documentation"],
            },
        },
    },

    # ============ AE12 — Lignes souterraines ============
    "AE12": {
        "module_coach_profile": "Chef de chantier câbles souterrains MT/BT",
        "module_focus": "2 questions. Câbles souterrains = le quotidien d'un électricien de réseau.",
        "competences": {
            "Choisir et dimensionner les câbles souterrains": {
                "level": "drill",
                "coach_note": "Section + type de câble = question CLASSIQUE. Drill les tableaux de courant admissible.",
                "exam_tip": "Iz ≥ In (avec facteurs correction : température, groupement, sol). Δu vérifié. PdC suffisant.",
                "key_points": ["Types de câbles (XLPE, PVC)", "Courant admissible Iz", "Facteurs de correction", "Désignation normalisée"],
            },
            "Connaître les techniques de pose (tranchée, forage dirigé, etc.)": {
                "level": "maitriser",
                "coach_note": "Profondeurs, distances de croisement, lit de pose = connaissances PRATIQUES essentielles.",
                "exam_tip": "Profondeur BT: 0.6m, MT: 0.8m (minimum). Croisement câble/eau : 0.2m. Sable fin autour.",
                "key_points": ["Profondeur de pose", "Lit de pose (sable)", "Grillage avertisseur", "Distances de croisement", "Forage dirigé"],
            },
            "Réaliser et contrôler les jonctions et terminaisons": {
                "level": "maitriser",
                "coach_note": "Les jonctions et terminaisons sont critiques pour la fiabilité. Questions pratiques fréquentes.",
                "exam_tip": "Jonction droite, dérivation en T, terminaison intérieure/extérieure. Contrôle : isolement + manteau.",
                "key_points": ["Types de jonctions", "Terminaisons", "Préparation de câble", "Contrôle après pose"],
            },
            "Appliquer les normes de pose et de croisement": {
                "level": "drill",
                "coach_note": "Les distances de croisement et de voisinage = AUTOMATISME. Tableau à connaître par cœur.",
                "exam_tip": "Câble/câble parallèle : 0.2m. Câble/conduite gaz : 0.2m. Câble/conduite eau : 0.2m.",
                "key_points": ["Distances de croisement normalisées", "Distances de voisinage", "Marquage des câbles", "Plan de pose"],
            },
            "Effectuer les essais après pose (isolement, manteau)": {
                "level": "maitriser",
                "coach_note": "Après pose d'un câble MT : essais OBLIGATOIRES avant mise en service. Savoir lesquels et les valeurs.",
                "exam_tip": "Essai d'isolement (mégohmmètre), essai de manteau (2.5kV DC), vérification de continuité.",
                "key_points": ["Essai d'isolement", "Essai de manteau", "Tension d'essai", "PV de mesure", "Mise en service"],
            },
        },
    },

    # ============ AE13 — Lignes aériennes ============
    "AE13": {
        "module_coach_profile": "Spécialiste lignes aériennes et travaux en hauteur",
        "module_focus": "1 question. Dimensionnement basique et types de supports.",
        "competences": {
            "Dimensionner les lignes aériennes (conducteurs, supports)": {
                "level": "maitriser",
                "coach_note": "Savoir choisir le conducteur et dimensionner les portées. Calculs mécaniques simples.",
                "exam_tip": "Section selon courant + résistance mécanique. Charge permanente + vent + givre.",
                "key_points": ["Choix du conducteur", "Section mécanique vs électrique", "Charges climatiques"],
            },
            "Calculer les portées et flèches": {
                "level": "maitriser",
                "coach_note": "La formule de la flèche est un classique de calcul. Pas quotidien mais à maîtriser.",
                "exam_tip": "f = (w × a²) / (8 × T). flèche = poids/m × portée² / (8 × tension mécanique).",
                "key_points": ["Formule de la flèche", "Portée maximale", "Gabarit au sol", "Température de référence"],
            },
            "Connaître les types de supports (bois, béton, acier)": {
                "level": "connaitre",
                "coach_note": "Avantages/inconvénients de chaque type de support. QCM simple.",
                "exam_tip": "Bois : léger, isolant, durée limitée. Béton : durable, lourd. Acier : résistant, fondation nécessaire.",
                "key_points": ["Supports bois", "Supports béton", "Pylônes acier", "Durée de vie", "Fondations"],
            },
            "Appliquer les règles de croisement et voisinage": {
                "level": "connaitre",
                "coach_note": "Distances minimales entre ligne aérienne et bâtiments, routes, autres lignes.",
                "exam_tip": "Gabarit au sol minimum, distances aux bâtiments, croisements avec autres lignes/routes.",
                "key_points": ["Gabarit au sol", "Distances de voisinage", "Croisements", "Zone de servitude"],
            },
            "Effectuer la maintenance des lignes aériennes": {
                "level": "reconnaitre",
                "coach_note": "Savoir que les lignes aériennes nécessitent un contrôle visuel régulier + élagage.",
                "exam_tip": "Contrôle visuel, contrôle par grimpeur, élagage, remplacement isolateurs/conducteurs défectueux.",
                "key_points": ["Inspection visuelle", "Contrôle par grimpeur", "Élagage", "Remplacement composants"],
            },
        },
    },
}


# ============================================================
# PROFILS DE COACHING IA PAR DOMAINE
# ============================================================
MODULE_COACH_PROMPTS = {
    "AA01-AA04": {
        "role": "Chef de chantier et responsable de projet expérimenté",
        "expertise": "Management d'équipe, planification de chantier, gestion de mandat",
        "tone": "Direct et pragmatique. Tu donnes des conseils issus de 20 ans de terrain.",
        "focus": "Mises en situation professionnelles, cas concrets, bon sens du chef d'équipe",
    },
    "AA05-AE02": {
        "role": "Responsable sécurité certifié MSST et chargé de sécurité ESTI",
        "expertise": "Sécurité au travail, consignations, accidents électriques, règlementation SUVA/ESTI",
        "tone": "STRICT et sans compromis. La sécurité n'est JAMAIS négociable. Tu insistes sur les automatismes.",
        "focus": "Règles de sécurité vitales, procédures de consignation, premiers secours, EPI",
    },
    "AA09-AA11": {
        "role": "Professeur d'électrotechnique et mathématiques appliquées au réseau",
        "expertise": "Lois fondamentales, calcul AC/DC, trigonométrie, dimensionnement",
        "tone": "Pédagogue et méthodique. Tu décomposes chaque calcul étape par étape et tu vérifies la compréhension.",
        "focus": "Formules, méthodes de calcul, vérification des unités, exercices progressifs",
    },
    "AE01-AE05": {
        "role": "Ingénieur planificateur réseau de distribution et expert mise à terre",
        "expertise": "Étude de projet, dimensionnement réseau, câbles MT/BT, installation de mise à terre",
        "tone": "Technique et structuré. Tu guides l'étudiant comme un ingénieur mentor.",
        "focus": "Dimensionnement, calculs de chute de tension et Icc, choix de composants, normes",
    },
    "AE06-AE07": {
        "role": "Dispatcheur réseau et technicien de mesure certifié",
        "expertise": "Exploitation réseau, manœuvres MT/BT, mesures électriques, diagnostic",
        "tone": "Opérationnel et concret. Tu parles comme un collègue expérimenté en salle de commande.",
        "focus": "Procédures de manœuvre, protocoles de mesure, valeurs normatives, diagnostic de pannes",
    },
    "AE09": {
        "role": "Ingénieur protection réseau senior",
        "expertise": "Sélectivité, coordination des protections, dimensionnement fusibles/disjoncteurs",
        "tone": "Analytique et rigoureux. Tu aimes les courbes de déclenchement et les calculs d'Icc.",
        "focus": "Sélectivité, pouvoir de coupure, coordination MT/BT, calculs de court-circuit",
    },
    "AE10-AE13": {
        "role": "Chef de chantier terrain spécialisé câbles souterrains et lignes aériennes",
        "expertise": "Pose de câbles, jonctions, essais, lignes aériennes, maintenance des réseaux",
        "tone": "Pratique et terrain. Tu sens l'huile et la terre. Tes conseils viennent de l'expérience.",
        "focus": "Techniques de pose, essais après pose, normes de croisement, maintenance, défauts courants",
    },
}


def get_coach_for_module(module: str) -> Dict:
    """Retourne le profil de coach adapté à un module"""
    for key, profile in MODULE_COACH_PROMPTS.items():
        parts = key.split("-")
        if len(parts) == 2:
            start, end = parts
            # Extraire le préfixe et le numéro
            if module >= start and module <= end:
                return profile
        elif module == key or module.startswith(key):
            return profile
    # Fallback
    return MODULE_COACH_PROMPTS.get("AA09-AA11", {})


def get_competence_mastery_info(module: str, competence: str) -> Dict:
    """Retourne le niveau de maîtrise requis et les infos de coaching pour une compétence"""
    module_data = COMPETENCE_MASTERY.get(module, {})
    comp_data = module_data.get("competences", {}).get(competence, {})
    if not comp_data:
        return {
            "level": "connaitre",
            "coach_note": "Pas d'information spécifique. Étudie avec les flashcards.",
            "exam_tip": "",
            "key_points": [],
        }
    return comp_data


def get_module_mastery_summary(module: str) -> Dict:
    """Résumé des niveaux de maîtrise pour un module entier"""
    module_data = COMPETENCE_MASTERY.get(module, {})
    if not module_data:
        return {}

    competences = module_data.get("competences", {})
    counts = defaultdict(int)
    by_level = defaultdict(list)

    for comp, info in competences.items():
        level = info.get("level", "connaitre")
        counts[level] += 1
        by_level[level].append({
            "competence": comp,
            "coach_note": info.get("coach_note", ""),
            "exam_tip": info.get("exam_tip", ""),
            "key_points": info.get("key_points", []),
        })

    total = sum(counts.values())
    return {
        "module": module,
        "coach_profile": module_data.get("module_coach_profile", ""),
        "module_focus": module_data.get("module_focus", ""),
        "total_competences": total,
        "counts": dict(counts),
        "by_level": dict(by_level),
        "drill_pct": counts.get("drill", 0) / total * 100 if total > 0 else 0,
    }


def get_all_drill_items() -> List[Dict]:
    """Retourne TOUTES les compétences de niveau DRILL triées par poids d'examen"""
    from src.exam_focus import EXAM_WEIGHT
    drills = []
    for module, mod_data in COMPETENCE_MASTERY.items():
        weight = EXAM_WEIGHT.get(module, 1)
        for comp, info in mod_data.get("competences", {}).items():
            if info.get("level") == "drill":
                drills.append({
                    "module": module,
                    "competence": comp,
                    "exam_weight": weight,
                    "coach_note": info.get("coach_note", ""),
                    "exam_tip": info.get("exam_tip", ""),
                    "key_points": info.get("key_points", []),
                })
    drills.sort(key=lambda x: x["exam_weight"], reverse=True)
    return drills


def get_global_mastery_stats() -> Dict:
    """Statistiques globales des niveaux de maîtrise"""
    from src.exam_focus import EXAM_WEIGHT
    counts = defaultdict(int)
    total = 0
    by_module = {}

    for module, mod_data in COMPETENCE_MASTERY.items():
        mod_counts = defaultdict(int)
        for comp, info in mod_data.get("competences", {}).items():
            level = info.get("level", "connaitre")
            counts[level] += 1
            mod_counts[level] += 1
            total += 1
        by_module[module] = dict(mod_counts)

    return {
        "total": total,
        "counts": dict(counts),
        "by_module": by_module,
        "drill_total": counts.get("drill", 0),
        "drill_pct": counts.get("drill", 0) / total * 100 if total > 0 else 0,
        "maitriser_total": counts.get("maitriser", 0),
        "connaitre_total": counts.get("connaitre", 0),
        "reconnaitre_total": counts.get("reconnaitre", 0),
    }


def build_expert_coach_prompt(module: str, concept_name: str, 
                               user_question: str = "",
                               mastery_data: Dict = None) -> str:
    """
    Construit un prompt pour que l'IA agisse comme un VRAI coach expert
    spécialisé dans le domaine du module.
    """
    coach = get_coach_for_module(module)
    module_data = COMPETENCE_MASTERY.get(module, {})
    module_focus = module_data.get("module_focus", "")
    
    # Trouver les informations sur les compétences liées au concept
    relevant_comps = []
    for comp, info in module_data.get("competences", {}).items():
        if any(kw.lower() in concept_name.lower() for kw in comp.lower().split()[:3]):
            relevant_comps.append({
                "competence": comp,
                "level": info.get("level", "connaitre"),
                "coach_note": info.get("coach_note", ""),
                "exam_tip": info.get("exam_tip", ""),
                "key_points": info.get("key_points", []),
            })

    comp_context = ""
    if relevant_comps:
        comp_context = "\n\nCOMPÉTENCES LIÉES à ce concept :\n"
        for rc in relevant_comps:
            level_info = MASTERY_LEVELS.get(rc["level"], {})
            comp_context += f"\n• {rc['competence']}\n"
            comp_context += f"  Niveau requis : {level_info.get('icon', '')} {level_info.get('label', '')}\n"
            comp_context += f"  Mon conseil : {rc['coach_note']}\n"
            comp_context += f"  Astuce examen : {rc['exam_tip']}\n"
            if rc['key_points']:
                comp_context += f"  Points clés : {', '.join(rc['key_points'])}\n"

    prompt = f"""Tu es {coach.get('role', 'un expert technique')}.

TON EXPERTISE : {coach.get('expertise', '')}
TON STYLE : {coach.get('tone', '')}
TON FOCUS : {coach.get('focus', '')}

CONTEXTE DU MODULE : {module_focus}

Tu coaches Gabriel qui prépare le Brevet Fédéral de Spécialiste de Réseau (électricien de réseau) en Suisse.
Examen en mars 2027 au CIFER Penthalaz.

CONCEPT DISCUTÉ : {concept_name} (Module {module})
{comp_context}

{'QUESTION DE GABRIEL : ' + user_question if user_question else ''}

RÈGLES DE COACHING :
1. Parle comme un VRAI expert de terrain, pas comme un manuel
2. Sois DIRECT : dis clairement « ça tu DOIS le driller » ou « ça c'est du nice-to-know »
3. Donne des astuces CONCRÈTES d'examen (ce qui tombe souvent, les pièges classiques)
4. Si c'est du DRILL : insiste, donne des mnémotechniques, des façons de mémoriser
5. Si c'est juste du RECONNAÎTRE : dis-le clairement « perds pas de temps dessus, juste savoir que ça existe »
6. Toujours contextualiser pour la Suisse (NIBT, ESTI, Suva, normes CH)
7. Maximum 300 mots — sois percutant, pas verbeux

Réponds en JSON :
```json
{{
    "verdict": "<DRILL|MAÎTRISER|CONNAÎTRE|RECONNAÎTRE>",
    "message": "<ton coaching direct et percutant>",
    "must_know": ["<ce qu'il FAUT savoir par cœur>"],
    "nice_to_know": ["<ce qui est bien à savoir mais pas critique>"],
    "skip": ["<ce qu'il peut ignorer pour l'examen>"],
    "drill_exercise": "<un exercice concret de 2 min qu'il peut faire tout de suite>",
    "exam_trap": "<le piège classique de l'examen sur ce sujet>",
    "mnemonic": "<un truc mnémotechnique pour retenir l'essentiel>"
}}
```"""
    return prompt
