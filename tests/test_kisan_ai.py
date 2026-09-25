"""Unit tests for KrishiMitra Kisan AI Copilot & Knowledge Base RAG pipeline.

Tests language detection, Indic keyword extraction, RAG retrieval,
and chat history logging with Google Drive integration.
"""
import os
import json
from pathlib import Path
from backend.kisan_ai import detect_language_and_keywords
from backend import rag_service
from backend.chat_history import (
    append_chat_entry,
    get_all_chat_history,
    GDRIVE_FOLDER_URL,
    JSON_FILE,
    MD_FILE,
)


def test_language_and_keyword_detection():
    """Validates Indic script language detection and agronomic keyword mapping."""
    # Hindi query
    lang, retrieval_q = detect_language_and_keywords("धान की फसल में यूरिया कब डालना चाहिए?")
    assert lang == "Hindi"
    assert "rice paddy" in retrieval_q or "urea nitrogen" in retrieval_q

    # Malayalam query
    lang_ml, retrieval_q_ml = detect_language_and_keywords("നെല്ലിന്റെ ഇലകൾ മഞ്ഞളിക്കുന്നു, എന്ത് ചെയ്യണം?")
    assert lang_ml == "Malayalam"
    assert "rice paddy" in retrieval_q_ml

    # English query
    lang_en, retrieval_q_en = detect_language_and_keywords("When should I irrigate wheat with low soil moisture?")
    assert lang_en == "English"
    assert "wheat" in retrieval_q_en.lower()


def test_knowledge_base_retrieval():
    """Verifies that RAG service retrieves relevant chunks from the 4 knowledge base files."""
    ingested = rag_service.ingest_knowledge_base()
    assert ingested > 0

    # Retrieve for rice yellow leaves
    results = rag_service.retrieve("rice leaf yellowing nitrogen deficiency", top_k=3)
    assert len(results) > 0
    joined = " ".join(results).lower()
    assert "rice" in joined or "nitrogen" in joined or "chlorosis" in joined

    # Retrieve for irrigation FAO-56
    results_irri = rag_service.retrieve("FAO-56 Kc crop coefficient wheat irrigation", top_k=3)
    assert len(results_irri) > 0
    assert any("fao" in r.lower() or "kc" in r.lower() or "wheat" in r.lower() for r in results_irri)


def test_chat_history_and_gdrive_sync():
    """Tests conversation logging to local JSON/MD and Drive cloud reference."""
    sample_query = "What is the optimal pH for Cotton?"
    sample_answer = "Cotton requires a soil pH between 6.0 and 7.5. For acidic soils below 6.0, apply agricultural lime."
    sample_telemetry = {"n": 55.0, "p": 35.0, "k": 40.0, "ph": 5.5, "moisture": 22.0}

    entry = append_chat_entry(
        query=sample_query,
        answer=sample_answer,
        language="English",
        source="gemini",
        telemetry=sample_telemetry,
    )

    assert entry["query"] == sample_query
    assert entry["gdrive_folder"] == GDRIVE_FOLDER_URL
    assert "1wp9xKSZSxIzTriKEWmQYVlEhXcUfQXSE" in entry["gdrive_folder"]

    # Verify JSON file has entry
    history = get_all_chat_history()
    assert len(history) > 0
    assert any(h["query"] == sample_query for h in history)

    # Verify Markdown file contains query
    md_content = MD_FILE.read_text(encoding="utf-8")
    assert sample_query in md_content
    assert "Cotton" in md_content
    assert GDRIVE_FOLDER_URL in md_content
