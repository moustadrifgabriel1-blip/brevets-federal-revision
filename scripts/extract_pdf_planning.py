#!/usr/bin/env python3
"""Extraction du planning depuis le PDF"""

import pdfplumber
import pandas as pd
import re
from datetime import datetime

pdf_path = 'FSB 25-27 PROD Planning Brevet_v.04.pdf'

print(f"Lecture du PDF: {pdf_path}")

try:
    with pdfplumber.open(pdf_path) as pdf:
        print(f"Pages: {len(pdf.pages)}")
        
        # Extraire les tableaux
        all_tables = []
        for i, page in enumerate(pdf.pages, 1):
            tables = page.extract_tables()
            if tables:
                print(f"Page {i}: {len(tables)} tableau(x)")
                for table in tables:
                    if table and len(table) > 2:
                        all_tables.append((i, table))
        
        # Sauvegarder les données brutes pour analyse
        with open('data/planning_raw_tables.txt', 'w', encoding='utf-8') as f:
            for page_num, table in all_tables:
                f.write(f"{'='*80}\n")
                f.write(f"PAGE {page_num}\n")
                f.write(f"{'='*80}\n")
                for row in table:  # TOUTES les lignes
                    f.write(str(row) + '\n')
        
        print(f"\nTableaux extraits: {len(all_tables)}")
        print("Fichier cree: data/planning_raw_tables.txt")
        print("\nAnalysez ce fichier pour voir la structure des donnees")
        
except Exception as e:
    print(f"Erreur: {e}")
