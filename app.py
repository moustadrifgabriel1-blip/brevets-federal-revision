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

# Charger les variables d'environnement dès le démarrage
from dotenv import load_dotenv
load_dotenv()

# Charger la clé API depuis .env ou secrets.toml
def get_api_key():
    # Priorité 1: Variable d'environnement (chargée par dotenv)
    env_key = os.getenv('GOOGLE_API_KEY')
    if env_key:
        return env_key
    # Priorité 2: Streamlit secrets
    if hasattr(st, 'secrets') and 'api' in st.secrets:
        return st.secrets['api'].get('GOOGLE_API_KEY', '')
    # Priorité 3: Lecture directe du fichier .env
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

@st.cache_data(ttl=60)  # Cache expire après 60 secondes pour recharger la clé API
def load_config():
    config_path = Path("config/config.yaml")
    # Fallback pour Streamlit Cloud
    if not config_path.exists():
        config_path = Path("cloud_data/config.yaml")
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


def is_streamlit_cloud():
    """Détecte si on est sur Streamlit Cloud"""
    import os
    return os.environ.get('STREAMLIT_SERVER_HEADLESS', '') == 'true' or \
           os.environ.get('HOME', '').startswith('/home/appuser') or \
           not Path("cours").exists()


def get_cours_status():
    """Retourne le statut des cours (local, drive, ou cloud)"""
    cours_path = Path("cours")
    cloud_data = Path("cloud_data")
    
    if cours_path.exists():
        if cours_path.is_symlink():
            return "drive", len(list(cours_path.rglob('*.pdf')))
        else:
            return "local", len(list(cours_path.rglob('*.pdf')))
    elif cloud_data.exists():
        # Sur Streamlit Cloud, utiliser les données analysées
        concept_map = load_concept_map()
        if concept_map and 'nodes' in concept_map:
            return "cloud", len(concept_map.get('nodes', []))
        return "cloud", 0
    return "none", 0


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
    
    PAGES = ["🏠 Accueil", "📚 Mes Documents", "📅 Planning Cours", "🔬 Analyser", "🗺️ Concepts", "🎯 Couverture Examen", "� Focus Examen", "🎓 Coach Expert", "📆 Planning Révisions", "📊 Ma Progression", "🧠 Quiz", "🧪 Feynman", "📇 Flashcards", "📖 Ressources", "⚙️ Paramètres"]
    
    # Synchroniser avec les boutons de navigation
    default_index = 0
    if 'page' in st.session_state and st.session_state['page'] in PAGES:
        default_index = PAGES.index(st.session_state['page'])
    
    page = st.radio(
        "Menu",
        PAGES,
        index=default_index,
        key="nav_radio"
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
    
    # Bouton Focus Examen mis en avant
    st.divider()
    col_focus1, col_focus2, col_focus3 = st.columns([1, 2, 1])
    with col_focus2:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #e53935 0%, #ff6f00 100%); 
                    padding: 1.5rem; border-radius: 15px; text-align: center; color: white;">
            <h3>🔥 Focus Examen — Stratégie de Réussite</h3>
            <p>Analyse Pareto · Pratique terrain · Technique Feynman</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🔥 Accéder au Focus Examen", type="primary", key="btn_focus", use_container_width=True):
            st.session_state['page'] = "🔥 Focus Examen"
            st.rerun()
    
    # Coach Expert shortcut
    col_coach1, col_coach2, col_coach3 = st.columns([1, 2, 1])
    with col_coach2:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #1565c0 0%, #7b1fa2 100%); 
                    padding: 1.5rem; border-radius: 15px; text-align: center; color: white;">
            <h3>🎓 Coach Expert IA — Ton prof dans chaque domaine</h3>
            <p>Il te dit exactement : «ça DRILL» · «ça MAÎTRISE» · «ça IGNORE»</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🎓 Consulter le Coach Expert", type="secondary", key="btn_coach_accueil", use_container_width=True):
            st.session_state['page'] = "🎓 Coach Expert"
            st.rerun()

    # Mini résumé DRILL du jour
    try:
        from src.expert_coach import get_all_drill_items, get_global_mastery_stats
        drills = get_all_drill_items()
        mastery_stats = get_global_mastery_stats()
        
        st.markdown("""
        <div style="background: linear-gradient(135deg, #e53935 0%, #c62828 100%); 
                    padding: 1rem; border-radius: 10px; text-align: center; color: white; margin-top: 0.5rem;">
            <p style="margin:0; font-size: 1.1em;">🔴 <strong>{} compétences DRILL</strong> — à pratiquer TOUS LES JOURS</p>
        </div>
        """.format(mastery_stats.get('drill_total', 0)), unsafe_allow_html=True)
    except Exception:
        pass
    
    st.divider()
    
    # Statut actuel
    st.subheader("📋 Statut de votre préparation")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        cours_status, cours_count = get_cours_status()
        if cours_status == "drive":
            st.success(f"☁️ {cours_count} PDFs sur Google Drive")
        elif cours_status == "local":
            st.success(f"✅ {cours_count} fichiers de cours locaux")
        elif cours_status == "cloud":
            if cours_count > 0:
                st.info(f"☁️ {cours_count} concepts analysés (mode cloud)")
            else:
                st.warning("⚠️ Aucune analyse disponible")
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
        exam_date = config.get('user', {}).get('exam_date', '2027-03-20')
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
        
        # ---- ALERTE COUVERTURE DIRECTIVES D'EXAMEN ----
        st.divider()
        st.subheader("🎯 Couverture des Directives d'Examen")
        
        from src.directives_coverage import get_module_coverage, get_coverage_summary
        
        cov_concept_map = load_concept_map()
        cov_data = get_module_coverage(cov_concept_map, config)
        cov_summary = get_coverage_summary(cov_data)
        
        cov_rate = cov_summary['coverage_rate'] * 100
        
        # Barre de couverture globale avec couleur
        col1, col2, col3 = st.columns(3)
        with col1:
            cov_color = "🟢" if cov_rate >= 70 else ("🟡" if cov_rate >= 40 else "🔴")
            st.metric(f"{cov_color} Couverture examen", f"{cov_rate:.0f}%")
        with col2:
            st.metric("Compétences couvertes", f"{cov_summary['covered_competences']}/{cov_summary['total_competences']}")
        with col3:
            st.metric("🚨 Lacunes", cov_summary['total_gaps'])
        
        st.progress(cov_summary['coverage_rate'])
        
        # Alerte modules manquants
        modules_manquants = [c for c in cov_data.values() if c['status'] == 'manquant']
        modules_insuffisants = [c for c in cov_data.values() if c['status'] == 'insuffisant']
        
        if modules_manquants:
            st.error(
                f"🚨 **{len(modules_manquants)} modules évalués à l'examen n'ont AUCUN cours importé !**\n\n"
                + "\n".join(
                    f"- **{code}** — {cov_data[code]['name']} ({cov_data[code]['poids_examen']})"
                    for code in sorted(cov_data.keys()) if cov_data[code]['status'] == 'manquant'
                )
                + "\n\n👉 Importe les cours manquants ou consulte la page **🎯 Couverture Examen** pour les détails."
            )
        
        if modules_insuffisants:
            st.warning(
                f"⚠️ **{len(modules_insuffisants)} modules ont une couverture insuffisante** (< 30%)\n\n"
                + "\n".join(
                    f"- **{code}** — {cov_data[code]['name']} : {cov_data[code]['coverage_score']*100:.0f}% couvert"
                    for code in sorted(cov_data.keys()) if cov_data[code]['status'] == 'insuffisant'
                )
            )
        
        if not modules_manquants and not modules_insuffisants:
            st.success("✅ Tous les modules d'examen sont couverts ! Continue à réviser.")


elif page == "📚 Mes Documents":
    st.header("📚 Gestion des Documents")
    
    # Bouton supprimer tout (avec session_state pour éviter le nested-interaction pattern)
    col1, col2 = st.columns([4, 1])
    with col2:
        if st.button("🗑️ Tout Supprimer", type="secondary", key="del_all"):
            st.session_state['confirm_delete_all'] = True
    
    if st.session_state.get('confirm_delete_all', False):
        st.warning("⚠️ **Êtes-vous sûr de vouloir tout supprimer ?**")
        col_yes, col_no = st.columns(2)
        with col_yes:
            if st.button("✅ Oui, supprimer", type="primary", key="confirm_del_yes"):
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
                    st.session_state['confirm_delete_all'] = False
                    st.success(f"✅ {deleted} supprimé(s)")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ {e}")
        with col_no:
            if st.button("❌ Annuler", key="confirm_del_no"):
                st.session_state['confirm_delete_all'] = False
                st.rerun()
    
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
                
                module_codes = sorted(load_config().get('modules', {}).keys()) if load_config() and 'modules' in load_config() else [
                    "AA01", "AA02", "AA03", "AA04", "AA05", "AA06", "AA07", "AA08", "AA09", "AA10", "AA11",
                    "AE01", "AE02", "AE03", "AE04", "AE05", "AE06", "AE07", "AE09", "AE10", "AE11", "AE12", "AE13"
                ]
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
        
        # --- Scan avec session_state pour éviter le nested-button pattern ---
        if source_path and st.button("🚀 Scanner et Importer", type="primary", use_container_width=True):
            source_path_clean = source_path.strip().strip("'").strip('"')
            
            if Path(source_path_clean).exists():
                try:
                    import sys
                    sys.path.insert(0, str(Path.cwd()))
                    from src.folder_importer import FolderImporter, calculate_study_time
                    
                    config = load_config()
                    importer = FolderImporter(config)
                    modules = importer.scan_source_folder(source_path_clean)
                    
                    # Stocker les résultats dans session_state
                    st.session_state['scan_results'] = {
                        'source_path': source_path_clean,
                        'modules': modules,
                        'status': importer.get_modules_status(),
                        'total_files': sum(m.file_count for m in modules),
                    }
                    st.rerun()
                except Exception as e:
                    st.error(f"Erreur: {e}")
                    st.exception(e)
            else:
                st.error(f"❌ Le dossier n'existe pas: {source_path_clean}")
                st.info("💡 Vérifiez que le chemin est correct. Essayez de glisser-déposer le dossier dans le champ ci-dessus.")
        
        # Afficher les résultats du scan (persistés dans session_state)
        if 'scan_results' in st.session_state:
            scan = st.session_state['scan_results']
            modules = scan['modules']
            status = scan['status']
            
            st.success(f"✅ {len(modules)} modules détectés!")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("📚 Avec contenu", len(status['with_content']))
            with col2:
                st.metric("📭 Sans contenu", len(status['empty']))
            with col3:
                st.metric("📄 Fichiers total", scan['total_files'])
            
            st.divider()
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
            
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                if st.button("✅ Confirmer l'import", type="primary"):
                    with st.spinner("Copie des fichiers en cours..."):
                        try:
                            import sys
                            sys.path.insert(0, str(Path.cwd()))
                            from src.folder_importer import FolderImporter
                            
                            config = load_config()
                            importer = FolderImporter(config)
                            importer.scan_source_folder(scan['source_path'])
                            
                            report = importer.import_folders(
                                scan['source_path'],
                                "cours",
                                copy_mode=copy_files
                            )
                            importer.update_config_modules("config/config.yaml")
                            
                            del st.session_state['scan_results']
                            st.success(f"✅ Import terminé!")
                            st.write(f"- {len(report['modules_imported'])} modules avec contenu")
                            st.write(f"- {len(report['modules_empty'])} modules en attente de cours")
                            st.write(f"- {report['total_files']} fichiers copiés")
                            st.balloons()
                        except Exception as e:
                            st.error(f"Erreur: {e}")
                            st.exception(e)
            with col_btn2:
                if st.button("❌ Annuler"):
                    del st.session_state['scan_results']
                    st.rerun()
        
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
    
    with tab3:
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
    
    with tab4:
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
    
    with tab5:
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


elif page == "📅 Planning Cours":
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
    
    # Vérifier si on est sur Streamlit Cloud
    if is_streamlit_cloud():
        st.info("""
### ☁️ Mode Cloud actif

Les fichiers PDF de cours (1.6 GB) ne sont pas disponibles sur Streamlit Cloud.

**Bonne nouvelle:** L'analyse a déjà été faite ! Tu as accès à:
- ✅ **503 concepts** analysés
- ✅ **Planning de révision** généré
- ✅ **Cartographie** des modules

👉 Va dans **🗺️ Concepts** ou **📆 Planning Révisions** pour voir les résultats.

---
**Pour relancer une analyse:**
1. Clone le projet sur ton Mac
2. Assure-toi que les cours sont synchronisés avec Google Drive
3. Lance l'analyse en local
4. Exécute `python scripts/backup_data.py cloud` pour exporter
        """)
        
        # Afficher un aperçu des données analysées
        concept_map = load_concept_map()
        if concept_map and 'nodes' in concept_map:
            st.success(f"📊 **{len(concept_map['nodes'])} concepts** disponibles dans la base de données")
            
            # Compter par catégorie
            categories = {}
            for node in concept_map['nodes']:
                cat = node.get('category', 'Autre')
                categories[cat] = categories.get(cat, 0) + 1
            
            if categories:
                st.markdown("**Répartition par catégorie:**")
                for cat, count in sorted(categories.items(), key=lambda x: -x[1])[:5]:
                    st.write(f"- {cat}: {count} concepts")
    
    elif len(cours_files) == 0:
        st.warning("⚠️ Veuillez d'abord importer vos documents dans l'onglet 'Mes Documents'")
    else:
        st.info("🤖 **Gemini 3 Pro** sera utilisé pour l'analyse (délai de 2s entre chaque document)")
        
        # --- ANALYSE INCRÉMENTALE ---
        import sys
        sys.path.insert(0, str(Path.cwd()))
        from src.incremental_analyzer import IncrementalAnalyzer
        
        incr = IncrementalAnalyzer()
        last_info = incr.get_last_analysis_info()
        
        if last_info:
            last_dt = last_info['date'][:19].replace('T', ' ')
            st.success(f"📊 Dernière analyse : **{last_dt}** ({last_info['total_files']} fichiers)")
        
        # Choix du mode
        analysis_mode = st.radio(
            "Mode d'analyse",
            ["⚡ Incrémentale (recommandé)", "🔄 Complète (tout ré-analyser)"],
            horizontal=True,
            help="L'analyse incrémentale ne ré-analyse que les documents nouveaux ou modifiés."
        )
        
        is_incremental = analysis_mode.startswith("⚡")
        
        # Pré-scan pour estimer le travail
        if is_incremental and last_info:
            if st.button("🔍 Pré-scanner les changements", use_container_width=True):
                try:
                    from src.scanner import DocumentScanner
                    config = load_config()
                    scanner = DocumentScanner(config)
                    results = scanner.scan_all()
                    cours_docs = scanner.get_documents_by_category('cours')
                    
                    comparison = incr.compare_with_previous(cours_docs)
                    summary = incr.get_comparison_summary(comparison)
                    
                    st.session_state['incr_comparison'] = comparison
                    st.session_state['incr_summary'] = summary
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Erreur de scan : {e}")
            
            if 'incr_summary' in st.session_state:
                s = st.session_state['incr_summary']
                col_s1, col_s2, col_s3, col_s4 = st.columns(4)
                with col_s1:
                    st.metric("🆕 Nouveaux", s['new_count'])
                with col_s2:
                    st.metric("✏️ Modifiés", s['modified_count'])
                with col_s3:
                    st.metric("✅ Inchangés", s['unchanged_count'])
                with col_s4:
                    st.metric("🗑️ Supprimés", s['deleted_count'])
                
                if s['total_to_analyze'] == 0:
                    st.success("🎉 Aucun changement détecté ! Tous les documents sont à jour.")
                else:
                    st.info(f"📊 **{s['total_to_analyze']}** document(s) à analyser ({s['savings_pct']}% économisé)")
                    
                    if s['new_files']:
                        with st.expander(f"🆕 {len(s['new_files'])} nouveau(x)"):
                            for f in s['new_files']:
                                st.write(f"• {f}")
                    if s['modified_files']:
                        with st.expander(f"✏️ {len(s['modified_files'])} modifié(s)"):
                            for f in s['modified_files']:
                                st.write(f"• {f}")
                    if s['deleted_files']:
                        with st.expander(f"🗑️ {len(s['deleted_files'])} supprimé(s)"):
                            for f in s['deleted_files']:
                                st.write(f"• {f}")
        
        # Bouton lancer l'analyse
        btn_label = "⚡ Lancer l'analyse incrémentale" if is_incremental else "🚀 Lancer l'analyse complète"
        
        if st.button(btn_label, type="primary", use_container_width=True):
            
            with st.spinner("Analyse en cours... Cela peut prendre quelques minutes."):
                try:
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
                    
                    cours_docs = scanner.get_documents_by_category('cours')
                    
                    # Étape 1b: Comparaison incrémentale
                    incr_analyzer = IncrementalAnalyzer()
                    
                    if is_incremental and incr_analyzer.has_previous_analysis():
                        comparison = incr_analyzer.compare_with_previous(cours_docs)
                        summary = incr_analyzer.get_comparison_summary(comparison)
                        docs_to_analyze = comparison['new'] + comparison['modified']
                        deleted_paths = comparison['deleted']
                        
                        st.info(f"⚡ Mode incrémental : **{summary['total_to_analyze']}** documents à analyser "
                                f"({summary['savings_pct']}% économisé)")
                    else:
                        docs_to_analyze = cours_docs
                        deleted_paths = []
                        if is_incremental:
                            st.info("ℹ️ Première analyse — tous les documents seront analysés.")
                    
                    # Étape 2: Analyse IA (seulement les docs nécessaires)
                    st.info(f"🤖 Analyse IA de {len(docs_to_analyze)} document(s)...")
                    analyzer = ContentAnalyzer(config)
                    
                    api_key = config.get('api', {}).get('gemini_api_key', '')
                    if api_key:
                        st.success(f"🔑 Clé API détectée ({api_key[:10]}...)")
                    else:
                        st.error("❌ Aucune clé API trouvée ! L'analyse ne fonctionnera pas.")
                    
                    directives_docs = results.get('directives', [])
                    if directives_docs:
                        st.info(f"📋 Chargement de {len(directives_docs)} directive(s) d'examen...")
                        directives_content = "\n\n".join([doc.content[:5000] for doc in directives_docs])
                        analyzer.load_directives_context(directives_content)
                        st.success(f"✅ Directives chargées - Orientation: {analyzer.orientation}")
                    else:
                        st.warning("⚠️ Aucune directive d'examen trouvée - analyse sans contexte d'examen")
                    
                    all_new_concepts = []
                    
                    if docs_to_analyze:
                        modules_found = {}
                        for doc in docs_to_analyze:
                            if doc.module:
                                modules_found.setdefault(doc.module, []).append(doc.filename)
                        
                        if modules_found:
                            st.info(f"📚 {len(modules_found)} modules à analyser: {', '.join(sorted(modules_found.keys()))}")
                        
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                        error_count = 0
                        
                        for i, doc in enumerate(docs_to_analyze):
                            percent = int(((i + 1) / len(docs_to_analyze)) * 100)
                            status_text.text(f"⏳ Analyse en cours... {i+1}/{len(docs_to_analyze)} documents ({percent}%)")
                            
                            try:
                                concepts = analyzer.analyze_course_document(
                                    doc.content, 
                                    doc.filename, 
                                    doc.module
                                )
                                all_new_concepts.extend(concepts)
                            except Exception as e:
                                error_count += 1
                                st.warning(f"⚠️ Erreur d'analyse pour {doc.filename}: {str(e)[:100]}")
                                continue
                            
                            progress_bar.progress((i + 1) / len(docs_to_analyze))
                        
                        status_text.empty()
                        progress_bar.empty()
                        
                        if error_count > 0:
                            st.warning(f"⚠️ {error_count} document(s) n'ont pas pu être analysés")
                        
                        st.success(f"✅ {len(all_new_concepts)} nouveaux concepts identifiés")
                    else:
                        st.success("✅ Aucun document à analyser — tout est à jour")
                    
                    # Étape 3: Fusion / Cartographie
                    existing_map = load_concept_map()
                    
                    if is_incremental and incr_analyzer.has_previous_analysis() and existing_map:
                        st.info("🔀 Fusion des concepts (incrémental)...")
                        merged = incr_analyzer.merge_concepts(
                            existing_map, all_new_concepts, docs_to_analyze, deleted_paths
                        )
                        if merged:
                            # Sauvegarder directement le concept_map fusionné
                            with open("exports/concept_map.json", 'w', encoding='utf-8') as f:
                                json.dump(merged, f, indent=2, ensure_ascii=False)
                            st.success(f"✅ Carte conceptuelle mise à jour ({len(merged['nodes'])} concepts)")
                        else:
                            # Pas de données existantes — reconstruire
                            mapper = ConceptMapper(config)
                            mapper.build_from_concepts(all_new_concepts)
                            mapper.export_to_json("exports/concept_map.json")
                            st.success(f"✅ Carte conceptuelle reconstruite")
                    else:
                        st.info("🗺️ Création de la cartographie...")
                        # Analyse complète : rassembler tous les concepts
                        all_concepts_complete = all_new_concepts
                        mapper = ConceptMapper(config)
                        mapper.build_from_concepts(all_concepts_complete)
                        mapper.export_to_json("exports/concept_map.json")
                    
                    # Sauvegarder l'état incrémental
                    incr_analyzer.save_state()
                    
                    # Étape 4: Planning de révision
                    st.info("📆 Génération du planning de révision...")
                    from src.revision_planner import auto_generate_planning
                    planning_result = auto_generate_planning(config)
                    
                    if planning_result['success']:
                        st.success(f"Planning généré: {planning_result['total_sessions']} sessions, {planning_result['total_hours']}h de révision")
                    else:
                        st.warning(f"Erreur planning: {planning_result.get('error', 'Inconnu')}")
                    
                    # Nettoyer l'état de session du pré-scan
                    for key in ['incr_comparison', 'incr_summary']:
                        if key in st.session_state:
                            del st.session_state[key]
                    
                    st.success("✅ Analyse et planning terminés!")
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
        
        tab_list, tab_graph = st.tabs(["📋 Liste des concepts", "🕸️ Graphe interactif"])
        
        with tab_list:
            # Filtres
            col1, col2, col3 = st.columns(3)
            with col1:
                importance_filter = st.multiselect(
                    "Filtrer par importance",
                    ['critical', 'high', 'medium', 'low'],
                    default=['critical', 'high']
                )
            with col2:
                exam_only = st.checkbox("Uniquement liés à l'examen", value=False)
            
            with col3:
                # Filtrer par module
                all_modules = sorted(set(n.get('module') for n in nodes if n.get('module')))
                selected_modules = st.multiselect(
                    "Filtrer par module",
                    all_modules,
                    default=all_modules if all_modules else []
                )
            
            # Liste des concepts
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
                            
                            # Références du document source
                            source_doc = node.get('source_document', '')
                            page_ref = node.get('page_references', '')
                            if source_doc or page_ref:
                                st.markdown("**📖 Où réviser:**")
                                if source_doc:
                                    st.caption(f"📄 Document: {source_doc}")
                                if page_ref:
                                    st.caption(f"📖 Références: {page_ref}")
                            
                            # Mots-clés
                            keywords = node.get('keywords', [])
                            if keywords:
                                st.markdown(f"**🔑 Mots-clés:** {', '.join(keywords)}")
                            
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
        
        # ===== ONGLET GRAPHE INTERACTIF =====
        with tab_graph:
            from src.concept_graph import build_graph, graph_to_plotly, get_graph_stats, MODULE_COLORS
            
            st.markdown("### 🕸️ Graphe des concepts et leurs liens")
            st.markdown("*Les nœuds sont colorés par module, dimensionnés par importance. Les liens montrent les prérequis et dépendances.*")
            
            # Contrôles du graphe
            gc1, gc2, gc3 = st.columns(3)
            with gc1:
                graph_modules = st.multiselect(
                    "Modules à afficher",
                    sorted(set(n.get('module') for n in nodes if n.get('module'))),
                    default=sorted(set(n.get('module') for n in nodes if n.get('module'))),
                    key="graph_modules"
                )
            with gc2:
                graph_importance = st.multiselect(
                    "Importance",
                    ['critical', 'high', 'medium', 'low'],
                    default=['critical', 'high'],
                    key="graph_importance"
                )
            with gc3:
                graph_layout = st.selectbox(
                    "Disposition",
                    ["spring", "shell", "circular", "kamada_kawai"],
                    index=0,
                    key="graph_layout",
                    help="spring = force-directed, shell = par module, circular = cercle, kamada_kawai = distances optimisées"
                )
            
            max_nodes = st.slider("Nombre max de concepts", 20, 300, 100, step=10, key="graph_max_nodes")
            
            # Construire et afficher le graphe
            G = build_graph(
                nodes,
                modules_filter=graph_modules if graph_modules else None,
                importance_filter=graph_importance if graph_importance else None,
                max_nodes=max_nodes
            )
            
            # Statistiques du graphe
            gstats = get_graph_stats(G)
            
            gs1, gs2, gs3, gs4 = st.columns(4)
            with gs1:
                st.metric("🔵 Nœuds", gstats['nodes'])
            with gs2:
                st.metric("🔗 Liens", gstats['edges'])
            with gs3:
                st.metric("🏝️ Composantes", gstats['components'])
            with gs4:
                st.metric("📐 Densité", f"{gstats['density']:.3f}")
            
            # Rendu Plotly
            fig = graph_to_plotly(G, layout=graph_layout, height=700)
            st.plotly_chart(fig, use_container_width=True)
            
            # Légende des couleurs par module
            with st.expander("🎨 Légende des couleurs (modules)"):
                legend_cols = st.columns(4)
                for idx, mod in enumerate(sorted(graph_modules)):
                    color = MODULE_COLORS.get(mod, '#999')
                    count = gstats['modules'].get(mod, 0)
                    with legend_cols[idx % 4]:
                        st.markdown(f"<span style='color:{color}; font-size:20px;'>●</span> **{mod}** ({count})", unsafe_allow_html=True)
            
            # Hubs (nœuds les plus connectés)
            if gstats['hub_nodes']:
                with st.expander("🌟 Concepts les plus connectés (hubs)"):
                    for hub in gstats['hub_nodes']:
                        st.markdown(f"- **{hub['name']}** ({hub['module']}) — {hub['connections']} connexions")


elif page == "🎯 Couverture Examen":
    st.header("🎯 Matrice de Couverture — Directives d'Examen")
    st.markdown("**Compare tes cours et concepts analysés avec les exigences officielles des directives d'examen.**")
    
    # Charger les données
    from src.directives_coverage import get_module_coverage, get_coverage_summary, EXAM_REQUIREMENTS
    
    concept_map = load_concept_map()
    config = load_config()
    coverage = get_module_coverage(concept_map, config)
    summary = get_coverage_summary(coverage)
    
    # ---- RÉSUMÉ GLOBAL ----
    st.subheader("📊 Résumé global")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        rate_pct = summary['coverage_rate'] * 100
        color = "🟢" if rate_pct >= 70 else ("🟡" if rate_pct >= 40 else "🔴")
        st.metric(f"{color} Couverture globale", f"{rate_pct:.0f}%")
    with col2:
        st.metric("Compétences couvertes", f"{summary['covered_competences']}/{summary['total_competences']}")
    with col3:
        st.metric("⚠️ Lacunes", summary['total_gaps'])
    with col4:
        st.metric("🚨 Modules manquants", summary['modules_manquant'])
    
    st.divider()
    
    # ---- BARRE DE PROGRESSION PAR STATUT ----
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"✅ **Complet** : {summary['modules_complet']}")
    with col2:
        st.markdown(f"🟡 **Partiel** : {summary['modules_partiel']}")
    with col3:
        st.markdown(f"🟠 **Insuffisant** : {summary['modules_insuffisant']}")
    with col4:
        st.markdown(f"🔴 **Manquant** : {summary['modules_manquant']}")
    
    st.progress(summary['coverage_rate'])
    
    st.divider()
    
    # ---- ALERTES CRITIQUES ----
    if summary['critical_gaps']:
        st.subheader("🚨 ALERTES — Modules critiques sans couverture")
        st.error(f"**{len(summary['critical_gaps'])} modules évalués à l'examen n'ont pas ou peu de couverture !**")
        
        for gap in summary['critical_gaps']:
            with st.expander(f"🔴 {gap['module']} — {gap['name']} ({gap['poids_examen']})", expanded=True):
                st.markdown("**Compétences NON couvertes :**")
                for g in gap['gaps']:
                    st.markdown(f"- ❌ {g}")
                st.warning(f"⚠️ Ce module sera évalué à l'examen ({gap['poids_examen']}). Il faut obtenir les cours correspondants.")
    
    st.divider()
    
    # ---- MATRICE DÉTAILLÉE ----
    st.subheader("📋 Matrice détaillée par module")
    
    # Filtres
    col1, col2 = st.columns(2)
    with col1:
        filter_type = st.selectbox(
            "Afficher",
            ["Tous les modules", "Modules de base (AA)", "Modules spécialisés (AE)", "Modules avec lacunes", "Modules manquants uniquement"],
            index=0,
            key="coverage_filter"
        )
    with col2:
        sort_by = st.selectbox(
            "Trier par",
            ["Code module", "Score de couverture (croissant)", "Score de couverture (décroissant)", "Nombre de lacunes"],
            index=1,
            key="coverage_sort"
        )
    
    # Appliquer les filtres
    filtered = dict(coverage)
    if filter_type == "Modules de base (AA)":
        filtered = {k: v for k, v in filtered.items() if k.startswith("AA")}
    elif filter_type == "Modules spécialisés (AE)":
        filtered = {k: v for k, v in filtered.items() if k.startswith("AE")}
    elif filter_type == "Modules avec lacunes":
        filtered = {k: v for k, v in filtered.items() if v['status'] != 'complet'}
    elif filter_type == "Modules manquants uniquement":
        filtered = {k: v for k, v in filtered.items() if v['status'] == 'manquant'}
    
    # Appliquer le tri
    if sort_by == "Score de couverture (croissant)":
        items = sorted(filtered.items(), key=lambda x: x[1]['coverage_score'])
    elif sort_by == "Score de couverture (décroissant)":
        items = sorted(filtered.items(), key=lambda x: x[1]['coverage_score'], reverse=True)
    elif sort_by == "Nombre de lacunes":
        items = sorted(filtered.items(), key=lambda x: len(x[1]['gaps']), reverse=True)
    else:
        items = sorted(filtered.items())
    
    # Afficher chaque module
    for module_code, cov in items:
        score = cov['coverage_score']
        status_icon = {
            'complet': '✅',
            'partiel': '🟡',
            'insuffisant': '🟠',
            'manquant': '🔴',
        }.get(cov['status'], '⚪')
        
        content_icon = "📚" if cov['has_content'] else "📭"
        
        header = f"{status_icon} {module_code} — {cov['name']} | {content_icon} {cov['num_concepts']} concepts | Couverture: {score*100:.0f}%"
        
        with st.expander(header, expanded=(cov['status'] in ('manquant', 'insuffisant'))):
            # Barre de progression du module
            st.progress(score)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown(f"**Cours importés :** {'✅ Oui' if cov['has_content'] else '❌ Non'}")
            with col2:
                st.markdown(f"**Concepts analysés :** {cov['num_concepts']}")
            with col3:
                st.markdown(f"**Poids examen :** {cov['poids_examen']}")
            
            st.divider()
            
            # Liste des compétences avec statut
            st.markdown("**Compétences évaluées à l'examen :**")
            for comp in cov['competences']:
                # Vérifier si cette compétence est couverte
                is_covered = comp not in cov['gaps']
                if is_covered:
                    # Trouver le concept qui la couvre
                    matching = [m for m in cov['matched_concepts'] if m['competence'] == comp]
                    concept_name = matching[0]['concept'] if matching else "—"
                    st.markdown(f"- ✅ {comp}")
                    st.caption(f"   ↳ Couvert par : *{concept_name}*")
                else:
                    st.markdown(f"- ❌ **{comp}**")
                    st.caption(f"   ↳ ⚠️ NON COUVERT — À réviser / cours à obtenir")
    
    st.divider()
    
    # ---- TABLEAU RÉCAPITULATIF ----
    st.subheader("📊 Tableau récapitulatif")
    
    table_data = []
    for code in sorted(coverage.keys()):
        cov = coverage[code]
        status_emoji = {'complet': '✅', 'partiel': '🟡', 'insuffisant': '🟠', 'manquant': '🔴'}.get(cov['status'], '⚪')
        table_data.append({
            "Module": code,
            "Nom": cov['name'],
            "Statut": status_emoji,
            "Cours": "✅" if cov['has_content'] else "❌",
            "Concepts": cov['num_concepts'],
            "Couverture": f"{cov['coverage_score']*100:.0f}%",
            "Lacunes": len(cov['gaps']),
            "Examen": cov['poids_examen'],
        })
    
    df_coverage = pd.DataFrame(table_data)
    st.dataframe(df_coverage, use_container_width=True, hide_index=True)


