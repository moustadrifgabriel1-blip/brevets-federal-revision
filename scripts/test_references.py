#!/usr/bin/env python3
"""Test des références dans les concepts"""
import sys
import os
sys.path.insert(0, '.')

from dotenv import load_dotenv
load_dotenv()

from src.scanner import DocumentScanner
from src.analyzer import ContentAnalyzer
import yaml

# Charger config
with open('config/config.yaml', 'r') as f:
    config = yaml.safe_load(f)

config['api']['gemini_api_key'] = os.getenv('GOOGLE_API_KEY')
print(f"API Key: {config['api']['gemini_api_key'][:20]}...")

# Scanner
print("\n--- SCAN ---")
scanner = DocumentScanner(config)
results = scanner.scan_all()

cours_docs = scanner.get_documents_by_category('cours')
print(f"Cours trouvés: {len(cours_docs)}")

# Analyser UN document
print("\n--- TEST ANALYSE AVEC RÉFÉRENCES ---")
analyzer = ContentAnalyzer(config)

docs_with_content = [d for d in cours_docs if len(d.content) > 500][:1]
if docs_with_content:
    doc = docs_with_content[0]
    print(f"Document: {doc.filename}")
    print(f"Contenu: {len(doc.content)} chars")
    
    concepts = analyzer.analyze_course_document(doc.content, doc.filename, doc.module)
    print(f"\n✅ {len(concepts)} concepts trouvés\n")
    
    for c in concepts[:3]:
        print(f"📌 {c.name}")
        print(f"   📄 Source: {c.source_document}")
        print(f"   📖 Références: {c.page_references or 'Non spécifié'}")
        print(f"   🔑 Mots-clés: {', '.join(c.keywords) if c.keywords else 'Aucun'}")
        print()
else:
    print("❌ Aucun document trouvé")
