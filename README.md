# 🎓 Système de Révision Intelligent - Brevet Fédéral Spécialiste Réseaux Énergétiques

## 📋 Description

Ce système vous aide à :
- **Organiser** vos cours et directives d'examen
- **Analyser** automatiquement le contenu avec l'IA
- **Identifier** les concepts clés et leurs prérequis
- **Générer** un planning de révision optimisé
- **Cibler** uniquement ce qui est essentiel pour vos examens

## 📁 Structure du Projet

```
Brevets federal/
├── cours/                      # Vos fichiers de cours (PDF, Word, etc.)
│   ├── module_1/
│   ├── module_2/
│   └── ...
├── directives_examen/          # Directives officielles d'examen
├── planning_cours/             # Votre planning de cours actuel
├── exports/                    # Plannings de révision générés
├── src/                        # Code source du système
│   ├── scanner.py              # Scanner de documents
│   ├── analyzer.py             # Analyseur IA des contenus
│   ├── planner.py              # Générateur de planning
│   ├── concept_mapper.py       # Cartographie des concepts
│   └── main.py                 # Point d'entrée principal
├── config/
│   └── config.yaml             # Configuration du système
├── requirements.txt            # Dépendances Python
└── README.md
```

## 🚀 Installation

```bash
# 1. Créer un environnement virtuel
python3 -m venv venv
source venv/bin/activate

# 2. Installer les dépendances
pip install -r requirements.txt

# 3. Configurer votre clé API OpenAI dans config/config.yaml
```

## 📖 Utilisation

```bash
# Lancer le système
python src/main.py

# Ou utiliser des commandes spécifiques
python src/main.py --scan           # Scanner les cours
python src/main.py --analyze        # Analyser avec l'IA
python src/main.py --plan           # Générer le planning
```

## 📌 Workflow

1. **Ajoutez vos cours** dans le dossier `cours/`
2. **Ajoutez les directives d'examen** dans `directives_examen/`
3. **Configurez votre planning** dans `planning_cours/`
4. **Lancez l'analyse** - Le système va :
   - Scanner tous vos documents
   - Extraire les concepts clés
   - Identifier ce qui est demandé aux examens
   - Créer les liens entre cours et exigences
   - Générer votre planning de révision personnalisé

## 💡 Fonctionnalités Clés

- **Mapping Directives ↔ Cours** : Le système identifie exactement quels chapitres couvrent quelles exigences
- **Détection des Prérequis** : "Tu dois savoir X pour comprendre Y"
- **Élimination du Bruit** : Focus uniquement sur ce qui sera évalué
- **Planning Adaptatif** : Respecte votre calendrier de cours réel
