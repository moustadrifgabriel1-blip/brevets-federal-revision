"""
Audit complet de toutes les fonctionnalités de l'application
"""
import json
import yaml
import sys
import os
import traceback
from datetime import datetime
from pathlib import Path

# Fixer le path pour pouvoir importer src.*
ROOT = Path(__file__).parent.parent
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))

ERRORS = []
WARNINGS = []
OK_COUNT = 0

def test(name, func):
    global OK_COUNT
    try:
        result = func()
        if result:
            print(f"  ✅ {name}")
            OK_COUNT += 1
        else:
            print(f"  ❌ {name} — retour False")
            ERRORS.append(f"{name}: retour False")
    except Exception as e:
        print(f"  ❌ {name} — {e}")
        ERRORS.append(f"{name}: {e}")
        traceback.print_exc()

def warn(msg):
    WARNINGS.append(msg)
    print(f"  ⚠️  {msg}")

# =====================================================
print("=" * 60)
print("1. CONFIG")
print("=" * 60)

def test_config_local():
    with open("config/config.yaml") as f:
        c = yaml.safe_load(f)
    assert c.get("user", {}).get("exam_date"), "exam_date manquant"
    assert c.get("user", {}).get("formation_start"), "formation_start manquant"
    assert c.get("modules"), "modules manquant"
    return True

def test_config_cloud():
    with open("cloud_data/config.yaml") as f:
        c = yaml.safe_load(f)
    with open("config/config.yaml") as f:
        local = yaml.safe_load(f)
    assert c["user"]["exam_date"] == local["user"]["exam_date"], \
        f"exam_date désync: cloud={c['user']['exam_date']} vs local={local['user']['exam_date']}"
    assert c["user"]["formation_start"] == local["user"]["formation_start"], \
        f"formation_start désync"
    return True

test("Config locale", test_config_local)
test("Config cloud sync", test_config_cloud)

# =====================================================
print("\n" + "=" * 60)
print("2. COURSE SCHEDULE MANAGER")
print("=" * 60)

def test_csm_load():
    from src.course_schedule_manager import CourseScheduleManager
    m = CourseScheduleManager({})
    m.load()
    assert len(m.sessions) > 0, "Aucune session chargée"
    return True

def test_csm_sync_statuses():
    from src.course_schedule_manager import CourseScheduleManager
    m = CourseScheduleManager({})
    m.load()
    now = datetime.now()
    for s in m.sessions:
        if s.date <= now:
            assert s.status == "completed", f"Session {s.module_code} {s.date} devrait être completed, est {s.status}"
        else:
            assert s.status == "planned", f"Session {s.module_code} {s.date} devrait être planned, est {s.status}"
    return True

def test_csm_module_progress():
    from src.course_schedule_manager import CourseScheduleManager
    m = CourseScheduleManager({})
    m.load()
    modules = set(s.module_code for s in m.sessions)
    for mod in list(modules)[:3]:
        p = m.get_module_progress(mod)
        assert "total_sessions" in p
        assert "completed" in p
        assert p["total_sessions"] >= p["completed"]
    return True

def test_csm_get_completed():
    from src.course_schedule_manager import CourseScheduleManager
    m = CourseScheduleManager({})
    m.load()
    completed = m.get_completed_sessions()
    upcoming = m.get_upcoming_sessions()
    assert len(completed) + len(upcoming) == len(m.sessions), \
        f"completed({len(completed)}) + upcoming({len(upcoming)}) != total({len(m.sessions)})"
    return True

def test_csm_learned_topics():
    from src.course_schedule_manager import CourseScheduleManager
    m = CourseScheduleManager({})
    m.load()
    topics = m.get_learned_topics()
    assert isinstance(topics, dict)
    return True

test("CSM: chargement", test_csm_load)
test("CSM: sync statuts auto", test_csm_sync_statuses)
test("CSM: progression module", test_csm_module_progress)
test("CSM: sessions complétées/à venir", test_csm_get_completed)
test("CSM: thèmes appris", test_csm_learned_topics)

