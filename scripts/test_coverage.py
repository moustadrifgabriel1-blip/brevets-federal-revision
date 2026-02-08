#!/usr/bin/env python3
"""Test rapide de la matrice de couverture"""
import json
import yaml
import sys
sys.path.insert(0, '.')

from src.directives_coverage import get_module_coverage, get_coverage_summary

with open('cloud_data/concept_map.json', 'r') as f:
    concept_map = json.load(f)

with open('config/config.yaml', 'r') as f:
    config = yaml.safe_load(f)

coverage = get_module_coverage(concept_map, config)
summary = get_coverage_summary(coverage)

print('=== RÉSUMÉ COUVERTURE ===')
print(f"Couverture globale: {summary['coverage_rate']*100:.0f}%")
print(f"Compétences: {summary['covered_competences']}/{summary['total_competences']}")
print(f"Lacunes: {summary['total_gaps']}")
print(f"Modules complets: {summary['modules_complet']}")
print(f"Modules partiels: {summary['modules_partiel']}")
print(f"Modules insuffisants: {summary['modules_insuffisant']}")
print(f"Modules manquants: {summary['modules_manquant']}")
print()
print('=== PAR MODULE ===')
for code in sorted(coverage.keys()):
    c = coverage[code]
    icons = {'complet': 'OK', 'partiel': 'PARTIEL', 'insuffisant': 'INSUFFISANT', 'manquant': 'MANQUANT'}
    icon = icons[c['status']]
    print(f"[{icon}] {code} {c['name']}: {c['coverage_score']*100:.0f}% | {c['num_concepts']} concepts | {len(c['gaps'])} lacunes")
