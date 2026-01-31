## 🚀 Déploiement sur Streamlit Cloud

### 1. Créer un compte GitHub (si vous n'en avez pas)
- Allez sur https://github.com
- Créez un compte gratuit

### 2. Créer un nouveau repository
```bash
# Dans le terminal, initialiser Git
cd "/Users/gabrielmoustadrif/development/Brevets federal"
git init
git add .
git commit -m "Initial commit - Système révision Brevet Fédéral"

# Créer un repository sur GitHub puis :
git remote add origin https://github.com/VOTRE_USERNAME/brevets-federal.git
git branch -M main
git push -u origin main
```

### 3. Déployer sur Streamlit Cloud
1. Allez sur https://share.streamlit.io
2. Connectez-vous avec votre compte GitHub
3. Cliquez sur "New app"
4. Sélectionnez votre repository `brevets-federal`
5. Fichier principal : `app.py`
6. Cliquez sur "Deploy"

### 4. Configurer les secrets (API Gemini)
Dans Streamlit Cloud :
1. Allez dans "Settings" → "Secrets"
2. Ajoutez :
```toml
[general]
GOOGLE_API_KEY = "AIzaSyAAYGSAwWt5E7YTH_ywxhMxIdqKYTUNY5M"
```

### 5. URL de l'application
Vous obtiendrez une URL comme :
`https://votre-app.streamlit.app`

Accessible depuis n'importe quel appareil ! 📱💻

### ⚠️ Important
- Les données (cours, planning) devront être réimportées sur la version en ligne
- L'application sera publique (sauf si vous payez pour un compte privé)
- Limites gratuites : 1 Go de stockage, ressources partagées

### 🔒 Sécurité
Pour rendre l'app privée (optionnel), vous pouvez ajouter un mot de passe dans le code.
