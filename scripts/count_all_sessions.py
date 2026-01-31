import pdfplumber
import re

pdf_path = 'FSB 25-27 PROD Planning Brevet_v.04.pdf'

with pdfplumber.open(pdf_path) as pdf:
    table = pdf.pages[0].extract_tables()[1]
    
    print(f"Table complète: {len(table)} lignes\n")
    
    session_count = 0
    year_2027_count = 0
    
    for i, row in enumerate(table):
        if 'Examen' in str(row) and 'professionnel' in str(row):
            print(f"\nLigne {i}: EXAMEN - Arrêt")
            break
            
        # Lignes matin/après-midi = sessions
        if row and len(row) > 2 and row[2] in ['Matin', 'Après-midi']:
            modules = 0
            for j in range(3, min(14, len(row)), 2):
                if j+1 < len(row) and row[j+1]:
                    if 'AA' in str(row[j+1]) or 'AE' in str(row[j+1]):
                        match = re.search(r'(AA\d{2}|AE\d{2})', str(row[j+1]))
                        if match:
                            modules += 1
            
            if modules > 0:
                session_count += modules
                print(f"L{i:2d} {row[2]:12s}: {modules} session(s) | Total: {session_count}")
                
                if i >= 49:
                    year_2027_count += modules

    print(f"\n=== RÉSULTAT ===")
    print(f"Total sessions: {session_count}")
    print(f"Sessions 2027 (lignes ≥49): {year_2027_count}")
