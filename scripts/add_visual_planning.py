#!/usr/bin/env python3
"""Script pour ajouter des visualisations a la page Planning"""

# Nouveau contenu de la page Planning avec graphiques
NEW_PAGE = '''elif page == "📆 Planning Révisions":
    st.header("📆 Planning de Révision Automatique")
    
    revision_plan = load_revision_plan()
    concept_map = load_concept_map()
    
    if not concept_map:
        st.warning("⚠️ Lancez d'abord l'analyse pour générer les concepts et le planning.")
        st.info("👉 Allez dans l'onglet 'Analyser' pour démarrer.")
    elif not revision_plan:
        st.warning("⚠️ Le planning n'a pas encore été généré.")
        st.info("Le planning est généré automatiquement après l'analyse. Relancez l'analyse.")
        
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
        import plotly.express as px
        import plotly.graph_objects as go
        from collections import Counter
        
        stats = revision_plan.get('statistics', {})
        sessions = revision_plan.get('sessions', [])
        
        # ===== METRIQUES EN HAUT =====
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
        
        # ===== ONGLETS VISUELS =====
        tab1, tab2, tab3, tab4 = st.tabs(["📊 Vue d'ensemble", "📅 Calendrier", "📈 Progression", "📋 Sessions"])
        
        with tab1:
            # Vue d'ensemble avec graphiques
            col1, col2 = st.columns(2)
            
            with col1:
                # Graphique en anneau - Sessions par priorité
                st.subheader("Sessions par priorité")
                priority_data = stats.get('sessions_by_priority', {})
                if priority_data:
                    fig_priority = go.Figure(data=[go.Pie(
                        labels=['Haute', 'Moyenne', 'Basse'],
                        values=[priority_data.get('high', 0), priority_data.get('medium', 0), priority_data.get('low', 0)],
                        hole=.4,
                        marker_colors=['#e53935', '#fdd835', '#43a047']
                    )])
                    fig_priority.update_layout(height=300, margin=dict(t=20, b=20, l=20, r=20))
                    st.plotly_chart(fig_priority, use_container_width=True)
            
            with col2:
                # Graphique - Sessions par type
                st.subheader("Type de sessions")
                type_data = stats.get('sessions_by_type', {})
                if type_data:
                    fig_type = go.Figure(data=[go.Pie(
                        labels=['Apprentissage', 'Révision', 'Pratique'],
                        values=[type_data.get('new_learning', 0), type_data.get('revision', 0), type_data.get('practice', 0)],
                        hole=.4,
                        marker_colors=['#1E88E5', '#7E57C2', '#26A69A']
                    )])
                    fig_type.update_layout(height=300, margin=dict(t=20, b=20, l=20, r=20))
                    st.plotly_chart(fig_type, use_container_width=True)
            
            # Timeline des jalons
            st.subheader("🏁 Timeline des jalons")
            milestones = revision_plan.get('milestones', [])
            if milestones:
                milestone_dates = [m['date'] for m in milestones]
                milestone_names = [m['name'] for m in milestones]
                milestone_progress = [m['progress'] for m in milestones]
                
                fig_timeline = go.Figure()
                fig_timeline.add_trace(go.Scatter(
                    x=milestone_dates,
                    y=[1]*len(milestones),
                    mode='markers+text',
                    marker=dict(size=30, color=milestone_progress, colorscale='Viridis', showscale=True),
                    text=milestone_names,
                    textposition='top center',
                    hovertemplate='%{text}<br>%{x}<br>Progression: %{marker.color}%<extra></extra>'
                ))
                fig_timeline.update_layout(
                    height=200,
                    showlegend=False,
                    yaxis=dict(visible=False, range=[0.5, 1.8]),
                    xaxis=dict(title='Date'),
                    margin=dict(t=40, b=40)
                )
                st.plotly_chart(fig_timeline, use_container_width=True)
            
            # Distribution par catégorie
            st.subheader("📂 Concepts par catégorie")
            categories = revision_plan.get('categories', [])
            if categories:
                cat_counts = Counter(categories)
                top_cats = dict(cat_counts.most_common(10))
                fig_cats = px.bar(
                    x=list(top_cats.values()),
                    y=list(top_cats.keys()),
                    orientation='h',
                    color=list(top_cats.values()),
                    color_continuous_scale='Blues'
                )
                fig_cats.update_layout(
                    height=400,
                    showlegend=False,
                    yaxis_title='',
                    xaxis_title='Nombre de concepts',
                    margin=dict(l=200)
                )
                st.plotly_chart(fig_cats, use_container_width=True)
        
        with tab2:
            # Calendrier visuel
            st.subheader("📅 Calendrier des sessions")
            
            if sessions:
                # Créer un heatmap calendrier
                session_dates = [s['date'] for s in sessions]
                session_durations = [s['duration_minutes'] for s in sessions]
                
                # Créer DataFrame pour le calendrier
                df_calendar = pd.DataFrame({
                    'date': pd.to_datetime(session_dates),
                    'duration': session_durations
                })
                df_calendar['week'] = df_calendar['date'].dt.isocalendar().week
                df_calendar['day'] = df_calendar['date'].dt.dayofweek
                df_calendar['month'] = df_calendar['date'].dt.strftime('%Y-%m')
                
                # Grouper par semaine/jour
                today = datetime.now()
                next_8_weeks = df_calendar[df_calendar['date'] <= today + timedelta(weeks=8)]
                
                if not next_8_weeks.empty:
                    # Heatmap
                    fig_heatmap = px.density_heatmap(
                        next_8_weeks,
                        x='week',
                        y='day',
                        z='duration',
                        color_continuous_scale='YlOrRd',
                        labels={'week': 'Semaine', 'day': 'Jour', 'duration': 'Minutes'}
                    )
                    fig_heatmap.update_yaxes(
                        ticktext=['Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam', 'Dim'],
                        tickvals=[0, 1, 2, 3, 4, 5, 6]
                    )
                    fig_heatmap.update_layout(height=300)
                    st.plotly_chart(fig_heatmap, use_container_width=True)
                
                # Sessions du mois
                st.subheader("📆 Sessions ce mois-ci")
                current_month = today.strftime('%Y-%m')
                month_sessions = [s for s in sessions if s['date'].startswith(current_month)]
                
                if month_sessions:
                    for session in month_sessions[:10]:
                        priority_color = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}.get(session['priority'], '⚪')
                        st.markdown(f"{priority_color} **{session['day_name']} {session['date']}** - {session['duration_minutes']} min - {session['category']}")
                else:
                    st.info("Pas de sessions ce mois-ci")
        
        with tab3:
            # Graphique de progression
            st.subheader("📈 Progression prévue")
            
            if sessions:
                # Calculer la progression cumulative
                df_progress = pd.DataFrame(sessions)
                df_progress['date'] = pd.to_datetime(df_progress['date'])
                df_progress = df_progress.sort_values('date')
                df_progress['cumulative_concepts'] = df_progress['concepts'].apply(len).cumsum()
                df_progress['cumulative_hours'] = (df_progress['duration_minutes'].cumsum() / 60).round(1)
                
                # Graphique
                fig_progress = go.Figure()
                fig_progress.add_trace(go.Scatter(
                    x=df_progress['date'],
                    y=df_progress['cumulative_hours'],
                    mode='lines+markers',
                    name='Heures cumulées',
                    line=dict(color='#1E88E5', width=3),
                    fill='tozeroy',
                    fillcolor='rgba(30, 136, 229, 0.2)'
                ))
                
                # Ajouter les jalons
                milestones = revision_plan.get('milestones', [])
                for m in milestones:
                    fig_progress.add_vline(
                        x=m['date'],
                        line_dash='dash',
                        line_color='gray',
                        annotation_text=m['name'],
                        annotation_position='top'
                    )
                
                fig_progress.update_layout(
                    height=400,
                    xaxis_title='Date',
                    yaxis_title='Heures de révision',
                    hovermode='x unified'
                )
                st.plotly_chart(fig_progress, use_container_width=True)
                
                # Stats de progression
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("📚 Concepts à couvrir", len(df_progress))
                with col2:
                    avg_per_week = round(df_progress['duration_minutes'].sum() / 60 / max(1, stats.get('days_until_exam', 1) / 7), 1)
                    st.metric("⏱️ Heures/semaine (moy)", f"{avg_per_week}h")
                with col3:
                    st.metric("📅 Date examen", revision_plan.get('exam_date', 'N/A'))
        
        with tab4:
            # Liste des sessions
            st.subheader("📋 Toutes les sessions à venir")
            
            today = datetime.now().strftime('%Y-%m-%d')
            upcoming = [s for s in sessions if s['date'] >= today]
            
            # Filtres
            col1, col2 = st.columns(2)
            with col1:
                filter_priority = st.multiselect(
                    "Filtrer par priorité",
                    ['high', 'medium', 'low'],
                    default=['high', 'medium', 'low'],
                    format_func=lambda x: {'high': '🔴 Haute', 'medium': '🟡 Moyenne', 'low': '🟢 Basse'}[x]
                )
            with col2:
                num_sessions = st.slider("Nombre de sessions à afficher", 5, 50, 14)
            
            filtered = [s for s in upcoming if s['priority'] in filter_priority][:num_sessions]
            
            if filtered:
                for session in filtered:
                    priority_icon = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}.get(session['priority'], '⚪')
                    type_icon = {'new_learning': '📚', 'revision': '🔄', 'practice': '✏️'}.get(session['session_type'], '📖')
                    
                    with st.expander(f"{priority_icon} {type_icon} {session['day_name']} {session['date']} - {session['duration_minutes']} min"):
                        col1, col2 = st.columns([2, 1])
                        with col1:
                            st.markdown(f"**Catégorie:** {session['category']}")
                            st.markdown("**Concepts à étudier:**")
                            for concept in session['concepts'][:10]:
                                st.markdown(f"  - {concept}")
                            if len(session['concepts']) > 10:
                                st.caption(f"... et {len(session['concepts']) - 10} autres")
                        with col2:
                            if session.get('objectives'):
                                st.markdown("**Objectifs:**")
                                for obj in session['objectives']:
                                    st.markdown(f"  - {obj}")
            else:
                st.info("Aucune session trouvée avec ces filtres.")
        
        st.divider()
        
        # Boutons d'action
        col1, col2, col3 = st.columns(3)
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
        with col3:
            json_path = Path("exports/revision_plan.json")
            if json_path.exists():
                with open(json_path, 'r', encoding='utf-8') as f:
                    json_content = f.read()
                st.download_button(
                    "📥 Télécharger (JSON)",
                    json_content,
                    file_name="planning_revision.json",
                    mime="application/json"
                )


'''

# Lire app.py
with open('app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Trouver les lignes
start_line = None
end_line = None

for i, line in enumerate(lines):
    if 'elif page == "📆 Planning Révisions":' in line:
        start_line = i
    elif start_line is not None and line.startswith('elif page =='):
        end_line = i
        break

if start_line is None:
    print("Page non trouvee")
    exit(1)

if end_line is None:
    end_line = len(lines)

print(f"Remplacement lignes {start_line+1} a {end_line}")

# Remplacer
new_lines = lines[:start_line] + [NEW_PAGE] + lines[end_line:]

with open('app.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("OK - Page visuelle ajoutee!")
