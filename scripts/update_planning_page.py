#!/usr/bin/env python3
"""Script pour simplifier la page Planning Revisions dans app.py"""

with open('app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Trouver les lignes de debut et fin de la page Planning Revisions
start_line = None
end_line = None

for i, line in enumerate(lines):
    if 'elif page == "� Planning Révisions":' in line or 'elif page == "📆 Planning Révisions":' in line:
        start_line = i
    elif start_line is not None and line.startswith('elif page =='):
        end_line = i
        break

if start_line is None:
    print("Page Planning Revisions non trouvee")
    exit(1)

if end_line is None:
    end_line = len(lines)

print(f"Page trouvee: lignes {start_line+1} a {end_line}")

# Nouvelle page simplifiee
new_page = '''elif page == "📆 Planning Révisions":
    st.header("📆 Planning de Révision Automatique")
    
    revision_plan = load_revision_plan()
    concept_map = load_concept_map()
    
    if not concept_map:
        st.warning("⚠️ Lancez d'abord l'analyse pour générer les concepts et le planning.")
        st.info("👉 Allez dans l'onglet 'Analyser' pour démarrer.")
    elif not revision_plan:
        st.warning("⚠️ Le planning n'a pas encore été généré.")
        st.info("Le planning est généré automatiquement après l'analyse. Relancez l'analyse.")
        
        # Bouton pour regenerer le planning
        if st.button("🔄 Générer le planning maintenant", type="primary"):
            with st.spinner("Génération en cours..."):
                try:
                    from src.revision_planner import auto_generate_planning
                    config = load_config()
                    result = auto_generate_planning(config)
                    if result['success']:
                        st.success(f"✅ Planning généré: {result['total_sessions']} sessions")
                        st.rerun()
                    else:
                        st.error(f"Erreur: {result['error']}")
                except Exception as e:
                    st.error(f"Erreur: {e}")
    else:
        # Afficher les statistiques
        stats = revision_plan.get('statistics', {})
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("⏱️ Heures totales", f"{revision_plan.get('total_hours', 0):.1f}h")
        with col2:
            st.metric("📚 Concepts", revision_plan.get('total_concepts', 0))
        with col3:
            st.metric("📅 Sessions", revision_plan.get('total_sessions', 0))
        with col4:
            days_left = stats.get('days_until_exam', 0)
            st.metric("🎯 Jours restants", days_left)
        
        st.divider()
        
        # Jalons
        st.subheader("🏁 Jalons de progression")
        milestones = revision_plan.get('milestones', [])
        if milestones:
            for m in milestones:
                col1, col2 = st.columns([1, 4])
                with col1:
                    st.markdown(f"**{m['date']}**")
                with col2:
                    progress = m.get('progress', 0)
                    st.progress(progress / 100)
                    st.caption(f"{m['name']}: {m['objective']}")
        
        st.divider()
        
        # Sessions de la semaine
        st.subheader("📆 Sessions à venir")
        
        sessions = revision_plan.get('sessions', [])
        today = datetime.now().strftime('%Y-%m-%d')
        
        # Filtrer les sessions futures
        upcoming = [s for s in sessions if s['date'] >= today][:14]
        
        if upcoming:
            for session in upcoming:
                priority_icon = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}.get(session['priority'], '⚪')
                type_icon = {'new_learning': '📚', 'revision': '🔄', 'practice': '✏️'}.get(session['session_type'], '📖')
                
                with st.expander(f"{priority_icon} {type_icon} {session['day_name']} {session['date']} - {session['duration_minutes']} min"):
                    st.markdown(f"**Catégorie:** {session['category']}")
                    st.markdown("**Concepts à étudier:**")
                    for concept in session['concepts'][:10]:
                        st.markdown(f"  - {concept}")
                    if len(session['concepts']) > 10:
                        st.caption(f"... et {len(session['concepts']) - 10} autres")
                    
                    if session.get('objectives'):
                        st.markdown("**Objectifs:**")
                        for obj in session['objectives']:
                            st.markdown(f"  - {obj}")
        else:
            st.info("Aucune session à venir.")
        
        st.divider()
        
        # Boutons d'action
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Régénérer le planning"):
                Path("exports/revision_plan.json").unlink(missing_ok=True)
                from src.revision_planner import auto_generate_planning
                config = load_config()
                result = auto_generate_planning(config)
                if result['success']:
                    st.success("Planning régénéré!")
                    st.rerun()
        with col2:
            # Telecharger le planning
            md_path = Path("exports/revision_plan.md")
            if md_path.exists():
                with open(md_path, 'r', encoding='utf-8') as f:
                    md_content = f.read()
                st.download_button(
                    "📥 Télécharger (Markdown)",
                    md_content,
                    file_name="planning_revision.md",
                    mime="text/markdown"
                )


'''

# Remplacer les lignes
new_lines = lines[:start_line] + [new_page] + lines[end_line:]

with open('app.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print(f"OK - Page Planning Revisions remplacee (lignes {start_line+1}-{end_line})")
