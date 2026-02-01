"""
🎓 Interface Visuelle - Système de Révision Intelligent
========================================================
Interface web Streamlit pour gérer vos révisions
"""

import streamlit as st
import json
import os
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd

# Charger la clé API depuis .env ou secrets.toml
def get_api_key():
    if hasattr(st, 'secrets') and 'api' in st.secrets:
        return st.secrets['api'].get('GOOGLE_API_KEY', '')
    env_path = Path('.env')
    if env_path.exists():
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line.startswith('GOOGLE_API_KEY='):
                    return line.split('=', 1)[1].strip()
    return ''


# Configuration de la page
st.set_page_config(
    page_title="🎓 Révision Brevet Fédéral",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Styles CSS personnalisés
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1E88E5;
        text-align: center;
        padding: 1rem;
    }
    .stat-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    .concept-critical { border-left: 4px solid #e53935; padding-left: 10px; }
    .concept-high { border-left: 4px solid #fb8c00; padding-left: 10px; }
    .concept-medium { border-left: 4px solid #fdd835; padding-left: 10px; }
    .concept-low { border-left: 4px solid #43a047; padding-left: 10px; }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        padding: 1rem;
        border-radius: 5px;
        color: #155724;
    }
    .warning-box {
        background-color: #fff3cd;
        border: 1px solid #ffeeba;
        padding: 1rem;
        border-radius: 5px;
        color: #856404;
    }
</style>
""", unsafe_allow_html=True)


# ===== CONFIGURATION =====
import yaml

@st.cache_data
def load_config():
    config_path = Path("config/config.yaml")
    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        # Charger la clé API depuis .env ou secrets
        api_key = get_api_key()
        if api_key and config:
            if 'api' not in config:
                config['api'] = {}
            config['api']['gemini_api_key'] = api_key
        return config
    return None


def save_uploaded_file(uploaded_file, destination_folder):
    """Sauvegarde un fichier uploadé"""
    dest_path = Path(destination_folder)
    dest_path.mkdir(parents=True, exist_ok=True)
    
    file_path = dest_path / uploaded_file.name
    with open(file_path, 'wb') as f:
        f.write(uploaded_file.getbuffer())
    return file_path


def get_files_in_folder(folder_path):
    """Liste les fichiers dans un dossier"""
    path = Path(folder_path)
    if not path.exists():
        return []
    
    extensions = {'.pdf', '.docx', '.doc', '.txt', '.md'}
    files = []
    for f in path.rglob('*'):
        if f.is_file() and f.suffix.lower() in extensions:
            files.append({
                'name': f.name,
                'path': str(f),
                'size': f.stat().st_size / 1024,  # KB
                'modified': datetime.fromtimestamp(f.stat().st_mtime)
            })
    return files


def load_concept_map():
    """Charge la cartographie des concepts (local ou cloud_data)"""
    # Essayer d'abord le chemin local, puis cloud_data pour Streamlit Cloud
    for folder in ["exports", "cloud_data"]:
        path = Path(folder) / "concept_map.json"
        if path.exists():
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
    return None


def load_revision_plan():
    """Charge le planning de révision (local ou cloud_data)"""
    # Essayer d'abord le chemin local, puis cloud_data pour Streamlit Cloud
    for folder in ["exports", "cloud_data"]:
        path = Path(folder) / "revision_plan.json"
        if path.exists():
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
    return None


# ===== SIDEBAR =====
with st.sidebar:
    st.image("https://img.icons8.com/color/96/000000/graduation-cap.png", width=80)
    st.title("Navigation")
    
    page = st.radio(
        "Menu",
        ["🏠 Accueil", "📚 Mes Documents", "� Planning Cours", "🔬 Analyser", "🗺️ Concepts", "📆 Planning Révisions", "📖 Ressources", "⚙️ Paramètres"],
        index=0
    )
    
    st.divider()
    
    # Statistiques rapides
    st.subheader("📊 Aperçu rapide")
    
    cours_files = get_files_in_folder("cours")
    directives_files = get_files_in_folder("directives_examen")
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Cours", len(cours_files))
    with col2:
        st.metric("Directives", len(directives_files))
    
    concept_map = load_concept_map()
    if concept_map:
        st.metric("Concepts", len(concept_map.get('nodes', [])))
    
    st.divider()
    st.caption("v1.0 - Brevet Fédéral")


# ===== PAGES =====

if page == "🏠 Accueil":
    st.markdown('<p class="main-header">🎓 Système de Révision Intelligent</p>', unsafe_allow_html=True)
    st.markdown("### Brevet Fédéral - Spécialiste Réseaux Énergétiques")
    
    st.divider()
    
    # Étapes du workflow
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("### 1️⃣ Importer")
        st.markdown("Ajoutez vos cours et directives d'examen")
        if st.button("📚 Aller aux documents", key="btn1"):
            st.session_state['page'] = "📚 Mes Documents"
            st.rerun()
    
    with col2:
        st.markdown("### 2️⃣ Analyser")
        st.markdown("L'IA analyse vos contenus automatiquement")
        if st.button("🔬 Lancer l'analyse", key="btn2"):
            st.session_state['page'] = "🔬 Analyser"
            st.rerun()
    
    with col3:
        st.markdown("### 3️⃣ Cartographier")
        st.markdown("Visualisez les liens entre concepts")
        if st.button("🗺️ Voir les concepts", key="btn3"):
            st.session_state['page'] = "🗺️ Concepts"
            st.rerun()
    
    with col4:
        st.markdown("### 4️⃣ Planifier")
        st.markdown("Obtenez votre planning personnalisé")
        if st.button("📅 Voir le planning", key="btn4"):
            st.session_state['page'] = "📅 Planning"
            st.rerun()
    
    st.divider()
    
    # Statut actuel
    st.subheader("📋 Statut de votre préparation")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        cours_count = len(cours_files)
        if cours_count > 0:
            st.success(f"✅ {cours_count} fichiers de cours importés")
        else:
            st.warning("⚠️ Aucun cours importé")
    
    with col2:
        if concept_map and len(concept_map.get('nodes', [])) > 0:
            st.success(f"✅ {len(concept_map['nodes'])} concepts identifiés")
        else:
            st.warning("⚠️ Analyse non effectuée")
    
    with col3:
        revision_plan = load_revision_plan()
        if revision_plan:
            st.success(f"✅ Planning généré ({revision_plan.get('total_hours', 0):.1f}h)")
        else:
            st.warning("⚠️ Planning non généré")
    
    # Configuration requise
    config = load_config()
    if config:
        exam_date = config.get('user', {}).get('exam_date', '2026-06-15')
        exam_dt = datetime.strptime(exam_date, '%Y-%m-%d')
        days_left = (exam_dt - datetime.now()).days
        
        st.divider()
        
        # Temps de révision
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader(f"⏰ Compte à rebours: **{days_left} jours**")
            progress = max(0, min(100, 100 - (days_left / 365 * 100)))
            st.progress(progress / 100)
        
        with col2:
            weekday_min = config.get('planning', {}).get('weekday_minutes', 30)
            weekend_hrs = config.get('planning', {}).get('weekend_hours', 8)
            weekly_total = (weekday_min / 60 * 5) + weekend_hrs
            
            st.subheader("📚 Votre rythme de révision")
            st.markdown(f"""
            - **Semaine:** {weekday_min} min/jour (lun-ven)
            - **Week-end:** {weekend_hrs}h total
            - **= {weekly_total:.1f}h/semaine** soit **{weekly_total * 4.33:.0f}h/mois**
            """)
        
        # Modules overview
        if 'modules' in config:
            st.divider()
            modules = config['modules']
            with_content = sum(1 for m in modules.values() if isinstance(m, dict) and m.get('has_content'))
            total = len([m for m in modules.values() if isinstance(m, dict)])
            
            st.subheader(f"📊 Modules: {with_content}/{total} avec cours")
            st.progress(with_content / total if total > 0 else 0)


elif page == "📚 Mes Documents":
    st.header("📚 Gestion des Documents")
    
    # Bouton supprimer tout
    col1, col2 = st.columns([4, 1])
    with col2:
        if st.button("🗑️ Tout Supprimer", type="secondary", key="del_all"):
            if st.checkbox("✓ Confirmer", key="confirm_del"):
                try:
                    import shutil
                    deleted = 0
                    for item in Path("cours/").iterdir():
                        if item.name != "README.md":
                            if item.is_dir():
                                shutil.rmtree(item)
                            else:
                                item.unlink()
                            deleted += 1
                    st.success(f"✅ {deleted} supprimé(s)")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ {e}")
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📤 Upload", "📁 Import Dossiers", "📖 Cours", "📋 Directives", "📊 Vue Modules"])
    
    with tab1:
        st.subheader("📤 Télécharger vos documents")
        st.info("💡 Upload depuis mobile, tablette, etc.")
        
        upload_method = st.radio("Méthode :", ["📦 Fichier ZIP (tout le dossier)", "📄 Fichiers individuels"], horizontal=True)
        
        if upload_method == "📦 Fichier ZIP (tout le dossier)":
            st.markdown("""
            **Instructions :**
            1. Sur ton Mac, sélectionne le dossier complet
            2. Clic droit > "Compresser"
            3. Upload le fichier .zip ici
            """)
            
            uploaded_zip = st.file_uploader("Fichier ZIP", type=['zip'], key="zip_uploader")
            
            if uploaded_zip and st.button("📦 Extraire", type="primary", key="import_zip"):
                with st.spinner("Extraction..."):
                    try:
                        import zipfile
                        from io import BytesIO
                        
                        zip_data = BytesIO(uploaded_zip.getbuffer())
                        total = 0
                        
                        with zipfile.ZipFile(zip_data, 'r') as zip_ref:
                            for f in zip_ref.filelist:
                                if not f.is_dir() and not '__MACOSX' in f.filename:
                                    zip_ref.extract(f, 'cours/')
                                    total += 1
                        
                        st.success(f"✅ {total} fichiers extraits !")
                        st.balloons()
                    except Exception as e:
                        st.error(f"❌ {e}")
        
        else:
            uploaded_files = st.file_uploader(
                "Fichiers (plusieurs à la fois)",
                type=['pdf', 'docx', 'doc', 'xlsx', 'xls', 'pptx'],
                accept_multiple_files=True,
                key="doc_uploader"
            )
            
            if uploaded_files:
                st.write(f"📦 {len(uploaded_files)} fichier(s)")
                
                module_codes = ["AA01", "AA02", "AA03", "AA04", "AA05", "AA06", "AA07", "AA08", "AA09", "AA10",
                              "AE01", "AE02", "AE03", "AE04", "AE05", "AE06", "AE07", "AE08", "AE09", "AE10"]
                selected_module = st.selectbox("📂 Module", module_codes)
                
                if st.button("💾 Sauvegarder", type="primary", key="save_uploaded"):
                    with st.spinner("Sauvegarde..."):
                        try:
                            dest_folder = Path(f"cours/{selected_module}")
                            dest_folder.mkdir(parents=True, exist_ok=True)
                            
                            for uploaded_file in uploaded_files:
                                file_path = dest_folder / uploaded_file.name
                                with open(file_path, 'wb') as f:
                                    f.write(uploaded_file.getbuffer())
                            
                            st.success(f"✅ {len(uploaded_files)} sauvegardé(s) !")
                            st.balloons()
                        except Exception as e:
                            st.error(f"❌ {e}")
    with tab2:
        st.subheader("📁 Importer vos dossiers de formation")
        
        # Aide pour obtenir le chemin sur Mac
        with st.expander("❓ Comment obtenir le chemin de mon dossier sur Mac ?", expanded=False):
            st.markdown("""
            ### 🍎 3 méthodes pour copier le chemin complet :
            
            #### ⭐ **Méthode 1 : Clic droit + Option (LA PLUS RAPIDE)**
            1. Faites un **clic droit** sur votre dossier
            2. Maintenez la touche **⌥ Option** enfoncée
            3. Cliquez sur **"Copier ... comme nom de chemin"**
            4. Collez ici avec ⌘ Cmd + V
            
            #### 🖱️ **Méthode 2 : Glisser-déposer**
            1. Glissez votre dossier directement dans le champ ci-dessous
            2. Le chemin apparaîtra automatiquement
            
            #### ℹ️ **Méthode 3 : Lire les informations**
            1. Sélectionnez le dossier
            2. Appuyez sur **⌘ Cmd + I**
            3. Copiez le chemin dans "Emplacement"
            4. Ajoutez `/Nom_du_dossier` à la fin
            
            ---
            **Exemple de chemin valide :**
            ```
            /Users/gabrielmoustadrif/Documents/Brevets Fédéral Electricité
            ```
            """)
        
        st.markdown("""
        **Instructions :**
        1. Utilisez une des méthodes ci-dessus pour obtenir le chemin
        2. Le système détectera automatiquement les modules avec/sans contenu
        3. Les dossiers seront copiés et organisés
        """)
        
        # Chemin du dossier source
        source_path = st.text_input(
            "📂 Chemin complet du dossier (glissez-déposez ou collez)",
            placeholder="/Users/gabrielmoustadrif/Documents/Brevets Fédéral Electricité",
            help="Utilisez ⌥ Option + Clic droit > 'Copier comme nom de chemin' sur votre dossier"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            copy_files = st.checkbox("Copier les fichiers", value=True, 
                                     help="Décocher pour créer des liens symboliques (économise l'espace)")
        with col2:
            include_empty = st.checkbox("Inclure dossiers vides", value=True,
                                       help="Créer les dossiers même s'ils n'ont pas encore de cours")
        
        if source_path and st.button("🚀 Scanner et Importer", type="primary", use_container_width=True):
            # Nettoyer le chemin (enlever guillemets, espaces en début/fin)
            source_path_clean = source_path.strip().strip("'").strip('"')
            
            if Path(source_path_clean).exists():
                with st.spinner("Analyse des dossiers en cours..."):
                    try:
                        import sys
                        sys.path.insert(0, str(Path.cwd()))
                        from src.folder_importer import FolderImporter, calculate_study_time
                        
                        config = load_config()
                        importer = FolderImporter(config)
                        
                        # Scanner
                        modules = importer.scan_source_folder(source_path_clean)
                        
                        st.success(f"✅ {len(modules)} modules détectés!")
                        
                        # Afficher le résumé
                        status = importer.get_modules_status()
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("📚 Avec contenu", len(status['with_content']))
                        with col2:
                            st.metric("📭 Sans contenu", len(status['empty']))
                        with col3:
                            total_files = sum(m.file_count for m in modules)
                            st.metric("📄 Fichiers total", total_files)
                        
                        st.divider()
                        
                        # Liste des modules
                        st.subheader("📋 Modules détectés")
                        
                        for module in sorted(modules, key=lambda x: (x.category, x.order)):
                            icon = "✅" if module.has_content else "🔴"
                            cat_icon = "📘" if module.category == "base" else "📙"
                            
                            with st.expander(f"{icon} {cat_icon} {module.code} - {module.name} ({module.file_count} fichiers)"):
                                st.write(f"**Catégorie:** {'Base (AA)' if module.category == 'base' else 'Avancé (AE)'}")
                                st.write(f"**Fichiers:** {module.file_count}")
                                st.write(f"**Taille:** {module.total_size_kb:.1f} KB")
                                if module.files:
                                    st.write("**Contenu:**")
                                    for f in module.files[:10]:
                                        st.caption(f"  • {f}")
                                    if len(module.files) > 10:
                                        st.caption(f"  ... et {len(module.files) - 10} autres fichiers")
                        
                        st.divider()
                        
                        # Bouton pour confirmer l'import
                        if st.button("✅ Confirmer l'import", type="primary"):
                            with st.spinner("Copie des fichiers en cours..."):
                                report = importer.import_folders(
                                    source_path_clean, 
                                    "cours",
                                    copy_mode=copy_files
                                )
                                
                                # Mettre à jour la config
                                importer.update_config_modules("config/config.yaml")
                                
                                st.success(f"✅ Import terminé!")
                                st.write(f"- {len(report['modules_imported'])} modules avec contenu")
                                st.write(f"- {len(report['modules_empty'])} modules en attente de cours")
                                st.write(f"- {report['total_files']} fichiers copiés")
                                st.balloons()
                                
                    except Exception as e:
                        st.error(f"Erreur: {e}")
                        st.exception(e)
            else:
                st.error(f"❌ Le dossier n'existe pas: {source_path_clean}")
                st.info("💡 Vérifiez que le chemin est correct. Essayez de glisser-déposer le dossier dans le champ ci-dessus.")
        
        # Afficher les modules déjà configurés
        st.divider()
        st.subheader("📊 Modules configurés")
        
        config = load_config()
        if config and 'modules' in config:
            modules_config = config['modules']
            
            # Créer un dataframe
            data = []
            for code, info in sorted(modules_config.items()):
                if isinstance(info, dict):
                    data.append({
                        'Code': code,
                        'Nom': info.get('name', ''),
                        'Statut': '✅ Cours' if info.get('has_content') else '🔴 En attente',
                        'Catégorie': 'Base' if code.startswith('AA') else 'Avancé'
                    })
            
            if data:
                df = pd.DataFrame(data)
                st.dataframe(df, use_container_width=True, hide_index=True)
    
    with tab2:
        st.subheader("📖 Fichiers de cours importés")
        
        cours_files = get_files_in_folder("cours")
        if cours_files:
            # Grouper par module
            modules_dict = {}
            for f in cours_files:
                parts = Path(f['path']).parts
                for part in parts:
                    if part.startswith('AA') or part.startswith('AE'):
                        module = part
                        break
                else:
                    module = 'Autres'
                
                if module not in modules_dict:
                    modules_dict[module] = []
                modules_dict[module].append(f)
            
            for module, files in sorted(modules_dict.items()):
                with st.expander(f"📁 {module} ({len(files)} fichiers)"):
                    df = pd.DataFrame(files)
                    df['size'] = df['size'].round(1).astype(str) + ' KB'
                    df['modified'] = df['modified'].dt.strftime('%d/%m/%Y')
                    st.dataframe(df[['name', 'size', 'modified']], use_container_width=True, hide_index=True)
        else:
            st.info("Aucun cours importé. Utilisez l'onglet 'Import Dossiers' pour commencer.")
    
    with tab3:
        st.subheader("Importer les directives d'examen")
        
        uploaded_directives = st.file_uploader(
            "Glissez les directives officielles ici",
            type=['pdf', 'docx', 'doc', 'txt', 'md'],
            accept_multiple_files=True,
            key="directives_uploader"
        )
        
        if uploaded_directives:
            for file in uploaded_directives:
                save_uploaded_file(file, "directives_examen")
                st.success(f"✅ {file.name} importé avec succès!")
        
        st.divider()
        st.subheader("Directives importées")
        
        directives_files = get_files_in_folder("directives_examen")
        if directives_files:
            df = pd.DataFrame(directives_files)
            df['size'] = df['size'].round(1).astype(str) + ' KB'
            df['modified'] = df['modified'].dt.strftime('%d/%m/%Y %H:%M')
            st.dataframe(df[['name', 'size', 'modified']], use_container_width=True)
        else:
            st.info("Aucune directive importée.")
    
    with tab4:
        st.subheader("📊 Vue d'ensemble des modules")
        
        config = load_config()
        if config and 'modules' in config:
            modules_config = config['modules']
            
            # Statistiques
            total = len(modules_config)
            with_content = sum(1 for m in modules_config.values() if isinstance(m, dict) and m.get('has_content'))
            without_content = total - with_content
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("📚 Total modules", total)
            with col2:
                st.metric("✅ Avec cours", with_content)
            with col3:
                st.metric("🔴 Sans cours", without_content)
            with col4:
                progress = (with_content / total * 100) if total > 0 else 0
                st.metric("📈 Progression", f"{progress:.0f}%")
            
            st.divider()
            
            # Temps d'étude
            st.subheader("⏰ Votre temps de révision")
            
            weekday_min = config.get('planning', {}).get('weekday_minutes', 30)
            weekend_hrs = config.get('planning', {}).get('weekend_hours', 8)
            
            weekly_total = (weekday_min / 60 * 5) + weekend_hrs
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.info(f"📅 **Semaine:** {weekday_min} min/jour")
            with col2:
                st.info(f"🗓️ **Week-end:** {weekend_hrs}h total")
            with col3:
                st.success(f"📊 **Total hebdo:** {weekly_total:.1f}h")
            
            st.caption(f"Soit environ {weekly_total * 4.33:.0f}h par mois")
            
            st.divider()
            
            # Grille des modules
            st.subheader("📋 État des modules")
            
            # Modules de base (AA)
            st.markdown("#### 📘 Modules de base (AA)")
            aa_modules = {k: v for k, v in modules_config.items() if k.startswith('AA') and isinstance(v, dict)}
            
            cols = st.columns(4)
            for i, (code, info) in enumerate(sorted(aa_modules.items())):
                with cols[i % 4]:
                    status = "✅" if info.get('has_content') else "🔴"
                    st.markdown(f"{status} **{code}**")
                    st.caption(info.get('name', '')[:20])
            
            st.markdown("#### 📙 Modules avancés (AE)")
            ae_modules = {k: v for k, v in modules_config.items() if k.startswith('AE') and isinstance(v, dict)}
            
            cols = st.columns(4)
            for i, (code, info) in enumerate(sorted(ae_modules.items())):
                with cols[i % 4]:
                    status = "✅" if info.get('has_content') else "🔴"
                    st.markdown(f"{status} **{code}**")
                    st.caption(info.get('name', '')[:20])
        else:
            st.info("Importez vos dossiers dans l'onglet 'Import Dossiers' pour voir la vue d'ensemble.")


elif page == "� Planning Cours":
    st.header("📅 Planning de Formation")
    
    st.markdown("""
    **Objectif :** Renseigner votre calendrier de formation pour que le système sache:
    - Ce que vous avez déjà vu en cours
    - Ce qui n'a pas encore été enseigné
    - Quand réviser (seulement après avoir vu le cours)
    """)
    
    import sys
    sys.path.insert(0, str(Path.cwd()))
    from src.course_schedule_manager import CourseScheduleManager, CourseSession
    
    config = load_config()
    schedule_manager = CourseScheduleManager(config)
    schedule_manager.load()
    
    tab1, tab2, tab3 = st.tabs(["➕ Ajouter Sessions", "📋 Mon Planning", "📊 Progression"])
    
    with tab1:
        st.subheader("Ajouter des sessions de cours")
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.markdown("### 📝 Saisie manuelle")
            
            # Sélectionner le module
            if 'modules' in config:
                module_options = [f"{code} - {info.get('name', '')}" 
                                for code, info in config['modules'].items() 
                                if isinstance(info, dict)]
                selected_module = st.selectbox("Module", module_options)
                module_code = selected_module.split(' - ')[0]
            else:
                module_code = st.text_input("Code module (ex: AA01)")
            
            session_date = st.date_input("Date du cours", value=datetime.now())
            duration = st.number_input("Durée (heures)", min_value=0.5, max_value=12.0, value=4.0, step=0.5)
            
            topics_input = st.text_area(
                "Thèmes abordés (un par ligne)", 
                placeholder="Loi d'Ohm\nPuissance électrique\nCircuits en série"
            )
            topics = [t.strip() for t in topics_input.split('\n') if t.strip()]
            
            if st.button("➕ Ajouter cette session", type="primary"):
                session = schedule_manager.parse_manual_input({
                    'module': module_code,
                    'date': datetime.combine(session_date, datetime.min.time()),
                    'duration': duration,
                    'topics': topics,
                    'status': 'planned' if datetime.combine(session_date, datetime.min.time()) > datetime.now() else 'completed'
                })
                schedule_manager.save()
                st.success(f"✅ Session {module_code} ajoutée pour le {session_date.strftime('%d.%m.%Y')}")
                st.rerun()
        
        with col2:
            st.markdown("### 📤 Import depuis Excel")
            
            st.markdown("""
            **Format Excel attendu:**
            
            | Date | Module | Durée | Thèmes |
            |------|--------|-------|--------|
            | 15.02.2026 | AA01 | 4 | Introduction, Bases |
            | 22.02.2026 | AA01 | 4 | Suite du module |
            
            Les colonnes peuvent être nommées différemment (date/jour, module/cours, durée/h, thèmes/sujets).
            """)
            
            # Vérifier si des sessions existent déjà
            if schedule_manager.sessions:
                st.warning(f"⚠️ Attention : {len(schedule_manager.sessions)} sessions sont déjà enregistrées.")
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.info("Si vous importez un nouveau fichier, les sessions existantes seront **écrasées**.")
                with col2:
                    if st.button("🗑️ Effacer tout", type="secondary"):
                        schedule_manager.sessions = []
                        schedule_manager.save()
                        st.success("✅ Toutes les sessions ont été supprimées")
                        st.rerun()
            
            uploaded_excel = st.file_uploader(
                "Importer un fichier Excel (.xlsx)",
                type=['xlsx', 'xls'],
                key="schedule_uploader"
            )
            
            if uploaded_excel:
                # Vérifier si un fichier a déjà été importé
                if schedule_manager.sessions and not st.session_state.get('confirm_reimport', False):
                    st.error("❌ Un planning est déjà chargé ! Cliquez sur '🗑️ Effacer tout' ci-dessus pour réimporter.")
                else:
                    try:
                        # Sauvegarder temporairement
                        temp_path = Path("data/temp_schedule.xlsx")
                        temp_path.parent.mkdir(parents=True, exist_ok=True)
                        with open(temp_path, 'wb') as f:
                            f.write(uploaded_excel.getbuffer())
                        
                        # Parser
                        sessions = schedule_manager.parse_excel_schedule(str(temp_path))
                        schedule_manager.save()
                        
                        st.success(f"✅ {len(sessions)} sessions importées!")
                        
                        # Aperçu
                        st.markdown("**Aperçu:**")
                        for s in sessions[:5]:
                            st.write(f"• {s.date.strftime('%d.%m.%Y')} - {s.module_code} ({s.duration_hours}h)")
                        if len(sessions) > 5:
                            st.caption(f"... et {len(sessions) - 5} autres sessions")
                        
                        temp_path.unlink()
                        st.session_state['confirm_reimport'] = False
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"Erreur lors de l'import: {e}")
                        st.exception(e)
    
    with tab2:
        st.subheader("📋 Mes sessions de cours")
        
        if not schedule_manager.sessions:
            st.info("Aucune session enregistrée. Ajoutez votre première session dans l'onglet 'Ajouter Sessions'.")
        else:
            # Filtres
            col1, col2, col3 = st.columns(3)
            
            with col1:
                filter_status = st.selectbox(
                    "Statut",
                    ["Toutes", "Passées", "À venir"],
                    index=0
                )
            
            with col2:
                all_modules = sorted(set(s.module_code for s in schedule_manager.sessions))
                filter_module = st.multiselect(
                    "Modules",
                    all_modules,
                    default=all_modules
                )
            
            with col3:
                sort_by = st.selectbox(
                    "Trier par",
                    ["Date (récent)", "Date (ancien)", "Module"],
                    index=0
                )
            
            # Appliquer les filtres
            filtered_sessions = schedule_manager.sessions
            
            if filter_status == "Passées":
                filtered_sessions = schedule_manager.get_completed_sessions()
            elif filter_status == "À venir":
                filtered_sessions = schedule_manager.get_upcoming_sessions()
            
            if filter_module:
                filtered_sessions = [s for s in filtered_sessions if s.module_code in filter_module]
            
            # Trier
            if sort_by == "Date (récent)":
                filtered_sessions = sorted(filtered_sessions, key=lambda s: s.date, reverse=True)
            elif sort_by == "Date (ancien)":
                filtered_sessions = sorted(filtered_sessions, key=lambda s: s.date)
            else:
                filtered_sessions = sorted(filtered_sessions, key=lambda s: (s.module_code, s.date))
            
            st.divider()
            
            # Afficher les sessions
            for idx, session in enumerate(filtered_sessions):
                is_past = session.date <= datetime.now()
                status_icon = "✅" if is_past else "📅"
                date_str = session.date.strftime("%d.%m.%Y")
                
                with st.expander(f"{status_icon} {session.module_code} - {date_str} ({session.duration_hours}h)"):
                    st.markdown(f"**Module:** {session.module_code} - {session.module_name}")
                    st.markdown(f"**Date:** {date_str}")
                    st.markdown(f"**Durée:** {session.duration_hours}h")
                    st.markdown(f"**Statut:** {'Cours passé' if is_past else 'À venir'}")
                    
                    if session.topics:
                        st.markdown("**Thèmes:**")
                        for topic in session.topics:
                            st.write(f"  • {topic}")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("🗑️ Supprimer", key=f"del_{idx}_{session.date}_{session.module_code}"):
                            schedule_manager.sessions.remove(session)
                            schedule_manager.save()
                            st.rerun()
    
    with tab3:
        st.subheader("📊 Progression par module")
        
        if not schedule_manager.sessions:
            st.info("Ajoutez des sessions pour voir la progression.")
        else:
            # Récupérer tous les modules
            modules = sorted(set(s.module_code for s in schedule_manager.sessions))
            
            for module_code in modules:
                progress = schedule_manager.get_module_progress(module_code)
                
                # Nom du module
                module_name = ""
                if 'modules' in config and module_code in config['modules']:
                    module_info = config['modules'][module_code]
                    if isinstance(module_info, dict):
                        module_name = module_info.get('name', '')
                
                with st.expander(f"📚 {module_code} - {module_name}", expanded=True):
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("Sessions totales", progress['total_sessions'])
                    with col2:
                        st.metric("Complétées", progress['completed'])
                    with col3:
                        st.metric("À venir", progress['upcoming'])
                    with col4:
                        st.metric("Heures totales", f"{progress['total_hours']:.1f}h")
                    
                    st.progress(progress['progress_percent'] / 100)
                    st.caption(f"{progress['progress_percent']:.0f}% complété")
                    
                    if progress['next_session']:
                        next_s = progress['next_session']
                        st.info(f"📅 Prochaine session: {next_s.date.strftime('%d.%m.%Y')} ({next_s.duration_hours}h)")


elif page == "🔬 Analyser":
    st.header("🔬 Analyse IA des Documents")
    
    st.markdown("""
    Cette étape va :
    1. **Scanner** tous vos documents
    2. **Extraire** les concepts clés avec l'IA
    3. **Identifier** ce qui est demandé aux examens
    4. **Mapper** les cours aux exigences
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        cours_files = get_files_in_folder("cours")
        st.metric("Documents de cours", len(cours_files))
    
    with col2:
        directives_files = get_files_in_folder("directives_examen")
        st.metric("Directives d'examen", len(directives_files))
    
    st.divider()
    
    # Afficher les modules qui seront analysés
    config = load_config()
    if config and 'modules' in config:
        modules_to_analyze = {
            code: info for code, info in config['modules'].items()
            if isinstance(info, dict) and info.get('has_content', False)
        }
        
        st.subheader("📚 Modules qui seront analysés")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**📘 Base (AA):**")
            aa_mods = [f"{code} - {info.get('name', '')}" for code, info in sorted(modules_to_analyze.items()) if code.startswith('AA')]
            for mod in aa_mods:
                st.write(f"✅ {mod}")
        
        with col2:
            st.markdown("**📙 Avancé (AE):**")
            ae_mods = [f"{code} - {info.get('name', '')}" for code, info in sorted(modules_to_analyze.items()) if code.startswith('AE')]
            for mod in ae_mods:
                st.write(f"✅ {mod}")
        
        st.divider()
    
    if len(cours_files) == 0:
        st.warning("⚠️ Veuillez d'abord importer vos documents dans l'onglet 'Mes Documents'")
    else:
        st.info("🤖 **Gemini 2.5 Pro** sera utilisé pour l'analyse (délai de 2s entre chaque document)")
        
        if st.button("🚀 Lancer l'analyse IA", type="primary", use_container_width=True):
            
            with st.spinner("Analyse en cours... Cela peut prendre quelques minutes."):
                try:
                    # Import des modules
                    import sys
                    sys.path.insert(0, str(Path.cwd()))
                    
                    from src.scanner import DocumentScanner
                    from src.analyzer import ContentAnalyzer
                    from src.concept_mapper import ConceptMapper
                    
                    config = load_config()
                    
                    # Étape 1: Scan
                    st.info("📂 Scan des documents...")
                    scanner = DocumentScanner(config)
                    results = scanner.scan_all()
                    
                    total_docs = sum(len(docs) for docs in results.values())
                    st.success(f"✅ {total_docs} documents scannés")
                    
                    # Étape 2: Analyse IA
                    st.info("🤖 Analyse IA en cours...")
                    analyzer = ContentAnalyzer(config)
                    
                    all_concepts = []
                    
                    cours_docs = scanner.get_documents_by_category('cours')
                    
                    # Afficher les modules trouvés
                    modules_found = {}
                    for doc in cours_docs:
                        if doc.module:
                            if doc.module not in modules_found:
                                modules_found[doc.module] = []
                            modules_found[doc.module].append(doc.filename)
                    
                    if modules_found:
                        st.info(f"📚 {len(modules_found)} modules détectés: {', '.join(sorted(modules_found.keys()))}")
                    
                    # Barre de progression avec %
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    for i, doc in enumerate(cours_docs):
                        percent = int(((i + 1) / len(cours_docs)) * 100)
                        status_text.text(f"⏳ Analyse en cours... {i+1}/{len(cours_docs)} documents ({percent}%)")
                        
                        concepts = analyzer.analyze_course_document(
                            doc.content, 
                            doc.filename, 
                            doc.module
                        )
                        all_concepts.extend(concepts)
                        progress_bar.progress((i + 1) / len(cours_docs))
                    
                    # Clear progress et afficher succès
                    status_text.empty()
                    progress_bar.empty()
                    
                    st.success(f"✅ {len(all_concepts)} concepts identifiés")
                    
                    # Étape 3: Cartographie
                    st.info("🗺️ Création de la cartographie...")
                    mapper = ConceptMapper(config)
                    mapper.build_from_concepts(all_concepts)
                    mapper.export_to_json("exports/concept_map.json")
                    
                    # Etape 4: Generation automatique du planning
                    st.info("📆 Generation du planning de revision...")
                    from src.revision_planner import auto_generate_planning
                    planning_result = auto_generate_planning(config)
                    
                    if planning_result['success']:
                        st.success(f"Planning genere: {planning_result['total_sessions']} sessions, {planning_result['total_hours']}h de revision")
                    else:
                        st.warning(f"Erreur planning: {planning_result.get('error', 'Inconnu')}")
                    
                    st.success("Analyse et planning termines!")
                    st.balloons()
                    
                except Exception as e:
                    st.error(f"❌ Erreur lors de l'analyse: {str(e)}")
                    st.exception(e)


elif page == "🗺️ Concepts":
    st.header("🗺️ Cartographie des Concepts")
    
    concept_map = load_concept_map()
    
    if not concept_map:
        st.warning("⚠️ Aucune analyse effectuée. Lancez d'abord l'analyse dans l'onglet 'Analyser'.")
    else:
        nodes = concept_map.get('nodes', [])
        
        # Statistiques
        col1, col2, col3, col4 = st.columns(4)
        
        critical_count = len([n for n in nodes if n.get('importance') == 'critical'])
        high_count = len([n for n in nodes if n.get('importance') == 'high'])
        exam_relevant = len([n for n in nodes if n.get('exam_relevant')])
        
        with col1:
            st.metric("Total Concepts", len(nodes))
        with col2:
            st.metric("🔴 Critiques", critical_count)
        with col3:
            st.metric("🟠 Importants", high_count)
        with col4:
            st.metric("📝 Liés à l'examen", exam_relevant)
        
        st.divider()
        
        # Filtres
        col1, col2, col3 = st.columns(3)
        with col1:
            importance_filter = st.multiselect(
                "Filtrer par importance",
                ['critical', 'high', 'medium', 'low'],
                default=['critical', 'high']
            )
        with col2:
            exam_only = st.checkbox("Uniquement liés à l'examen", value=True)
        
        with col3:
            # Filtrer par module
            all_modules = sorted(set(n.get('module') for n in nodes if n.get('module')))
            selected_modules = st.multiselect(
                "Filtrer par module",
                all_modules,
                default=all_modules if all_modules else []
            )
        
        # Liste des concepts
        st.subheader("📋 Liste des concepts")
        
        filtered_nodes = nodes
        if importance_filter:
            filtered_nodes = [n for n in filtered_nodes if n.get('importance') in importance_filter]
        if exam_only:
            filtered_nodes = [n for n in filtered_nodes if n.get('exam_relevant')]
        if selected_modules:
            filtered_nodes = [n for n in filtered_nodes if n.get('module') in selected_modules]
        
        # Grouper par module
        concepts_by_module = {}
        for node in filtered_nodes:
            module = node.get('module', 'Sans module')
            if module not in concepts_by_module:
                concepts_by_module[module] = []
            concepts_by_module[module].append(node)
        
        for module, concepts in sorted(concepts_by_module.items()):
            with st.expander(f"📚 {module} ({len(concepts)} concepts)", expanded=(len(concepts_by_module) <= 3)):
                for node in concepts:
                    importance = node.get('importance', 'medium')
                    icon = {'critical': '🔴', 'high': '🟠', 'medium': '🟡', 'low': '🟢'}.get(importance, '⚪')
                    exam_icon = '📝' if node.get('exam_relevant') else ''
                    
                    with st.container():
                        st.markdown(f"### {icon} {node.get('name', 'Concept')} {exam_icon}")
                        st.markdown(f"**Catégorie:** {node.get('category', 'N/A')}")
                        st.markdown(f"**Importance:** {importance}")
                        
                        prereqs = node.get('prerequisites', [])
                        if prereqs:
                            st.markdown(f"**Prérequis:** {', '.join(prereqs)}")
                        
                        deps = node.get('dependents', [])
                        if deps:
                            st.markdown(f"**Concepts dépendants:** {', '.join(deps)}")
                        
                        st.divider()
        
        # Ordre d'apprentissage
        st.divider()
        st.subheader("📚 Ordre d'apprentissage recommandé")
        
        learning_order = concept_map.get('learning_order', [])
        if learning_order:
            for i, concept in enumerate(learning_order[:20], 1):
                st.markdown(f"{i}. {concept}")
            if len(learning_order) > 20:
                st.caption(f"... et {len(learning_order) - 20} autres concepts")


elif page == "📆 Planning Révisions":
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
            categories = revision_plan.get('categories', {})
            if categories and isinstance(categories, dict):
                # categories est un dict {nom_categorie: [liste de concepts]}
                cat_counts = {cat: len(concepts) for cat, concepts in categories.items()}
                # Trier par nombre de concepts et prendre le top 10
                sorted_cats = sorted(cat_counts.items(), key=lambda x: x[1], reverse=True)[:10]
                # Créer un DataFrame pour le graphique
                df_cats = pd.DataFrame({
                    'categorie': [c[0] for c in sorted_cats],
                    'count': [c[1] for c in sorted_cats]
                })
                fig_cats = px.bar(
                    df_cats,
                    x='count',
                    y='categorie',
                    orientation='h',
                    color='count',
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
                    try:
                        milestone_date = pd.to_datetime(m['date'])
                        fig_progress.add_vline(
                            x=milestone_date,
                            line_dash='dash',
                            line_color='gray',
                            annotation_text=m.get('name', ''),
                            annotation_position='top'
                        )
                    except Exception:
                        pass  # Ignorer les dates invalides
                
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


elif page == "📖 Ressources":
    st.header("📖 Ressources et Guides")
    
    tab1, tab2, tab3, tab4 = st.tabs(["📘 Guide Complet", "🏫 CIFER Info", "🎴 Flashcards", "📐 Formules"])
    
    with tab1:
        st.subheader("📘 Guide Brevet Fédéral")
        guide_path = Path("docs/GUIDE_BREVET_FEDERAL.md")
        if guide_path.exists():
            with open(guide_path, 'r', encoding='utf-8') as f:
                guide_content = f.read()
            st.markdown(guide_content)
        else:
            st.warning("Guide non disponible")
    
    with tab2:
        st.subheader("🏫 CIFER - Centre de Formation Officiel")
        st.markdown("""
### Brevet Fédéral de Spécialiste de Réseau - Orientation Énergie

**CIFER** (Centre Intercantonal de Formation des Électriciens de Réseau) est l'organisme 
officiel de formation pour le brevet fédéral en Suisse romande.

#### 📍 Coordonnées
| Information | Détails |
|-------------|---------|
| **Adresse** | Chemin de l'Islettaz 9, 1305 Penthalaz |
| **Téléphone** | +41 21 863 11 80 |
| **Email** | formation@cifer.ch |
| **Site web** | [cifer.ch](https://cifer.ch/formations-certifiantes/#13111) |

#### 📅 Calendrier Formation 2025-2027
| Étape | Date |
|-------|------|
| Cours d'accompagnement (facultatifs) | Automne 2026 |
| Concours d'entrée | Printemps 2027 |
| Début cours préparatoires | Automne 2027 |
| **Examen final** | **Mars 2029** |

#### 📋 Documents Officiels
- [Règlement d'examen](https://www.netzelektriker.ch/sites/default/files/2022-07/R%C3%A8glement%20EP%20du%2001.01.2024.pdf)
- [Directives d'examen](https://www.netzelektriker.ch/sites/default/files/2022-07/Directives%20EP%20du%2001.01.2024.pdf)
- [Conditions d'admission](https://cifer.ch/wp-content/uploads/2024/11/FSB-Conditions-dadmission-25-27_v.01.pdf)
- [Info cours préparatoires](https://cifer.ch/wp-content/uploads/2024/11/FSB-Information-cours-preparatoires-25-27_V01.pdf)

#### 💰 Subventions
Des subventions peuvent couvrir jusqu'à **50% des coûts** :
- **SEFRI** : Subvention fédérale
- **FONPRO** : Canton de Vaud
        """)
    
    with tab3:
        st.subheader("🎴 Flashcards d'Étude")
        flashcards_path = Path("docs/FLASHCARDS.md")
        if flashcards_path.exists():
            with open(flashcards_path, 'r', encoding='utf-8') as f:
                flashcards_content = f.read()
            
            # Mode d'affichage
            mode = st.radio("Mode d'affichage", ["📖 Lecture complète", "🎯 Mode Quiz"], horizontal=True)
            
            if mode == "📖 Lecture complète":
                st.markdown(flashcards_content)
            else:
                # Mode Quiz interactif
                st.markdown("### 🎯 Testez vos connaissances!")
                
                # Parser les flashcards
                import re
                flashcard_pattern = r'\*\*Question:\*\* (.*?)\n\*\*Réponse:\*\* (.*?)(?=\n---|\n\n##|\Z)'
                matches = re.findall(flashcard_pattern, flashcards_content, re.DOTALL)
                
                if matches:
                    import random
                    if 'current_card' not in st.session_state:
                        st.session_state.current_card = 0
                        st.session_state.show_answer = False
                        st.session_state.shuffled = list(range(len(matches)))
                        random.shuffle(st.session_state.shuffled)
                    
                    idx = st.session_state.shuffled[st.session_state.current_card % len(matches)]
                    question, answer = matches[idx]
                    
                    st.progress((st.session_state.current_card + 1) / len(matches))
                    st.caption(f"Carte {st.session_state.current_card + 1} / {len(matches)}")
                    
                    st.markdown(f"### ❓ {question.strip()}")
                    
                    col1, col2, col3 = st.columns([1, 1, 1])
                    
                    with col1:
                        if st.button("👁️ Voir la réponse"):
                            st.session_state.show_answer = True
                    
                    with col2:
                        if st.button("➡️ Carte suivante"):
                            st.session_state.current_card += 1
                            st.session_state.show_answer = False
                            st.rerun()
                    
                    with col3:
                        if st.button("🔀 Mélanger"):
                            random.shuffle(st.session_state.shuffled)
                            st.session_state.current_card = 0
                            st.session_state.show_answer = False
                            st.rerun()
                    
                    if st.session_state.show_answer:
                        st.success(f"**Réponse:** {answer.strip()}")
                else:
                    st.warning("Aucune flashcard trouvée dans le fichier")
        else:
            st.warning("Flashcards non disponibles")
    
    with tab4:
        st.subheader("📐 Formules Essentielles")
        formules_path = Path("docs/FORMULES_ESSENTIELLES.md")
        if formules_path.exists():
            with open(formules_path, 'r', encoding='utf-8') as f:
                formules_content = f.read()
            st.markdown(formules_content)
        else:
            st.warning("Formules non disponibles")
    
    st.divider()
    
    # Section Conseils Pratiques
    st.subheader("💡 Conseils du jour")
    
    tips = [
        "🧠 **Répétition espacée**: Révisez une notion à J+1, J+3, J+7, J+14, J+30 pour une mémorisation optimale.",
        "📚 **Technique Pomodoro**: 25 min de travail concentré, puis 5 min de pause. Répétez 4 fois, puis pause longue.",
        "✍️ **Rappel actif**: Fermez vos notes et essayez de vous souvenir plutôt que de relire passivement.",
        "🗣️ **Technique Feynman**: Expliquez un concept comme si vous l'enseigniez à un enfant de 10 ans.",
        "😴 **Sommeil**: Dormez 8h par nuit - le cerveau consolide les apprentissages pendant le sommeil.",
        "🏃 **Exercice**: L'activité physique améliore la mémoire et réduit le stress.",
        "📅 **Régularité**: Mieux vaut 1h par jour que 7h le dimanche.",
        "👥 **Groupe d'étude**: Révisez avec 2-3 collègues pour s'entraider et se motiver."
    ]
    
    import random
    daily_tip = tips[datetime.now().day % len(tips)]
    st.info(daily_tip)


elif page == "⚙️ Paramètres":
    st.header("⚙️ Paramètres")
    
    config = load_config()
    
    tab_api, tab_planning, tab_drive = st.tabs(["🔑 API", "📅 Planning", "☁️ Google Drive"])
    
    with tab_api:
        if config:
            st.subheader("🔑 Configuration API")
            
            api_key = st.text_input(
                "Clé API Google Gemini",
                value=config['api'].get('gemini_api_key', ''),
                type="password"
            )
            
            model = st.selectbox(
                "Modèle IA",
                ["gemini-2.0-flash", "gemini-1.5-pro", "gemini-1.5-flash"],
                index=0
            )
            
            if st.button("💾 Sauvegarder API", type="primary"):
                config['api']['gemini_api_key'] = api_key
                config['api']['model'] = model
                
                with open("config/config.yaml", 'w', encoding='utf-8') as f:
                    yaml.dump(config, f, allow_unicode=True, default_flow_style=False)
                
                st.success("✅ Configuration API sauvegardée!")
                st.cache_data.clear()
    
    with tab_planning:
        if config:
            st.subheader("📅 Dates importantes")
            
            exam_date = st.date_input(
                "Date de l'examen",
                value=datetime.strptime(config['user'].get('exam_date', '2029-03-01'), '%Y-%m-%d')
            )
            
            st.divider()
            st.subheader("⏱️ Planning")
            
            hours_per_day = st.slider(
                "Heures de révision par jour",
                min_value=0.5,
                max_value=8.0,
                value=float(config['planning'].get('default_hours_per_day', 2)),
                step=0.5
            )
            
            if st.button("💾 Sauvegarder Planning", type="primary"):
                config['user']['exam_date'] = exam_date.strftime('%Y-%m-%d')
                config['planning']['default_hours_per_day'] = hours_per_day
                
                with open("config/config.yaml", 'w', encoding='utf-8') as f:
                    yaml.dump(config, f, allow_unicode=True, default_flow_style=False)
                
                st.success("✅ Planning sauvegardé!")
                st.cache_data.clear()
    
    with tab_drive:
        st.subheader("☁️ Synchronisation Google Drive")
        
        st.markdown("""
### 📂 Comment ça fonctionne ?

Tes fichiers de cours sont stockés sur **Google Drive** pour:
- 📱 Accéder depuis n'importe quel appareil
- 💾 Sauvegarde automatique (2 To disponibles)
- 🔄 Synchronisation en temps réel

### 🗂️ Structure sur Google Drive

```
Mon Drive/
└── Brevets_Federal_Backup/
    ├── cours/                    ← Tes PDFs de cours (1.6 GB)
    ├── Brevets Fédéral.../       ← Documents originaux
    ├── directives_examen/        ← Directives officielles
    ├── exports/                  ← Planning exporté
    ├── data/                     ← Base de données
    └── config/                   ← Configuration
```

### 🔗 Mode de fonctionnement

| Mode | Description |
|------|-------------|
| **🔗 Lien Drive** | L'app lit directement depuis Drive (recommandé) |
| **📁 Copie locale** | Fichiers copiés sur ton ordinateur |
| **☁️ Cloud uniquement** | Streamlit Cloud utilise `cloud_data/` |
        """)
        
        st.divider()
        
        # Vérifier le statut
        st.subheader("📊 Statut actuel")
        
        # Vérifier si les dossiers sont des liens symboliques
        cours_path = Path("cours")
        brevets_path = Path("Brevets Fédéral Electricien de réseaux")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if cours_path.is_symlink():
                st.success("✅ **cours/** → Google Drive")
                try:
                    files = len(list(cours_path.iterdir()))
                    st.caption(f"📁 {files} modules accessibles")
                except:
                    st.caption("⚠️ Vérifier l'accès")
            elif cours_path.exists():
                st.warning("📁 **cours/** (local)")
                st.caption("💡 Utilise `sync_drive.py drive` pour lier à Drive")
            else:
                st.error("❌ **cours/** non trouvé")
        
        with col2:
            if brevets_path.is_symlink():
                st.success("✅ **Brevets.../** → Google Drive")
                try:
                    files = len(list(brevets_path.iterdir()))
                    st.caption(f"📁 {files} modules accessibles")
                except:
                    st.caption("⚠️ Vérifier l'accès")
            elif brevets_path.exists():
                st.warning("📁 **Brevets.../** (local)")
            else:
                st.error("❌ **Brevets.../** non trouvé")
        
        st.divider()
        
        st.subheader("🛠️ Commandes Terminal")
        
        st.code("""
# Voir le statut de synchronisation
python scripts/sync_drive.py status

# Synchroniser local → Drive
python scripts/sync_drive.py sync

# Travailler depuis Drive (créer liens)
python scripts/sync_drive.py drive

# Restaurer depuis Drive → local
python scripts/sync_drive.py restore
        """, language="bash")
        
        st.info("""
**💡 Conseil:** Lance `python scripts/sync_drive.py status` dans le terminal 
pour voir un rapport détaillé de la synchronisation.
        """)
    
    if not config:
        st.error("Fichier de configuration non trouvé!")


# Footer
st.divider()
st.caption("🎓 Système de Révision Intelligent - Brevet Fédéral de Spécialiste de Réseau | Formation CIFER")
