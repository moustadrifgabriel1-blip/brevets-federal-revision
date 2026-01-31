# 🎓 Système de Révision Intelligent - Brevet Fédéral

Application web intelligente pour réviser efficacement le **Brevet Fédéral d'Électricien de Réseaux** (Suisse).

## ✨ Fonctionnalités

- 📚 **Import automatique** de vos cours (PDF, Word, dossiers)
- 🤖 **Analyse IA** avec Google Gemini (extraction de concepts, dépendances)
- 📅 **Planning de cours** synchronisé (109 sessions, oct 2025 - jan 2027)
- 📆 **Planning de révision** personnalisé avec répétition espacée
- 🗺️ **Carte conceptuelle** interactive
- ⏰ **Gestion du temps** (30 min/jour + 8h weekends)
- 📊 **Suivi de progression** en temps réel

## 🚀 Utilisation

### En ligne (recommandé pour mobile)
Accédez à l'application depuis n'importe quel appareil :
👉 **[Votre URL Streamlit Cloud]**

### En local
```bash
pip install -r requirements.txt
streamlit run app.py
```

## 📋 Configuration

L'application nécessite une clé API Google Gemini (gratuite) :
1. Obtenez votre clé sur https://makersuite.google.com/app/apikey
2. Ajoutez-la dans les secrets Streamlit ou `.streamlit/secrets.toml`

## 🎯 Calendrier Brevet Fédéral 2025-2027

- **Début** : 7 octobre 2025
- **Fin** : 21 janvier 2027
- **Examen** : 22-26 mars 2027
- **Sessions** : 109 (21 en 2025, 81 en 2026, 7 en 2027)

## 🛠️ Technologies

- Python 3.9+
- Streamlit (interface web)
- Google Gemini AI (analyse de contenu)
- Pandas (gestion de données)
- NetworkX (graphes de concepts)

## 📱 Mobile-Friendly

Interface responsive optimisée pour smartphone et tablette.

## 📄 Licence

Utilisation personnelle - Brevet Fédéral Suisse 2025-2027
