#!/usr/bin/env python3
"""Analyse détaillée du planning PDF"""

import pdfplumber
import pandas as pd
import re

pdf_path = 'FSB 25-27 PROD Planning Brevet_v.04.pdf'

print("=" * 80)
print("ANALYSE DÉTAILLÉE DU PLANNING")
print("=" * 80)

with pdfplumber.open(pdf_path) as pdf:
    page = pdf.pages[0]
    tables = page.extract_tables()
    
    table = tables[1]  # Le grand tableau
    
    print(f"\nTableau: {len(table)} lignes x {len(table[0])} colonnes\n")
    
    # Afficher les 30 premières lignes
    for i, row in enumerate(table[:30]):
        print(f"L{i:2d}: {row[:6]}")  # 6 premières colonnes
    
    print("\n" + "=" * 80)
    print("STRUCTURE:")
    print("=" * 80)
    
    sessions = []
    current_year = '2025'
    dates = {}
    
    for i, row in enumerate(table):
        # Arrêter si on atteint la ligne d'examen
        if 'Examen' in str(row) and 'professionnel' in str(row):
            print(f"\n>>> LIGNE EXAMEN ATTEINTE (ligne {i}) - Arrêt de l'extraction")
            break
        
        # Détecter l'année
        if row[0]:
            first = str(row[0]).replace('\n', '')
            if first == '5':
                current_year = '2025'
                print(f"\n>>> ANNÉE 2025 détectée (ligne {i})")
            elif first == '6':
                current_year = '2026'
                print(f"\n>>> ANNÉE 2026 détectée (ligne {i})")
            elif first == '7':
                current_year = '2027'
                print(f"\n>>> ANNÉE 2027 détectée (ligne {i})")
        
        # Ligne de semaine avec dates
        if 'Semaine' in str(row):
            week_num = re.search(r'Semaine (\d+)', str(row))
            if week_num:
                week_number = int(week_num.group(1))
                print(f"\nLigne {i} - SEMAINE {week_number}")
                
                # LOGIQUE DE CHANGEMENT D'ANNÉE basée sur les semaines
                # Si on est en semaine 1-10 et qu'on était en 2025 → passer en 2026
                # Car 2025 se termine en décembre (semaines 40+) et 2026 commence en janvier (semaines 1-3)
                if current_year == '2025' and week_number <= 12:
                    # Vérifier s'il y a des dates de janvier/février/mars dans cette ligne
                    for cell in row:
                        if cell and re.search(r'\d{2}\.(01|02|03)\b', str(cell)):
                            current_year = '2026'
                            print(f">>> TRANSITION 2025→2026 détectée (semaine {week_number} avec dates jan/fév/mar)")
                            break
            
            # Extraire les dates
            dates = {}
            days = ['Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi']
            day_idx = 0
            
            for j, cell in enumerate(row):
                if cell:
                    cell_str = str(cell).upper()
                    # Format standard: '07.10'
                    if re.match(r'^\d{2}\.\d{2}$', str(cell)):
                        if day_idx < len(days):
                            dates[days[day_idx]] = cell
                            day_idx += 1
                    # Format spécial: '18.01 LUNDI', '19.01 MARDI', '20.01 MERCREDI', etc.
                    else:
                        # Extraire la date (DD.MM)
                        date_match = re.search(r'(\d{2}\.\d{2})', cell_str)
                        if date_match:
                            date_val = date_match.group(1)
                            # Extraire le jour de la semaine
                            if 'LUNDI' in cell_str:
                                dates['Lundi'] = date_val
                            elif 'MARDI' in cell_str:
                                dates['Mardi'] = date_val
                            elif 'MERCREDI' in cell_str:
                                dates['Mercredi'] = date_val
                            elif 'JEUDI' in cell_str:
                                dates['Jeudi'] = date_val
                            elif 'VENDREDI' in cell_str:
                                dates['Vendredi'] = date_val
                            elif 'SAMEDI' in cell_str:
                                dates['Samedi'] = date_val
            
            print(f"  Dates: {dates}")
        
        # Lignes matin/après-midi
        elif row[2] in ['Matin', 'Après-midi']:
            period = row[2]
            
            # LOGIQUE CORRECTE: Parcourir les colonnes impaires (4, 6, 8, 10, 12) = modules
            # Chaque cellule avec un module = 1 session
            # Structure: col 3=instructeur1, col 4=module1, col 5=instructeur2, col 6=module2...
            
            # Associer chaque colonne de module à une date
            # Les dates sont dans la ligne d'en-tête précédente (dans 'dates')
            date_keys = list(dates.keys())  # ['Mardi', 'Mercredi', 'Jeudi', ...]
            
            # Colonnes de modules: 4, 6, 8, 10, 12 (numérotation 0-based)
            for col_idx in range(4, 15, 2):  # 4, 6, 8, 10, 12, 14
                if col_idx >= len(row):
                    break
                
                module_text = row[col_idx]
                if not module_text:
                    continue
                
                # Trouver le jour correspondant (chaque paire = 1 jour)
                day_idx = (col_idx - 4) // 2  # 4->0, 6->1, 8->2, 10->3, 12->4
                if day_idx >= len(date_keys):
                    continue
                
                day = date_keys[day_idx]
                date = dates[day]
                instructor = row[col_idx - 1] if col_idx > 0 else None
                
                # Extraire le module
                match = re.search(r'(AA\d{2}|AE\d{2})', str(module_text))
                if match:
                    module = match.group(1)
                    subject = re.sub(r'(AA\d{2}|AE\d{2})\s*', '', str(module_text)).strip()
                    
                    sessions.append({
                        'Ligne': i,
                        'Annee': current_year,
                        'Date': f"{date}.{current_year}",
                        'Jour': day,
                        'Periode': period,
                        'Module': module,
                        'Sujets': subject,
                        'Instructeur': instructor if instructor else ''
                    })
                    
                    if i <= 3:  # Debug
                        print(f"    {day} {date} {period}: {module}")

print("\n" + "=" * 80)
print(f"TOTAL SESSIONS EXTRAITES: {len(sessions)}")
print("=" * 80)

# Créer DataFrame et sauvegarder
df = pd.DataFrame(sessions)
df['Date'] = pd.to_datetime(df['Date'], format='%d.%m.%Y')
df = df.sort_values('Date')

print(f"\nPremière session: {df['Date'].min()}")
print(f"Dernière session: {df['Date'].max()}")
print(f"\nPar année:")
print(df.groupby('Annee').size())

# Sauvegarder
df['Duree'] = '0.5j'
df_final = df[['Date', 'Module', 'Periode', 'Duree', 'Sujets', 'Instructeur']].copy()
df_final.to_excel('data/planning_cours_brevet_2025-2027.xlsx', index=False, sheet_name='Planning')

print(f"\nFichier sauvegardé: data/planning_cours_brevet_2025-2027.xlsx")
