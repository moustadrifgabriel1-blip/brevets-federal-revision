qw
y   !/usr/bin/env python3
"""Test de l'analyseur IA"""
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

# Forcer la clé API depuis .env
config['api']['gemini_api_key'] = os.getenv('GOOGLE_API_KEY')
print(f"API Key: {config['api']['gemini_api_key'][:20]}...")
print(f"Model: {config['api']['model']}")

# Scanner
print("\n--- SCAN ---")
scanner = DocumentScanner(config)
results = scanner.scan_all()

print(f"\nCours dans results: {len(results.get('cours', []))}")
print(f"Directives dans results: {len(results.get('directives', []))}")

# Vérifier get_documents_by_category
cours_docs = scanner.get_documents_by_category('cours')
print(f"\nCours via get_documents_by_category: {len(cours_docs)}")

# Vérifier les catégories des documents
categories = {}
for doc in scanner.documents:
    cat = doc.category
    if cat not in categories:
        categories[cat] = 0
    categories[cat] += 1
print(f"Catégories: {categories}")

# Analyser quelques docs
print("\n--- ANALYSE TEST ---")
analyzer = ContentAnalyzer(config)
print(f"Orientation: {analyzer.orientation}")

# Charger directives
directives_docs = results.get('directives', [])
if directives_docs:
    directives_content = "\n\n".join([doc.content[:5000] for doc in directives_docs])
    analyzer.load_directives_context(directives_content)
    print(f"Directives chargées: {len(directives_content)} caractères")

# Analyser 3 documents avec du contenu
all_concepts = []
docs_with_content = [d for d in cours_docs if len(d.content) > 500][:3]
print(f"\nTest sur {len(docs_with_content)} documents...")

for doc in docs_with_content:
    print(f"\n  Document: {doc.filename}")
    print(f"  Module: {doc.module}")
    print(f"  Contenu: {len(doc.content)} chars")
    
    concepts = analyzer.analyze_course_document(doc.content, doc.filename, doc.module)
    print(f"  → {len(concepts)} concepts trouvés")
    all_concepts.extend(concepts)

print(f"\n=== TOTAL: {len(all_concepts)} concepts ===")