# =====================================================
print("\n" + "=" * 60)
print("3. REVISION PLANNER")
print("=" * 60)

def test_planner_generate():
    from src.revision_planner import auto_generate_planning
    with open("config/config.yaml") as f:
        config = yaml.safe_load(f)
    result = auto_generate_planning(config)
    assert result["success"], f"Erreur: {result.get('error')}"
    assert result["total_sessions"] > 0
    assert result["total_concepts"] > 0
    return True

def test_planner_dual_write():
    for path in ["exports/revision_plan.json", "cloud_data/revision_plan.json"]:
        assert Path(path).exists(), f"{path} manquant"
    with open("exports/revision_plan.json") as f:
        e = json.load(f)
    with open("cloud_data/revision_plan.json") as f:
        c = json.load(f)
    assert e["total_sessions"] == c["total_sessions"], "Sessions différentes exports/ vs cloud_data/"
    assert e["generated_at"] == c["generated_at"], "Timestamps différents"
    return True

def test_planner_sessions_structure():
    with open("exports/revision_plan.json") as f:
        rp = json.load(f)
    required_fields = ["date", "day_name", "duration_minutes", "concepts", "category", "priority", "session_type", "module", "completed", "id"]
    for i, s in enumerate(rp["sessions"][:5]):
        for field in required_fields:
            assert field in s, f"Session {i} manque le champ '{field}'"
        assert isinstance(s["concepts"], list), f"Session {i}: concepts n'est pas une liste"
        assert len(s["concepts"]) > 0, f"Session {i}: concepts vide"
        assert s["id"].startswith("rev_"), f"Session {i}: ID invalide '{s['id']}'"
    # Vérifier unicité des IDs
    all_ids = [s["id"] for s in rp["sessions"]]
    assert len(all_ids) == len(set(all_ids)), f"IDs non uniques: {len(all_ids)} vs {len(set(all_ids))}"
    return True

def test_planner_no_past_gaps():
    with open("exports/revision_plan.json") as f:
        rp = json.load(f)
    today = datetime.now().strftime("%Y-%m-%d")
    past = [s for s in rp["sessions"] if s["date"] < today]
    future = [s for s in rp["sessions"] if s["date"] >= today]
    total = len(rp["sessions"])
    assert past and future, f"past={len(past)}, future={len(future)}"
    return True

test("Planner: génération", test_planner_generate)
test("Planner: double-écriture", test_planner_dual_write)
test("Planner: structure sessions", test_planner_sessions_structure)
test("Planner: sessions passées/futures", test_planner_no_past_gaps)

# =====================================================
print("\n" + "=" * 60)
print("4. CONCEPT MAPPER")
print("=" * 60)

def test_concept_map_exists():
    for path in ["exports/concept_map.json", "cloud_data/concept_map.json"]:
        assert Path(path).exists(), f"{path} manquant"
    return True

def test_concept_map_structure():
    with open("exports/concept_map.json") as f:
        cm = json.load(f)
    assert "nodes" in cm, "Pas de 'nodes'"
    assert len(cm["nodes"]) > 0, "Aucun concept"
    required = ["id", "name", "category", "importance", "module"]
    for node in cm["nodes"][:5]:
        for field in required:
            assert field in node, f"Concept '{node.get('name', '?')}' manque '{field}'"
    return True

def test_concept_map_sync():
    with open("exports/concept_map.json") as f:
        e = json.load(f)
    with open("cloud_data/concept_map.json") as f:
        c = json.load(f)
    assert len(e["nodes"]) == len(c["nodes"]), \
        f"Désync: exports={len(e['nodes'])} vs cloud={len(c['nodes'])}"
    return True

def test_concept_map_modules():
    with open("exports/concept_map.json") as f:
        cm = json.load(f)
    modules = set(n.get("module", "") for n in cm["nodes"] if n.get("module"))
    if len(modules) < 10:
        warn(f"Seulement {len(modules)} modules avec contenu: {sorted(modules)}")
    return True

test("ConceptMap: fichiers existent", test_concept_map_exists)
test("ConceptMap: structure valide", test_concept_map_structure)
test("ConceptMap: sync exports/cloud", test_concept_map_sync)
test("ConceptMap: modules couverts", test_concept_map_modules)

