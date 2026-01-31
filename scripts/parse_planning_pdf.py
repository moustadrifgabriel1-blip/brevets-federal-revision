#!/usr/bin/env python3
"""Parser le planning PDF en format Excel"""

import pdfplumber
import pandas as pd
import re
from datetime import datetime

pdf_path = 'FSB 25-27 PROD Planning Brevet_v.04.pdf'

print("Extraction des sessions de cours du PDF...")

sessions = []
current_year = '2025'  # Année de départ par défaut

with pdfplumber.open(pdf_path) as pdf:
    for page in pdf.pages:
        tables = page.extract_tables()
        
        for table in tables:
            if not table or len(table) < 3:
                continue
            
            # Parcourir les lignes du tableau
            current_week = None
            dates = {}
            
            for row in table:
                if not row:
                    continue
                
                # Détecter l'année - Chercher dans la première colonne
                # '5' + 'B0x' = 2025
                # '6' + 'B1x' = 2026  
                # '7' + 'B1x' = 2027
                if row[0] and row[1]:
                    first_col = str(row[0]).replace('\n', '').replace(' ', '')
                    second_col = str(row[1])
                    
                    # Patterns: '5' avec B01-B05 = 2025
                    if first_col == '5' and 'B0' in second_col:
                        current_year = '2025'
                    # '6' avec B06-B12 = 2026
                    elif first_col == '6' and ('B0' in second_col or 'B1' in second_col):
                        current_year = '2026'
                    # '2\n0' (2026 vertical) ou '2' seul après 2025 = 2026
                    elif first_col in ['20', '2'] and current_year == '2025' and 'B' in second_col:
                        current_year = '2026'
                    # '7' avec B13-B16 = 2027
                    elif first_col == '7' and 'B' in second_col:
                        current_year = '2027'
                    # '2\n0' après 2026 = 2027
                    elif first_col in ['20', '2'] and current_year == '2026' and 'B' in second_col:
                        current_year = '2027'
                
                # Ligne avec les dates (format: '07.10', '08.10', etc.)
                # Structure: ['', 'B01', 'Semaine 41', '07.10', None, '08.10', None, '09.10', None, '10.10', None, '11.10', ...]
                if 'Semaine' in str(row):
                    # Extraire le numéro de semaine pour aider à déterminer l'année
                    week_match = re.search(r'Semaine (\d+)', str(row))
                    if week_match:
                        week_num = int(week_match.group(1))
                        # Semaines 40-52 = fin d'année (oct-déc) = 2025
                        # Semaines 1-39 = milieu d'année (jan-sep) = 2026 ou 2027
                        if week_num >= 40:
                            if current_year == '2025':
                                pass  # Reste en 2025
                            else:
                                # Si on est déjà en 2026+, c'est peut-être oct-déc 2026
                                current_year = '2026'
                        else:
                            # Semaines 1-39: si on était en 2025, on passe à 2026
                            if current_year == '2025':
                                current_year = '2026'
                            # Si on était en 2026 et on voit une semaine basse, on passe à 2027
                            elif current_year == '2026' and week_num <= 10:
                                current_year = '2027'
                    
                    # Extraire les dates
                    dates = {}
                    day_names = ['Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi']
                    day_index = 0
                    
                    for i, cell in enumerate(row):
                        if cell and re.match(r'\d{2}\.\d{2}', str(cell)):
                            # C'est une date
                            date_str = cell
                            # Déterminer le jour de la semaine
                            if day_index < len(day_names):
                                dates[day_names[day_index]] = date_str
                                day_index += 1
                
                # Lignes Matin/Après-midi avec les modules
                elif row and len(row) > 3 and str(row[2]) in ['Matin', 'Après-midi', 'Après-midi']:
                    period = str(row[2])
                    
                    # Extraire les sessions pour chaque jour
                    # Format: ['', None, 'Matin', 'JCB', 'AA09 Electrotechnique', 'JA', 'AA11 Mathématiques', ...]
                    day_names = ['Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi']
                    
                    # Les données commencent à l'index 3
                    for day_idx, day_name in enumerate(day_names):
                        # Chaque jour occupe 2 colonnes (instructeur, module)
                        instructor_idx = 3 + (day_idx * 2)
                        module_idx = instructor_idx + 1
                        
                        if instructor_idx < len(row) and module_idx < len(row):
                            instructor = row[instructor_idx]
                            module_text = row[module_idx]
                            
                            if module_text and instructor and day_name in dates:
                                # Extraire le code module (AA01, AE03, etc.)
                                module_match = re.search(r'(AA\d{2}|AE\d{2})', str(module_text))
                                if module_match:
                                    module_code = module_match.group(1)
                                    
                                    # Extraire le sujet (après le code module)
                                    subject = re.sub(r'(AA\d{2}|AE\d{2})\s*', '', str(module_text)).strip()
                                    
                                    date_str = dates[day_name]
                                    
                                    # Vérifier que c'est une date valide
                                    if not re.match(r'^\d{2}\.\d{2}$', date_str):
                                        continue
                                    
                                    # Utiliser l'année courante détectée (ne PAS la recalculer)
                                    full_date = f"{date_str}.{current_year}"
                                    
                                    sessions.append({
                                        'Date': full_date,
                                        'Module': module_code,
                                        'Periode': period,
                                        'Duree': '0.5j',
                                        'Sujets': subject,
                                        'Instructeur': str(instructor).strip()
                                    })

# Créer le DataFrame
df = pd.DataFrame(sessions)

# Convertir les dates
df['Date'] = pd.to_datetime(df['Date'], format='%d.%m.%Y')

# Trier par date
df = df.sort_values('Date')

# Supprimer les doublons
df = df.drop_duplicates()

print(f"\nSessions extraites: {len(df)}")
print(f"Modules: {sorted(df['Module'].unique())}")
print(f"Periode: {df['Date'].min()} a {df['Date'].max()}")

# Sauvegarder en Excel
excel_file = 'data/planning_cours_brevet_2025-2027.xlsx'
df.to_excel(excel_file, index=False, sheet_name='Planning')
print(f"\nFichier cree: {excel_file}")

# Afficher un aperçu
print("\nApercu des premieres sessions:")
print(df.head(20).to_string(index=False))
