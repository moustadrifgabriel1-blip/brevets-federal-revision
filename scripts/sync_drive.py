#!/usr/bin/env python3
"""
☁️ Synchronisation Google Drive
================================
Sauvegarde automatique des cours sur Google Drive (2 To)
"""

import os
import subprocess
import shutil
from pathlib import Path
from datetime import datetime

# Configuration
DRIVE_FOLDER = Path.home() / "Library/CloudStorage/GoogleDrive-" # Sera complété
LOCAL_FOLDERS = [
    "cours",
    "Brevets Fédéral Electricien de réseaux",
    "directives_examen",
    "exports",
    "data",
    "config"
]

def find_google_drive_path():
    """Trouve le chemin de Google Drive sur Mac"""
    cloud_storage = Path.home() / "Library/CloudStorage"
    
    if not cloud_storage.exists():
        print("❌ Dossier CloudStorage non trouvé")
        return None
    
    # Chercher le dossier Google Drive
    for folder in cloud_storage.iterdir():
        if folder.name.startswith("GoogleDrive"):
            print(f"✅ Google Drive trouvé: {folder}")
            return folder
    
    print("❌ Google Drive non trouvé dans CloudStorage")
    print("💡 Vérifie que Google Drive est installé et connecté")
    return None


def sync_to_drive(drive_path: Path):
    """Synchronise les dossiers vers Google Drive"""
    # Chercher le dossier principal (My Drive, Mon Drive, etc.)
    possible_names = ["My Drive", "Mon Drive", "Mi unidad", "Meine Ablage"]
    main_folder = None
    
    for name in possible_names:
        if (drive_path / name).exists():
            main_folder = drive_path / name
            break
    
    if not main_folder:
        # Essayer directement dans le dossier Drive
        main_folder = drive_path
    
    backup_folder = main_folder / "Brevets_Federal_Backup"
    backup_folder.mkdir(parents=True, exist_ok=True)
    print(f"📁 Dossier de backup: {backup_folder}")
    
    total_size = 0
    synced_files = 0
    
    for folder_name in LOCAL_FOLDERS:
        src = Path(folder_name)
        if not src.exists():
            print(f"  ⚠️ {folder_name} n'existe pas, ignoré")
            continue
        
        dest = backup_folder / folder_name
        print(f"\n📂 Synchronisation: {folder_name}")
        
        # Utiliser rsync pour une synchro efficace
        try:
            result = subprocess.run([
                "rsync", "-av", "--delete",
                str(src) + "/",
                str(dest) + "/"
            ], capture_output=True)
            
            if result.returncode == 0:
                # Compter la taille
                folder_size = sum(f.stat().st_size for f in src.rglob('*') if f.is_file())
                total_size += folder_size
                synced_files += len(list(src.rglob('*')))
                print(f"  ✅ {folder_name} synchronisé ({folder_size / 1024 / 1024:.1f} MB)")
            else:
                print(f"  ❌ Erreur rsync (code {result.returncode})")
        except FileNotFoundError:
            # rsync non disponible, utiliser shutil
            print(f"  ⚠️ rsync non disponible, copie classique...")
            if dest.exists():
                shutil.rmtree(dest)
            shutil.copytree(src, dest)
            folder_size = sum(f.stat().st_size for f in src.rglob('*') if f.is_file())
            total_size += folder_size
            print(f"  ✅ {folder_name} copié ({folder_size / 1024 / 1024:.1f} MB)")
    
    # Créer un fichier de timestamp
    timestamp_file = backup_folder / "last_sync.txt"
    with open(timestamp_file, 'w') as f:
        f.write(f"Dernière synchronisation: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Taille totale: {total_size / 1024 / 1024 / 1024:.2f} GB\n")
        f.write(f"Fichiers: {synced_files}\n")
    
    print(f"\n{'='*50}")
    print(f"✅ Synchronisation terminée!")
    print(f"📊 Taille totale: {total_size / 1024 / 1024 / 1024:.2f} GB")
    print(f"📁 Emplacement: {backup_folder}")
    
    return backup_folder


def restore_from_drive(drive_path: Path):
    """Restaure depuis Google Drive"""
    # Chercher le dossier principal
    possible_names = ["My Drive", "Mon Drive", "Mi unidad", "Meine Ablage"]
    main_folder = None
    
    for name in possible_names:
        if (drive_path / name).exists():
            main_folder = drive_path / name
            break
    
    if not main_folder:
        main_folder = drive_path
    
    backup_folder = main_folder / "Brevets_Federal_Backup"
    
    if not backup_folder.exists():
        print(f"❌ Backup non trouvé: {backup_folder}")
        return False
    
    print(f"📂 Restauration depuis: {backup_folder}")
    
    for folder_name in LOCAL_FOLDERS:
        src = backup_folder / folder_name
        if not src.exists():
            continue
        
        dest = Path(folder_name)
        print(f"  📥 {folder_name}...")
        
        try:
            result = subprocess.run([
                "rsync", "-av", "--progress",
                str(src) + "/",
                str(dest) + "/"
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"  ✅ {folder_name} restauré")
        except FileNotFoundError:
            if dest.exists():
                shutil.rmtree(dest)
            shutil.copytree(src, dest)
            print(f"  ✅ {folder_name} restauré")
    
    print("\n✅ Restauration terminée!")
    return True


def show_status(drive_path: Path):
    """Affiche le statut du backup"""
    # Chercher le dossier principal
    possible_names = ["My Drive", "Mon Drive", "Mi unidad", "Meine Ablage"]
    main_folder = None
    
    for name in possible_names:
        if (drive_path / name).exists():
            main_folder = drive_path / name
            break
    
    if not main_folder:
        main_folder = drive_path
    
    backup_folder = main_folder / "Brevets_Federal_Backup"
    
    if not backup_folder.exists():
        print("❌ Aucun backup trouvé sur Google Drive")
        return
    
    timestamp_file = backup_folder / "last_sync.txt"
    if timestamp_file.exists():
        print("📊 Statut du backup Google Drive:")
        print("-" * 40)
        print(timestamp_file.read_text())
    
    print("\n📁 Contenu du backup:")
    for item in backup_folder.iterdir():
        if item.is_dir():
            size = sum(f.stat().st_size for f in item.rglob('*') if f.is_file())
            files = len(list(item.rglob('*')))
            print(f"  📂 {item.name}: {size / 1024 / 1024:.1f} MB ({files} fichiers)")


if __name__ == "__main__":
    import sys
    
    print("""
☁️ Synchronisation Google Drive
================================
""")
    
    # Trouver Google Drive
    drive_path = find_google_drive_path()
    
    if not drive_path:
        print("\n💡 Solutions:")
        print("1. Installe Google Drive: https://www.google.com/drive/download/")
        print("2. Connecte-toi à ton compte Google")
        print("3. Active la synchronisation")
        sys.exit(1)
    
    if len(sys.argv) < 2:
        print("""
Usage:
  python sync_drive.py sync      - Synchroniser vers Drive
  python sync_drive.py restore   - Restaurer depuis Drive  
  python sync_drive.py status    - Voir le statut
        """)
        sys.exit(0)
    
    command = sys.argv[1].lower()
    
    if command == "sync":
        sync_to_drive(drive_path)
    elif command == "restore":
        restore_from_drive(drive_path)
    elif command == "status":
        show_status(drive_path)
    else:
        print(f"❌ Commande inconnue: {command}")