# =====================================================
print("\n" + "=" * 60)
print("5. PROGRESS TRACKER")
print("=" * 60)

def test_progress_load():
    from src.progress_tracker import ProgressTracker
    t = ProgressTracker()
    stats = t.get_stats()
    assert "total_sessions" in stats
    assert "completed_sessions" in stats
    assert "total_concepts" in stats
    return True

def test_progress_sync():
    from src.progress_tracker import ProgressTracker
    from src.course_schedule_manager import CourseScheduleManager
    t = ProgressTracker()
    m = CourseScheduleManager({})
    m.load()
    with open("exports/revision_plan.json") as f:
        rp = json.load(f)
    with open("exports/concept_map.json") as f:
        cm = json.load(f)
    result = t.sync_with_calendar(rp, m.sessions, cm)
    # sync met à jour les totaux et course_stats (pas d'auto-complétion)
    assert result["total_sessions"] > 0, "total_sessions vide après sync"
    assert len(result["completed_modules"]) > 0, "Aucun module complété"
    assert "course_stats" in result
    return True

def test_progress_course_stats():
    with open("data/progress.json") as f:
        p = json.load(f)
    cs = p.get("course_stats", {})
    assert cs.get("total_course_sessions", 0) > 0, "total_course_sessions vide"
    assert cs.get("completed_course_sessions", 0) > 0, "completed_course_sessions vide"
    assert cs.get("concepts_seen_in_class", 0) > 0, "concepts_seen_in_class vide"
    return True

def test_progress_rates():
    from src.progress_tracker import ProgressTracker
    t = ProgressTracker()
    cr = t.get_completion_rate()
    mr = t.get_mastery_rate()
    assert 0 <= cr <= 100, f"completion_rate hors bornes: {cr}"
    assert 0 <= mr <= 100, f"mastery_rate hors bornes: {mr}"
    return True

test("Progress: chargement", test_progress_load)
test("Progress: sync calendrier", test_progress_sync)
test("Progress: stats cours", test_progress_course_stats)
test("Progress: taux valides", test_progress_rates)

# =====================================================
print("\n" + "=" * 60)
print("6. QUIZ GENERATOR")
print("=" * 60)

def test_quiz_load():
    from src.quiz_generator import QuizGenerator
    qg = QuizGenerator(api_key="test", model="test")
    stats = qg.get_stats()
    assert "total_quizzes" in stats
    return True

def test_quiz_bank():
    from src.quiz_generator import QuizGenerator
    qg = QuizGenerator(api_key="test", model="test")
    bank_stats = qg.get_bank_stats()
    assert "total" in bank_stats
    return True

test("Quiz: chargement", test_quiz_load)
test("Quiz: banque questions", test_quiz_bank)

# =====================================================
print("\n" + "=" * 60)
print("7. WEAK CONCEPTS TRACKER")
print("=" * 60)

def test_weak_tracker():
    from src.weak_concepts_tracker import WeakConceptsTracker
    wt = WeakConceptsTracker()
    stats = wt.get_stats()
    assert "total_tracked" in stats
    assert "weak_count" in stats
    return True

test("WeakTracker: chargement", test_weak_tracker)

# =====================================================
print("\n" + "=" * 60)
print("8. APP.PY - PAGES PRINCIPALES")
print("=" * 60)

def test_load_functions():
    # Simuler les fonctions de chargement de app.py
    import yaml
    def load_config():
        for path in ["config/config.yaml", "cloud_data/config.yaml"]:
            if Path(path).exists():
                with open(path, "r", encoding="utf-8") as f:
                    return yaml.safe_load(f)
        return {}
    
    def load_concept_map():
        for folder in ["exports", "cloud_data"]:
            path = Path(folder) / "concept_map.json"
            if path.exists():
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
        return None
    
    def load_revision_plan():
        for folder in ["exports", "cloud_data"]:
            path = Path(folder) / "revision_plan.json"
            if path.exists():
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
        return None
    
    config = load_config()
    assert config, "Config vide"
    cm = load_concept_map()
    assert cm and len(cm.get("nodes", [])) > 0, "ConceptMap vide"
    rp = load_revision_plan()
    assert rp and len(rp.get("sessions", [])) > 0, "RevisionPlan vide"
    return True

