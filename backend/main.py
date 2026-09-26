import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Dict, List

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend import kisan_ai
from backend import rag as rag_service
from backend.chat_history import GDRIVE_FOLDER_URL, get_all_chat_history
from backend.config import settings
from backend.database import engine, get_db
from backend.ml_service import load_model
from backend.models import TelemetryLog
from backend.routers import auth, irrigation, recommendations, telemetry
from backend.schemas import KisanAIChatRequest, KisanAIChatResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan context manager handling startup and shutdown events."""
    # ------------------ STARTUP ------------------
    print("KrishiMitra: Starting up backend services...")

    # 1. Load ML Model into memory (lifespan startup — never per-request)
    try:
        load_model()
    except Exception as e:
        print(f"[Lifespan Startup Warning] ML Model load skipped: {e}")
        print("Note: Train the model by running 'python ml/train_model.py' to enable ML recommendations.")

    # 2. Ingest Knowledge Base into ChromaDB
    try:
        count = rag_service.ingest_knowledge_base()
        print(f"RAG Knowledge Base ready with {count} indexed chunks.")
    except Exception as e:
        print(f"[Lifespan Startup Warning] Knowledge base ingestion warning: {e}")

    # 3. Initialize Chroma persistent client and store on app.state
    try:
        import importlib
        if importlib.util.find_spec("chromadb") is not None:
            chroma_mod = importlib.import_module("chromadb")
            app.state.chroma_client = chroma_mod.PersistentClient(path=settings.CHROMA_DB_PATH)
            print(f"ChromaDB persistent client successfully initialized at '{settings.CHROMA_DB_PATH}'")
        else:
            app.state.chroma_client = None
    except Exception as e:
        print(f"[Lifespan Startup Warning] ChromaDB initialization skipped/failed: {e}")
        app.state.chroma_client = None

    # 4. MySQL database connectivity check & table auto-creation
    try:
        from backend.database import Base
        import backend.models
        Base.metadata.create_all(bind=engine)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("MySQL database connected and tables verified: telemetry_logs, crop_recommendations, prescriptions.")
    except Exception as e:
        print(
            f"[Lifespan Startup Warning] MySQL check/migration failed: {e}. "
            "Ensure MySQL is running on localhost:3306 with schema 'krishi_precision_db'."
        )

    yield

    # ----------------- SHUTDOWN -----------------
    print("KrishiMitra: Shutting down backend...")
    engine.dispose()
    print("SQLAlchemy database engine connection pool disposed.")


app = FastAPI(
    title="KrishiMitra API",
    description="AI-powered precision soil intelligence & irrigation advisory platform",
    version="1.0.0",
    lifespan=lifespan,
)

# Enable permissive CORS for local dev, Vercel frontend, and mobile native apps
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_origin_regex=r"https?://.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers with /api prefix
app.include_router(telemetry.router, prefix="/api", tags=["Telemetry & Soil Health"])
app.include_router(
    recommendations.router,
    prefix="/api",
    tags=["Crop Recommendations & Fertilizer Prescriptions"],
)
app.include_router(irrigation.router, prefix="/api", tags=["Irrigation Advisory"])
app.include_router(auth.router)


# -------------------------------------------------------------
# Kisan AI Multilingual RAG Copilot Endpoint
# -------------------------------------------------------------
@app.post(
    "/api/kisan-ai/chat",
    response_model=KisanAIChatResponse,
    tags=["Kisan AI Copilot"],
    summary="Multilingual agricultural advisory with RAG and Gemini/Ollama fallback",
)
async def kisan_ai_chat(payload: KisanAIChatRequest, db: Session = Depends(get_db)):
    """Async route for genuinely I/O-bound LLM generation and retrieval.

    Takes a farmer's natural language query (Hindi, Malayalam, Tamil, English, etc.)
    and active telemetry context, runs the 4-stage RAG pipeline, and logs conversation.
    """
    telemetry_row = (
        db.query(TelemetryLog).filter(TelemetryLog.id == payload.telemetry_id).first()
    )
    if not telemetry_row:
        telemetry_row = db.query(TelemetryLog).order_by(TelemetryLog.id.desc()).first()

    if telemetry_row:
        telemetry_dict = {
            "n": float(telemetry_row.n),
            "p": float(telemetry_row.p),
            "k": float(telemetry_row.k),
            "ph": float(telemetry_row.ph),
            "moisture": float(telemetry_row.moisture),
            "temperature": float(telemetry_row.temperature),
            "humidity": float(telemetry_row.humidity),
            "rainfall": float(telemetry_row.rainfall),
        }
    else:
        telemetry_dict = {
            "n": 60.0,
            "p": 45.0,
            "k": 50.0,
            "ph": 6.5,
            "moisture": 25.0,
            "temperature": 28.0,
            "humidity": 65.0,
            "rainfall": 100.0,
        }

    result = await kisan_ai.answer_query(query=payload.query, live_telemetry=telemetry_dict)

    return KisanAIChatResponse(
        answer=result["answer"],
        language=result["language"],
        source=result["source"],
        gdrive_folder=GDRIVE_FOLDER_URL,
        gdrive_resources_folder=rag_service.GDRIVE_RESOURCES_URL,
    )


@app.get(
    "/api/kisan-ai/history",
    tags=["Kisan AI Copilot"],
    summary="Retrieve persistent chat history log and cloud mirror link",
)
def get_chat_history():
    """Returns all recorded conversations along with the Google Drive cloud mirror folder link."""
    return {
        "gdrive_folder": GDRIVE_FOLDER_URL,
        "gdrive_resources_folder": rag_service.GDRIVE_RESOURCES_URL,
        "history": get_all_chat_history(),
    }


@app.get(
    "/api/kisan-ai/resources",
    tags=["Kisan AI Copilot"],
    summary="Retrieve actively indexed research documents, tables, and Google Drive resources link",
)
def get_kisan_ai_resources():
    """Returns active knowledge base & resources metadata, file list, and Drive folder link."""
    summary = rag_service.get_indexed_resources_summary()
    has_key = bool(kisan_ai.get_gemini_api_key())
    summary["engine_mode"] = (
        "Gemini 1.5 Flash (Audited)"
        if has_key
        else "ICAR & FAO-56 Grounded"
    )
    summary["has_gemini_key"] = has_key
    return summary


@app.post(
    "/api/kisan-ai/set-key",
    tags=["Kisan AI Copilot"],
    summary="Configure Google Gemini API key dynamically",
)
def set_gemini_api_key(payload: Dict[str, str]):
    """Dynamically activates and saves the farmer's Google Gemini API key."""
    api_key = (payload.get("api_key") or "").strip()
    if not api_key:
        raise HTTPException(status_code=400, detail="API key cannot be empty.")

    os.environ["GEMINI_API_KEY"] = api_key
    settings.GEMINI_API_KEY = api_key

    # Persist to .env file
    env_path = Path(__file__).resolve().parent.parent / ".env"
    try:
        lines = []
        if env_path.exists():
            for line in env_path.read_text(encoding="utf-8").splitlines():
                if not line.strip().startswith("GEMINI_API_KEY="):
                    lines.append(line)
        lines.append(f"GEMINI_API_KEY={api_key}")
        env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    except Exception as e:
        print(f"Warning: could not write key to .env: {e}")

    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
    except Exception:
        pass

    return {
        "status": "success",
        "message": "Google Gemini API key activated successfully.",
        "engine_mode": "Gemini 1.5 Flash (Audited)",
        "has_gemini_key": True,
    }


@app.get("/api/mobile/status")
async def get_mobile_status():
    """Return backend status, local IP discovery addresses, and mobile features."""
    import socket
    local_ips = []
    try:
        hostname = socket.gethostname()
        local_ips.append(socket.gethostbyname(hostname))
    except Exception:
        pass

    return {
        "status": "online",
        "app_name": "KrishiMitra Mobile",
        "version": "1.0.0",
        "pwa_ready": True,
        "capacitor_ready": True,
        "local_hostnames": local_ips,
        "server_port": 8000,
        "supported_plugins": ["camera", "geolocation", "haptics", "notifications"]
    }


# Mount frontend directory as static files at "/" AFTER all /api routes are registered
frontend_dir = Path(__file__).resolve().parent.parent / "frontend"
if frontend_dir.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")
