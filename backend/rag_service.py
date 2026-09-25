"""Backward compatibility layer for backend.rag_service.

All modular RAG components are now housed in the `backend.rag` package.
This module re-exports all symbols from `backend.rag` to preserve zero-breaking-change compatibility.
"""

from backend.rag import (
    BASE_DIR,
    KB_DIR,
    RESOURCES_DIR,
    CHROMA_DB_PATH,
    COLLECTION_NAME,
    GDRIVE_RESOURCES_URL,
    GDRIVE_CHAT_LOGS_URL,
    CHROMA_AVAILABLE,
    RAGService,
    rag_service,
    retrieve,
    ingest_knowledge_base,
    get_indexed_resources_summary,
    VectorStore,
    HybridRetriever,
    chunk_text,
    extract_file_chunks,
)

# For backward compatibility with any internal functions that used private names:
_chunk_text = chunk_text
_extract_file_chunks = extract_file_chunks

__all__ = [
    "BASE_DIR",
    "KB_DIR",
    "RESOURCES_DIR",
    "CHROMA_DB_PATH",
    "COLLECTION_NAME",
    "GDRIVE_RESOURCES_URL",
    "GDRIVE_CHAT_LOGS_URL",
    "CHROMA_AVAILABLE",
    "RAGService",
    "rag_service",
    "retrieve",
    "ingest_knowledge_base",
    "get_indexed_resources_summary",
    "VectorStore",
    "HybridRetriever",
    "chunk_text",
    "extract_file_chunks",
    "_chunk_text",
    "_extract_file_chunks",
]