def test_progression_page_data():
    """Simuler ce que fait la page Ma Progression"""
    from src.progress_tracker import ProgressTracker
    from src.course_schedule_manager import CourseScheduleManager
    
    with open("exports/revision_plan.json") as f:
        rp = json.load(f)
    with open("exports/concept_map.json") as f:
        cm = json.load(f)
    
    tracker = ProgressTracker()
    manager = CourseScheduleManager({})
    manager.load()
    
    result = tracker.sync_with_calendar(rp, manager.sessions, cm)
    stats = tracker.get_stats()
    
    # Vérifier que les données sont cohérentes pour l'affichage
    assert stats["total_sessions"] == len(rp["sessions"]), \
        f"total_sessions({stats['total_sessions']}) != sessions dans plan({len(rp['sessions'])})"
    assert stats["completed_sessions"] <= stats["total_sessions"]
    assert stats["total_concepts"] == len(cm["nodes"]), \
        f"total_concepts({stats['total_concepts']}) != nodes({len(cm['nodes'])})"
    
    cs = result.get("course_stats", {})
    assert cs["total_course_sessions"] == len(manager.sessions)
    return True

def test_planning_cours_page():
    """Simuler ce que fait la page Planning Cours"""
    from src.course_schedule_manager import CourseScheduleManager
    with open("config/config.yaml") as f:
        config = yaml.safe_load(f)
    manager = CourseScheduleManager(config)
    manager.load()
    
    # Test filtres
    completed = manager.get_completed_sessions()
    upcoming = manager.get_upcoming_sessions()
    modules = sorted(set(s.module_code for s in manager.sessions))
    
    assert len(modules) > 0, "Aucun module"
    
    # Test progression par module
    for mod in modules[:3]:
        progress = manager.get_module_progress(mod)
        assert progress["progress_percent"] >= 0
        assert progress["progress_percent"] <= 100
    return True

def test_revision_plan_display():
    """Simuler ce que fait la page Planning Révisions"""
    with open("exports/revision_plan.json") as f:
        rp = json.load(f)
    
    sessions = rp.get("sessions", [])
    stats = rp.get("statistics", {})
    
    today_str = datetime.now().strftime("%Y-%m-%d")
    past = [s for s in sessions if s["date"] < today_str]
    future = [s for s in sessions if s["date"] >= today_str]
    progress_pct = len(past) / max(1, len(sessions))
    
    assert 0 <= progress_pct <= 1
    assert rp.get("exam_date"), "exam_date manquant dans revision_plan"
    assert rp.get("milestones"), "milestones manquant"
    assert stats.get("days_until_exam", 0) > 0, "days_until_exam <= 0"
    return True

def test_sessions_display_fields():
    """Vérifier que les champs utilisés dans l'affichage existent"""
    with open("exports/revision_plan.json") as f:
        rp = json.load(f)
    
    issues = []
    for i, s in enumerate(rp["sessions"]):
        # Champs utilisés dans app.py pour l'affichage
        if not s.get("concepts"):
            issues.append(f"Session {i} ({s.get('date')}): concepts vide")
        if not s.get("module"):
            issues.append(f"Session {i} ({s.get('date')}): module manquant")
        if not s.get("category"):
            issues.append(f"Session {i} ({s.get('date')}): category manquant")
        if s.get("duration_minutes", 0) <= 0:
            issues.append(f"Session {i} ({s.get('date')}): duration_minutes <= 0")
    
    if issues:
        for issue in issues[:5]:
            warn(issue)
        if len(issues) > 5:
            warn(f"... et {len(issues)-5} autres problèmes")
    return True

test("App: fonctions de chargement", test_load_functions)
test("App: page Progression (données)", test_progression_page_data)
test("App: page Planning Cours", test_planning_cours_page)
test("App: page Planning Révisions", test_revision_plan_display)
test("App: champs affichage sessions", test_sessions_display_fields)

