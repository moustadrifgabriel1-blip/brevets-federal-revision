#!/usr/bin/env python3
"""
☁️ Synchronisation Google Drive
================================
Sauvegarde et récupération des cours sur Google Drive (2 To)
Fonctionne avec Google Drive installé sur Mac
"""

import os
import subprocess
import shutil
from pathlib import Path
from datetime import datetime

# Configuration
DRIVE_ACCOUNT = "moustadrifgabriel1@gmail.com"
BACKUP_FOLDER_NAME = "Brevets_Federal_Backup"

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
    
    # Chercher le dossier Google Drive (avec ou sans compte spécifique)
    for folder in cloud_storage.iterdir():
        if folder.name.startswith("GoogleDrive"):
            print(f"✅ Google Drive trouvé: {folder}")
            return folder
    
    print("❌ Google Drive non trouvé dans CloudStorage")
    print("💡 Vérifie que Google Drive est installé et connecté")
    return None


def get_backup_path(drive_path: Path) -> Path:
    """Retourne le chemin du backup sur Drive"""
    # Chercher le dossier principal (My Drive, Mon Drive, etc.)
    possible_names = ["My Drive", "Mon Drive", "Mi unidad", "Meine Ablage"]
    
    for name in possible_names:
        if (drive_path / name).exists():
            return drive_path / name / BACKUP_FOLDER_NAME
    
    # Fallback: directement dans le dossier Drive
    return drive_path / BACKUP_FOLDER_NAME


def sync_to_drive(drive_path: Path):
    """Synchronise les dossiers locaux vers Google Drive"""
    backup_folder = get_backup_path(drive_path)
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
    """Restaure depuis Google Drive vers le dossier local"""
    backup_folder = get_backup_path(drive_path)
    
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


def get_folder_info(folder_path: Path):
    """Retourne le nombre de fichiers et la taille totale d'un dossier"""
    if not folder_path.exists():
        return 0, 0
    try:
        files = [f for f in folder_path.rglob('*') if f.is_file()]
        total_size = sum(f.stat().st_size for f in files)
        return len(files), total_size
    except Exception:
        return 0, 0


def compare_folders(local_path: Path, drive_path: Path):
    """Compare deux dossiers et retourne les différences"""
    local_files = set()
    drive_files = set()
    
    if local_path.exists():
        for f in local_path.rglob('*'):
            if f.is_file():
                local_files.add(f.relative_to(local_path))
    
    if drive_path.exists():
        for f in drive_path.rglob('*'):
            if f.is_file():
                drive_files.add(f.relative_to(drive_path))
    
    only_local = local_files - drive_files
    only_drive = drive_files - local_files
    common = local_files & drive_files
    
    return {
        'local_only': only_local,
        'drive_only': only_drive,
        'common': common,
        'synced': len(only_local) == 0 and len(only_drive) == 0
    }


def show_status(drive_path: Path):
    """Affiche le statut détaillé du backup et de la synchronisation"""
    backup_folder = get_backup_path(drive_path)
    
    print("=" * 60)
    print("📊 STATUT DE SYNCHRONISATION GOOGLE DRIVE")
    print("=" * 60)
    
    # 1. Vérifier si le backup existe
    if not backup_folder.exists():
        print("\n❌ DRIVE: Aucun backup trouvé")
        print(f"   Chemin: {backup_folder}")
        print("\n💡 Lance: python sync_drive.py sync")
        return False
    
    print(f"\n✅ DRIVE: Backup trouvé")
    print(f"   📁 {backup_folder}")
    
    # 2. Afficher le timestamp de dernière sync
    timestamp_file = backup_folder / "last_sync.txt"
    if timestamp_file.exists():
        content = timestamp_file.read_text().strip().split('\n')
        for line in content:
            print(f"   {line}")
    
    # 3. Vérifier chaque dossier
    print("\n" + "-" * 60)
    print("📂 ÉTAT DES DOSSIERS")
    print("-" * 60)
    
    all_synced = True
    
    for folder_name in LOCAL_FOLDERS:
        local_path = Path(folder_name)
        drive_folder = backup_folder / folder_name
        
        # Vérifier si c'est un lien symbolique vers Drive
        is_symlink = local_path.is_symlink()
        symlink_ok = False
        
        if is_symlink:
            try:
                target = local_path.resolve()
                symlink_ok = target == drive_folder.resolve()
            except:
                pass
        
        # Obtenir les infos
        local_files, local_size = get_folder_info(local_path)
        drive_files, drive_size = get_folder_info(drive_folder)
        
        # Déterminer le statut
        if symlink_ok:
            status = "🔗 LIEN DRIVE"
            synced = True
        elif is_symlink:
            status = "⚠️ MAUVAIS LIEN"
            synced = False
        elif not local_path.exists() and not drive_folder.exists():
            status = "❌ INEXISTANT"
            synced = True  # Rien à sync
        elif not local_path.exists():
            status = "📥 À RESTAURER"
            synced = False
        elif not drive_folder.exists():
            status = "📤 À SAUVEGARDER"
            synced = False
        elif local_files == drive_files and abs(local_size - drive_size) < 1024:
            status = "✅ SYNCHRONISÉ"
            synced = True
        else:
            status = "🔄 DIFFÉRENT"
            synced = False
        
        if not synced:
            all_synced = False
        
        # Affichage
        print(f"\n  {folder_name}")
        print(f"    {status}")
        if symlink_ok:
            print(f"    → Lecture directe depuis Drive ({drive_files} fichiers)")
        else:
            print(f"    Local: {local_files} fichiers ({local_size / 1024 / 1024:.1f} MB)")
            print(f"    Drive: {drive_files} fichiers ({drive_size / 1024 / 1024:.1f} MB)")
    
    # 4. Résumé final
    print("\n" + "=" * 60)
    
    # Compter les liens
    links_count = sum(1 for f in ["cours", "Brevets Fédéral Electricien de réseaux"] 
                      if Path(f).is_symlink())
    
    if links_count == 2:
        print("✅ SYNCHRONISATION PARFAITE")
        print("   Tu travailles directement depuis Google Drive")
        print("   Toute modification est automatiquement synchronisée")
    elif all_synced:
        print("✅ FICHIERS SYNCHRONISÉS")
        print("   💡 Lance 'python sync_drive.py drive' pour travailler depuis Drive")
    else:
        print("⚠️ SYNCHRONISATION REQUISE")
        print("   💡 Lance 'python sync_drive.py sync' pour sauvegarder vers Drive")
        print("   💡 Lance 'python sync_drive.py drive' pour travailler depuis Drive")
    
    print("=" * 60)
    
    return all_synced


