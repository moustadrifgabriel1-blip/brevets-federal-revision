import pdfplumber
import re

with pdfplumber.open('FSB 25-27 PROD Planning Brevet_v.04.pdf') as pdf:
    table = pdf.pages[0].extract_tables()[1]
    
    print("=== BLOCS ET SESSIONS 2025 ===\n")
    
    current_block = None
    block_sessions = 0
    total = 0
    
    for i in range(1, 28):
        row = table[i]
        
        # Détecter un nouveau bloc (B##)
        if row[1] and re.match(r'B\d+', str(row[1])):
            if current_block:
                print(f"{current_block}: {block_sessions} sessions")
                total += block_sessions
            current_block = row[1]
            block_sessions = 0
        
        # Compter les sessions
        if len(row) > 2 and row[2] in ['Matin', 'Après-midi']:
            has_module = any('AA' in str(cell) or 'AE' in str(cell) for cell in row[3:])
            if has_module:
                block_sessions += 1
    
    if current_block:
        print(f"{current_block}: {block_sessions} sessions")
        total += block_sessions
    
    print(f"\n=== TOTAL: {total} sessions ===")