# =====================================================
print("\n" + "=" * 60)
print("9. FICHIERS DE DONNÉES")
print("=" * 60)

def test_data_files():
    required = [
        "data/course_schedule.json",
        "data/progress.json",
        "exports/revision_plan.json",
        "exports/concept_map.json",
        "cloud_data/revision_plan.json",
        "cloud_data/concept_map.json",
        "cloud_data/config.yaml",
        "cloud_data/course_schedule.json",
        "config/config.yaml",
    ]
    for f in required:
        assert Path(f).exists(), f"Fichier manquant: {f}"
    return True

def test_database_json():
    with open("data/database.json") as f:
        db = json.load(f)
    if not db.get("documents") and not db.get("concepts"):
        warn("database.json est vide (aucun document/concept)")
    return True

def test_cloud_schedule_sync():
    with open("data/course_schedule.json") as f:
        local = json.load(f)
    with open("cloud_data/course_schedule.json") as f:
        cloud = json.load(f)
    local_statuses = {s["status"] for s in local["sessions"]}
    cloud_statuses = {s["status"] for s in cloud["sessions"]}
    assert local_statuses == cloud_statuses, \
        f"Statuts différents: local={local_statuses}, cloud={cloud_statuses}"
    assert len(local["sessions"]) == len(cloud["sessions"])
    return True

test("Données: fichiers requis", test_data_files)
test("Données: database.json", test_database_json)
test("Données: schedule sync local/cloud", test_cloud_schedule_sync)

# =====================================================
print("\n" + "=" * 60)
print("10. COHÉRENCE GLOBALE")
print("=" * 60)

def test_concept_coverage():
    """Vérifier que les concepts du plan correspondent à la carte"""
    with open("exports/revision_plan.json") as f:
        rp = json.load(f)
    with open("exports/concept_map.json") as f:
        cm = json.load(f)
    
    plan_concepts = set()
    for s in rp["sessions"]:
        for c in s.get("concepts", []):
            clean = c.replace("Reviser: ", "")
            plan_concepts.add(clean)
    
    map_concepts = set(n["name"] for n in cm["nodes"])
    
    # Concepts dans le plan mais pas dans la carte
    orphans = plan_concepts - map_concepts
    if orphans:
        warn(f"{len(orphans)} concepts dans le plan mais pas dans la carte: {list(orphans)[:3]}...")
    
    # Concepts dans la carte mais pas dans le plan
    uncovered = map_concepts - plan_concepts
    if uncovered:
        warn(f"{len(uncovered)} concepts dans la carte mais pas dans le plan: {list(uncovered)[:3]}...")
    
    return True

def test_modules_consistency():
    """Vérifier la cohérence des modules entre cours et concepts"""
    with open("data/course_schedule.json") as f:
        cs = json.load(f)
    with open("exports/concept_map.json") as f:
        cm = json.load(f)
    
    schedule_modules = set(s["module_code"] for s in cs["sessions"])
    concept_modules = set(n.get("module", "") for n in cm["nodes"] if n.get("module"))
    
    no_content = schedule_modules - concept_modules
    if no_content:
        warn(f"Modules dans le planning SANS contenu analysé: {sorted(no_content)}")
    
    return True

test("Cohérence: couverture concepts", test_concept_coverage)
test("Cohérence: modules cours/concepts", test_modules_consistency)

# =====================================================
print("\n" + "=" * 60)
print("RÉSUMÉ DE L'AUDIT")
print("=" * 60)
total_tests = OK_COUNT + len(ERRORS)
print(f"\n✅ Tests réussis: {OK_COUNT}/{total_tests}")
if ERRORS:
    print(f"❌ Erreurs: {len(ERRORS)}")
    for e in ERRORS:
        print(f"   • {e}")
if WARNINGS:
    print(f"⚠️  Avertissements: {len(WARNINGS)}")
    for w in WARNINGS:
        print(f"   • {w}")
if not ERRORS:
    print("\n🎉 TOUS LES TESTS PASSENT!")
