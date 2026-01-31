#!/usr/bin/env python3
"""Script pour créer le fichier Excel du planning de cours"""

import pandas as pd

# Données extraites du planning PDF (sessions visibles jusqu'à janvier 2026)
data = {
    'Date': [
        '07.10.2025', '08.10.2025', '10.10.2025',
        '11.11.2025', '12.11.2025', '13.11.2025', '14.11.2025', '15.11.2025',
        '02.12.2025', '04.12.2025', '05.12.2025', '06.12.2025',
        '13.01.2026', '14.01.2026', '15.01.2026', '16.01.2026', '17.01.2026',
        '27.01.2026', '28.01.2026', '29.01.2026', '30.01.2026', '31.01.2026'
    ],
    'Module': [
        'AA06', 'AA01', 'AA01',
        'AA02', 'AA01', 'AA01', 'AA01', 'AA10',
        'AA06', 'AA01', 'AA02', 'AA06',
        'AA06', 'AA06', 'AA01', 'AA01', 'AA06',
        'AA01', 'AA01', 'AA01', 'AA01', 'AA10'
    ],
    'Duree': ['1j'] * 22,
    'Sujets': [
        'Production Distribution Transport',
        'Mathematiques prealables',
        'Bases de la mecanique',
        'Mathematiques',
        'Mathematiques',
        'Mathematiques',
        'Bases de la mecanique',
        'Machinisme',
        'Techniques de matrice',
        'Preparation du travail',
        'Mathematiques des temps',
        'Shell de la cloture',
        'Techniques de la basse',
        'Shell en etat derive',
        'Maintenance reseau BT',
        'Maintenance reseau BT',
        'Shell de la cloture',
        'Bilan installation',
        'Installation en entraines',
        'Installation en entraines',
        'Installation en entraines',
        'Machinisme'
    ],
    'Instructeur': [
        'ALA', 'JA', 'LJP', 'JA', 'JA', 'JA', 'LJP', 'JDV', 
        'ALA', 'JFC', 'JFC', 'ALA', 'ALA', 'ALA', 'ALA', 'ALA', 
        'ALA', 'JFC', 'JFC', 'JFC', 'JFC', 'JDV'
    ]
}

df = pd.DataFrame(data)

# Sauvegarder en Excel
excel_file = 'data/planning_cours_brevet_2025-2027.xlsx'
df.to_excel(excel_file, index=False, sheet_name='Planning')

print(f"Fichier cree: {excel_file}")
print(f"Sessions: {len(df)}")
print(f"Modules: {sorted(df['Module'].unique())}")
