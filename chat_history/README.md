# 🌾 KrishiMitra Kisan AI — Persistent Chat History & Google Drive Mirror

This directory stores the complete, persistent audit trail of all conversations held with the **Kisan AI Multilingual RAG Copilot**.

## ☁️ Google Drive Cloud Folder
- **Direct Link**: [Google Drive Folder](https://drive.google.com/drive/folders/1wp9xKSZSxIzTriKEWmQYVlEhXcUfQXSE?usp=drive_link)
- **Folder ID**: `1wp9xKSZSxIzTriKEWmQYVlEhXcUfQXSE`

---

## 📁 Files Stored Here

1. **`chat_history.json`**:
   Structured JSON array containing every farmer session:
   - `timestamp`: Date and time of conversation.
   - `query`: The raw natural language query (Hindi, Malayalam, Tamil, English, etc.).
   - `language`: Detected language.
   - `source`: LLM engine (`gemini` [Gemini 1.5 Flash audited] or `ollama` [Llama 3.2:3b offline]).
   - `telemetry_snapshot`: Live soil NPK, pH, moisture, temperature, humidity, rainfall at the time of query.
   - `answer`: Verified agronomic advice.
   - `gdrive_folder`: Link to cloud folder.

2. **`chat_history.md`**:
   Clean, human-readable Markdown digest of all advisory logs, formatted with session headers, telemetry badges, and ICAR/FAO-56 citation references.

---

## 🔄 Automatic Synchronization

Each time a farmer sends a question via the `#kisan-chat` widget or API endpoint `POST /api/kisan-ai/chat`:
1. Both local files (`chat_history.json` and `chat_history.md`) are immediately updated.
2. The `backend/drive_sync.py` module automatically connects and updates the file `KrishiMitra_KisanAI_ChatHistory.md` in the Google Drive folder.
3. If a Google Cloud service account JSON key (`service_account.json` or `credentials.json`) is placed in the project root, live automated cloud push is performed using the Drive v3 API. Even without Google credentials, full local persistence is preserved and each response includes the direct Google Drive link.
