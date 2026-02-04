# 📖 Références de Documents - Guide d'Utilisation

## ✨ Nouvelle Fonctionnalité

L'analyse IA extrait maintenant **automatiquement** les références exactes (pages, chapitres, sections) pour chaque concept, te permettant de retrouver facilement où réviser dans tes documents.

## 🎯 Ce que tu obtiens

Pour chaque concept analysé, l'IA identifie :

1. **📄 Document source** : Nom exact du fichier PDF
2. **📖 Références précises** : Pages, chapitres ou sections (ex: "Chapitre 2 (p.19-26)", "Section 3.1")
3. **🔑 Mots-clés** : Termes techniques importants pour rechercher rapidement

## 💡 Exemple

```
📌 Grandeurs photométriques fondamentales
   📄 Source: AE03_Eclairage public_Support de cours_V2.1-FR.pdf
   📖 Références: Chapitre 1.4 (p.11-17)
   🔑 Mots-clés: Lumen, Lux, Candela, Luminance, Kelvin, IRC
```

## 📍 Où trouver les références

### 1️⃣ Dans le Planning de Révisions (`📆 Planning Révisions`)

Quand tu ouvres une session de révision :

```
🔴 📚 Lundi 2026-02-03 - 90 min

Concepts à étudier:
  - Grandeurs photométriques fondamentales
    📄 AE03_Eclairage public_Support de cours_V2.1-FR.pdf
    📖 Chapitre 1.4 (p.11-17)
  
  - Technologies de sources lumineuses et LED
    📄 AE03_Eclairage public_Support de cours_V2.1-FR.pdf
    📖 Chapitre 2 (p.19-26)
```

### 2️⃣ Dans la Cartographie (`🗺️ Concepts`)

Chaque concept affiche :

- **📖 Où réviser:**
  - 📄 Document: `nom_du_fichier.pdf`
  - 📖 Références: `pages ou chapitres`
- **🔑 Mots-clés:** liste de termes importants

## 🚀 Comment ça marche

1. **Scan automatique** : L'IA lit le contenu des PDFs
2. **Extraction intelligente** : Gemini identifie :
   - Les concepts importants
   - Leur localisation dans le document
   - Les mots-clés associés
3. **Affichage contextuel** : Chaque session de révision montre où trouver les concepts

## 📋 Cas d'usage

### Scénario 1 : Révision ciblée
```
Session: "Électrotechnique avancée"
Concept: "Courant de court-circuit"
→ 📄 AE03_Eclairage public
→ 📖 Section 4.3 (p.38-40)
→ Tu ouvres directement la bonne page !
```

### Scénario 2 : Recherche rapide
```
Tu veux revoir les "LED"
→ 🔑 Mots-clés: LED, Durée de vie, Optique
→ 📖 Chapitre 2 (p.19-26)
```

## ⚙️ Configuration technique

### Structure des données

Les références sont stockées dans `exports/concept_map.json` :

```json
{
  "nodes": [
    {
      "name": "Concept X",
      "source_document": "fichier.pdf",
      "page_references": "p.5-8, Section 2.1",
      "keywords": ["mot1", "mot2"]
    }
  ]
}
```

### Prompts d'analyse

L'IA reçoit cette instruction :

```
Pour chaque concept, identifie:
- page_references: "Pages ou sections où trouver ce concept"
- keywords: ["termes", "techniques", "importants"]
```

## 🎓 Avantages

✅ **Gain de temps** : Plus besoin de chercher dans 94 PDFs  
✅ **Précision** : Références exactes (pages + chapitres)  
✅ **Contexte** : Mots-clés pour comprendre rapidement  
✅ **Organisation** : Toutes les infos au même endroit

## 🔄 Pour mettre à jour

Si tu ajoutes de nouveaux documents :

1. Va dans **🔧 Système**
2. Clique sur **🔄 Lancer l'analyse complète**
3. L'IA va :
   - Scanner tous les documents
   - Extraire les concepts + références
   - Régénérer le planning

## 📝 Notes

- Les références dépendent de la qualité des PDFs (certains PDFs sans numérotation claire peuvent avoir des références approximatives)
- L'IA fait de son mieux pour identifier chapitres et pages
- Si une référence est manquante, le document source est toujours indiqué

## 🆘 Support

Si un concept n'a pas de références :
- Vérifie que le PDF est bien structuré
- Relance l'analyse pour ce module spécifique
- Les références apparaîtront lors de la prochaine analyse
