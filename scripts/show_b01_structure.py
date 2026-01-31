import pdfplumber

with pdfplumber.open('FSB 25-27 PROD Planning Brevet_v.04.pdf') as pdf:
    table = pdf.pages[0].extract_tables()[1]
    
    print("=== STRUCTURE BLOC B01 ===\n")
    print("Ligne 1 (En-tête semaine):")
    row1 = table[1]
    for i, cell in enumerate(row1):
        if cell:
            print(f"  Col {i}: [{cell}]")
    
    print("\nLigne 2 (Matin):")
    row2 = table[2]
    for i, cell in enumerate(row2):
        if cell:
            print(f"  Col {i}: [{cell}]")
    
    print("\nLigne 3 (Après-midi):")
    row3 = table[3]
    for i, cell in enumerate(row3):
        if cell:
            print(f"  Col {i}: [{cell}]")
