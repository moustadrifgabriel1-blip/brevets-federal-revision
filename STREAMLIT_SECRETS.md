# Configuration des Secrets Streamlit Cloud

## 📝 Instructions pour ajouter la clé API

1. **Aller sur Streamlit Cloud**  
   https://share.streamlit.io/

2. **Ouvrir ton app**  
   brevets-federal-revision

3. **Cliquer sur les 3 points** (⋮) en haut à droite → **Settings**

4. **Aller dans "Secrets"**

5. **Copier/coller ce contenu** :
```toml
[api]
GOOGLE_API_KEY = "AIzaSyCxQzaZUdJV4Z_mbn6FBGyKz-JbgFSk87A"
```

6. **Cliquer sur "Save"**

7. **Redémarrer l'app** : Les modifications prendront effet après redémarrage

## ✅ Vérification

Une fois fait :
- L'app locale utilise `.env` (déjà configuré ✅)
- L'app cloud utilise `secrets.toml` (à configurer sur Streamlit Cloud)
- L'ancienne clé compromise a été retirée du code ✅
- La nouvelle clé n'est jamais committée sur GitHub ✅

## 🔐 Sécurité

- `.env` est dans `.gitignore` → jamais sur GitHub
- `secrets.toml` n'existe que localement dans `.streamlit/` → jamais sur GitHub  
- La clé sur Streamlit Cloud est stockée de manière sécurisée
