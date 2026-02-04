# 🔐 Sécurité des Clés API

## ⚠️ Problème Actuel

La clé API Gemini a été exposée dans l'historique Git (commit `b6ab8b4`).
Google détecte automatiquement les clés exposées sur GitHub et les désactive.

## ✅ Solution Mise en Place

### 1. Stockage Local (développement)

La clé API est stockée dans `.env` (jamais commitée) :
```bash
GOOGLE_API_KEY=votre_nouvelle_clé_ici
```

### 2. Stockage Cloud (Streamlit Cloud)

La clé est dans les secrets Streamlit :
- Aller sur [Streamlit Cloud](https://share.streamlit.io)
- Settings → Secrets
- Ajouter :
```toml
GOOGLE_API_KEY = "votre_nouvelle_clé_ici"
```

### 3. Fichiers Ignorés par Git

`.gitignore` contient :
```
.env
.streamlit/secrets.toml
*.pem
*.key
```

## 🔄 Pour Créer une Nouvelle Clé

1. **Révoquer l'ancienne clé** (si pas déjà fait par Google) :
   - Aller sur [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
   - Supprimer la clé compromise

2. **Créer une nouvelle clé** :
   - Aller sur [AI Studio](https://aistudio.google.com/app/apikey)
   - Cliquer "Create API Key"
   - Copier la clé

3. **Mettre à jour localement** :
   ```bash
   echo 'GOOGLE_API_KEY=votre_nouvelle_clé' > .env
   ```

4. **Mettre à jour sur Streamlit Cloud** :
   - Settings → Secrets → Modifier

## 🛡️ Bonnes Pratiques

| ✅ Faire | ❌ Ne Pas Faire |
|----------|----------------|
| Stocker dans `.env` | Mettre dans le code |
| Stocker dans Streamlit Secrets | Mettre dans `config.yaml` |
| Vérifier `.gitignore` avant commit | Commiter sans vérifier |
| Utiliser `os.getenv()` | Hardcoder la clé |

## 🔍 Vérification

Avant chaque commit, vérifier qu'aucune clé n'est exposée :
```bash
# Chercher des clés API dans les fichiers
grep -r "AIzaSy" --include="*.py" --include="*.yaml" .

# Vérifier le statut Git
git status
git diff --cached
```

## 📊 Historique de l'Incident

| Date | Événement |
|------|-----------|
| 31/01/2026 | Clé exposée dans config.yaml (commit initial) |
| 31/01/2026 | Clé retirée, .env créé |
| 01/02/2026 | Clé bloquée par Google (détection automatique) |
| 01/02/2026 | Documentation sécurité créée |

## 🧹 Nettoyage de l'Historique (Optionnel)

Si vous voulez supprimer la clé de l'historique Git (attention, cela réécrit l'historique) :

```bash
# Installer BFG Repo-Cleaner
brew install bfg

# Créer un fichier avec les secrets à supprimer
echo "AIzaSyAAYGSAwWt5E7YTH_ywxhMxIdqKYTUNY5M" > secrets.txt

# Nettoyer l'historique
bfg --replace-text secrets.txt

# Force push (attention!)
git reflog expire --expire=now --all
git gc --prune=now --aggressive
git push --force
```

⚠️ **Note** : Le force push peut causer des problèmes si d'autres personnes travaillent sur le repo.
