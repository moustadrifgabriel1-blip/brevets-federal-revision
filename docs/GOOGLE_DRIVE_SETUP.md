# ☁️ Configuration Google Drive pour Streamlit Cloud

## 🎯 Objectif
Permettre à l'app Streamlit Cloud d'accéder aux fichiers de cours stockés sur ton Google Drive.

---

## 📋 Étapes de configuration

### 1. Créer un projet Google Cloud (gratuit)

1. Va sur https://console.cloud.google.com/
2. Connecte-toi avec **moustadrifgabriel1@gmail.com**
3. Clique sur **"Créer un projet"**
   - Nom : `brevets-federal-app`
4. Sélectionne le projet créé

### 2. Activer l'API Google Drive

1. Dans le menu, va dans **APIs & Services → Bibliothèque**
2. Cherche **"Google Drive API"**
3. Clique sur **Activer**

### 3. Créer un compte de service

1. Va dans **APIs & Services → Identifiants**
2. Clique **+ Créer des identifiants → Compte de service**
3. Nom : `streamlit-drive-access`
4. Clique **Créer et continuer** → **OK**
5. Clique sur le compte de service créé
6. Onglet **Clés** → **Ajouter une clé → Créer une clé → JSON**
7. **Télécharge le fichier JSON** (garde-le précieusement !)

### 4. Partager le dossier Drive avec le compte de service

1. Ouvre le fichier JSON téléchargé
2. Copie l'email du compte de service : `streamlit-drive-access@brevets-federal-app.iam.gserviceaccount.com`
3. Va sur **Google Drive** (drive.google.com)
4. Trouve le dossier **Brevets_Federal_Backup**
5. Clic droit → **Partager**
6. Colle l'email du compte de service
7. Donne l'accès **Lecteur**

### 5. Configurer Streamlit Cloud

1. Va sur https://share.streamlit.io
2. Ouvre les **Settings** de ton app
3. Va dans **Secrets**
4. Colle le contenu suivant :

```toml
[api]
GOOGLE_API_KEY = "ta_clé_gemini"

[gcp_service_account]
type = "service_account"
project_id = "brevets-federal-app"
private_key_id = "..."
private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
client_email = "streamlit-drive-access@brevets-federal-app.iam.gserviceaccount.com"
client_id = "..."
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "..."
```

> ⚠️ Remplace les `...` par les valeurs du fichier JSON téléchargé

### 6. Redéployer l'app

L'app va automatiquement se redéployer avec l'accès Google Drive !

---

## ✅ Vérification

Une fois configuré, tu verras dans l'app :
- ✅ **"Connecté à Google Drive"** si tout fonctionne
- Les fichiers de cours seront chargés depuis Drive

---

## 💰 Coût

**Gratuit !** Google Cloud offre :
- API Google Drive : gratuit jusqu'à 1 milliard de requêtes/jour
- Pas de carte bancaire requise pour ce niveau d'utilisation

---

## 🔒 Sécurité

- Le compte de service n'a accès qu'en **lecture seule**
- Il n'a accès qu'au dossier **Brevets_Federal_Backup** que tu as partagé
- Les credentials sont stockés de façon sécurisée dans Streamlit Secrets
