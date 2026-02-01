#!/usr/bin/env python3
"""Affiche les statistiques du planning"""
import json

with open('exports/revision_plan.json', 'r') as f:
    plan = json.load(f)

print('=' * 60)
print('PLANNING DE REVISION GENERE')
print('=' * 60)
print()
print(f'Date examen: {plan["exam_date"]}')
print(f'Genere le: {plan["generated_at"][:10]}')
print()
print('STATISTIQUES:')
stats = plan['statistics']
print(f'  - Heures totales de revision: {stats["total_revision_hours"]}h')
print(f'  - Jours avant examen: {stats["days_until_exam"]}')
print(f'  - Concepts par session (moy): {stats["average_concepts_per_session"]}')
print()
print(f'  - Sessions haute priorite: {stats["sessions_by_priority"]["high"]}')
print(f'  - Sessions priorite moyenne: {stats["sessions_by_priority"]["medium"]}')
print()
print(f'  - Sessions apprentissage: {stats["sessions_by_type"]["new_learning"]}')
print(f'  - Sessions revision: {stats["sessions_by_type"]["revision"]}')
print()
print('JALONS:')
for m in plan['milestones']:
    print(f'  {m["date"]}: {m["name"]} - {m["objective"]}')
print()
print(f'Total sessions: {plan["total_sessions"]}')
print(f'Total concepts: {plan["total_concepts"]}')
