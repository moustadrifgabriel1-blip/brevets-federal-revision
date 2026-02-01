#!/usr/bin/env python3
"""Script pour modifier app.py et ajouter la generation auto du planning"""

import re

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Pattern a chercher
old_pattern = r'mapper\.export_to_json\("exports/concept_map\.json"\)\s*\n\s*st\.success\("✅ Analyse terminée avec succès!"\)\s*\n\s*st\.balloons\(\)'

# Nouveau code
new_code = '''mapper.export_to_json("exports/concept_map.json")
                    
                    # Etape 4: Generation automatique du planning
                    st.info("📆 Generation du planning de revision...")
                    from src.revision_planner import auto_generate_planning
                    planning_result = auto_generate_planning(config)
                    
                    if planning_result['success']:
                        st.success(f"Planning genere: {planning_result['total_sessions']} sessions, {planning_result['total_hours']}h de revision")
                    else:
                        st.warning(f"Erreur planning: {planning_result.get('error', 'Inconnu')}")
                    
                    st.success("Analyse et planning termines!")
                    st.balloons()'''

# Remplacer
new_content = re.sub(old_pattern, new_code, content)

if new_content != content:
    with open('app.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("OK - app.py modifie avec succes")
else:
    print("Pattern non trouve, modification manuelle necessaire")
