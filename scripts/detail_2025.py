import pdfplumber
import re

pdf_path = 'FSB 25-27 PROD Planning Brevet_v.04.pdf'

with pdfplumber.open(pdf_path) as pdf:
    table = pdf.pages[0].extract_tables()[1]
    
    print("=== DÉTAIL DES LIGNES 2025 ===\n")
    
    current_year = '2025'
    count_2025 = 0
    
    for i, row in enumerate(table):
        if 'Examen' in str(row) and 'professionnel' in str(row):
            break
        
        # Détecter l'année
        if row[0]:
            first = str(row[0]).replace('\n', '')
            if first == '6':
                current_year = '2026'
                print(f"\n>>> FIN 2025 - {count_2025} sessions\n")
                break
        
        # Lignes matin/après-midi
        if row[2] in ['Matin', 'Après-midi']:
            # Compter s'il y a un module
            has_module = False
            for cell in row[3:]:
                if cell and ('AA' in str(cell) or 'AE' in str(cell)):
                    has_module = True
                    break
            
            if has_module:
                count_2025 += 1
                print(f"L{i:2d} {row[2]:12s} - Session #{count_2025}")
            else:
                print(f"L{i:2d} {row[2]:12s} - VIDE (pas de module)")

    print(f"\n=== TOTAL 2025: {count_2025} sessions ===")
