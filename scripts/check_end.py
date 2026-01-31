#!/usr/bin/env python3
import pdfplumber
import re

pdf_path = 'FSB 25-27 PROD Planning Brevet_v.04.pdf'

with pdfplumber.open(pdf_path) as pdf:
    table = pdf.pages[0].extract_tables()[1]
    
    print("=== DERNIÈRES LIGNES DU PDF ===\n")
    for i, row in enumerate(table[-12:]):
        line_num = len(table) - 12 + i
        print(f"L{line_num}: {row[:6]}")
