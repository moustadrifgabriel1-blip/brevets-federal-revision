import pdfplumber

with pdfplumber.open('FSB 25-27 PROD Planning Brevet_v.04.pdf') as pdf:
    table = pdf.pages[0].extract_tables()[1]
    
    print("=== BLOC B01 (lignes 1-3) ===\n")
    
    for i in range(1, 4):
        row = table[i]
        print(f"\nLigne {i}:")
        print(f"  Col 1 (Bloc): [{row[1]}]")
        print(f"  Col 2 (Période): [{row[2]}]")
        
        # Vérifier s'il y a des modules
        has_module = False
        for j, cell in enumerate(row[3:], start=3):
            if cell and ('AA' in str(cell) or 'AE' in str(cell)):
                print(f"  Col {j}: [{cell}]")
                has_module = True
        
        if has_module:
            print(f"  ✅ SESSION DÉTECTÉE")
        else:
            print(f"  ❌ PAS DE MODULE")