def create_drive_link(drive_path: Path):
    """Crée un lien symbolique vers le backup Drive pour accès direct"""
    backup_folder = get_backup_path(drive_path)
    
    if not backup_folder.exists():
        print("❌ Backup non trouvé, lance d'abord 'sync'")
        return False
    
    link_path = Path("drive_backup")
    
    if link_path.exists():
        if link_path.is_symlink():
            link_path.unlink()
        else:
            print(f"❌ {link_path} existe déjà et n'est pas un lien")
            return False
    
    link_path.symlink_to(backup_folder)
    print(f"✅ Lien créé: {link_path} → {backup_folder}")
    print("\n💡 Tu peux maintenant accéder aux fichiers via ./drive_backup/")
    return True


def work_from_drive(drive_path: Path):
    """Configure le projet pour travailler directement depuis Drive"""
    backup_folder = get_backup_path(drive_path)
    
    if not backup_folder.exists():
        print("❌ Backup non trouvé sur Drive")
        return False
    
    print(f"📂 Backup Drive: {backup_folder}")
    print("\n🔗 Création des liens symboliques...")
    
    folders_to_link = ["cours", "Brevets Fédéral Electricien de réseaux"]
    
    for folder_name in folders_to_link:
        src = backup_folder / folder_name
        dest = Path(folder_name)
        
        if not src.exists():
            print(f"  ⚠️ {folder_name} n'existe pas sur Drive")
            continue
        
        # Sauvegarder le dossier local s'il existe
        if dest.exists() and not dest.is_symlink():
            backup_local = Path(f"{folder_name}_local_backup")
            if not backup_local.exists():
                print(f"  📦 Sauvegarde locale: {folder_name} → {backup_local}")
                dest.rename(backup_local)
            else:
                print(f"  ⚠️ {folder_name} local existe, suppression...")
                shutil.rmtree(dest)
        elif dest.is_symlink():
            dest.unlink()
        
        # Créer le lien symbolique
        dest.symlink_to(src)
        print(f"  ✅ {folder_name} → Drive")
    
    print("\n✅ Configuration terminée!")
    print("📁 Tes cours sont maintenant lus directement depuis Google Drive")
    print("💡 Les modifications sont automatiquement synchronisées")
    return True


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
  python sync_drive.py sync      - Synchroniser local → Drive
  python sync_drive.py restore   - Restaurer Drive → local  
  python sync_drive.py status    - Voir le statut
  python sync_drive.py link      - Créer un lien vers Drive
  python sync_drive.py drive     - Travailler directement depuis Drive
        """)
        sys.exit(0)
    
    command = sys.argv[1].lower()
    
    if command == "sync":
        sync_to_drive(drive_path)
    elif command == "restore":
        restore_from_drive(drive_path)
    elif command == "status":
        show_status(drive_path)
    elif command == "link":
        create_drive_link(drive_path)
    elif command == "drive":
        work_from_drive(drive_path)
    else:
        print(f"❌ Commande inconnue: {command}")
