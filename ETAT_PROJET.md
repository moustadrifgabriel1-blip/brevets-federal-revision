# 📊 État du Projet - Système de Révision Brevet Fédéral

> **Dernière mise à jour :** 1 février 2026

---

## 🌐 Liens Importants

| Ressource | URL |
|-----------|-----|
| **🚀 App en production** | https://brevets-federal-revision-wa6ryvzs5fvwhtevepwhhz.streamlit.app/ |
| **📦 Repository GitHub** | https://github.com/moustadrifgabriel1-blip/brevets-federal-revision |
| **💻 App locale** | http://localhost:8501 |

---

## ✅ Fonctionnalités Opérationnelles

- [x] **Page d'accueil** - Tableau de bord avec compte à rebours examen
- [x] **Gestion documents** - Upload ZIP et fichiers individuels
- [x] **Planning cours** - Visualisation du calendrier de formation
- [x] **Analyse IA** - Analyse des contenus avec Google Gemini
- [x] **Cartographie concepts** - Visualisation des liens entre concepts
- [x] **Planning révisions** - Planning personnalisé généré
- [x] **Ressources** - Documentation et guides
- [x] **Paramètres** - Configuration utilisateur

---

## 📈 Statistiques Actuelles

| Métrique | Valeur |
|----------|--------|
| Heures totales de révision | 182.5h |
| Concepts identifiés | 503 |
| Sessions planifiées | 65 |
| Jours restants avant examen | 392 |
| Date d'examen | Mars 2027 |

---

## 🐛 Bugs Corrigés

### 1 février 2026
- ✅ **Fix `px.bar()` categories** - Le dictionnaire `categories` était traité comme une liste. Correction : comptage du nombre de concepts par catégorie avec `len(concepts)`.

---

## 🔧 Stack Technique

- **Frontend** : Streamlit
- **IA** : Google Gemini (langchain-google-genai)
- **Visualisation** : Plotly, Matplotlib, NetworkX
- **Données** : JSON, Pandas
- **Déploiement** : Streamlit Cloud

---

## 📁 Structure du Projet

```
Brevets federal/
├── app.py                 # Application principale
├── config/
│   └── config.yaml        # Configuration utilisateur
├── cours/                 # Fichiers de cours par module (AA01-AE13)
├── data/
│   ├── database.json      # Base de données locale
│   └── course_schedule.json
├── exports/
│   ├── concept_map.json   # Cartographie des concepts
│   └── revision_plan.json # Planning de révision généré
├── directives_examen/     # Directives d'examen officielles
├── scripts/               # Scripts utilitaires
└── src/                   # Code source additionnel
```

---

## 📝 TODO / Prochaines étapes

- [ ] Ajouter système de flashcards interactives
- [ ] Implémenter quiz auto-générés par l'IA
- [ ] Tracker de progression avec graphiques
- [ ] Notifications de rappel de révision
- [ ] Mode hors-ligne (PWA)
- [ ] Export PDF du planning

---

## 🔐 Configuration Secrets (Streamlit Cloud)

```toml
[api]
GOOGLE_API_KEY = "votre_clé_gemini"
```

---

## 📱 Accès

L'application est accessible depuis :
- 💻 Ordinateur
- 📱 Téléphone
- 📲 Tablette

**URL publique :** https://brevets-federal-revision-wa6ryvzs5fvwhtevepwhhz.streamlit.app/
