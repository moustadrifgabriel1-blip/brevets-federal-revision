"""
☁️ Intégration Google Drive pour Streamlit
==========================================
Permet de charger les fichiers de cours depuis Google Drive
"""

import streamlit as st
import json
import io
from pathlib import Path

# Essayer d'importer les dépendances Google Drive
try:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaIoBaseDownload
    GOOGLE_DRIVE_AVAILABLE = True
except ImportError:
    GOOGLE_DRIVE_AVAILABLE = False


def get_drive_credentials():
    """Récupère les credentials depuis Streamlit secrets"""
    if not hasattr(st, 'secrets') or 'gcp_service_account' not in st.secrets:
        return None
    
    try:
        credentials = service_account.Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=['https://www.googleapis.com/auth/drive.readonly']
        )
        return credentials
    except Exception as e:
        st.error(f"Erreur credentials: {e}")
        return None


def get_drive_service():
    """Crée le service Google Drive"""
    credentials = get_drive_credentials()
    if not credentials:
        return None
    
    try:
        service = build('drive', 'v3', credentials=credentials)
        return service
    except Exception as e:
        st.error(f"Erreur service Drive: {e}")
        return None


def list_drive_files(folder_id=None, file_types=None):
    """Liste les fichiers dans un dossier Drive"""
    service = get_drive_service()
    if not service:
        return []
    
    try:
        query_parts = ["trashed=false"]
        
        if folder_id:
            query_parts.append(f"'{folder_id}' in parents")
        
        if file_types:
            type_queries = [f"mimeType='{t}'" for t in file_types]
            query_parts.append(f"({' or '.join(type_queries)})")
        
        query = " and ".join(query_parts)
        
        results = service.files().list(
            q=query,
            pageSize=100,
            fields="files(id, name, mimeType, size, modifiedTime)"
        ).execute()
        
        return results.get('files', [])
    except Exception as e:
        st.error(f"Erreur liste fichiers: {e}")
        return []


def download_file_from_drive(file_id):
    """Télécharge un fichier depuis Drive"""
    service = get_drive_service()
    if not service:
        return None
    
    try:
        request = service.files().get_media(fileId=file_id)
        file_buffer = io.BytesIO()
        downloader = MediaIoBaseDownload(file_buffer, request)
        
        done = False
        while not done:
            status, done = downloader.next_chunk()
        
        file_buffer.seek(0)
        return file_buffer
    except Exception as e:
        st.error(f"Erreur téléchargement: {e}")
        return None


def find_backup_folder():
    """Trouve le dossier Brevets_Federal_Backup sur Drive"""
    service = get_drive_service()
    if not service:
        return None
    
    try:
        results = service.files().list(
            q="name='Brevets_Federal_Backup' and mimeType='application/vnd.google-apps.folder' and trashed=false",
            fields="files(id, name)"
        ).execute()
        
        files = results.get('files', [])
        if files:
            return files[0]['id']
        return None
    except Exception as e:
        st.error(f"Erreur recherche dossier: {e}")
        return None


def is_drive_configured():
    """Vérifie si Google Drive est configuré"""
    return GOOGLE_DRIVE_AVAILABLE and hasattr(st, 'secrets') and 'gcp_service_account' in st.secrets


def render_drive_status():
    """Affiche le statut de la connexion Drive dans l'app"""
    if not GOOGLE_DRIVE_AVAILABLE:
        st.warning("⚠️ Librairies Google Drive non installées")
        st.code("pip install google-api-python-client google-auth")
        return False
    
    if not hasattr(st, 'secrets') or 'gcp_service_account' not in st.secrets:
        st.info("💡 Google Drive non configuré. Les données locales seront utilisées.")
        return False
    
    # Tester la connexion
    service = get_drive_service()
    if service:
        st.success("✅ Connecté à Google Drive")
        return True
    else:
        st.error("❌ Impossible de se connecter à Google Drive")
        return False
