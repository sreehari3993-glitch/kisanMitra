import os
from pathlib import Path

# Base directories
PACKAGE_DIR = Path(__file__).resolve().parent
BACKEND_DIR = PACKAGE_DIR.parent
BASE_DIR = BACKEND_DIR.parent

KB_DIR = BASE_DIR / "knowledge_base"
RESOURCES_DIR = BASE_DIR / "resources"
CHROMA_DB_PATH = BASE_DIR / "chroma_db"

COLLECTION_NAME = "krishimitra_kb"
MODEL_NAME = "all-MiniLM-L6-v2"

# Google Drive folder where user stores research papers, tables, and water balance manuals
GDRIVE_RESOURCES_URL = (
    "https://drive.google.com/drive/folders/1LdRwAKBybFYsijbMmOd2EdLRDqISTpI6?usp=drive_link"
)

# Google Drive folder for farmer chat logs
GDRIVE_CHAT_LOGS_URL = (
    "https://drive.google.com/drive/folders/1wp9xKSZSxIzTriKEWmQYVlEhXcUfQXSE?usp=drive_link"
)
