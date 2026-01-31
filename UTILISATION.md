# 📖 Guide d'Utilisation - Système de Révision

## 🎯 Vue d'ensemble

Votre système est maintenant synchronisé et prêt à analyser vos modules importés !

## ✅ Ce qui a été configuré

### Modules importés
- ✅ Modules **avec cours** : Seront analysés par l'IA
- 🔴 Modules **sans cours** : Ignorés automatiquement (en attente)

### Temps de révision
- **30 min/jour** en semaine (lundi-vendredi)
- **8h le week-end** (samedi + dimanche)
- = **10.5h par semaine** / **45h par mois**

## 🚀 Prochaines étapes

### 1. Vérifier l'import ✅ FAIT
Vous avez déjà importé vos dossiers ! Le système a détecté automatiquement :
- Quels modules ont du contenu
- Quels modules sont vides
- La structure complète

### 2. Lancer l'analyse 🔬 À FAIRE
1. Allez dans l'onglet **🔬 Analyser**
2. Vérifiez la liste des modules qui seront analysés
3. Cliquez sur **🚀 Lancer l'analyse complète**
4. Attendez quelques minutes (l'IA analyse chaque document)

**Ce qui va se passer :**
- Le scanner va lire tous les PDF/Word de vos modules avec contenu
- L'IA va extraire les concepts clés de chaque document
- Le système va identifier les prérequis et dépendances
- Une cartographie complète sera créée

### 3. Explorer les concepts 🗺️
Une fois l'analyse terminée :
1. Allez dans **🗺️ Concepts**
2. Filtrez par :
   - Module (AA01, AE03, etc.)
   - Importance (critique, haute, moyenne)
   - Lien avec l'examen
3. Explorez les dépendances entre concepts

### 4. Générer votre planning 📅
1. Allez dans **📅 Planning**
2. Configurez vos dates (examen, disponibilités)
3. Générez le planning personnalisé
4. Suivez vos sessions quotidiennes

### 5. Utiliser les ressources 📖
Pendant vos révisions :
- **Guide complet** : Méthodologie, statistiques, conseils
- **Flashcards** : Mode quiz interactif
- **Formules** : Toutes les formules essentielles

## 🎓 Synchronisation avec vos modules

### Comment ça marche ?

Le système lit votre `config.yaml` qui contient maintenant :

```yaml
modules:
  AA01:
    name: "Conduite de collaborateurs"
    has_content: true  # ← Sera analysé
  AA06:
    name: "Suivi des travaux"
    has_content: false  # ← Ignoré
  ...
```

### Lors de l'analyse

1. **Scanner** : Lit uniquement les dossiers des modules avec `has_content: true`
2. **Analyzer** : Extrait les concepts de chaque document
3. **Mapper** : Crée les liens entre concepts en tenant compte du module d'origine
4. **Planner** : Génère le planning en respectant l'ordre des modules

### Avantages

✅ **Focalisé** : Seuls les modules avec cours sont analysés
✅ **Organisé** : Chaque concept est lié à son module
✅ **Évolutif** : Ajoutez des cours plus tard, relancez l'analyse
✅ **Efficace** : Pas de bruit, pas de temps perdu

## 📊 Vue dans l'application

### Page d'accueil
Affiche :
- Compte à rebours avant l'examen
- Votre rythme de révision (30min + 8h)
- Progression des modules (X/Y avec cours)

### Mes Documents > Vue Modules
Grille visuelle :
- 📘 Modules AA avec statut ✅/🔴
- 📙 Modules AE avec statut ✅/🔴
- État global de votre préparation

### Analyser
Liste des modules qui seront analysés :
- Uniquement ceux avec contenu
- Organisés par catégorie (Base/Avancé)

### Concepts
Filtres avancés :
- Par module (AA01, AE03, etc.)
- Par importance
- Par lien avec l'examen
- Groupés par module pour faciliter la navigation

## 🔄 Mise à jour des modules

### Si vous ajoutez des cours plus tard

1. Placez les nouveaux fichiers dans le bon dossier (ex: `AA06/`)
2. Allez dans **Mes Documents > Import Dossiers**
3. Relancez le scan
4. Allez dans **Analyser** et relancez l'analyse
5. Le système détectera automatiquement les nouveaux contenus

### Si vous marquez un module comme vide par erreur

1. Ouvrez `config/config.yaml`
2. Changez `has_content: false` en `has_content: true`
3. Relancez l'analyse

## 💡 Conseils d'utilisation

### Première analyse
- Lancez-la le soir (elle peut prendre 15-30 minutes selon le nombre de documents)
- Vérifiez ensuite que tous les modules attendus sont bien détectés
- Explorez les concepts pour vous familiariser avec la structure

### Révisions quotidiennes
1. Consultez votre planning du jour
2. Révisez les concepts selon la répétition espacée
3. Utilisez les flashcards en mode quiz
4. Marquez les sessions comme terminées

### Avant l'examen
- Consultez le guide complet
- Révisez toutes les formules essentielles
- Focalisez sur les concepts "critiques" liés à l'examen

## ❓ Questions fréquentes

### Pourquoi certains modules ne sont pas analysés ?
→ Parce qu'ils sont marqués `has_content: false` (pas encore de cours)

### Comment ajouter de nouveaux documents ?
→ Placez-les dans le dossier du module et relancez le scan

### Puis-je modifier le temps de révision ?
→ Oui, dans **⚙️ Paramètres** ou directement dans `config.yaml`

### L'IA peut-elle se tromper ?
→ Oui, vérifiez toujours les concepts identifiés et complétez avec vos propres notes

---

**Votre système est prêt ! Lancez l'analyse pour commencer ! 🚀**
