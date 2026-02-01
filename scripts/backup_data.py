#!/usr/bin/env python3
"""
🔄 Système de Backup/Restore des données analysées
===================================================
Ce script permet de sauvegarder et restaurer toutes les données
analysées (concepts, planning, etc.) sans les gros fichiers PDF.
"""

import json
import os
import zipfile
from pathlib import Path
from datetime import datetime
import shutil

BACKUP_DIR = Path("backups")
DATA_FILES = [
    "exports/concept_map.json",
    "exports/revision_plan.json",
    "data/database.json",
    "data/course_schedule.json",
    "config/config.yaml",
]


def create_backup():
    """Crée un backup ZIP de toutes les données analysées"""
    BACKUP_DIR.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"backup_donnees_{timestamp}.zip"
    backup_path = BACKUP_DIR / backup_name
    
    print(f"📦 Création du backup: {backup_name}")
    
    with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file_path in DATA_FILES:
            if Path(file_path).exists():
                zipf.write(file_path)
                print(f"  ✅ {file_path}")
            else:
                print(f"  ⚠️ {file_path} (non trouvé)")
        
        # Ajouter les README des dossiers cours pour garder la structure
        for readme in Path("cours").rglob("README.md"):
            zipf.write(readme)
            print(f"  ✅ {readme}")
    
    size_kb = backup_path.stat().st_size / 1024
    print(f"\n✅ Backup créé: {backup_path} ({size_kb:.1f} KB)")
    return backup_path


def restore_backup(backup_path: str):
    """Restaure un backup ZIP"""
    backup_file = Path(backup_path)
    
    if not backup_file.exists():
        print(f"❌ Fichier non trouvé: {backup_path}")
        return False
    
    print(f"📂 Restauration depuis: {backup_file.name}")
    
    with zipfile.ZipFile(backup_file, 'r') as zipf:
        zipf.extractall(".")
        for name in zipf.namelist():
            print(f"  ✅ {name}")
    
    print("\n✅ Restauration terminée!")
    return True


def list_backups():
    """Liste tous les backups disponibles"""
    if not BACKUP_DIR.exists():
        print("📭 Aucun backup trouvé")
        return []
    
    backups = sorted(BACKUP_DIR.glob("backup_*.zip"), reverse=True)
    
    if not backups:
        print("📭 Aucun backup trouvé")
        return []
    
    print("📋 Backups disponibles:")
    for i, backup in enumerate(backups, 1):
        size_kb = backup.stat().st_size / 1024
        print(f"  {i}. {backup.name} ({size_kb:.1f} KB)")
    
    return backups


def export_for_cloud():
    """Exporte les données pour utilisation sur Streamlit Cloud"""
    export_dir = Path("cloud_data")
    export_dir.mkdir(exist_ok=True)
    
    print("☁️ Export pour Streamlit Cloud...")
    
    for file_path in DATA_FILES:
        src = Path(file_path)
        if src.exists():
            # Copier dans cloud_data/
            dest = export_dir / src.name
            shutil.copy2(src, dest)
            print(f"  ✅ {src.name}")
    
    # Créer un fichier d'info
    info = {
        "exported_at": datetime.now().isoformat(),
        "files": [Path(f).name for f in DATA_FILES if Path(f).exists()]
    }
    with open(export_dir / "info.json", 'w') as f:
        json.dump(info, f, indent=2)
    
    print(f"\n✅ Données exportées dans: {export_dir}/")
    print("💡 Ces fichiers peuvent être uploadés sur Streamlit Cloud")
    return export_dir


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("""
🔄 Gestionnaire de Backup
========================

Usage:
  python backup_data.py backup     - Créer un backup
  python backup_data.py restore    - Restaurer le dernier backup
  python backup_data.py list       - Lister les backups
  python backup_data.py cloud      - Exporter pour Streamlit Cloud
        """)
        sys.exit(0)
    
    command = sys.argv[1].lower()
    
    if command == "backup":
        create_backup()
    elif command == "restore":
        backups = list_backups()
        if backups:
            restore_backup(str(backups[0]))
    elif command == "list":
        list_backups()
    elif command == "cloud":
        export_for_cloud()
    else:
        print(f"❌ Commande inconnue: {command}")
