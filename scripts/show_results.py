#!/usr/bin/env python3
"""Affiche les résultats de l'analyse"""
import json

with open('exports/concept_map.json', 'r') as f:
    data = json.load(f)

print("📊 RÉSULTATS DE L'ANALYSE")
print("=" * 40)

if 'concepts' in data:
    concepts = data['concepts']
    print(f"✅ Concepts extraits: {len(concepts)}")
    
    # Par importance
    by_importance = {}
    for c in concepts:
        imp = c.get('importance', 'unknown')
        by_importance[imp] = by_importance.get(imp, 0) + 1
    
    print(f"\n📈 Par importance:")
    for imp, count in sorted(by_importance.items()):
        print(f"  - {imp}: {count}")
    
    # Par catégorie
    by_cat = {}
    for c in concepts:
        cat = c.get('category', 'unknown')
        by_cat[cat] = by_cat.get(cat, 0) + 1
    
    print(f"\n📚 Par catégorie:")
    for cat, count in sorted(by_cat.items(), key=lambda x: -x[1])[:10]:
        print(f"  - {cat}: {count}")
    
    # Exemple de concepts
    print(f"\n🎯 Exemples de concepts:")
    for c in concepts[:5]:
        print(f"  • {c.get('name', 'N/A')}")
else:
    print("Structure différente:")
    print(list(data.keys()))
