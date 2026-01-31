import pdfplumber

with pdfplumber.open('FSB 25-27 PROD Planning Brevet_v.04.pdf') as pdf:
    table = pdf.pages[0].extract_tables()[1]
    
    # Ligne 2 devrait avoir 4 sessions "Matin"
    print("=== LIGNE 2 (4 sessions Matin) ===")
    row = table[2]
    print(f"Colonne 2: {row[2]}")  # Matin
    print(f"\nToutes les colonnes (3 à 14):")
    for j in range(3, 15):
        if j < len(row):
            print(f"Col {j}: [{row[j]}]")
