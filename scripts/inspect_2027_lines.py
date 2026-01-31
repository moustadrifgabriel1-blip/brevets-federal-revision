import pdfplumber

with pdfplumber.open('FSB 25-27 PROD Planning Brevet_v.04.pdf') as pdf:
    table = pdf.pages[0].extract_tables()[1]
    
    print("=== LIGNES 49-51 (2027) ===\n")
    
    for i in range(49, 52):
        row = table[i]
        print(f"\nLigne {i}:")
        for j in range(min(15, len(row))):
            if row[j]:
                print(f"  Col {j}: [{row[j]}]")