# ======================================================================
# 🔥 PAGE FOCUS EXAMEN — Priorisation Pareto + Pratique Terrain + Feynman
# ======================================================================
elif page == "🔥 Focus Examen":
    st.header("🔥 Focus Examen — Stratégie de Réussite")
    st.markdown("""
**Cibler ce qui rapporte le plus de points.** Cette page analyse chaque compétence et te dit :
- 📖 Ce que tu peux réviser par **quiz et flashcards** (théorie + calcul)
- 🔧 Ce que tu **dois pratiquer sur le terrain** (non quizzable)
- 🎤 Ce que tu dois préparer pour l'**oral et les projets**
- 🎯 La **priorité Pareto** : quels modules te feront gagner le plus de points
""")

    from src.exam_focus import ExamFocusAnalyzer, EXAM_WEIGHT, TYPE_LABELS, COMPETENCE_TYPES
    from src.practice_tracker import PracticeTracker
    from src.weak_concepts_tracker import WeakConceptsTracker

    config = load_config()
    weak_tracker = WeakConceptsTracker()
    practice_tracker = PracticeTracker()
    analyzer = ExamFocusAnalyzer(weak_tracker=weak_tracker, concept_map=load_concept_map(), config=config)

    # ---- ONGLETS ----
    tab_priority, tab_types, tab_practice, tab_stats = st.tabs([
        "🎯 Priorité Pareto", "📊 Types d'apprentissage", "🔧 Pratique Terrain", "📈 Statistiques"
    ])

    # ============================================================
    # TAB 1 : PRIORITÉ PARETO
    # ============================================================
    with tab_priority:
        st.subheader("🎯 Classement Pareto — Où investir ton temps")
        st.markdown("""
> **Principe Pareto 80/20** : Les modules en haut de la liste te feront gagner le plus de points 
> à l'examen car ils ont un **poids élevé** ET une **maîtrise faible**. Concentre-toi dessus en priorité.
""")

        ranking = analyzer.get_priority_ranking()

        # Top 5 en surbrillance
        st.markdown("### 🏆 Top 5 — Tes priorités absolues")
        for i, mod in enumerate(ranking[:5], 1):
            prio_color = "🔴" if mod['priority_score'] > 50 else ("🟡" if mod['priority_score'] > 25 else "🟢")
            quizzable_icon = "✅" if mod['quizzable_pct'] > 50 else "⚠️"

            with st.expander(f"{prio_color} **#{i} — {mod['module']} {mod['name']}** | "
                           f"Poids: {mod['exam_questions']}Q | Maîtrise: {mod['mastery_pct']:.0f}% | "
                           f"Score priorité: {mod['priority_score']:.0f}"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("📝 Questions examen", f"{mod['exam_questions']}/42")
                    st.caption(mod['poids_examen'])
                with col2:
                    st.metric("📊 Maîtrise", f"{mod['mastery_pct']:.0f}%")
                    st.progress(mod['mastery_pct'] / 100)
                with col3:
                    st.metric(f"{quizzable_icon} Quizzable", f"{mod['quizzable_pct']:.0f}%")
                    if mod['practice_needed']:
                        st.warning("🔧 Pratique terrain requise")

                # Breakdown par type
                if mod.get('breakdown', {}).get('breakdown'):
                    st.markdown("**Répartition par type d'apprentissage :**")
                    for ctype, info in mod['breakdown']['breakdown'].items():
                        if info['count'] > 0:
                            tl = TYPE_LABELS[ctype]
                            st.markdown(f"- {tl['icon']} **{tl['label']}** : {info['count']} compétences ({info['pct']:.0f}%)")

                if mod['weak_concepts']:
                    st.error(f"⚠️ Concepts faibles : {', '.join(mod['weak_concepts'][:5])}")

        # Tableau complet
        st.markdown("### 📋 Classement complet")
        table_data = []
        for mod in ranking:
            prio_emoji = "🔴" if mod['priority_score'] > 50 else ("🟡" if mod['priority_score'] > 25 else "🟢")
            table_data.append({
                "Priorité": f"{prio_emoji} {mod['priority_score']:.0f}",
                "Module": f"{mod['module']} {mod['name']}",
                "Questions": f"{mod['exam_questions']}",
                "Maîtrise": f"{mod['mastery_pct']:.0f}%",
                "Quizzable": f"{mod['quizzable_pct']:.0f}%",
                "Épreuve": mod['poids_examen'],
            })
        st.dataframe(pd.DataFrame(table_data), use_container_width=True, hide_index=True)

    # ============================================================
    # TAB 2 : TYPES D'APPRENTISSAGE
    # ============================================================
    with tab_types:
        st.subheader("📊 Classification par Type d'Apprentissage")
        st.markdown("""
Chaque compétence de l'examen est classée selon **comment** tu dois l'apprendre.
Certaines compétences sont quizzables (📖 théorie, 🧮 calcul), d'autres non (🔧 pratique, 🎤 oral, 📐 projet).
""")

        global_stats = analyzer.get_global_stats()

        # Résumé global
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total compétences", global_stats['total_competences'])
        with col2:
            st.metric("✅ Quizzables", f"{global_stats['quizzable']} ({global_stats['quizzable_pct']:.0f}%)")
        with col3:
            st.metric("🔧 Non quizzables", f"{global_stats['non_quizzable']} ({global_stats['non_quizzable_pct']:.0f}%)")

        # Bars par type
        st.markdown("### Répartition globale")
        import plotly.graph_objects as go

        types_data = global_stats['by_type']
        fig = go.Figure(go.Bar(
            x=[TYPE_LABELS[t]['label'] for t in types_data],
            y=[types_data[t]['count'] for t in types_data],
            marker_color=[TYPE_LABELS[t]['color'] for t in types_data],
            text=[f"{types_data[t]['count']} ({types_data[t]['pct']:.0f}%)" for t in types_data],
            textposition='auto',
        ))
        fig.update_layout(
            title="Compétences d'examen par type d'apprentissage",
            xaxis_title="Type", yaxis_title="Nombre",
            height=350, margin=dict(l=20, r=20, t=40, b=20),
        )
        st.plotly_chart(fig, use_container_width=True, key="exam_types_chart")

        # Plan d'étude par type
        study_plan = analyzer.get_study_plan_by_type()

        for ctype, items in study_plan.items():
            if not items:
                continue
            tl = TYPE_LABELS[ctype]
            with st.expander(f"{tl['icon']} **{tl['label']}** — {len(items)} compétences | {'✅ Quizzable' if tl['quizzable'] else '🔧 Hors quiz'}"):
                st.markdown(f"*{tl['description']}*")
                for item in items:
                    weight_emoji = "🔴" if item['exam_weight'] >= 3 else ("🟡" if item['exam_weight'] >= 2 else "⚪")
                    st.markdown(f"- {weight_emoji} **[{item['module']}]** {item['competence']}")

    # ============================================================
    # TAB 3 : PRATIQUE TERRAIN
    # ============================================================
    with tab_practice:
        st.subheader("🔧 Checklist Pratique Terrain")
        st.markdown("""
> Ces compétences **ne sont PAS testables par quiz**. Tu dois les pratiquer **physiquement** 
> sur le terrain, en atelier ou par simulation. Coche ce que tu as fait !
""")

        checklist = analyzer.get_practice_checklist()
        practice_stats = practice_tracker.get_global_practice_stats(checklist)

        # Stats
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Exercices", f"{practice_stats['completed']}/{practice_stats['total_exercises']}")
        with col2:
            st.metric("Complétion", f"{practice_stats['completion_pct']:.0f}%")
            st.progress(practice_stats['completion_pct'] / 100)
        with col3:
            st.metric("Heures terrain", f"{practice_stats['total_practice_hours']:.1f}h")
        with col4:
            st.metric("🔥 Série", f"{practice_stats['streak_days']}j")

        # Exercices en retard
        overdue = practice_tracker.get_overdue_exercises(checklist)
        if overdue:
            st.warning(f"⏰ **{len(overdue)} exercices en retard** (jamais faits ou > 14 jours)")
            with st.expander("Voir les exercices en retard"):
                for ex in overdue[:10]:
                    tl = TYPE_LABELS.get(ex['type'], {})
                    st.markdown(f"- {tl.get('icon', '🔧')} **[{ex['module']}]** {ex['competence']} — _{ex['reason']}_")

        st.divider()

        # Checklist par module
        completion_by_mod = practice_tracker.get_completion_by_module(checklist)

        for mod_code in sorted(completion_by_mod.keys()):
            mod_data = completion_by_mod[mod_code]
            pct = mod_data['pct']
            pct_emoji = "🟢" if pct >= 70 else ("🟡" if pct >= 30 else "🔴")

            with st.expander(f"{pct_emoji} **{mod_code}** — {mod_data['completed']}/{mod_data['total']} exercices ({pct:.0f}%)"):
                for ex in mod_data['exercises']:
                    tl = TYPE_LABELS.get(ex['type'], {})
                    col1, col2 = st.columns([3, 1])

                    with col1:
                        done = st.checkbox(
                            f"{tl.get('icon', '🔧')} {ex['competence']}",
                            value=ex['done'],
                            key=f"practice_{ex['id']}"
                        )

                        # Si changement de statut
                        if done and not ex['done']:
                            practice_tracker.mark_exercise(ex['id'], completed=True, duration_min=15)
                            st.rerun()

                        if ex.get('suggestion'):
                            st.caption(f"💡 {ex['suggestion']}")

                    with col2:
                        if ex['done']:
                            st.success(f"✅ Fait ({ex['attempts']}x)")
                            if ex['confidence'] > 0:
                                conf_stars = "⭐" * ex['confidence']
                                st.caption(f"Confiance: {conf_stars}")

        # Journal de pratique
        st.divider()
        st.subheader("📝 Ajouter une session de pratique")

        with st.form("practice_log_form"):
            pr_module = st.selectbox("Module", sorted(EXAM_WEIGHT.keys()),
                                     format_func=lambda m: f"{m} — {COMPETENCE_TYPES.get(m, {}).keys().__class__.__name__}",
                                     key="practice_module")
            pr_desc = st.text_area("Qu'as-tu pratiqué ?", placeholder="Ex: Exercice de consignation complète avec formulaire...")
            pr_duration = st.slider("Durée (minutes)", 5, 240, 30)

            if st.form_submit_button("📝 Enregistrer la session", type="primary"):
                if pr_desc:
                    practice_tracker.log_practice_session(pr_module, pr_desc, pr_duration)
                    st.success(f"✅ Session de {pr_duration} min enregistrée !")
                    st.rerun()

    # ============================================================
    # TAB 4 : STATISTIQUES
    # ============================================================
    with tab_stats:
        st.subheader("📈 Vue d'ensemble de ta préparation")

        global_stats = analyzer.get_global_stats()

        # Graphique donut quizzable vs non-quizzable
        import plotly.graph_objects as go
        fig = go.Figure(go.Pie(
            values=[global_stats['quizzable'], global_stats['non_quizzable']],
            labels=["✅ Quizzable (quiz + flashcards)", "🔧 Hors quiz (terrain + oral + projet)"],
            marker_colors=["#2196F3", "#FF9800"],
            hole=0.4,
            textinfo='label+percent+value',
        ))
        fig.update_layout(title="Répartition Quizzable vs Non-Quizzable", height=350)
        st.plotly_chart(fig, use_container_width=True, key="quizzable_donut")

        # Répartition des questions d'examen
        st.markdown("### 📝 Répartition des questions d'examen (42 questions)")

        exam_data = sorted(EXAM_WEIGHT.items(), key=lambda x: x[1], reverse=True)
        fig2 = go.Figure(go.Bar(
            x=[f"{m}" for m, w in exam_data],
            y=[w for m, w in exam_data],
            marker_color=["#e53935" if w >= 3 else ("#fb8c00" if w >= 2 else "#43a047") for m, w in exam_data],
            text=[f"{w}Q" for m, w in exam_data],
            textposition='auto',
        ))
        fig2.update_layout(
            title="Questions par module à l'examen",
            xaxis_title="Module", yaxis_title="Nombre de questions",
            height=350, margin=dict(l=20, r=20, t=40, b=20),
        )
        st.plotly_chart(fig2, use_container_width=True, key="exam_qs_chart")

        # Top priorités
        st.markdown("### 🎯 Top concepts à impact maximal")
        top_concepts = analyzer.get_top_priority_concepts(15)
        if top_concepts:
            for i, tc in enumerate(top_concepts[:10], 1):
                impact = tc.get('exam_impact', 0)
                mastery = tc.get('mastery_score', 50)
                st.markdown(f"**{i}.** [{tc.get('module', '?')}] {tc.get('concept_name', 'N/A')} — "
                          f"Impact: {impact:.1f} | Maîtrise: {mastery}%")
        else:
            st.info("📊 Fais quelques quiz pour voir apparaître tes concepts prioritaires ici.")

        # Conseil stratégique
        st.divider()
        st.markdown("""
### 💡 Stratégie d'étude optimale

| Méthode | Pour quoi | Quand |
|---------|-----------|-------|
| 🧠 **Quiz adaptatif** | Théorie + Calcul | Tous les jours, 15-30 min |
| 📇 **Flashcards SM-2** | Mémorisation normes/valeurs | 2x par jour, 10 min |
| 🧪 **Technique Feynman** | Compréhension profonde | 1 concept/jour, 20 min |
| 🔧 **Pratique terrain** | Compétences manuelles | Weekend + chantier |
| 📝 **Examen blanc** | Condition d'examen | 1x par mois |
| 🎤 **Simulation orale** | Présentation projet | 1x par semaine |

**Principe clé :** 80% de ton score viendra de 20% des modules. 
Concentre-toi sur les modules en 🔴 dans l'onglet Priorité Pareto.
""")


# ======================================================================
# 🧪 PAGE TECHNIQUE FEYNMAN
# ======================================================================
elif page == "🧪 Feynman":
    st.header("🧪 Technique Feynman — Compréhension Profonde")
    st.markdown("""
> **Richard Feynman** : *« Si tu ne peux pas l'expliquer simplement, tu ne le comprends pas vraiment. »*
> 
> **Comment ça marche :**
> 1. Choisis un concept
> 2. Explique-le **avec tes propres mots** (comme à un collègue débutant)
> 3. L'IA identifie les **lacunes** dans ton explication
> 4. Tu combles les trous et tu réessayes
""")

    from src.feynman_method import FeynmanTracker, build_feynman_prompt
    from src.exam_focus import ExamFocusAnalyzer, EXAM_WEIGHT

    config = load_config()
    feynman_tracker = FeynmanTracker()
    concept_map = load_concept_map()

    api_key = config.get('api', {}).get('gemini_api_key') or os.getenv('GOOGLE_API_KEY') if config else os.getenv('GOOGLE_API_KEY')
    model_name = config.get('api', {}).get('model', 'gemini-3-pro-preview') if config else 'gemini-3-pro-preview'

    # Stats Feynman
    feynman_stats = feynman_tracker.get_stats()
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Concepts testés", feynman_stats['total_concepts'])
    with col2:
        st.metric("✅ Maîtrisés", feynman_stats['mastered'])
    with col3:
        st.metric("📝 En cours", feynman_stats['in_progress'])
    with col4:
        st.metric("Score moyen", f"{feynman_stats['average_score']:.0f}%")

    st.divider()

    tab_feynman, tab_history = st.tabs(["🧪 Nouvelle session", "📜 Historique"])

    with tab_feynman:
        if not concept_map or not concept_map.get('nodes'):
            st.warning("⚠️ Analyse d'abord tes documents pour avoir des concepts disponibles.")
            st.stop()

        nodes = concept_map.get('nodes', [])
        modules_available = sorted(set(n.get('module', '') for n in nodes if n.get('module')))

        # Sélection module + concept
        selected_module = st.selectbox("📁 Module", modules_available,
                                        format_func=lambda m: f"{m} — {EXAM_WEIGHT.get(m, 0)}Q d'examen",
                                        key="feynman_module")

        module_concepts = [n for n in nodes if n.get('module') == selected_module]
        if not module_concepts:
            st.info("Aucun concept analysé pour ce module.")
            st.stop()

        concept_names = [n.get('name', 'N/A') for n in module_concepts]
        selected_name = st.selectbox("📖 Concept", concept_names, key="feynman_concept")
        selected_concept = next((n for n in module_concepts if n.get('name') == selected_name), {})

        # Statut Feynman de ce concept
        concept_id = selected_concept.get('id', selected_name)
        feynman_status = feynman_tracker.get_concept_status(concept_id)
        
        if feynman_status.get('status') == 'mastered':
            st.success(f"✅ Ce concept est maîtrisé (score : {feynman_status['best_score']}%)")
        elif feynman_status.get('attempts', 0) > 0:
            st.info(f"📝 Déjà {feynman_status['attempts']} tentative(s) — Meilleur score : {feynman_status['best_score']}%")

        # Zone d'explication
        st.markdown(f"### 📝 Explique **{selected_name}** avec tes propres mots")
        st.caption("Imagine que tu expliques ce concept à un collègue qui débute. Sois précis et concret.")

        user_explanation = st.text_area(
            "Ton explication :",
            height=200,
            placeholder=f"Explique ici ce qu'est '{selected_name}', à quoi ça sert, comment ça fonctionne, "
                        f"quelles sont les normes/règles associées, et donne un exemple concret du terrain...",
            key="feynman_text"
        )

        if st.button("🧪 Évaluer mon explication", type="primary", key="feynman_evaluate"):
            if not user_explanation or len(user_explanation.strip()) < 30:
                st.error("✏️ Ton explication est trop courte. Développe davantage !")
            elif not api_key:
                st.error("🔑 Configure ta clé API dans les Paramètres.")
            else:
                # Construire le prompt avec contexte
                previous_gaps = []
                if feynman_status.get('history'):
                    last = feynman_status['history'][-1]
                    previous_gaps = last.get('gaps', [])

                prompt = build_feynman_prompt(
                    concept_name=selected_name,
                    module=f"{selected_module} — {selected_concept.get('category', '')}",
                    concept_description=selected_concept.get('description', ''),
                    user_explanation=user_explanation,
                    previous_gaps=previous_gaps,
                )

                with st.spinner("🧠 L'IA analyse ton explication..."):
                    try:
                        import google.generativeai as genai
                        genai.configure(api_key=api_key)
                        model = genai.GenerativeModel(model_name)
                        response = model.generate_content(prompt)
                        response_text = response.text.strip()

                        # Parser le JSON
                        import re
                        json_match = re.search(r'\{[\s\S]*\}', response_text)
                        if json_match:
                            result = json.loads(json_match.group())
                        else:
                            result = {"score": 50, "verdict": "ERREUR", "feedback": response_text,
                                     "strengths": [], "gaps": ["Impossible d'analyser"], "corrections": [],
                                     "tip": "", "simplified_explanation": ""}

                        score = result.get('score', 50)
                        verdict = result.get('verdict', 'N/A')

                        # Enregistrer
                        feynman_tracker.start_session(concept_id, selected_name, selected_module)
                        feynman_tracker.record_attempt(
                            concept_id, user_explanation, score,
                            result.get('feedback', ''),
                            result.get('gaps', []),
                            result.get('strengths', []),
                        )

                        # Afficher les résultats
                        st.divider()

                        verdict_colors = {
                            "EXCELLENT": "🟢", "BON": "🔵", "MOYEN": "🟡",
                            "INSUFFISANT": "🟠", "FAUX": "🔴"
                        }
                        v_color = verdict_colors.get(verdict, "⚪")

                        st.markdown(f"## {v_color} Score : {score}/100 — {verdict}")

                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown("### ✅ Points forts")
                            for s in result.get('strengths', []):
                                st.markdown(f"- ✅ {s}")
                        with col2:
                            st.markdown("### ❌ Lacunes")
                            for g in result.get('gaps', []):
                                st.markdown(f"- ❌ {g}")

                        if result.get('corrections'):
                            st.error("### ⚠️ Corrections")
                            for c in result['corrections']:
                                st.markdown(f"- ⚠️ {c}")

                        st.info(f"💡 **Conseil :** {result.get('tip', 'N/A')}")

                        if result.get('simplified_explanation'):
                            with st.expander("📖 Explication modèle de l'IA"):
                                st.markdown(result['simplified_explanation'])

                        st.markdown(result.get('feedback', ''))

                    except Exception as e:
                        st.error(f"Erreur IA : {e}")

    with tab_history:
        st.subheader("📜 Historique Feynman")

        sessions = feynman_tracker.data.get('sessions', {})
        if not sessions:
            st.info("Aucune session Feynman encore. Lance-toi !")
        else:
            for cid, session in sorted(sessions.items(),
                                        key=lambda x: x[1].get('best_score', 0)):
                status_icon = "✅" if session['status'] == 'mastered' else ("📝" if session['status'] == 'in_progress' else "⚪")
                with st.expander(f"{status_icon} **{session.get('concept_name', cid)}** [{session.get('module', '?')}] — "
                               f"Score: {session['best_score']}% | Tentatives: {session['attempts']}"):
                    for i, attempt in enumerate(session.get('history', []), 1):
                        st.markdown(f"**Tentative {i}** ({attempt.get('date', '')[:10]}) — Score: {attempt['score']}%")
                        if attempt.get('gaps'):
                            st.caption(f"Lacunes: {', '.join(attempt['gaps'])}")

        # Concepts à revoir
        to_review = feynman_tracker.get_concepts_to_review()
        if to_review:
            st.divider()
            st.subheader("🔄 Concepts à revoir")
            for c in to_review[:10]:
                st.markdown(f"- 🔄 **{c.get('concept_name', '?')}** [{c.get('module', '?')}] — Score: {c['best_score']}%")


# ======================================================================
# 🎓 PAGE COACH EXPERT — IA spécialisée par domaine
# ======================================================================
elif page == "🎓 Coach Expert":
    st.header("🎓 Coach Expert — Ton prof spécialisé par domaine")
    st.markdown("""
**Un vrai formateur CIFER te dit exactement quoi étudier et à quel niveau.**

| Niveau | Signification | Méthode d'étude |
|--------|--------------|-----------------|
| 🔴 **DRILL** | Automatisme — réponse en 3 secondes | Quiz quotidien + flashcards + chrono |
| 🟠 **MAÎTRISER** | Comprendre + appliquer dans tout contexte | Feynman + cas pratiques + exercices |
| 🟡 **CONNAÎTRE** | Comprendre le principe, savoir expliquer | Flashcards + lecture active |
| 🟢 **RECONNAÎTRE** | Juste savoir que ça existe | Lecture seule, 1 passage |
""")

    try:
        from src.expert_coach import (
            COMPETENCE_MASTERY, MASTERY_LEVELS, MODULE_COACH_PROMPTS,
            get_all_drill_items, get_global_mastery_stats, get_module_mastery_summary,
            build_expert_coach_prompt, get_coach_for_module
        )
        from src.exam_focus import EXAM_WEIGHT

        tab_overview, tab_drill, tab_module, tab_coach_ia = st.tabs([
            "📊 Vue globale", "🔴 Plan de Drill", "📋 Par Module", "🤖 Coach IA"
        ])

        # -------- TAB 1 : VUE GLOBALE --------
        with tab_overview:
            stats = get_global_mastery_stats()
            st.subheader(f"📊 {stats['total']} compétences classées par niveau d'exigence")

            # KPI Cards
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("🔴 DRILL", stats['drill_total'],
                          help="À driller quotidiennement")
            with col2:
                st.metric("🟠 MAÎTRISER", stats['maitriser_total'],
                          help="Comprendre en profondeur + appliquer")
            with col3:
                st.metric("🟡 CONNAÎTRE", stats['connaitre_total'],
                          help="Comprendre le principe")
            with col4:
                st.metric("🟢 RECONNAÎTRE", stats['reconnaitre_total'],
                          help="Juste savoir que ça existe")

            st.divider()

            # Graphique par module
            st.subheader("📊 Répartition par module")
            import plotly.graph_objects as go

            modules_sorted = sorted(stats['by_module'].keys())
            fig = go.Figure()

            colors = {
                "drill": "#e53935",
                "maitriser": "#ff6f00",
                "connaitre": "#fdd835",
                "reconnaitre": "#43a047",
            }
            labels = {
                "drill": "🔴 Drill",
                "maitriser": "🟠 Maîtriser",
                "connaitre": "🟡 Connaître",
                "reconnaitre": "🟢 Reconnaître",
            }

            for level in ["drill", "maitriser", "connaitre", "reconnaitre"]:
                values = [stats['by_module'].get(m, {}).get(level, 0) for m in modules_sorted]
                fig.add_trace(go.Bar(
                    name=labels[level],
                    x=modules_sorted,
                    y=values,
                    marker_color=colors[level],
                ))

            fig.update_layout(
                barmode='stack',
                title="Niveaux de maîtrise requis par module",
                xaxis_title="Module",
                yaxis_title="Nombre de compétences",
                height=450,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            )
            st.plotly_chart(fig, use_container_width=True)

            # Poids d'examen overlay
            st.subheader("⚖️ Impact examen")
            st.caption("Modules triés par poids × nombre de compétences DRILL")
            impact_data = []
            for m, mod_counts in stats['by_module'].items():
                weight = EXAM_WEIGHT.get(m, 1)
                drill_count = mod_counts.get("drill", 0)
                maitriser_count = mod_counts.get("maitriser", 0)
                impact = weight * (drill_count * 3 + maitriser_count * 2)
                impact_data.append((m, weight, drill_count, maitriser_count, impact))
            
            impact_data.sort(key=lambda x: x[4], reverse=True)
            for m, weight, dc, mc, impact in impact_data:
                bar_len = min(impact * 2, 40)
                bar = "█" * bar_len
                st.markdown(f"**{m}** — {weight}q examen | {dc} drill + {mc} maîtriser = impact **{impact}**")
                st.progress(min(impact / 30, 1.0))

        # -------- TAB 2 : PLAN DE DRILL --------
        with tab_drill:
            st.subheader("🔴 Les compétences que tu dois DRILLER — Plan quotidien")
            st.markdown("""
> **Règle d'or :** Si tu te trompes sur un item DRILL à l'examen, tu perds des points FACILES.  
> Ces compétences doivent devenir des **automatismes**. Réponse en 3 secondes.
""")
            drills = get_all_drill_items()
            st.info(f"**{len(drills)} compétences** de niveau DRILL identifiées")

            # Grouper par module
            from collections import defaultdict as ddict
            drill_by_module = ddict(list)
            for d in drills:
                drill_by_module[d['module']].append(d)

            for module in sorted(drill_by_module.keys()):
                items = drill_by_module[module]
                weight = EXAM_WEIGHT.get(module, 1)
                with st.expander(f"🔴 {module} — {weight} question(s) examen — {len(items)} compétences DRILL", expanded=(weight >= 3)):
                    for item in items:
                        st.markdown(f"### 🔴 {item['competence']}")
                        st.markdown(f"**💬 Coach :** {item['coach_note']}")
                        st.markdown(f"**📝 Astuce examen :** {item['exam_tip']}")
                        if item['key_points']:
                            st.markdown("**🎯 Points clés à retenir PAR CŒUR :**")
                            for kp in item['key_points']:
                                st.markdown(f"  - ✅ {kp}")
                        st.divider()

            # Planning de drill quotidien
            st.divider()
            st.subheader("📅 Planning de Drill Quotidien Suggéré")
            st.markdown("""
| Moment | Durée | Quoi | Comment |
|--------|-------|------|---------|
| ☀️ Matin | 10 min | Flashcards DRILL | Réviser les 20 items les plus critiques |
| 🌤️ Midi | 5 min | Mini-quiz DRILL | 5 questions chronométrées sur les formules |
| 🌙 Soir | 15 min | Feynman sur 1 concept | Expliquer un concept DRILL à voix haute |
| 🔄 Weekend | 30 min | Exercices complets | Cas pratiques mélangeant plusieurs DRILL |
""")

        # -------- TAB 3 : PAR MODULE --------
        with tab_module:
            st.subheader("📋 Analyse détaillée par module")

            module_list = sorted(COMPETENCE_MASTERY.keys())
            selected_module = st.selectbox(
                "Choisis un module :",
                module_list,
                format_func=lambda m: f"{m} ({EXAM_WEIGHT.get(m, 1)}q) — {COMPETENCE_MASTERY.get(m, {}).get('module_coach_profile', '')}"
            )

            if selected_module:
                summary = get_module_mastery_summary(selected_module)
                if summary:
                    st.markdown(f"### 🎓 {summary['coach_profile']}")
                    st.info(f"📌 **Focus examen :** {summary['module_focus']}")

                    # Compteurs par niveau
                    cols = st.columns(4)
                    for idx, level in enumerate(["drill", "maitriser", "connaitre", "reconnaitre"]):
                        level_info = MASTERY_LEVELS.get(level, {})
                        count = summary['counts'].get(level, 0)
                        with cols[idx]:
                            st.metric(
                                f"{level_info['icon']} {level.upper()}",
                                count,
                                help=level_info.get('description', '')
                            )

                    st.divider()

                    # Détail par niveau
                    for level in ["drill", "maitriser", "connaitre", "reconnaitre"]:
                        level_info = MASTERY_LEVELS.get(level, {})
                        items = summary['by_level'].get(level, [])
                        if items:
                            st.markdown(f"### {level_info['icon']} {level_info['label']} — {len(items)} compétences")
                            st.caption(f"📖 Méthode : {level_info['study_method']}")
                            st.caption(f"⏰ Fréquence : {level_info['frequency']}")
                            st.caption(f"⚠️ Risque examen : {level_info['exam_risk']}")
                            
                            for item in items:
                                with st.container():
                                    st.markdown(f"**{item['competence']}**")
                                    st.markdown(f"💬 _{item['coach_note']}_")
                                    if item.get('exam_tip'):
                                        st.success(f"📝 Astuce : {item['exam_tip']}")
                                    if item.get('key_points'):
                                        kp_text = " | ".join(item['key_points'])
                                        st.caption(f"🎯 {kp_text}")
                                st.markdown("---")

        # -------- TAB 4 : COACH IA --------
        with tab_coach_ia:
            st.subheader("🤖 Demande conseil à ton Coach Expert IA")
            st.markdown("""
Sélectionne un module et pose ta question. L'IA se comportera comme un **vrai formateur spécialisé** 
dans ce domaine et te dira exactement ce que tu dois savoir, maîtriser ou ignorer.
""")

            coach_module = st.selectbox(
                "Module :",
                sorted(COMPETENCE_MASTERY.keys()),
                format_func=lambda m: f"{m} — {COMPETENCE_MASTERY.get(m, {}).get('module_coach_profile', '')}",
                key="coach_module_select"
            )

            coach_profile = get_coach_for_module(coach_module)
            if coach_profile:
                st.info(f"🎓 **Ton coach :** {coach_profile.get('role', '')}")
                st.caption(f"Expertise : {coach_profile.get('expertise', '')}")
                st.caption(f"Style : {coach_profile.get('tone', '')}")

            # Sélection de compétence
            comp_list = list(COMPETENCE_MASTERY.get(coach_module, {}).get("competences", {}).keys())
            selected_comp = st.selectbox(
                "Compétence (optionnel) :",
                ["— Général —"] + comp_list,
                key="coach_comp_select"
            )

            user_question = st.text_area(
                "Ta question au coach :",
                placeholder="Ex: Comment je dois m'y prendre pour apprendre les 5 règles de sécurité ? C'est quoi le plus important à retenir pour l'examen ?",
                key="coach_question"
            )

            if st.button("🎓 Demander au Coach", type="primary", key="btn_coach"):
                if not user_question.strip():
                    st.warning("Pose une question à ton coach !")
                else:
                    concept_name = selected_comp if selected_comp != "— Général —" else f"Module {coach_module} en général"
                    prompt = build_expert_coach_prompt(
                        coach_module, concept_name, user_question
                    )

                    with st.spinner("🎓 Ton coach réfléchit..."):
                        try:
                            model = genai.GenerativeModel("gemini-2.0-flash")
                            response = model.generate_content(prompt)
                            coach_response = response.text

                            st.markdown("### 🎓 Réponse du Coach Expert")
                            
                            # Essayer de parser le JSON
                            import json as json_lib
                            try:
                                # Extraire le JSON de la réponse
                                json_text = coach_response
                                if "```json" in json_text:
                                    json_text = json_text.split("```json")[1].split("```")[0]
                                elif "```" in json_text:
                                    json_text = json_text.split("```")[1].split("```")[0]
                                
                                data = json_lib.loads(json_text.strip())
                                
                                # Afficher le verdict
                                verdict = data.get("verdict", "")
                                verdict_colors = {
                                    "DRILL": "🔴", "MAÎTRISER": "🟠",
                                    "CONNAÎTRE": "🟡", "RECONNAÎTRE": "🟢"
                                }
                                verdict_icon = verdict_colors.get(verdict, "📌")
                                st.markdown(f"## {verdict_icon} Verdict : **{verdict}**")
                                
                                # Message du coach
                                st.markdown(f"### 💬 {data.get('message', '')}")
                                
                                # Ce qu'il FAUT savoir
                                must = data.get("must_know", [])
                                if must:
                                    st.markdown("### ✅ Ce que tu DOIS savoir par cœur :")
                                    for m in must:
                                        st.markdown(f"- 🔴 **{m}**")
                                
                                # Nice to know
                                nice = data.get("nice_to_know", [])
                                if nice:
                                    st.markdown("### 🟡 Bien à savoir mais pas critique :")
                                    for n in nice:
                                        st.markdown(f"- 🟡 {n}")
                                
                                # Skip
                                skip = data.get("skip", [])
                                if skip:
                                    st.markdown("### ⏭️ Tu peux ignorer :")
                                    for s in skip:
                                        st.markdown(f"- ⚪ ~~{s}~~")
                                
                                # Exercice de drill
                                drill_ex = data.get("drill_exercise", "")
                                if drill_ex:
                                    st.info(f"🏋️ **Exercice rapide (2 min) :** {drill_ex}")
                                
                                # Piège d'examen
                                trap = data.get("exam_trap", "")
                                if trap:
                                    st.warning(f"⚠️ **Piège classique :** {trap}")
                                
                                # Mnémotechnique
                                mnemonic = data.get("mnemonic", "")
                                if mnemonic:
                                    st.success(f"🧠 **Mnémotechnique :** {mnemonic}")
                                    
                            except (json_lib.JSONDecodeError, IndexError):
                                # Si le JSON ne parse pas, afficher la réponse brute
                                st.markdown(coach_response)

                        except Exception as e:
                            st.error(f"❌ Erreur IA : {e}")

            # Afficher les infos de compétence sélectionnée
            if selected_comp != "— Général —":
                st.divider()
                comp_data = COMPETENCE_MASTERY.get(coach_module, {}).get("competences", {}).get(selected_comp, {})
                if comp_data:
                    level = comp_data.get("level", "connaitre")
                    level_info = MASTERY_LEVELS.get(level, {})
                    st.markdown(f"### {level_info.get('icon', '')} Niveau requis : **{level_info.get('label', '')}**")
                    st.markdown(f"_{level_info.get('description', '')}_")
                    st.markdown(f"**💬 Coach :** {comp_data.get('coach_note', '')}")
                    st.markdown(f"**📝 Astuce examen :** {comp_data.get('exam_tip', '')}")
                    if comp_data.get('key_points'):
                        st.markdown("**🎯 Points clés :**")
                        for kp in comp_data['key_points']:
                            st.markdown(f"  - {kp}")

    except Exception as e:
        st.error(f"❌ Erreur lors du chargement du module Coach : {e}")
        import traceback
        st.code(traceback.format_exc())


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
        
        # ===== METRIQUES EN HAUT — DESIGN PREMIUM =====
        days_left = stats.get('days_until_exam', 0)
        total_hours = revision_plan.get('total_hours', 0)
        total_concepts = revision_plan.get('total_concepts', 0)
        total_sessions = revision_plan.get('total_sessions', 0)
        
        # Calcul du % de progression (sessions passées)
        today_str = datetime.now().strftime('%Y-%m-%d')
        past_sessions = [s for s in sessions if s['date'] < today_str]
        future_sessions = [s for s in sessions if s['date'] >= today_str]
        progress_pct = len(past_sessions) / max(1, len(sessions))
        
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #1a237e 0%, #0d47a1 50%, #01579b 100%); 
                     padding: 1.5rem 2rem; border-radius: 16px; color: white; margin-bottom: 1.5rem;
                     box-shadow: 0 8px 32px rgba(0,0,0,0.15);">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 1rem;">
                <div style="text-align: center;">
                    <div style="font-size: 2.5rem; font-weight: bold;">{days_left}</div>
                    <div style="opacity: 0.8; font-size: 0.85rem;">Jours restants</div>
                </div>
                <div style="text-align: center;">
                    <div style="font-size: 2.5rem; font-weight: bold;">{total_hours:.0f}h</div>
                    <div style="opacity: 0.8; font-size: 0.85rem;">Heures planifiées</div>
                </div>
                <div style="text-align: center;">
                    <div style="font-size: 2.5rem; font-weight: bold;">{total_concepts}</div>
                    <div style="opacity: 0.8; font-size: 0.85rem;">Concepts à couvrir</div>
                </div>
                <div style="text-align: center;">
                    <div style="font-size: 2.5rem; font-weight: bold;">{len(future_sessions)}</div>
                    <div style="opacity: 0.8; font-size: 0.85rem;">Sessions à venir</div>
                </div>
                <div style="text-align: center;">
                    <div style="font-size: 2.5rem; font-weight: bold;">{progress_pct*100:.0f}%</div>
                    <div style="opacity: 0.8; font-size: 0.85rem;">Progression</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Barre de progression exam
        st.progress(progress_pct, text=f"📅 Examen le {revision_plan.get('exam_date', 'N/A')} — {progress_pct*100:.0f}% du parcours écoulé")
        
        # ===== ONGLETS VISUELS REFONDUS =====
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Vue d'ensemble", "📅 Semaine en cours", "🗓️ Calendrier", "📈 Progression", "📋 Toutes les sessions"])
        
        with tab1:
            col1, col2 = st.columns(2)
            
            with col1:
                # Graphique en anneau - Sessions par priorité (design amélioré)
                st.subheader("Sessions par priorité")
                priority_data = stats.get('sessions_by_priority', {})
                if priority_data:
                    fig_priority = go.Figure(data=[go.Pie(
                        labels=['🔴 Haute', '🟡 Moyenne', '🟢 Basse'],
                        values=[priority_data.get('high', 0), priority_data.get('medium', 0), priority_data.get('low', 0)],
                        hole=.5,
                        marker_colors=['#e53935', '#fdd835', '#43a047'],
                        textinfo='label+percent',
                        textfont_size=13
                    )])
                    fig_priority.update_layout(
                        height=320, 
                        margin=dict(t=20, b=20, l=20, r=20),
                        showlegend=False,
                        annotations=[dict(text=f"{total_sessions}<br>sessions", x=0.5, y=0.5, font_size=16, showarrow=False)]
                    )
                    st.plotly_chart(fig_priority, use_container_width=True)
            
            with col2:
                # Graphique - Sessions par type (design amélioré)
                st.subheader("Type de sessions")
                type_data = stats.get('sessions_by_type', {})
                if type_data:
                    fig_type = go.Figure(data=[go.Pie(
                        labels=['📚 Apprentissage', '🔄 Révision', '✏️ Pratique'],
                        values=[type_data.get('new_learning', 0), type_data.get('revision', 0), type_data.get('practice', 0)],
                        hole=.5,
                        marker_colors=['#1E88E5', '#7E57C2', '#26A69A'],
                        textinfo='label+percent',
                        textfont_size=13
                    )])
                    fig_type.update_layout(
                        height=320, 
                        margin=dict(t=20, b=20, l=20, r=20),
                        showlegend=False
                    )
                    st.plotly_chart(fig_type, use_container_width=True)
            
            # Timeline des jalons — design amélioré
            st.subheader("🏁 Jalons du parcours")
            milestones = revision_plan.get('milestones', [])
            if milestones:
                for i, m in enumerate(milestones):
                    m_date = m.get('date', '')
                    m_name = m.get('name', '')
                    m_obj = m.get('objective', '')
                    m_progress = m.get('progress', 0)
                    is_past = m_date < today_str
                    
                    icon = "✅" if is_past else "🔜"
                    color = "#4CAF50" if is_past else "#1976D2"
                    
                    st.markdown(f"""
                    <div style="display: flex; align-items: center; padding: 0.5rem 1rem; margin: 0.3rem 0; 
                                border-left: 4px solid {color}; background: {'#e8f5e9' if is_past else '#e3f2fd'}; 
                                border-radius: 0 8px 8px 0;">
                        <span style="font-size: 1.3rem; margin-right: 0.8rem;">{icon}</span>
                        <div style="flex: 1;">
                            <strong>{m_name}</strong> — {m_obj}
                            <br><small style="color: #666;">{m_date} · {m_progress}%</small>
                        </div>
                        <div style="width: 60px; text-align: right; font-weight: bold; color: {color};">{m_progress}%</div>
                    </div>
                    """, unsafe_allow_html=True)
            
            # Distribution par catégorie
            st.subheader("📂 Concepts par catégorie")
            categories = revision_plan.get('categories', {})
            if categories and isinstance(categories, dict):
                cat_counts = {cat: len(concepts) for cat, concepts in categories.items()}
                sorted_cats = sorted(cat_counts.items(), key=lambda x: x[1], reverse=True)[:10]
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
            # SEMAINE EN COURS — vue la plus utile au quotidien
            st.subheader("📅 Votre semaine de révision")
            
            today = datetime.now()
            # Début de la semaine (lundi)
            start_of_week = today - timedelta(days=today.weekday())
            end_of_week = start_of_week + timedelta(days=6)
            
            week_sessions = [s for s in sessions 
                           if start_of_week.strftime('%Y-%m-%d') <= s['date'] <= end_of_week.strftime('%Y-%m-%d')]
            
            if not week_sessions:
                st.info("Aucune session planifiée cette semaine.")
            else:
                # Charger le concept_map une seule fois pour la semaine
                concept_dict = {}
                if concept_map and 'nodes' in concept_map:
                    concept_dict = {node['name']: node for node in concept_map['nodes']}
                
                total_week_min = sum(s['duration_minutes'] for s in week_sessions)
                st.markdown(f"**{len(week_sessions)} sessions** · **{total_week_min} min** de révision prévues")
                st.markdown("---")
                
                # Afficher chaque jour de la semaine
                days_fr = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche']
                
                for day_offset in range(7):
                    current_day = start_of_week + timedelta(days=day_offset)
                    day_str = current_day.strftime('%Y-%m-%d')
                    day_name = days_fr[day_offset]
                    day_sessions = [s for s in week_sessions if s['date'] == day_str]
                    
                    is_today = day_str == today_str
                    is_past = day_str < today_str
                    
                    if day_sessions:
                        for session in day_sessions:
                            priority_color = {'high': '#e53935', 'medium': '#fb8c00', 'low': '#43a047'}.get(session['priority'], '#757575')
                            type_icon = {'new_learning': '📚', 'revision': '🔄', 'practice': '✏️'}.get(session['session_type'], '📖')
                            bg_color = '#fff8e1' if is_today else ('#f5f5f5' if is_past else '#ffffff')
                            border = '3px solid #ff9800' if is_today else f'3px solid {priority_color}'
                            today_badge = ' <span style="background: #ff9800; color: white; padding: 2px 8px; border-radius: 12px; font-size: 0.75rem; margin-left: 8px;">AUJOURD\'HUI</span>' if is_today else ''
                            
                            st.markdown(f"""
                            <div style="border-left: {border}; padding: 1rem 1.2rem; margin: 0.5rem 0; 
                                        background: {bg_color}; border-radius: 0 12px 12px 0;
                                        box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
                                <div style="display: flex; justify-content: space-between; align-items: center;">
                                    <div>
                                        <strong style="font-size: 1.1rem;">{type_icon} {day_name} {current_day.strftime('%d/%m')}</strong>{today_badge}
                                        <br><span style="color: #666;">{session['duration_minutes']} min · {session['category']}</span>
                                    </div>
                                    <div style="text-align: right;">
                                        <span style="background: {priority_color}; color: white; padding: 2px 10px; border-radius: 12px; font-size: 0.8rem;">
                                            {'Priorité haute' if session['priority'] == 'high' else 'Priorité moyenne' if session['priority'] == 'medium' else 'Priorité basse'}
                                        </span>
                                    </div>
                                </div>
                                <div style="margin-top: 0.5rem; font-size: 0.9rem;">
                                    {''.join(f'<div style="margin: 2px 0;">• <strong>{c}</strong></div>' for c in session['concepts'][:5])}
                                    {'<div style="color: #999;">... +' + str(len(session["concepts"]) - 5) + ' autres</div>' if len(session["concepts"]) > 5 else ''}
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                    elif not is_past:
                        st.markdown(f"""
                        <div style="padding: 0.5rem 1.2rem; margin: 0.3rem 0; color: #aaa; font-size: 0.9rem;">
                            {day_name} {current_day.strftime('%d/%m')} — <em>Pas de session</em>
                        </div>
                        """, unsafe_allow_html=True)
            
            # Navigation semaine
            st.markdown("---")
            st.caption("💡 Les sessions s'adaptent à votre charge : 30 min en semaine, 8h le weekend.")
        
        with tab3:
            # Calendrier heatmap
            st.subheader("🗓️ Calendrier des sessions")
            
            if sessions:
                session_dates = [s['date'] for s in sessions]
                session_durations = [s['duration_minutes'] for s in sessions]
                
                df_calendar = pd.DataFrame({
                    'date': pd.to_datetime(session_dates),
                    'duration': session_durations
                })
                df_calendar['week'] = df_calendar['date'].dt.isocalendar().week.astype(int)
                df_calendar['day'] = df_calendar['date'].dt.dayofweek
                df_calendar['month'] = df_calendar['date'].dt.strftime('%Y-%m')
                
                # Heatmap pour les 12 prochaines semaines
                today = datetime.now()
                next_weeks = df_calendar[
                    (df_calendar['date'] >= today - timedelta(weeks=1)) & 
                    (df_calendar['date'] <= today + timedelta(weeks=12))
                ]
                
                if not next_weeks.empty:
                    fig_heatmap = go.Figure(data=go.Heatmap(
                        x=next_weeks['week'],
                        y=next_weeks['day'],
                        z=next_weeks['duration'],
                        colorscale=[
                            [0, '#e3f2fd'],
                            [0.25, '#90caf9'],
                            [0.5, '#42a5f5'],
                            [0.75, '#1e88e5'],
                            [1, '#0d47a1']
                        ],
                        hoverongaps=False,
                        hovertemplate='Semaine %{x}<br>%{text}<br>%{z} minutes<extra></extra>',
                        text=[[days_fr[d] if d < 7 else '' for d in next_weeks['day'].unique()] for _ in next_weeks['week'].unique()],
                        colorbar=dict(title='Min.', ticksuffix=' min')
                    ))
                    fig_heatmap.update_yaxes(
                        ticktext=['Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam', 'Dim'],
                        tickvals=[0, 1, 2, 3, 4, 5, 6],
                        autorange='reversed'
                    )
                    fig_heatmap.update_xaxes(title='Semaine de l\'année')
                    fig_heatmap.update_layout(
                        height=300,
                        margin=dict(l=60, r=20, t=20, b=40)
                    )
                    st.plotly_chart(fig_heatmap, use_container_width=True)
                
                # Distribution heures par mois
                st.subheader("📊 Charge de travail par mois")
                df_monthly = df_calendar.groupby('month').agg(
                    total_min=('duration', 'sum'),
                    sessions=('duration', 'count')
                ).reset_index()
                df_monthly['heures'] = (df_monthly['total_min'] / 60).round(1)
                
                fig_monthly = px.bar(
                    df_monthly,
                    x='month',
                    y='heures',
                    text='heures',
                    color='heures',
                    color_continuous_scale='Blues',
                    labels={'month': 'Mois', 'heures': 'Heures'}
                )
                fig_monthly.update_traces(texttemplate='%{text}h', textposition='outside')
                fig_monthly.update_layout(
                    height=350,
                    showlegend=False,
                    xaxis_title='',
                    yaxis_title='Heures de révision',
                    margin=dict(t=30, b=20)
                )
                st.plotly_chart(fig_monthly, use_container_width=True)
        
        with tab4:
            # Graphique de progression amélioré
            st.subheader("📈 Courbe de progression")
            
            if sessions:
                df_progress = pd.DataFrame(sessions)
                df_progress['date'] = pd.to_datetime(df_progress['date'])
                df_progress = df_progress.sort_values('date')
                df_progress['cumulative_concepts'] = df_progress['concepts'].apply(len).cumsum()
                df_progress['cumulative_hours'] = (df_progress['duration_minutes'].cumsum() / 60).round(1)
                
                fig_progress = go.Figure()
                
                # Zone remplie pour les heures
                fig_progress.add_trace(go.Scatter(
                    x=df_progress['date'],
                    y=df_progress['cumulative_hours'],
                    mode='lines',
                    name='Heures cumulées',
                    line=dict(color='#1E88E5', width=3),
                    fill='tozeroy',
                    fillcolor='rgba(30, 136, 229, 0.15)'
                ))
                
                # Ligne pour les concepts
                fig_progress.add_trace(go.Scatter(
                    x=df_progress['date'],
                    y=df_progress['cumulative_concepts'],
                    mode='lines',
                    name='Concepts cumulés',
                    line=dict(color='#43A047', width=2, dash='dot'),
                    yaxis='y2'
                ))
                
                # Marqueur "Aujourd'hui"
                fig_progress.add_vline(
                    x=today_str,
                    line_dash='dash',
                    line_color='#FF5722',
                    line_width=2
                )
                fig_progress.add_annotation(
                    x=today_str,
                    y=1,
                    yref='paper',
                    text='Aujourd\'hui',
                    showarrow=False,
                    font=dict(color='#FF5722'),
                    yshift=10
                )
                
                # Jalons
                milestones = revision_plan.get('milestones', [])
                for m in milestones:
                    try:
                        milestone_date_str = str(pd.to_datetime(m['date']).strftime('%Y-%m-%d'))
                        fig_progress.add_vline(
                            x=milestone_date_str,
                            line_dash='dot',
                            line_color='rgba(0,0,0,0.2)'
                        )
                        fig_progress.add_annotation(
                            x=milestone_date_str,
                            y=1,
                            yref='paper',
                            text=m.get('name', ''),
                            showarrow=False,
                            font=dict(size=10),
                            yshift=10
                        )
                    except Exception:
                        pass
                
                fig_progress.update_layout(
                    height=450,
                    xaxis_title='Date',
                    yaxis_title='Heures de révision',
                    yaxis2=dict(
                        title='Concepts couverts',
                        overlaying='y',
                        side='right',
                        showgrid=False
                    ),
                    hovermode='x unified',
                    legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
                    margin=dict(t=60, b=40)
                )
                st.plotly_chart(fig_progress, use_container_width=True)
                
                # Stats résumées 
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("📚 Concepts à couvrir", total_concepts)
                with col2:
                    avg_per_week = round(total_hours / max(1, days_left / 7), 1)
                    st.metric("⏱️ Heures/semaine requises", f"{avg_per_week}h")
                with col3:
                    avg_concepts = stats.get('average_concepts_per_session', 0)
                    st.metric("📖 Concepts/session (moy)", f"{avg_concepts:.1f}")
                with col4:
                    st.metric("📅 Date examen", revision_plan.get('exam_date', 'N/A'))
        
        with tab5:
            # Liste des sessions avec meilleur design
            st.subheader("📋 Toutes les sessions à venir")
            
            today = datetime.now().strftime('%Y-%m-%d')
            upcoming = [s for s in sessions if s['date'] >= today]
            
            # Filtres améliorés 
            col1, col2, col3 = st.columns(3)
            with col1:
                filter_priority = st.multiselect(
                    "Priorité",
                    ['high', 'medium', 'low'],
                    default=['high', 'medium', 'low'],
                    format_func=lambda x: {'high': '🔴 Haute', 'medium': '🟡 Moyenne', 'low': '🟢 Basse'}[x]
                )
            with col2:
                filter_type = st.multiselect(
                    "Type",
                    ['new_learning', 'revision', 'practice'],
                    default=['new_learning', 'revision', 'practice'],
                    format_func=lambda x: {'new_learning': '📚 Apprentissage', 'revision': '🔄 Révision', 'practice': '✏️ Pratique'}[x]
                )
            with col3:
                num_sessions = st.slider("Nombre à afficher", 5, 50, 14)
            
            filtered = [s for s in upcoming 
                       if s['priority'] in filter_priority and s.get('session_type', 'new_learning') in filter_type][:num_sessions]
            
            if filtered:
                # Charger le concept_map une seule fois
                concept_dict = {}
                if concept_map and 'nodes' in concept_map:
                    concept_dict = {node['name']: node for node in concept_map['nodes']}
                
                for session in filtered:
                    priority_icon = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}.get(session['priority'], '⚪')
                    type_icon = {'new_learning': '📚', 'revision': '🔄', 'practice': '✏️'}.get(session['session_type'], '📖')
                    
                    with st.expander(f"{priority_icon} {type_icon} {session['day_name']} {session['date']} — {session['duration_minutes']} min · {session['category']}"):
                        col1, col2 = st.columns([2, 1])
                        with col1:
                            st.markdown("**Concepts à étudier :**")
                            for concept_name in session['concepts'][:10]:
                                concept_info = concept_dict.get(concept_name, {})
                                source_doc = concept_info.get('source_document', '')
                                page_ref = concept_info.get('page_references', '')
                                
                                if page_ref and source_doc:
                                    st.markdown(f"  - **{concept_name}**")
                                    st.caption(f"    📄 {source_doc} · 📖 {page_ref}")
                                elif source_doc:
                                    st.markdown(f"  - **{concept_name}**")
                                    st.caption(f"    📄 {source_doc}")
                                else:
                                    st.markdown(f"  - {concept_name}")
                            
                            if len(session['concepts']) > 10:
                                st.caption(f"... et {len(session['concepts']) - 10} autres")
                        with col2:
                            if session.get('objectives'):
                                st.markdown("**Objectifs :**")
                                for obj in session['objectives']:
                                    st.markdown(f"  - {obj}")
                            st.markdown(f"**Module :** {session.get('module', 'N/A')}")
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


elif page == "📊 Ma Progression":
    st.header("📊 Suivi de Ma Progression")
    
    # Charger le tracker de progression
    from src.progress_tracker import ProgressTracker
    from src.course_schedule_manager import CourseScheduleManager
    tracker = ProgressTracker()
    
    # Charger le planning de révision
    revision_plan = load_revision_plan()
    concept_map = load_concept_map()
    
    if not revision_plan:
        st.warning("⚠️ Vous devez d'abord générer un planning de révision")
        if st.button("📆 Aller au Planning Révisions"):
            st.session_state['page'] = "📆 Planning Révisions"
            st.rerun()
        st.stop()
    
    # Charger le calendrier des cours et synchroniser les statuts
    config = load_config()
    schedule_manager = CourseScheduleManager(config)
    schedule_manager.load()  # Auto-sync les statuts des cours passés
    
    # Synchronisation automatique progression ↔ calendrier
    sync_result = tracker.sync_with_calendar(
        revision_plan=revision_plan,
        course_schedule_sessions=schedule_manager.sessions,
        concept_map=concept_map
    )
    
    # Afficher les statistiques globales
    st.markdown("### 📈 Statistiques Globales")
    
    stats = tracker.get_stats()
    course_stats = sync_result.get('course_stats', {})
    
    # Bandeau de synchronisation cours
    if course_stats:
        completed_courses = course_stats.get('completed_course_sessions', 0)
        total_courses = course_stats.get('total_course_sessions', 0)
        concepts_seen = course_stats.get('concepts_seen_in_class', 0)
        total_concepts_map = len(concept_map.get('nodes', [])) if concept_map else 0
        completed_mods = course_stats.get('completed_modules', [])
        
        course_pct = (completed_courses / max(1, total_courses)) * 100
        
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #1b5e20 0%, #2e7d32 50%, #388e3c 100%); 
                     padding: 1rem 1.5rem; border-radius: 12px; color: white; margin-bottom: 1rem;
                     box-shadow: 0 4px 16px rgba(0,0,0,0.1);">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 1rem;">
                <div style="text-align: center;">
                    <div style="font-size: 1.8rem; font-weight: bold;">{completed_courses}/{total_courses}</div>
                    <div style="opacity: 0.85; font-size: 0.8rem;">Sessions de cours</div>
                </div>
                <div style="text-align: center;">
                    <div style="font-size: 1.8rem; font-weight: bold;">{course_pct:.0f}%</div>
                    <div style="opacity: 0.85; font-size: 0.8rem;">Formation avancée</div>
                </div>
                <div style="text-align: center;">
                    <div style="font-size: 1.8rem; font-weight: bold;">{len(completed_mods)}</div>
                    <div style="opacity: 0.85; font-size: 0.8rem;">Modules vus en cours</div>
                </div>
                <div style="text-align: center;">
                    <div style="font-size: 1.8rem; font-weight: bold;">{concepts_seen}/{total_concepts_map}</div>
                    <div style="opacity: 0.85; font-size: 0.8rem;">Concepts vus en cours</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        completion_rate = stats['completion_rate']
        st.metric(
            "Révisions Complétées", 
            f"{stats['completed_sessions']}/{stats['total_sessions']}",
            f"{completion_rate:.1f}%"
        )
        st.progress(completion_rate / 100)
    
    with col2:
        mastery_rate = stats['mastery_rate']
        st.metric(
            "Concepts Maîtrisés",
            f"{stats['mastered_concepts']}/{stats['total_concepts']}",
            f"{mastery_rate:.1f}%"
        )
        st.progress(mastery_rate / 100)
    
    with col3:
        remaining_sessions = stats['total_sessions'] - stats['completed_sessions']
        st.metric("Sessions Restantes", remaining_sessions)
    
    with col4:
        if stats['last_update']:
            from datetime import datetime
            last_update = datetime.fromisoformat(stats['last_update'])
            st.metric("Dernière MAJ", last_update.strftime("%d/%m/%Y"))
        else:
            st.metric("Dernière MAJ", "Jamais")
    
    st.divider()
    
    # Onglets pour les différentes vues
    tab1, tab2, tab3 = st.tabs(["📅 Sessions de Révision", "🎯 Concepts", "📊 Historique"])
    
    with tab1:
        st.markdown("### Sessions de Révision")
        st.caption("Cochez les sessions que vous avez complétées")
        
        sessions = revision_plan.get('sessions', [])
        
        # Grouper par catégorie
        categories = {}
        for session in sessions:
            cat = session.get('category', 'Autre')
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(session)
        
        # Afficher par catégorie
        for category, cat_sessions in categories.items():
            # Calculer le nombre de sessions complétées avec le bon ID
            completed_count = 0
            for idx_c, s_c in enumerate(cat_sessions):
                sid = s_c.get('id') or f"{category}_{s_c.get('date', '')}_{idx_c}"
                if tracker.is_session_completed(sid):
                    completed_count += 1
            
            with st.expander(f"📚 {category} ({completed_count}/{len(cat_sessions)} complétées)", expanded=False):
                for idx, session in enumerate(cat_sessions):
                    # Créer un ID unique pour chaque session
                    session_id = session.get('id') or f"{category}_{session.get('date', '')}_{idx}"
                    is_completed = tracker.is_session_completed(session_id)
                    
                    col_check, col_info = st.columns([1, 9])
                    
                    with col_check:
                        if st.checkbox("", value=is_completed, key=f"session_{session_id}", label_visibility="collapsed"):
                            if not is_completed:
                                tracker.mark_session_completed(session_id)
                                st.rerun()
                        else:
                            if is_completed:
                                tracker.unmark_session_completed(session_id)
                                st.rerun()
                    
                    with col_info:
                        status_icon = "✅" if is_completed else "⏳"
                        # Afficher le module et les concepts (pas 'topics' qui n'existe pas)
                        concepts_list = session.get('concepts', [])
                        concept_label = concepts_list[0] if concepts_list else session.get('category', 'Session')
                        # Si plusieurs concepts, montrer le nombre
                        extra = f" (+{len(concepts_list)-1})" if len(concepts_list) > 1 else ""
                        st.markdown(f"{status_icon} **{session.get('module', '')}** - {concept_label}{extra}")
                        
                        # Afficher la durée en minutes et le type de session
                        duration = session.get('duration_minutes', 0)
                        session_type_map = {
                            'new_learning': '📖 Nouveau',
                            'review': '🔄 Révision',
                            'spaced_repetition': '🧠 Répétition espacée',
                            'exam_prep': '📝 Prépa examen'
                        }
                        session_type = session_type_map.get(session.get('session_type', ''), '')
                        priority_icon = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}.get(session.get('priority', ''), '')
                        st.caption(f"📅 {session.get('date', 'N/A')} | ⏱️ {duration} min | {session_type} {priority_icon}")
    
    with tab2:
        st.markdown("### 🎯 Concepts à Maîtriser")
        st.caption("Marquez les concepts que vous maîtrisez parfaitement")
        
        if not concept_map or not concept_map.get('nodes'):
            st.info("Aucun concept analysé pour le moment")
        else:
            nodes = concept_map['nodes']
            
            # Filtrer par niveau d'importance
            importance_filter = st.selectbox(
                "Filtrer par importance",
                ["Tous", "🔴 Critique", "🟠 Très Important", "🟡 Important", "🟢 Faible"]
            )
            
            importance_map = {
                "🔴 Critique": "critical",
                "🟠 Très Important": "high",
                "🟡 Important": "medium",
                "🟢 Faible": "low",
            }
            
            if importance_filter != "Tous":
                target = importance_map.get(importance_filter, 'medium')
                nodes = [n for n in nodes if n.get('importance', 'medium') == target]
            
            # Grouper par catégorie
            concept_categories = {}
            for node in nodes:
                cat = node.get('category', 'Autre')
                if cat not in concept_categories:
                    concept_categories[cat] = []
                concept_categories[cat].append(node)
            
            for cat, concepts in concept_categories.items():
                mastered_count = len([c for c in concepts if tracker.is_concept_mastered(c.get('id', ''))])
                with st.expander(f"📖 {cat} ({mastered_count}/{len(concepts)} maîtrisés)", expanded=False):
                    for concept in concepts:
                        concept_id = concept.get('id', '')
                        is_mastered = tracker.is_concept_mastered(concept_id)
                        
                        col_check, col_info = st.columns([1, 9])
                        
                        with col_check:
                            if st.checkbox("", value=is_mastered, key=f"concept_{concept_id}", label_visibility="collapsed"):
                                if not is_mastered:
                                    tracker.mark_concept_mastered(concept_id)
                                    st.rerun()
                            else:
                                if is_mastered:
                                    tracker.unmark_concept_mastered(concept_id)
                                    st.rerun()
                        
                        with col_info:
                            status_icon = "🌟" if is_mastered else "📝"
                            importance = concept.get('importance', 'medium')
                            # Mapper les niveaux d'importance aux emojis
                            importance_emoji = {
                                'critical': '🔴',
                                'high': '🟠', 
                                'medium': '🟡',
                                'low': '🟢'
                            }.get(importance, '🟡')
                            st.markdown(f"{status_icon} **{concept.get('name', 'Concept')}** {importance_emoji}")
                            desc = concept.get('description') or ''
                            st.caption(desc[:150] + ('...' if len(desc) > 150 else ''))
    
    with tab3:
        st.markdown("### 📊 Historique et Tendances")
        
        # Afficher les dernières activités
        st.subheader("Activité Récente")
        recent = tracker.get_recent_activity(limit=10)
        
        if recent:
            for activity in recent:
                st.write(f"✅ Session {activity['session_id']} complétée")
        else:
            st.info("Aucune activité récente")
        
        # --- CONCEPTS FAIBLES (QUIZ ADAPTATIF) ---
        st.divider()
        st.subheader("🎯 Concepts Faibles — Détectés par vos Quiz")
        st.markdown("*Les concepts que vous ratez souvent sont suivis ici. Ils seront priorisés dans les prochains quiz adaptatifs.*")
        
        from src.weak_concepts_tracker import WeakConceptsTracker
        weak_tracker_prog = WeakConceptsTracker()
        weak_stats_prog = weak_tracker_prog.get_stats()
        
        if weak_stats_prog['total_tracked'] == 0:
            st.info("Aucun concept suivi pour l'instant. Faites des quiz pour alimenter le tracker !")
        else:
            col_w1, col_w2, col_w3, col_w4 = st.columns(4)
            with col_w1:
                st.metric("Concepts suivis", weak_stats_prog['total_tracked'])
            with col_w2:
                st.metric("🔴 Faibles", weak_stats_prog['weak_count'])
            with col_w3:
                st.metric("🟢 Acquis", weak_stats_prog['strong_count'])
            with col_w4:
                st.metric("Maîtrise moy.", f"{weak_stats_prog['average_mastery']:.0f}%")
            
            # Liste des concepts faibles
            weak_list = weak_tracker_prog.get_weak_concepts(min_errors=1, max_mastery=60)
            
            if weak_list:
                st.markdown("#### 🔴 Concepts à renforcer (triés par priorité)")
                for i, wc in enumerate(weak_list[:15], 1):
                    mastery = wc['mastery_score']
                    m_color = '🔴' if mastery < 30 else ('🟠' if mastery < 50 else '🟡')
                    module_tag = f"[{wc['module']}]" if wc.get('module') else ''
                    st.markdown(
                        f"{i}. {m_color} **{wc['concept_name']}** {module_tag} — "
                        f"Maîtrise: {mastery}% | Erreurs: {wc['error_count']} | "
                        f"Succès: {wc['success_count']}/{wc['total_attempts']}"
                    )
            else:
                st.success("✅ Aucun concept réellement faible détecté. Bien joué !")
            
            # Modules faibles
            weak_modules_data = weak_tracker_prog.get_weak_modules()
            if weak_modules_data:
                st.markdown("#### 📊 Taux d'erreur par module")
                for mod, data in list(weak_modules_data.items())[:10]:
                    if data['total'] > 0:
                        err_rate = data['error_rate']
                        bar_color = '🔴' if err_rate > 50 else ('🟠' if err_rate > 30 else '🟢')
                        st.markdown(f"{bar_color} **{mod}** — {err_rate:.0f}% d'erreurs ({data['errors']}/{data['total']})")
                        if data['weak_concepts']:
                            st.caption(f"   Concepts faibles : {', '.join(data['weak_concepts'][:5])}")
        
        # Bouton pour réinitialiser
        st.divider()
        st.warning("⚠️ Zone Dangereuse")
        col_reset1, col_reset2 = st.columns(2)
        with col_reset1:
            confirm_reset = st.checkbox("Je confirme vouloir réinitialiser", key="confirm_reset_prog")
        with col_reset2:
            if confirm_reset:
                if st.button("🔄 Réinitialiser Toute la Progression", type="secondary"):
                    tracker.reset_progress()
                    weak_tracker_prog.reset()
                    st.success("✅ Progression réinitialisée")
                    st.rerun()


elif page == "🧠 Quiz":
    st.header("🧠 Quiz d'Auto-Évaluation")
    
    from src.quiz_generator import QuizGenerator, QUESTION_TYPES, evaluate_answer
    import time
    
    # Charger les concepts
    concept_map = load_concept_map()
    
    if not concept_map or not concept_map.get('nodes'):
        st.warning("⚠️ Vous devez d'abord analyser vos documents pour générer des quiz")
        if st.button("🔬 Aller à l'Analyseur"):
            st.session_state['page'] = "🔬 Analyser"
            st.rerun()
        st.stop()
    
    # Initialiser le générateur
    config = load_config()
    api_key = config.get('api', {}).get('gemini_api_key') or os.getenv('GOOGLE_API_KEY')
    model = config.get('api', {}).get('model', 'gemini-3-pro-preview')
    
    quiz_gen = QuizGenerator(api_key=api_key, model=model)
    
    # --- STATISTIQUES PREMIUM ---
    quiz_stats = quiz_gen.get_stats()
    bank_stats = quiz_gen.get_bank_stats()
    
    # Tendance visuelle
    trend_icon = {"up": "📈", "down": "📉", "stable": "➡️"}.get(quiz_stats.get('score_trend', 'stable'), '➡️')
    trend_label = {"up": "En progression", "down": "En baisse", "stable": "Stable"}.get(quiz_stats.get('score_trend', 'stable'), 'Stable')
    
    st.markdown("### 📊 Tableau de Bord")
    
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    with col1:
        st.metric("Quiz", quiz_stats['total_quizzes'])
    with col2:
        st.metric("Score Moyen", f"{quiz_stats['average_score']:.0f}%")
    with col3:
        st.metric("Meilleur", f"{quiz_stats['best_score']:.0f}%")
    with col4:
        st.metric("🔥 Série", f"{quiz_stats.get('current_streak', 0)}")
    with col5:
        st.metric(f"{trend_icon} Tendance", trend_label)
    with col6:
        st.metric("🏦 Banque", f"{bank_stats.get('total', 0)} Q")
    
    # Mini sparkline des 5 derniers scores
    last_scores = quiz_stats.get('last_5_scores', [])
    if last_scores:
        import plotly.graph_objects as go
        fig_spark = go.Figure(go.Scatter(
            y=last_scores, mode='lines+markers',
            line=dict(color='#4CAF50', width=2),
            marker=dict(size=6)
        ))
        fig_spark.update_layout(
            height=80, margin=dict(l=0, r=0, t=0, b=0),
            xaxis=dict(visible=False), yaxis=dict(visible=False, range=[0, 100]),
            plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig_spark, use_container_width=True, key="quiz_sparkline")
    
    st.divider()
    
    # Onglets
    tab1, tab2, tab3 = st.tabs(["🆕 Nouveau Quiz", "🎓 Examen Blanc", "📊 Analytics & Historique"])
    
    with tab1:
        st.markdown("### Configurer votre Quiz")
        
        # Extraire les modules disponibles
        concepts = concept_map['nodes']
        modules = sorted(list(set(c.get('module', 'Non classé') for c in concepts if c.get('module'))))
        
        # Charger le tracker de concepts faibles
        from src.weak_concepts_tracker import WeakConceptsTracker
        weak_tracker = WeakConceptsTracker()
        weak_stats = weak_tracker.get_stats()
        
        col_a, col_b, col_c = st.columns(3)
        
        with col_a:
            selected_module = st.selectbox(
                "Module",
                ["Tous modules"] + modules,
                help="Choisir un module spécifique ou mélanger tous"
            )
        
        with col_b:
            num_questions = st.slider("Nombre de questions", 5, 20, 10)
        
        with col_c:
            difficulty = st.select_slider(
                "Difficulté",
                options=["facile", "moyen", "difficile"],
                value="moyen"
            )
        
        # --- MODE ADAPTATIF ---
        adaptive_mode = st.toggle(
            "🎯 Mode Adaptatif — Prioriser mes concepts faibles",
            value=True if weak_stats['weak_count'] > 0 else False,
            help="Active le quiz adaptatif : 60% des questions portent sur vos concepts les plus faibles (basé sur vos erreurs précédentes)"
        )
        
        if adaptive_mode and weak_stats['weak_count'] > 0:
            st.info(f"🎯 Mode adaptatif activé — **{weak_stats['weak_count']} concepts faibles** seront priorisés")
        elif adaptive_mode and weak_stats['weak_count'] == 0:
            st.caption("ℹ️ Aucun concept faible détecté pour l'instant. Faites quelques quiz d'abord !")
        
        # --- TYPES DE QUESTIONS ---
        all_type_labels = {v['label']: k for k, v in QUESTION_TYPES.items()}
        selected_labels = st.multiselect(
            "🎲 Types de questions",
            options=list(all_type_labels.keys()),
            default=list(all_type_labels.keys()),
            help="Choisissez les types de questions à inclure dans le quiz"
        )
        selected_types = [all_type_labels[l] for l in selected_labels] if selected_labels else None
        
        if selected_types:
            type_icons = " ".join([QUESTION_TYPES[t]["icon"] for t in selected_types])
            st.caption(f"Types actifs : {type_icons}")
        
        st.divider()
        
        if st.button("🚀 Générer et Démarrer le Quiz", type="primary", use_container_width=True):
            module_filter = None if selected_module == "Tous modules" else selected_module
            
            # Vérifier si les PDFs du cours sont disponibles
            if module_filter:
                cours_folder = quiz_gen._find_module_folder(module_filter)
                if cours_folder:
                    pdf_count = len(list(cours_folder.glob("*.pdf")))
                    st.info(f"📖 Scan des PDFs du cours **{cours_folder.name}** ({pdf_count} fichier{'s' if pdf_count > 1 else ''})...")
                else:
                    st.warning(f"⚠️ Pas de dossier cours trouvé pour {module_filter}. Les questions seront basées sur les métadonnées uniquement.")
            
            with st.spinner("🤖 Scan des PDFs + génération IA de questions d'examen..."):
                # Récupérer les concepts faibles si mode adaptatif
                weak_ids = weak_tracker.get_weak_concept_ids(limit=20) if adaptive_mode else None
                
                quiz = quiz_gen.generate_quiz(
                    concepts=concepts,
                    module=module_filter,
                    num_questions=num_questions,
                    difficulty=difficulty,
                    weak_concept_ids=weak_ids,
                    question_types=selected_types
                )
                
                if 'error' in quiz:
                    st.error(f"❌ {quiz['error']}")
                else:
                    st.session_state['current_quiz'] = quiz
                    st.session_state['quiz_answers'] = {}
                    st.session_state['quiz_confidence'] = {}
                    st.session_state['quiz_hints_used'] = set()
                    st.session_state['quiz_start_time'] = time.time()
                    st.session_state['quiz_submitted'] = False
                    st.rerun()
        
        # Afficher le quiz si généré
        if 'current_quiz' in st.session_state and not st.session_state.get('quiz_submitted', False):
            quiz = st.session_state['current_quiz']
            
            st.markdown("---")
            st.markdown(f"### 📝 Quiz: {quiz['module']}")
            
            # Barre de progression en temps réel
            answered_count = len(st.session_state.get('quiz_answers', {}))
            progress_pct = answered_count / quiz['num_questions']
            elapsed = int(time.time() - st.session_state.get('quiz_start_time', time.time()))
            
            col_prog1, col_prog2, col_prog3 = st.columns([3, 1, 1])
            with col_prog1:
                st.progress(progress_pct, text=f"📊 {answered_count}/{quiz['num_questions']} réponses")
            with col_prog2:
                st.caption(f"⏱️ {elapsed // 60}:{elapsed % 60:02d}")
            with col_prog3:
                st.caption(f"📈 {quiz['difficulty']}")
            
            # Afficher les questions (multi-type)
            for i, question in enumerate(quiz['questions'], 1):
                q_type = question.get('type', 'qcm')
                type_icon = QUESTION_TYPES.get(q_type, {}).get('icon', '📋')
                concept_name = question.get('concept_name', '')
                q_module = question.get('module', '')
                source_doc = question.get('source_document', '')
                
                st.markdown(f"#### {type_icon} Question {i}/{quiz['num_questions']}")
                if concept_name:
                    module_tag = f" · 📁 {q_module}" if q_module else ""
                    source_tag = f" · 📄 {source_doc}" if source_doc else ""
                    st.caption(f"📚 {concept_name}{module_tag}{source_tag}")
                
                # Scénario pour mise en situation
                if q_type == 'mise_en_situation' and question.get('scenario'):
                    st.info(f"📋 **Situation :** {question['scenario']}")
                
                st.markdown(f"**{question['question']}**")
                
                # --- BOUTON INDICE 💡 ---
                hint_text = question.get('hint')
                if hint_text:
                    hint_key = f"hint_{i}"
                    if st.button(f"💡 Indice", key=hint_key, type="secondary"):
                        st.session_state.setdefault('quiz_hints_used', set())
                        if isinstance(st.session_state['quiz_hints_used'], set):
                            st.session_state['quiz_hints_used'].add(i)
                        else:
                            st.session_state['quiz_hints_used'] = {i}
                    
                    hints_used = st.session_state.get('quiz_hints_used', set())
                    if isinstance(hints_used, set) and i in hints_used:
                        st.warning(f"💡 **Indice :** {hint_text}")
                
                # Rendu selon le type de question
                if q_type in ('qcm', 'mise_en_situation'):
                    answer = st.radio(
                        "Choisissez votre réponse :",
                        question['options'],
                        key=f"q_{i}",
                        index=None
                    )
                    if answer:
                        st.session_state['quiz_answers'][i] = question['options'].index(answer)
                
                elif q_type == 'vrai_faux':
                    answer = st.radio(
                        "Vrai ou Faux ?",
                        ["Vrai", "Faux"],
                        key=f"q_{i}",
                        index=None,
                        horizontal=True
                    )
                    if answer:
                        st.session_state['quiz_answers'][i] = (answer == "Vrai")
                
                elif q_type == 'texte_trous':
                    answer = st.text_input(
                        "Complétez le mot manquant :",
                        key=f"q_{i}",
                        placeholder="Votre réponse..."
                    )
                    if answer.strip():
                        st.session_state['quiz_answers'][i] = answer.strip()
                    elif i in st.session_state.get('quiz_answers', {}):
                        del st.session_state['quiz_answers'][i]
                
                elif q_type == 'calcul':
                    unit = question.get('unit', '')
                    lbl = f"Votre réponse ({unit}) :" if unit else "Votre réponse (numérique) :"
                    answer = st.text_input(
                        lbl,
                        key=f"q_{i}",
                        placeholder="ex: 42.5"
                    )
                    if answer.strip():
                        st.session_state['quiz_answers'][i] = answer.strip()
                    elif i in st.session_state.get('quiz_answers', {}):
                        del st.session_state['quiz_answers'][i]
                
                # --- SÉLECTEUR DE CONFIANCE ---
                confidence_options = {"🎲 Je devine": "devine", "🤔 Hésitant": "hesitant", "✅ Sûr de moi": "sur"}
                conf = st.radio(
                    "Niveau de confiance :",
                    list(confidence_options.keys()),
                    key=f"conf_{i}",
                    horizontal=True,
                    index=None
                )
                if conf:
                    st.session_state.setdefault('quiz_confidence', {})[i] = confidence_options[conf]
                
                st.markdown("---")
            
            # Bouton soumettre
            if len(st.session_state.get('quiz_answers', {})) == quiz['num_questions']:
                if st.button("✅ Soumettre le Quiz", type="primary", use_container_width=True):
                    st.session_state['quiz_submitted'] = True
                    st.rerun()
            else:
                remaining = quiz['num_questions'] - len(st.session_state.get('quiz_answers', {}))
                st.info(f"⏳ Veuillez répondre à toutes les questions ({remaining} restante(s))")
        
        # Afficher les résultats si soumis
        if st.session_state.get('quiz_submitted', False):
            quiz = st.session_state['current_quiz']
            answers = st.session_state['quiz_answers']
            confidence = st.session_state.get('quiz_confidence', {})
            hints_used = st.session_state.get('quiz_hints_used', set())
            if not isinstance(hints_used, set):
                hints_used = set()
            
            # Calculer le score
            correct = 0
            results = []
            
            for i, question in enumerate(quiz['questions'], 1):
                user_answer = answers.get(i)
                is_correct = evaluate_answer(question, user_answer)
                
                if is_correct:
                    correct += 1
                
                results.append({
                    'question_num': i,
                    'user_answer': user_answer,
                    'correct_answer': question.get('correct_answer'),
                    'is_correct': is_correct,
                    'concept_id': question.get('concept_id'),
                    'concept_name': question.get('concept_name', ''),
                    'type': question.get('type', 'qcm'),
                    'confidence': confidence.get(i, 'non_renseigne'),
                    'hint_used': i in hints_used
                })
            
            score = correct
            total = quiz['num_questions']
            percentage = (score / total * 100) if total > 0 else 0
            
            # Temps écoulé
            time_spent = int(time.time() - st.session_state.get('quiz_start_time', time.time()))
            
            # Préparer les données de confiance pour la sauvegarde
            confidence_save = {
                'levels': {str(k): v for k, v in confidence.items()},
                'hints_used': list(hints_used)
            }
            
            # Sauvegarder dans l'historique
            quiz_gen.save_quiz_result(
                quiz_id=quiz['id'],
                score=score,
                total=total,
                time_spent=time_spent,
                answers=results,
                confidence_data=confidence_save
            )
            
            # --- ALIMENTER LE TRACKER DE CONCEPTS FAIBLES ---
            from src.weak_concepts_tracker import WeakConceptsTracker
            weak_tracker_save = WeakConceptsTracker()
            weak_tracker_save.record_quiz_results([
                {
                    'concept_id': q.get('concept_id', ''),
                    'concept_name': q.get('concept_name', ''),
                    'is_correct': q['is_correct'],
                    'module': quiz.get('module', ''),
                }
                for q in results
            ])
            
            # --- MESSAGE MOTIVATIONNEL ---
            st.markdown("---")
            if percentage >= 90:
                st.success("## 🏆 Exceptionnel !")
                st.balloons()
                msg = "Performance remarquable ! Vous maîtrisez ce domaine."
            elif percentage >= 70:
                st.success("## 🎉 Très bien !")
                msg = "Solide performance ! Continuez ainsi."
            elif percentage >= 50:
                st.warning("## 💪 Encourageant")
                msg = "Bon début, mais certains concepts méritent d'être revus."
            else:
                st.error("## 📚 À retravailler")
                msg = "Pas de panique ! Revoyez les concepts et retentez."
            
            st.caption(msg)
            
            # Métriques principales
            col_r1, col_r2, col_r3, col_r4 = st.columns(4)
            with col_r1:
                st.metric("Score", f"{score}/{total}")
            with col_r2:
                color = "🟢" if percentage >= 70 else "🟡" if percentage >= 50 else "🔴"
                st.metric("Pourcentage", f"{color} {percentage:.0f}%")
            with col_r3:
                st.metric("⏱️ Temps", f"{time_spent // 60}:{time_spent % 60:02d}")
            with col_r4:
                st.metric("💡 Indices", f"{len(hints_used)}/{total}")
            
            # --- ANALYSE DE CONFIANCE ---
            if confidence:
                st.markdown("### 🎯 Analyse de Confiance")
                
                conf_stats = {"devine": {"correct": 0, "total": 0}, 
                              "hesitant": {"correct": 0, "total": 0}, 
                              "sur": {"correct": 0, "total": 0}}
                for r in results:
                    cl = r.get('confidence', '')
                    if cl in conf_stats:
                        conf_stats[cl]['total'] += 1
                        if r['is_correct']:
                            conf_stats[cl]['correct'] += 1
                
                col_c1, col_c2, col_c3 = st.columns(3)
                mappings = [
                    ("col_c1", "🎲 Deviné", "devine"),
                    ("col_c2", "🤔 Hésitant", "hesitant"),
                    ("col_c3", "✅ Sûr", "sur")
                ]
                for col_ref, label, key in mappings:
                    col_widget = col_c1 if col_ref == "col_c1" else (col_c2 if col_ref == "col_c2" else col_c3)
                    with col_widget:
                        data = conf_stats[key]
                        if data['total'] > 0:
                            pct = data['correct'] / data['total'] * 100
                            st.metric(label, f"{pct:.0f}%", f"{data['correct']}/{data['total']}")
                        else:
                            st.metric(label, "—")
                
                # Alerte si confiance élevée mais mauvaise réponse
                overconfident = [r for r in results if r.get('confidence') == 'sur' and not r['is_correct']]
                if overconfident:
                    st.warning(f"⚠️ **Attention :** {len(overconfident)} question(s) où vous étiez sûr mais avez eu tort — concepts à revoir en priorité !")
                
                # Alerte si deviné juste (faux savoir)
                lucky_guesses = [r for r in results if r.get('confidence') == 'devine' and r['is_correct']]
                if lucky_guesses:
                    st.info(f"🍀 {len(lucky_guesses)} réponse(s) correcte(s) par chance — à consolider !")
            
            # Analyse détaillée
            st.markdown("### 📋 Analyse Détaillée")
            
            for i, question in enumerate(quiz['questions'], 1):
                result = results[i-1]
                is_correct = result['is_correct']
                q_type = question.get('type', 'qcm')
                type_icon = QUESTION_TYPES.get(q_type, {}).get('icon', '📋')
                concept_name = question.get('concept_name', '')
                conf_label = {"devine": "🎲", "hesitant": "🤔", "sur": "✅"}.get(result.get('confidence', ''), '')
                hint_label = "💡" if result.get('hint_used') else ""
                
                with st.expander(
                    f"{'✅' if is_correct else '❌'} {type_icon} Q{i} — {concept_name[:50] if concept_name else 'Question'} {conf_label}{hint_label}",
                    expanded=not is_correct
                ):
                    # Afficher les métadonnées du concept
                    meta_parts = []
                    if question.get('module'):
                        meta_parts.append(f"**Module :** {question['module']}")
                    if question.get('source_document'):
                        meta_parts.append(f"📄 {question['source_document']}")
                    if question.get('page_references'):
                        meta_parts.append(f"📖 {question['page_references']}")
                    if meta_parts:
                        st.caption(" | ".join(meta_parts))
                    
                    if question.get('fallback'):
                        st.caption("⚠️ Question générée hors-ligne (l'IA n'a pas pu répondre)")
                    
                    if q_type == 'mise_en_situation' and question.get('scenario'):
                        st.info(f"📋 {question['scenario']}")
                    st.markdown(f"**{question['question']}**")
                    
                    # Affichage adapté au type
                    if q_type in ('qcm', 'mise_en_situation'):
                        user_idx = result['user_answer']
                        if isinstance(user_idx, int) and 0 <= user_idx < len(question.get('options', [])):
                            st.markdown(f"**Votre réponse :** {question['options'][user_idx]}")
                        else:
                            st.markdown("**Votre réponse :** _(non répondu)_")
                        st.markdown(f"**Bonne réponse :** {question['options'][question['correct_answer']]}")
                    
                    elif q_type == 'vrai_faux':
                        user_vf = "Vrai" if result['user_answer'] else "Faux"
                        correct_vf = "Vrai" if question['correct_answer'] else "Faux"
                        st.markdown(f"**Votre réponse :** {user_vf}")
                        st.markdown(f"**Bonne réponse :** {correct_vf}")
                    
                    elif q_type == 'texte_trous':
                        st.markdown(f"**Votre réponse :** {result['user_answer']}")
                        st.markdown(f"**Bonne réponse :** {question['correct_answer']}")
                        if question.get('acceptable_answers'):
                            st.caption(f"Réponses acceptées : {', '.join(question['acceptable_answers'])}")
                    
                    elif q_type == 'calcul':
                        unit = question.get('unit', '')
                        st.markdown(f"**Votre réponse :** {result['user_answer']} {unit}")
                        st.markdown(f"**Bonne réponse :** {question['correct_answer']} {unit}")
                        tol = question.get('tolerance', 0.02)
                        st.caption(f"Tolérance : ±{tol*100:.0f}%")
                    
                    st.markdown("**Explication :**")
                    st.info(question.get('explanation', 'Pas d\'explication disponible.'))
            
            # Bouton pour recommencer
            if st.button("🔄 Nouveau Quiz", use_container_width=True):
                for key in ['current_quiz', 'quiz_answers', 'quiz_submitted', 
                            'quiz_confidence', 'quiz_hints_used', 'quiz_start_time']:
                    st.session_state.pop(key, None)
                st.rerun()
    
    with tab2:
        st.markdown("### 🎓 Mode Examen Blanc")
        st.markdown("""
        **Simulez les conditions réelles de l'examen du Brevet Fédéral :**
        - ⏱️ **2 heures** chronométrées
        - 📝 **40 questions** réparties sur tous les modules (AA + AE)
        - 📊 **Score par module** pour identifier vos faiblesses
        - 🎯 Questions alignées sur les **directives d'examen**
        """)
        
        from src.exam_simulator import ExamGenerator, EXAM_STRUCTURE
        from src.directives_coverage import get_module_coverage
        
        exam_gen = ExamGenerator(api_key=api_key, model=model)
        
        # Stats des examens blancs
        exam_stats = exam_gen.get_stats()
        if exam_stats['total_exams'] > 0:
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Examens passés", exam_stats['total_exams'])
            with col2:
                st.metric("Score moyen", f"{exam_stats['average_score']:.0f}%")
            with col3:
                st.metric("Meilleur score", f"{exam_stats['best_score']:.0f}%")
            with col4:
                st.metric("Taux de réussite", f"{exam_stats['pass_rate']:.0f}%")
            st.divider()
        
        # Bouton lancer l'examen
        if not st.session_state.get('exam_in_progress', False):
            st.markdown("#### 📋 Structure de l'examen")
            
            # Afficher la répartition
            col_aa, col_ae = st.columns(2)
            with col_aa:
                st.markdown("**Modules de base (AA)**")
                for code, info in EXAM_STRUCTURE['repartition'].items():
                    if code.startswith('AA'):
                        st.caption(f"• {code} {info['label']} — {info['questions']} Q")
            with col_ae:
                st.markdown("**Modules spécialisés (AE)**")
                for code, info in EXAM_STRUCTURE['repartition'].items():
                    if code.startswith('AE'):
                        st.caption(f"• {code} {info['label']} — {info['questions']} Q")
            
            st.divider()
            
            if st.button("🚀 Démarrer l'Examen Blanc", type="primary", use_container_width=True):
                with st.spinner("🤖 Génération de l'examen blanc (40 questions, cela peut prendre 1-2 minutes)..."):
                    # Charger la couverture des directives pour enrichir les questions
                    cov_config = load_config()
                    cov_data = get_module_coverage(concept_map, cov_config)
                    
                    exam = exam_gen.generate_exam(
                        concepts=concepts,
                        directives_coverage=cov_data
                    )
                    
                    st.session_state['current_exam'] = exam
                    st.session_state['exam_answers'] = {}
                    st.session_state['exam_start_time'] = time.time()
                    st.session_state['exam_in_progress'] = True
                    st.session_state['exam_submitted'] = False
                    st.rerun()
        
        # --- EXAMEN EN COURS ---
        if st.session_state.get('exam_in_progress', False) and not st.session_state.get('exam_submitted', False):
            exam = st.session_state['current_exam']
            elapsed = int(time.time() - st.session_state.get('exam_start_time', time.time()))
            remaining = max(0, exam['duree_minutes'] * 60 - elapsed)
            
            # Header avec timer
            col_t1, col_t2, col_t3 = st.columns([2, 1, 1])
            with col_t1:
                st.markdown(f"### 📝 Examen Blanc en cours")
            with col_t2:
                mins = remaining // 60
                secs = remaining % 60
                timer_color = "🟢" if remaining > 1800 else ("🟡" if remaining > 600 else "🔴")
                st.metric(f"{timer_color} Temps restant", f"{mins}:{secs:02d}")
            with col_t3:
                answered = len(st.session_state.get('exam_answers', {}))
                st.metric("Répondu", f"{answered}/{exam['total_questions']}")
            
            st.progress(answered / exam['total_questions'])
            st.divider()
            
            # Afficher les questions (compatible multi-type)
            for i, question in enumerate(exam['questions'], 1):
                module_tag = question.get('module', '')
                module_label = question.get('module_label', '')
                q_type = question.get('type', 'qcm')
                type_icon = QUESTION_TYPES.get(q_type, {}).get('icon', '📋')
                
                st.markdown(f"#### {type_icon} Question {i}/{exam['total_questions']}  `{module_tag} — {module_label}`")
                
                if q_type == 'mise_en_situation' and question.get('scenario'):
                    st.info(f"📋 **Situation :** {question['scenario']}")
                
                st.markdown(f"**{question['question']}**")
                
                if q_type in ('qcm', 'mise_en_situation'):
                    answer = st.radio(
                        f"Réponse :",
                        question['options'],
                        key=f"exam_q_{i}",
                        index=None
                    )
                    if answer:
                        st.session_state['exam_answers'][i] = question['options'].index(answer)
                
                elif q_type == 'vrai_faux':
                    answer = st.radio("Vrai ou Faux ?", ["Vrai", "Faux"], key=f"exam_q_{i}", index=None, horizontal=True)
                    if answer:
                        st.session_state['exam_answers'][i] = (answer == "Vrai")
                
                elif q_type == 'texte_trous':
                    answer = st.text_input("Complétez :", key=f"exam_q_{i}", placeholder="Votre réponse...")
                    if answer.strip():
                        st.session_state['exam_answers'][i] = answer.strip()
                    elif i in st.session_state.get('exam_answers', {}):
                        del st.session_state['exam_answers'][i]
                
                elif q_type == 'calcul':
                    unit = question.get('unit', '')
                    answer = st.text_input(f"Réponse ({unit}) :" if unit else "Réponse :", key=f"exam_q_{i}", placeholder="ex: 42.5")
                    if answer.strip():
                        st.session_state['exam_answers'][i] = answer.strip()
                    elif i in st.session_state.get('exam_answers', {}):
                        del st.session_state['exam_answers'][i]
                
                st.markdown("---")
            
            # Boutons soumettre / abandonner
            col_s1, col_s2 = st.columns([3, 1])
            with col_s1:
                answered = len(st.session_state.get('exam_answers', {}))
                if answered == exam['total_questions']:
                    if st.button("✅ Soumettre l'Examen", type="primary", use_container_width=True):
                        st.session_state['exam_submitted'] = True
                        st.rerun()
                else:
                    remaining_q = exam['total_questions'] - answered
                    st.info(f"⏳ {remaining_q} question(s) sans réponse")
            with col_s2:
                if st.button("🛑 Abandonner", type="secondary"):
                    for key in ['current_exam', 'exam_answers', 'exam_start_time', 'exam_in_progress', 'exam_submitted']:
                        st.session_state.pop(key, None)
                    st.rerun()
        
        # --- RÉSULTATS DE L'EXAMEN ---
        if st.session_state.get('exam_submitted', False):
            exam = st.session_state['current_exam']
            answers = st.session_state['exam_answers']
            time_spent = int(time.time() - st.session_state.get('exam_start_time', time.time()))
            
            # Évaluer
            results = exam_gen.evaluate_exam(exam, answers)
            exam_gen.save_exam_result(results, time_spent)
            
            # --- ALIMENTER LE TRACKER DE CONCEPTS FAIBLES (examen blanc) ---
            from src.weak_concepts_tracker import WeakConceptsTracker
            weak_tracker_exam = WeakConceptsTracker()
            weak_tracker_exam.record_quiz_results([
                {
                    'concept_id': qr.get('concept_name', ''),
                    'concept_name': qr.get('concept_name', ''),
                    'is_correct': qr['is_correct'],
                    'module': qr.get('module', ''),
                }
                for qr in results['question_results']
            ])
            
            # --- Affichage des résultats ---
            st.markdown("---")
            pct = results['global_percentage']
            passed = results['passed']
            
            if passed:
                st.success(f"## 🎉 EXAMEN RÉUSSI — {pct:.0f}%")
                st.balloons()
            else:
                st.error(f"## ❌ EXAMEN ÉCHOUÉ — {pct:.0f}%")
            
            # Métriques globales
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Score", f"{results['total_correct']}/{results['total_questions']}")
            with col2:
                color = "🟢" if pct >= 70 else ("🟡" if pct >= 50 else "🔴")
                st.metric("Pourcentage", f"{color} {pct:.0f}%")
            with col3:
                st.metric("Temps", f"{time_spent // 60} min")
            with col4:
                st.metric("Résultat", "✅ Réussi" if passed else "❌ Échoué")
            
            st.divider()
            
            # --- SCORE PAR MODULE ---
            st.subheader("📊 Score par Module")
            st.markdown("*Identifiez vos forces et faiblesses par domaine*")
            
            import plotly.express as px
            
            module_data = []
            for mod in sorted(results['module_scores'].keys()):
                s = results['module_scores'][mod]
                module_data.append({
                    "Module": f"{mod}",
                    "Label": s['label'],
                    "Score (%)": s['percentage'],
                    "Détail": f"{s['correct']}/{s['total']}",
                    "Statut": s['status'],
                })
            
            df_modules = pd.DataFrame(module_data)
            
            fig = px.bar(
                df_modules,
                x="Module",
                y="Score (%)",
                color="Score (%)",
                color_continuous_scale=["#e53935", "#fb8c00", "#43a047"],
                range_color=[0, 100],
                hover_data=["Label", "Détail"],
                title="Résultats par module"
            )
            fig.add_hline(y=50, line_dash="dash", line_color="red", annotation_text="Seuil de réussite (50%)")
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
            
            st.dataframe(df_modules, use_container_width=True, hide_index=True)
            
            # Modules faibles
            if results['weak_modules']:
                st.divider()
                st.subheader("🚨 Modules à renforcer")
                for mod in results['weak_modules']:
                    s = results['module_scores'][mod]
                    st.error(f"**{mod} — {s['label']}** : {s['percentage']:.0f}% ({s['correct']}/{s['total']})")
            
            # Modules forts
            if results['strong_modules']:
                st.subheader("💪 Modules maîtrisés")
                for mod in results['strong_modules'][:5]:
                    s = results['module_scores'][mod]
                    st.success(f"**{mod} — {s['label']}** : {s['percentage']:.0f}% ({s['correct']}/{s['total']})")
            
            st.divider()
            
            # Analyse détaillée
            st.subheader("📋 Détail des réponses")
            
            for q_result in results['question_results']:
                q_num = q_result['question_num']
                question = exam['questions'][q_num - 1]
                is_correct = q_result['is_correct']
                q_type = question.get('type', 'qcm')
                type_icon = QUESTION_TYPES.get(q_type, {}).get('icon', '📋')
                
                with st.expander(
                    f"{'✅' if is_correct else '❌'} {type_icon} Q{q_num} [{q_result['module']}] — {q_result['concept_name'][:50]}",
                    expanded=not is_correct
                ):
                    if q_type == 'mise_en_situation' and question.get('scenario'):
                        st.info(f"📋 {question['scenario']}")
                    st.markdown(f"**{question['question']}**")
                    
                    if q_type in ('qcm', 'mise_en_situation'):
                        user_idx = q_result['user_answer']
                        correct_idx = q_result['correct_answer']
                        if isinstance(user_idx, int) and 0 <= user_idx < len(question.get('options', [])):
                            st.markdown(f"**Votre réponse :** {question['options'][user_idx]}")
                        else:
                            st.markdown("**Votre réponse :** _(non répondu)_")
                        st.markdown(f"**Bonne réponse :** {question['options'][correct_idx]}")
                    elif q_type == 'vrai_faux':
                        st.markdown(f"**Votre réponse :** {'Vrai' if q_result['user_answer'] else 'Faux'}")
                        st.markdown(f"**Bonne réponse :** {'Vrai' if question['correct_answer'] else 'Faux'}")
                    elif q_type == 'texte_trous':
                        st.markdown(f"**Votre réponse :** {q_result['user_answer']}")
                        st.markdown(f"**Bonne réponse :** {question['correct_answer']}")
                        if question.get('acceptable_answers'):
                            st.caption(f"Accepté : {', '.join(question['acceptable_answers'])}")
                    elif q_type == 'calcul':
                        unit = question.get('unit', '')
                        st.markdown(f"**Votre réponse :** {q_result['user_answer']} {unit}")
                        st.markdown(f"**Bonne réponse :** {question['correct_answer']} {unit}")
                    
                    if question.get('explanation'):
                        st.info(f"**Explication :** {question['explanation']}")
            
            # Bouton recommencer
            st.divider()
            if st.button("🔄 Nouvel Examen Blanc", use_container_width=True):
                for key in ['current_exam', 'exam_answers', 'exam_start_time', 'exam_in_progress', 'exam_submitted']:
                    st.session_state.pop(key, None)
                st.rerun()
        
        # --- HISTORIQUE EXAMENS BLANCS ---
        st.divider()
        st.subheader("📜 Historique des Examens Blancs")
        
        exam_history = exam_gen.get_history(limit=10)
        if not exam_history:
            st.info("Aucun examen blanc complété pour l'instant.")
        else:
            for h in exam_history:
                pct = h['global_percentage']
                color = "🟢" if pct >= 70 else ("🟡" if pct >= 50 else "🔴")
                passed_icon = "✅" if h['passed'] else "❌"
                
                with st.expander(
                    f"{passed_icon} {color} {pct:.0f}% — {h['total_correct']}/{h['total_questions']} — {h['completed_at'][:10]}",
                    expanded=False
                ):
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Score", f"{h['total_correct']}/{h['total_questions']}")
                    with col2:
                        st.metric("Pourcentage", f"{pct:.0f}%")
                    with col3:
                        t = h.get('time_spent', 0)
                        st.metric("Temps", f"{t // 60} min")
                    
                    if h.get('weak_modules'):
                        st.markdown("**Modules faibles :** " + ", ".join(h['weak_modules']))
    
    with tab3:
        st.markdown("### � Analytics & Historique Premium")
        
        history = quiz_gen.get_history(limit=50)
        
        if not history:
            st.info("Vous n'avez pas encore complété de quiz. Lancez votre premier quiz pour voir vos analytics ici !")
        else:
            import plotly.express as px
            import plotly.graph_objects as go
            
            # --- SECTION 1 : ÉVOLUTION DES SCORES ---
            st.markdown("#### 📈 Évolution des Scores")
            scores_data = []
            for h in sorted(history, key=lambda x: x.get('completed_at', '')):
                scores_data.append({
                    "Date": h.get('completed_at', '')[:10],
                    "Score (%)": h['percentage'],
                    "Questions": h['total'],
                    "Temps (s)": h.get('time_spent', 0)
                })
            
            df_scores = pd.DataFrame(scores_data)
            
            if len(df_scores) > 1:
                fig_evo = go.Figure()
                fig_evo.add_trace(go.Scatter(
                    x=list(range(1, len(df_scores) + 1)),
                    y=df_scores['Score (%)'],
                    mode='lines+markers',
                    name='Score',
                    line=dict(color='#2196F3', width=3),
                    marker=dict(size=8),
                    fill='tozeroy',
                    fillcolor='rgba(33, 150, 243, 0.1)'
                ))
                # Ligne de moyenne mobile (3 quiz)
                if len(df_scores) >= 3:
                    rolling_avg = df_scores['Score (%)'].rolling(window=3, min_periods=1).mean()
                    fig_evo.add_trace(go.Scatter(
                        x=list(range(1, len(df_scores) + 1)),
                        y=rolling_avg,
                        mode='lines',
                        name='Moyenne mobile (3)',
                        line=dict(color='#FF9800', width=2, dash='dash')
                    ))
                fig_evo.add_hline(y=60, line_dash="dot", line_color="red", annotation_text="Seuil réussite (60%)")
                fig_evo.update_layout(
                    height=350,
                    xaxis_title="Quiz #",
                    yaxis_title="Score (%)",
                    yaxis=dict(range=[0, 105]),
                    showlegend=True,
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )
                st.plotly_chart(fig_evo, use_container_width=True, key="analytics_evo")
            
            # --- SECTION 2 : PERFORMANCE PAR TYPE DE QUESTION ---
            st.markdown("#### 🎲 Performance par Type de Question")
            score_by_type = quiz_stats.get('score_by_type', {})
            
            if score_by_type:
                type_data = []
                for t, data in score_by_type.items():
                    label = QUESTION_TYPES.get(t, {}).get('label', t)
                    icon = QUESTION_TYPES.get(t, {}).get('icon', '📋')
                    type_data.append({
                        "Type": f"{icon} {label}",
                        "Score (%)": data['percentage'],
                        "Questions": data['total']
                    })
                
                df_types = pd.DataFrame(type_data)
                
                fig_types = px.bar(
                    df_types, x="Type", y="Score (%)",
                    color="Score (%)",
                    color_continuous_scale=["#e53935", "#fb8c00", "#43a047"],
                    range_color=[0, 100],
                    hover_data=["Questions"],
                    text="Score (%)"
                )
                fig_types.update_traces(texttemplate='%{text:.0f}%', textposition='outside')
                fig_types.update_layout(height=300, showlegend=False)
                st.plotly_chart(fig_types, use_container_width=True, key="analytics_types")
            else:
                st.caption("Pas assez de données par type de question.")
            
            # --- SECTION 3 : TEMPS D'ÉTUDE ---
            st.markdown("#### ⏱️ Temps d'Étude")
            total_time_min = sum(h.get('time_spent', 0) for h in history) / 60
            avg_time_per_q = quiz_stats.get('avg_time_per_question', 0)
            
            col_t1, col_t2, col_t3 = st.columns(3)
            with col_t1:
                hours = int(total_time_min // 60)
                mins = int(total_time_min % 60)
                st.metric("⏱️ Temps total", f"{hours}h {mins}min")
            with col_t2:
                st.metric("⏳ Moy. / question", f"{avg_time_per_q:.0f}s")
            with col_t3:
                st.metric("📝 Total questions", quiz_stats['total_questions'])
            
            # --- SECTION 4 : BADGES ET ACCOMPLISSEMENTS ---
            st.markdown("#### 🏅 Accomplissements")
            
            badges = []
            if quiz_stats['total_quizzes'] >= 1:
                badges.append(("🌟", "Premier Quiz", "Vous avez complété votre premier quiz !"))
            if quiz_stats['total_quizzes'] >= 10:
                badges.append(("🔥", "Assidu", "10 quiz complétés — belle constance !"))
            if quiz_stats['total_quizzes'] >= 25:
                badges.append(("💎", "Diamant", "25 quiz ! Vous êtes inarrêtable."))
            if quiz_stats['best_score'] >= 90:
                badges.append(("🏆", "Excellence", "Score de 90%+ atteint — bravo !"))
            if quiz_stats['best_score'] == 100:
                badges.append(("👑", "Perfection", "100% ! Score parfait obtenu."))
            if quiz_stats.get('current_streak', 0) >= 3:
                badges.append(("🔥", "En série", f"Série de {quiz_stats['current_streak']} quiz réussis !"))
            if quiz_stats.get('best_streak', 0) >= 5:
                badges.append(("⚡", "Imbattable", f"Meilleure série : {quiz_stats['best_streak']} quiz !"))
            if quiz_stats['total_questions'] >= 100:
                badges.append(("📚", "Centurion", "100+ questions répondues au total."))
            if total_time_min >= 60:
                badges.append(("⏰", "Marathonien", "1h+ de révision par quiz !"))
            if quiz_stats.get('total_hints_used', 0) == 0 and quiz_stats['total_quizzes'] > 0:
                badges.append(("🧠", "Sans filet", "Aucun indice utilisé !"))
            
            if badges:
                badge_cols = st.columns(min(len(badges), 5))
                for idx, (icon, title, desc) in enumerate(badges):
                    with badge_cols[idx % len(badge_cols)]:
                        st.markdown(f"### {icon}")
                        st.caption(f"**{title}**")
                        st.caption(desc)
            else:
                st.caption("Complétez des quiz pour débloquer vos premiers badges !")
            
            st.divider()
            
            # --- SECTION 5 : HISTORIQUE DÉTAILLÉ ---
            st.markdown("#### 📜 Historique Détaillé")
            
            for quiz_result in history[:20]:
                percentage = quiz_result['percentage']
                color = "🟢" if percentage >= 70 else "🟡" if percentage >= 50 else "🔴"
                
                with st.expander(
                    f"{color} {percentage:.1f}% - {quiz_result['score']}/{quiz_result['total']} - {quiz_result['completed_at'][:10]}",
                    expanded=False
                ):
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Score", f"{quiz_result['score']}/{quiz_result['total']}")
                    with col2:
                        st.metric("Pourcentage", f"{percentage:.1f}%")
                    with col3:
                        time_spent = quiz_result.get('time_spent', 0)
                        st.metric("Temps", f"{time_spent // 60}:{time_spent % 60:02d}")


elif page == "📇 Flashcards":
    st.header("📇 Flashcards — Répétition Espacée (SM-2)")
    st.markdown("*Mémorisez durablement grâce à l'algorithme SuperMemo 2 : les cartes difficiles reviennent plus souvent.*")
    
    from src.flashcards import FlashcardManager
    
    config = load_config()
    api_key = config.get('api', {}).get('gemini_api_key') or os.getenv('GOOGLE_API_KEY')
    model = config.get('api', {}).get('model', 'gemini-3-pro-preview')
    fc_mgr = FlashcardManager(api_key=api_key, model=model)
    
    concept_map = load_concept_map()
    concepts = concept_map.get('nodes', []) if concept_map else []
    modules = sorted(set(c.get('module') for c in concepts if c.get('module')))
    
    fc_stats = fc_mgr.get_stats()
    
    # --- Métriques avec style amélioré ---
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("📇 Total cartes", fc_stats['total_cards'])
    with col2:
        due_count = fc_stats['due_today']
        st.metric("📅 À réviser", due_count, delta=f"-{due_count}" if due_count > 0 else None, delta_color="inverse")
    with col3:
        st.metric("🆕 Nouvelles", fc_stats['new_cards'])
    with col4:
        mastered_pct = f"({round(fc_stats['mastered'] / max(1, fc_stats['total_cards']) * 100)}%)" if fc_stats['total_cards'] > 0 else ""
        st.metric("✅ Maîtrisées", f"{fc_stats['mastered']} {mastered_pct}")
    with col5:
        st.metric("🔥 Streak", f"{fc_stats['review_streak']} j")
    
    # Barre de progression globale
    if fc_stats['total_cards'] > 0:
        mastered_ratio = fc_stats['mastered'] / fc_stats['total_cards']
        learning_ratio = fc_stats['learning'] / fc_stats['total_cards']
        st.progress(mastered_ratio, text=f"✅ {fc_stats['mastered']} maîtrisées · 📗 {fc_stats['learning']} en apprentissage · 🆕 {fc_stats['new_cards']} nouvelles")
    
    st.divider()
    
    tab_review, tab_generate, tab_browse = st.tabs(["🔄 Réviser", "➕ Générer", "📋 Toutes les cartes"])
    
    # ===== ONGLET RÉVISER (REDESIGN PREMIUM) =====
    with tab_review:
        fc_filter_mod = st.selectbox("Filtrer par module", ["Tous"] + fc_mgr.get_module_list(), key="fc_rev_mod")
        mod_filter = None if fc_filter_mod == "Tous" else fc_filter_mod
        
        due_cards = fc_mgr.get_due_cards(module=mod_filter, limit=30)
        
        if not due_cards:
            st.success("🎉 Aucune carte à réviser pour le moment ! Revenez plus tard ou générez de nouvelles cartes.")
        else:
            st.info(f"📅 **{len(due_cards)} carte(s)** à réviser")
            
            # Index courant dans la session
            if 'fc_index' not in st.session_state:
                st.session_state['fc_index'] = 0
            if st.session_state['fc_index'] >= len(due_cards):
                st.session_state['fc_index'] = 0
            
            card = due_cards[st.session_state['fc_index']]
            
            st.progress((st.session_state['fc_index'] + 1) / len(due_cards))
            
            # --- Navigation Précédent / Passer ---
            nav_col1, nav_col2, nav_col3 = st.columns([1, 3, 1])
            with nav_col1:
                if st.button("⬅️ Précédente", key="fc_prev", use_container_width=True, disabled=(st.session_state['fc_index'] == 0)):
                    st.session_state['fc_index'] = max(0, st.session_state['fc_index'] - 1)
                    st.session_state['fc_show_back'] = False
                    st.rerun()
            with nav_col2:
                st.caption(f"Carte {st.session_state['fc_index'] + 1} / {len(due_cards)}")
            with nav_col3:
                if st.button("Passer ➡️", key="fc_skip", use_container_width=True, disabled=(st.session_state['fc_index'] >= len(due_cards) - 1)):
                    st.session_state['fc_index'] += 1
                    st.session_state['fc_show_back'] = False
                    st.rerun()
            
            # Badge type de carte + difficulté
            card_type = card.get('card_type', 'definition')
            type_badges = {
                'definition': '📖 Définition',
                'norme': '⚖️ Norme/Prescription',
                'pratique': '🔧 Pratique terrain',
                'formule': '📐 Formule/Calcul',
                'comparaison': '🔄 Comparaison',
                'analyse': '🧠 Analyse',
            }
            type_badge = type_badges.get(card_type, '📖 Concept')
            
            # Difficulté intrinsèque de la carte
            card_difficulty = card.get('difficulty', 2)
            diff_labels = {1: '🟢 Facile', 2: '🟡 Moyen', 3: '🔴 Difficile'}
            diff_label = diff_labels.get(card_difficulty, '🟡 Moyen')
            
            col_meta1, col_meta2, col_meta3 = st.columns(3)
            with col_meta1:
                st.caption(f"Module: **{card.get('module', '?')}**")
            with col_meta2:
                st.caption(f"{type_badge}")
            with col_meta3:
                interval = card.get('interval', 1)
                sm2_label = "🔴 Nouveau" if card.get('review_count', 0) == 0 else "🟡 En cours" if interval < 21 else "🟢 Maîtrisée"
                st.caption(f"{diff_label} · {sm2_label}")
            
            # --- FACE AVANT (design amélioré) ---
            st.markdown("""<div style='background: linear-gradient(135deg, #1a237e 0%, #283593 100%); 
                            padding: 2rem; border-radius: 12px; color: white; margin: 1rem 0;
                            box-shadow: 0 4px 6px rgba(0,0,0,0.1);'>
                <h3 style='margin:0; color: #e3f2fd;'>❓ Question</h3>
                <p style='font-size: 1.2rem; margin-top: 0.5rem;'>{}</p>
            </div>""".format(card['front']), unsafe_allow_html=True)
            
            if card.get('hint'):
                with st.expander("💡 Voir l'indice"):
                    st.markdown(f"**Indice :** {card['hint']}")
            
            # --- RÉVÉLER ---
            if st.button("👁️ Retourner la carte", key="fc_flip", use_container_width=True, type="primary"):
                st.session_state['fc_show_back'] = True
            
            if st.session_state.get('fc_show_back', False):
                st.markdown("""<div style='background: linear-gradient(135deg, #1b5e20 0%, #2e7d32 100%); 
                                padding: 2rem; border-radius: 12px; color: white; margin: 1rem 0;
                                box-shadow: 0 4px 6px rgba(0,0,0,0.1);'>
                    <h3 style='margin:0; color: #c8e6c9;'>✅ Réponse</h3>
                    <p style='font-size: 1.1rem; margin-top: 0.5rem;'>{}</p>
                </div>""".format(card['back']), unsafe_allow_html=True)
                
                # Référence source si disponible
                source_ref = card.get('source_ref', '')
                if source_ref and source_ref.strip():
                    st.caption(f"📄 Source : {source_ref}")
                
                st.markdown("---")
                st.markdown("### Comment avez-vous répondu ?")
                st.markdown("*(Note SM-2 : évaluez votre maîtrise de cette carte)*")
                
                # Boutons avec meilleur design -- 3 colonnes au lieu de 6
                col_bad, col_mid, col_good = st.columns(3)
                
                with col_bad:
                    st.markdown("##### 🔴 Pas su")
                    cb1, cb2 = st.columns(2)
                    with cb1:
                        if st.button("0 — Oublié", key="fc_q_0", use_container_width=True):
                            fc_mgr.review_card(card['id'], quality=0)
                            st.session_state['fc_show_back'] = False
                            st.session_state['fc_index'] += 1
                            st.rerun()
                    with cb2:
                        if st.button("1 — Vague", key="fc_q_1", use_container_width=True):
                            fc_mgr.review_card(card['id'], quality=1)
                            st.session_state['fc_show_back'] = False
                            st.session_state['fc_index'] += 1
                            st.rerun()
                
                with col_mid:
                    st.markdown("##### 🟡 Hésitant")
                    cm1, cm2 = st.columns(2)
                    with cm1:
                        if st.button("2 — Partiel", key="fc_q_2", use_container_width=True):
                            fc_mgr.review_card(card['id'], quality=2)
                            st.session_state['fc_show_back'] = False
                            st.session_state['fc_index'] += 1
                            st.rerun()
                    with cm2:
                        if st.button("3 — Difficile", key="fc_q_3", use_container_width=True):
                            fc_mgr.review_card(card['id'], quality=3)
                            st.session_state['fc_show_back'] = False
                            st.session_state['fc_index'] += 1
                            st.rerun()
                
                with col_good:
                    st.markdown("##### 🟢 Bien su")
                    cg1, cg2 = st.columns(2)
                    with cg1:
                        if st.button("4 — Hésitation", key="fc_q_4", use_container_width=True):
                            fc_mgr.review_card(card['id'], quality=4)
                            st.session_state['fc_show_back'] = False
                            st.session_state['fc_index'] += 1
                            st.rerun()
                    with cg2:
                        if st.button("5 — Parfait", key="fc_q_5", use_container_width=True):
                            fc_mgr.review_card(card['id'], quality=5)
                            st.session_state['fc_show_back'] = False
                            st.session_state['fc_index'] += 1
                            st.rerun()
            
            # Méta de la carte
            with st.expander("ℹ️ Détails SM-2"):
                mc1, mc2, mc3, mc4 = st.columns(4)
                with mc1:
                    st.caption(f"Intervalle : {card.get('interval', 1)} jour(s)")
                with mc2:
                    st.caption(f"Facilité (EF) : {card.get('easiness', 2.5):.2f}")
                with mc3:
                    st.caption(f"Révisions : {card.get('review_count', 0)}")
                with mc4:
                    st.caption(f"Concept : {card.get('concept_name', 'N/A')}")
    
    # ===== ONGLET GÉNÉRER =====
    with tab_generate:
        if not concepts:
            st.warning("⚠️ Analysez d'abord vos documents pour générer des flashcards.")
        else:
            st.markdown("### ➕ Générer des flashcards depuis vos cours")
            st.markdown("*L'IA scanne le contenu réel de vos PDFs de cours pour générer des cartes précises et factuelles.*")
            
            gc1, gc2 = st.columns(2)
            with gc1:
                gen_module = st.selectbox("Module", ["Tous modules"] + modules, key="fc_gen_mod")
            with gc2:
                gen_num = st.slider("Nombre de concepts à couvrir", 5, 30, 10, key="fc_gen_num")
            
            # Compter les concepts sans flashcard
            existing_ids = {c.get('concept_id') for c in fc_mgr.cards}
            mod_filter_gen = None if gen_module == "Tous modules" else gen_module
            available = [c for c in concepts if c.get('id') not in existing_ids]
            if mod_filter_gen:
                available = [c for c in available if c.get('module') == mod_filter_gen]
            
            # Vérifier si le dossier cours existe pour ce module
            if mod_filter_gen:
                cours_folder = fc_mgr._find_module_folder(mod_filter_gen)
                if cours_folder:
                    pdf_count = len(list(cours_folder.glob("*.pdf")))
                    st.success(f"📂 Dossier cours trouvé : **{cours_folder.name}** ({pdf_count} PDF{'s' if pdf_count > 1 else ''})")
                else:
                    st.warning(f"⚠️ Aucun dossier cours trouvé pour {mod_filter_gen}. L'IA utilisera uniquement les métadonnées des concepts.")
            
            st.caption(f"📊 {len(available)} concepts sans flashcard (sur {len(concepts)} total)")
            
            if st.button("🚀 Générer les Flashcards", type="primary", use_container_width=True):
                if not available:
                    st.warning("Tous les concepts ont déjà des flashcards !")
                else:
                    progress_msg = st.empty()
                    progress_msg.info(f"📖 Scan des cours du module en cours...")
                    with st.spinner(f"🤖 Scan des PDFs + génération IA de flashcards pour {min(gen_num, len(available))} concepts..."):
                        created = fc_mgr.generate_from_concepts(
                            concepts=concepts,
                            module=mod_filter_gen,
                            num_cards=gen_num
                        )
                    progress_msg.empty()
                    st.success(f"✅ {created} nouvelles flashcards créées depuis le contenu réel du cours !")
                    st.rerun()
    
    # ===== ONGLET TOUTES LES CARTES =====
    with tab_browse:
        if not fc_mgr.cards:
            st.info("Aucune flashcard. Utilisez l'onglet \"Générer\" pour en créer.")
        else:
            st.markdown(f"### 📋 {len(fc_mgr.cards)} flashcards")
            
            browse_mod = st.selectbox("Filtrer par module", ["Tous"] + fc_mgr.get_module_list(), key="fc_browse_mod")
            
            filtered = fc_mgr.cards[:]
            if browse_mod != "Tous":
                filtered = [c for c in filtered if c.get('module') == browse_mod]
            
            # Tri
            sort_by = st.radio("Trier par", ["Date création", "Prochaine révision", "Facilité (difficiles d'abord)"], horizontal=True, key="fc_sort")
            if sort_by == "Prochaine révision":
                filtered.sort(key=lambda c: c.get('next_review', ''))
            elif sort_by == "Facilité (difficiles d'abord)":
                filtered.sort(key=lambda c: c.get('easiness', 2.5))
            else:
                filtered.sort(key=lambda c: c.get('created_at', ''), reverse=True)
            
            for card in filtered:
                interval = card.get('interval', 1)
                ef = card.get('easiness', 2.5)
                status = "✅" if interval >= 21 else ("📗" if interval >= 7 else "📕")
                
                with st.expander(f"{status} [{card.get('module', '?')}] {card['front'][:80]}"):
                    st.markdown(f"**Question :** {card['front']}")
                    st.markdown(f"**Réponse :** {card['back']}")
                    if card.get('hint'):
                        st.caption(f"Indice : {card['hint']}")
                    
                    bc1, bc2, bc3, bc4 = st.columns(4)
                    with bc1:
                        st.caption(f"Intervalle : {interval}j")
                    with bc2:
                        st.caption(f"Facilité : {ef:.2f}")
                    with bc3:
                        st.caption(f"Révisions : {card.get('review_count', 0)}")
                    with bc4:
                        nr = card.get('next_review', '')[:10]
                        st.caption(f"Prochaine : {nr}")
            
            st.divider()
            
            # Stats par module
            if fc_stats.get('modules'):
                st.markdown("### 📊 Répartition par module")
                import pandas as pd
                mod_data = []
                for mod, ms in sorted(fc_stats['modules'].items()):
                    mod_data.append({
                        "Module": mod,
                        "Total": ms['total'],
                        "À réviser": ms['due'],
                        "Maîtrisées": ms['mastered'],
                    })
                st.dataframe(pd.DataFrame(mod_data), use_container_width=True, hide_index=True)


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
                value=config.get('api', {}).get('gemini_api_key', ''),
                type="password"
            )
            
            model = st.selectbox(
                "Modèle IA",
                ["gemini-3-pro-preview", "gemini-2.0-flash", "gemini-1.5-pro"],
                index=0
            )
            
            if st.button("💾 Sauvegarder API", type="primary"):
                config.setdefault('api', {})['gemini_api_key'] = api_key
                config.setdefault('api', {})['model'] = model
                
                with open("config/config.yaml", 'w', encoding='utf-8') as f:
                    yaml.dump(config, f, allow_unicode=True, default_flow_style=False)
                
                st.success("✅ Configuration API sauvegardée!")
                st.cache_data.clear()
    
    with tab_planning:
        if config:
            st.subheader("📅 Dates importantes")
            
            exam_date = st.date_input(
                "Date de l'examen",
                value=datetime.strptime(config.get('user', {}).get('exam_date', '2027-03-20'), '%Y-%m-%d')
            )
            
            st.divider()
            st.subheader("⏱️ Planning")
            
            hours_per_day = st.slider(
                "Heures de révision par jour",
                min_value=0.5,
                max_value=8.0,
                value=float(config.get('planning', {}).get('default_hours_per_day', 2)),
                step=0.5
            )
            
            if st.button("💾 Sauvegarder Planning", type="primary"):
                config.setdefault('user', {})['exam_date'] = exam_date.strftime('%Y-%m-%d')
                config.setdefault('planning', {})['default_hours_per_day'] = hours_per_day
                
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
