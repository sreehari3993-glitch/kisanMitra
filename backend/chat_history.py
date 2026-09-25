from datetime import datetime
import json
from pathlib import Path
from typing import Any, Dict, List

BASE_DIR = Path(__file__).resolve().parent.parent
HISTORY_DIR = BASE_DIR / "chat_history"
JSON_FILE = HISTORY_DIR / "chat_history.json"
MD_FILE = HISTORY_DIR / "chat_history.md"

GDRIVE_FOLDER_URL = (
    "https://drive.google.com/drive/folders/1wp9xKSZSxIzTriKEWmQYVlEhXcUfQXSE?usp=drive_link"
)


def init_chat_history() -> None:
    """Ensures chat_history directory and files exist."""
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    if not JSON_FILE.exists():
        JSON_FILE.write_text("[]", encoding="utf-8")
    if not MD_FILE.exists():
        header = (
            "# KrishiMitra Kisan AI — Persistent Chat History\n\n"
            f"> Cloud Drive Mirror: [{GDRIVE_FOLDER_URL}]({GDRIVE_FOLDER_URL})\n\n"
            "---\n\n"
        )
        MD_FILE.write_text(header, encoding="utf-8")


def append_chat_entry(
    query: str,
    answer: str,
    language: str,
    source: str,
    telemetry: Dict[str, Any],
) -> Dict[str, Any]:
    """Appends a new conversation entry to both JSON and Markdown history files."""
    init_chat_history()

    now_iso = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = {
        "timestamp": now_iso,
        "query": query,
        "language": language,
        "source": source,
        "telemetry_snapshot": telemetry,
        "answer": answer,
        "gdrive_folder": GDRIVE_FOLDER_URL,
    }

    # 1. Update JSON
    try:
        data: List[Dict[str, Any]] = json.loads(JSON_FILE.read_text(encoding="utf-8"))
    except Exception:
        data = []

    data.append(entry)
    JSON_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    # 2. Append to Markdown file
    md_entry = (
        f"### 🌾 Session: {now_iso}\n"
        f"- **Language**: `{language}` | **Engine**: `{source.upper()}`\n"
        f"- **Telemetry Context**: N={telemetry.get('n', '-')}, P={telemetry.get('p', '-')}, "
        f"K={telemetry.get('k', '-')}, pH={telemetry.get('ph', '-')}, Moisture={telemetry.get('moisture', '-')}\n\n"
        f"**Farmer Query**:\n> {query}\n\n"
        f"**Kisan AI Answer**:\n{answer}\n\n"
        "---\n\n"
    )
    with MD_FILE.open("a", encoding="utf-8") as f:
        f.write(md_entry)

    # 3. Synchronize with Google Drive folder
    try:
        from backend.drive_sync import sync_file_to_drive
        sync_result = sync_file_to_drive(MD_FILE)
        entry["drive_sync"] = sync_result
    except Exception as drive_err:
        entry["drive_sync"] = {"status": "local_only", "error": str(drive_err)}

    return entry


def get_all_chat_history() -> List[Dict[str, Any]]:
    """Retrieves full conversation history."""
    init_chat_history()
    try:
        return json.loads(JSON_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []
