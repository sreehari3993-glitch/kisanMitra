"""KrishiMitra RAG Package: Precision Multilingual Agronomic Retrieval-Augmented Generation.

Provides high-throughput document extraction, ChromaDB vector indexing,
and resilient hybrid keyword retrieval for ICAR agronomy and FAO-56 irrigation models.
"""

from .config import (
    BASE_DIR,
    KB_DIR,
    RESOURCES_DIR,
    CHROMA_DB_PATH,
    COLLECTION_NAME,
    GDRIVE_RESOURCES_URL,
    GDRIVE_CHAT_LOGS_URL,
)
from .extractor import chunk_text, extract_file_chunks
from .vector_store import VectorStore
from .retriever import HybridRetriever
from .service import RAGService, rag_service


def retrieve(query: str, top_k: int = 4):
    """Retrieve top-k relevant knowledge passages."""
    return rag_service.retrieve(query, top_k=top_k)


def ingest_knowledge_base(force_reload: bool = False):
    """Ingest all knowledge documents and resources."""
    return rag_service.ingest_knowledge_base(force_reload=force_reload)


def get_indexed_resources_summary():
    """Get active resources list and statistics."""
    return rag_service.get_indexed_resources_summary()


CHROMA_AVAILABLE = rag_service.vector_store.chroma_available

__all__ = [
    "RAGService",
    "rag_service",
    "retrieve",
    "ingest_knowledge_base",
    "get_indexed_resources_summary",
    "VectorStore",
    "HybridRetriever",
    "chunk_text",
    "extract_file_chunks",
    "GDRIVE_RESOURCES_URL",
    "GDRIVE_CHAT_LOGS_URL",
    "CHROMA_AVAILABLE",
    "BASE_DIR",
    "KB_DIR",
    "RESOURCES_DIR",
    "CHROMA_DB_PATH",
    "COLLECTION_NAME",
]
