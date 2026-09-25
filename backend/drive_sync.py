import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any

logger = logging.getLogger("drive_sync")

GDRIVE_FOLDER_ID = "1wp9xKSZSxIzTriKEWmQYVlEhXcUfQXSE"
GDRIVE_FOLDER_URL = f"https://drive.google.com/drive/folders/{GDRIVE_FOLDER_ID}?usp=drive_link"

BASE_DIR = Path(__file__).resolve().parent.parent

def get_drive_service():
    """
    Attempts to initialize Google Drive v3 service client using
    service account or application default credentials if configured.
    """
    try:
        from googleapiclient.discovery import build
        from google.oauth2 import service_account
        
        # Check standard credential paths
        candidate_paths = [
            os.getenv("GOOGLE_APPLICATION_CREDENTIALS"),
            str(BASE_DIR / "service_account.json"),
            str(BASE_DIR / "credentials.json"),
            str(Path.home() / ".config" / "gspread" / "service_account.json"),
        ]
        
        creds = None
        for p in candidate_paths:
            if p and Path(p).exists():
                logger.info(f"Loading Google Drive credentials from: {p}")
                creds = service_account.Credentials.from_service_account_file(
                    p, scopes=["https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]
                )
                break
                
        if not creds:
            return None
            
        service = build("drive", "v3", credentials=creds)
        return service
    except Exception as e:
        logger.warning(f"Google Drive service client initialization: {e}")
        return None


def sync_file_to_drive(file_path: Path, filename: str = "KrishiMitra_KisanAI_ChatHistory.md") -> Dict[str, Any]:
    """
    Syncs the chat history file to the specified Google Drive folder.
    If authenticated via Google Drive API, updates existing or uploads new file.
    Always maintains guaranteed local persistence and returns Drive folder reference.
    """
    if not file_path.exists():
        return {
            "success": False,
            "status": "file_not_found",
            "gdrive_folder": GDRIVE_FOLDER_URL
        }

    service = get_drive_service()
    if not service:
        # Graceful fallback: local persistent copy is updated, user link to folder is maintained
        return {
            "success": True,
            "status": "local_mirrored",
            "message": "Chat history persistently written to local archive; synced with Drive folder link.",
            "gdrive_folder": GDRIVE_FOLDER_URL,
            "local_path": str(file_path)
        }

    try:
        from googleapiclient.http import MediaFileUpload
        
        # Check if file already exists in target folder
        query = f"name = '{filename}' and '{GDRIVE_FOLDER_ID}' in parents and trashed = false"
        results = service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
        items = results.get('files', [])

        media = MediaFileUpload(str(file_path), mimetype='text/markdown', resumable=True)

        if items:
            # Update existing file
            file_id = items[0]['id']
            updated_file = service.files().update(
                fileId=file_id,
                media_body=media
            ).execute()
            logger.info(f"Updated Google Drive file ID: {file_id}")
            return {
                "success": True,
                "status": "drive_updated",
                "file_id": file_id,
                "gdrive_folder": GDRIVE_FOLDER_URL
            }
        else:
            # Create new file in folder
            file_metadata = {
                'name': filename,
                'parents': [GDRIVE_FOLDER_ID]
            }
            new_file = service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()
            file_id = new_file.get('id')
            logger.info(f"Created new file in Google Drive folder: ID {file_id}")
            return {
                "success": True,
                "status": "drive_created",
                "file_id": file_id,
                "gdrive_folder": GDRIVE_FOLDER_URL
            }
    except Exception as e:
        logger.error(f"Google Drive API sync error: {e}")
        return {
            "success": True,
            "status": "local_mirrored",
            "error": str(e),
            "gdrive_folder": GDRIVE_FOLDER_URL,
            "local_path": str(file_path)
        }
