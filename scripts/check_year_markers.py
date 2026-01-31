import pdfplumber

with pdfplumber.open('FSB 25-27 PROD Planning Brevet_v.04.pdf') as pdf:
    table = pdf.pages[0].extract_tables()[1]
    
    print("=== INDICATEURS D'ANNÉE DANS LE PDF ===\n")
    
    for i, row in enumerate(table[:35]):
        if row[0]:
            first = str(row[0]).replace('\n', '').strip()
            if first in ['5', '6', '7', '2025', '2026', '2027']:
                print(f"Ligne {i:2d} - Col 0: [{first}]")
        
        # Afficher les lignes de semaine
        if 'Semaine' in str(row):
            print(f"Ligne {i:2d} - {row[1]}")
