#!/usr/bin/env python3
"""Script pour modifier app.py et ajouter l'analyse locale"""

import re

# Lire le fichier
with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Trouver la section à modifier
pattern = r'(    if len\(cours_files\) == 0:\n        st\.warning.*?Mes Documents.*?\n    else:\n        if st\.button\("🚀 Lancer l\'analyse complète".*?use_container_width=True\):)'

new_code = '''    if len(cours_files) == 0:
        st.warning("⚠️ Veuillez d'abord importer vos documents dans l'onglet 'Mes Documents'")
    else:
        # Choix du mode d'analyse
        st.subheader("⚙️ Mode d'analyse")
        analysis_mode = st.radio(
            "Choisissez le mode d'analyse:",
            ["🚀 Analyse locale (rapide)", "🤖 Analyse IA (quota limité)"],
            help="L'analyse locale est instantanée. L'analyse IA utilise Gemini mais a des limites de quota (15/min)."
        )
        
        if analysis_mode == "🚀 Analyse locale (rapide)":
            if st.button("🚀 Lancer l'analyse locale", type="primary", use_container_width=True):
                with st.spinner("Analyse locale en cours..."):
                    try:
                        import sys
                        sys.path.insert(0, str(Path.cwd()))
                        from src.scanner import DocumentScanner
                        from src.local_analyzer import LocalContentAnalyzer
                        
                        config = load_config()
                        
                        st.info("📂 Scan des documents...")
                        scanner = DocumentScanner(config)
                        results = scanner.scan_all()
                        total_docs = sum(len(docs) for docs in results.values())
                        st.success(f"✅ {total_docs} documents scannés")
                        
                        st.info("🔍 Extraction des concepts...")
                        analyzer = LocalContentAnalyzer(config)
                        cours_docs = scanner.get_documents_by_category('cours')
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                        
                        for i, doc in enumerate(cours_docs):
                            percent = int(((i + 1) / len(cours_docs)) * 100)
                            status_text.text(f"⏳ {i+1}/{len(cours_docs)} ({percent}%)")
                            analyzer.analyze_course_document(doc.content, doc.filename, doc.module)
                            progress_bar.progress((i + 1) / len(cours_docs))
                        
                        status_text.empty()
                        progress_bar.empty()
                        
                        analyzer.export_concepts("exports/concepts_local.json")
                        summary = analyzer.get_summary()
                        
                        st.success(f"✅ {summary['total_concepts']} concepts extraits!")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Critiques", summary['by_importance']['critical'])
                            st.metric("Importants", summary['by_importance']['high'])
                        with col2:
                            st.metric("Moyens", summary['by_importance']['medium'])
                            st.metric("Modules", len(summary['modules']))
                        
                        st.subheader("📊 Par catégorie")
                        for cat, count in sorted(summary['by_category'].items(), key=lambda x: -x[1]):
                            st.write(f"• **{cat}**: {count}")
                        
                        st.balloons()
                        
                    except Exception as e:
                        st.error(f"❌ Erreur: {str(e)}")
                        st.exception(e)
        
        else:
            st.warning("⚠️ L'analyse IA est limitée à 15 requêtes/minute. Attends 24h si quota épuisé.")
            if st.button("🤖 Lancer l'analyse IA", type="primary", use_container_width=True):'''

match = re.search(pattern, content, re.DOTALL)
if match:
    content = content[:match.start()] + new_code + content[match.end():]
    with open('app.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("✅ app.py modifié avec succès!")
else:
    print("❌ Pattern non trouvé, essai alternatif...")
    # Essai simple avec replace
    old_text = 'if st.button("🚀 Lancer l\'analyse complète", type="primary", use_container_width=True):'
    if old_text in content:
        print(f"✅ Trouvé le bouton à modifier")
    else:
        print("❌ Bouton non trouvé")
