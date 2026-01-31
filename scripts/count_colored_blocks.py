import pdfplumber
import re

pdf_path = 'FSB 25-27 PROD Planning Brevet_v.04.pdf'

with pdfplumber.open(pdf_path) as pdf:
    table = pdf.pages[0].extract_tables()[1]
    
    print("=== COMPTAGE DES CASES COLORÉES (1 case = 1 session) ===\n")
    
    sessions_2025 = 0
    sessions_2026 = 0
    sessions_2027 = 0
    total = 0
    current_year = '2025'
    
    for i, row in enumerate(table):
        # Arrêter à l'examen
        if 'Examen' in str(row) and 'professionnel' in str(row):
            print(f"\nLigne {i}: EXAMEN - Arrêt")
            break
        
        # Détecter l'année
        if row[0]:
            first = str(row[0]).replace('\n', '')
            if first == '5':
                current_year = '2025'
            elif first == '6':
                current_year = '2026'
                print(f"\n>>> ANNÉE 2026 (ligne {i})")
            elif first == '7':
                current_year = '2027'
                print(f"\n>>> ANNÉE 2027 (ligne {i})")
        
        # Lignes matin/après-midi = 1 session (peu importe le nombre d'instructeurs)
        if row[2] in ['Matin', 'Après-midi']:
            # Vérifier s'il y a au moins un module (case colorée)
            has_module = False
            for cell in row[3:]:
                if cell and ('AA' in str(cell) or 'AE' in str(cell)):
                    has_module = True
                    break
            
            if has_module:
                total += 1
                if current_year == '2025':
                    sessions_2025 += 1
                elif current_year == '2026':
                    sessions_2026 += 1
                elif current_year == '2027':
                    sessions_2027 += 1
                
                if total <= 10 or i >= 49:
                    print(f"L{i:2d} {row[2]:12s} ({current_year}) | Total: {total}")

    print(f"\n=== RÉSULTAT ===")
    print(f"2025: {sessions_2025} sessions")
    print(f"2026: {sessions_2026} sessions")
    print(f"2027: {sessions_2027} sessions")
    print(f"TOTAL: {total} sessions")
