import logging
from pathlib import Path
from typing import Any, Dict, List
from .config import KB_DIR, RESOURCES_DIR, GDRIVE_RESOURCES_URL
from .extractor import extract_file_chunks
from .vector_store import VectorStore
from .retriever import HybridRetriever

logger = logging.getLogger("rag.service")


class RAGService:
    """Enterprise RAG Service orchestrating document extraction, vector indexing,

    and precision context retrieval.
    """

    def __init__(self):
        self.vector_store = VectorStore()
        self.retriever = HybridRetriever(self.vector_store)
        self.target_files: List[Path] = []
        self._auto_initialized = False

    def _discover_files(self) -> List[Path]:
        files: List[Path] = []
        if KB_DIR.exists():
            files.extend(list(KB_DIR.glob("*.md")) + list(KB_DIR.glob("*.txt")))
        if RESOURCES_DIR.exists():
            files.extend(
                list(RESOURCES_DIR.glob("*.pdf"))
                + list(RESOURCES_DIR.glob("*.txt"))
                + list(RESOURCES_DIR.glob("*.md"))
                + list(RESOURCES_DIR.glob("*.csv"))
            )
        self.target_files = files
        return files

    def ingest_knowledge_base(self, force_reload: bool = False) -> int:
        """Discovers and indexes all agronomic resources from knowledge_base/ and resources/."""
        target_files = self._discover_files()
        if not target_files:
            logger.warning("No reference files found in knowledge_base/ or resources/.")
            return 0

        # Check existing collection count
        if not force_reload and self.vector_store.chroma_available:
            existing_count = self.vector_store.count()
            if existing_count > 0:
                logger.info(
                    f"RAGService: Collection contains {existing_count} chunks. Populating in-memory cache..."
                )
                if not self.vector_store.fallback_chunks:
                    for f in target_files:
                        for chunk, meta in extract_file_chunks(f):
                            self.vector_store.fallback_chunks.append(chunk)
                            self.vector_store.fallback_metadata.append(meta)
                self._auto_initialized = True
                return existing_count

        all_chunks: List[str] = []
        all_metadatas: List[Dict[str, Any]] = []
        all_ids: List[str] = []

        counter = 0
        for f in target_files:
            extracted = extract_file_chunks(f)
            for chunk, meta in extracted:
                all_chunks.append(chunk)
                all_metadatas.append(meta)
                all_ids.append(f"doc_{meta.get('chunk_id', counter)}_{counter}")
                counter += 1

        self.vector_store.add_chunks(all_chunks, all_metadatas, all_ids)
        self._auto_initialized = True
        logger.info(
            f"RAGService Ready: {len(all_chunks)} semantic chunks indexed from {len(target_files)} resource files."
        )
        return len(all_chunks)

    def retrieve(self, query: str, top_k: int = 4) -> List[str]:
        """Retrieves top-k context passages relevant to the query."""
        if not self._auto_initialized and not self.vector_store.fallback_chunks:
            self.ingest_knowledge_base()

        return self.retriever.retrieve(query, top_k=top_k)

    def get_indexed_resources_summary(self) -> Dict[str, Any]:
        """Returns structured metadata of indexed files, chunk statistics, and Google Drive folder link."""
        target_files = self._discover_files()
        file_list = []
        for f in target_files:
            file_list.append({
                "name": f.name,
                "type": f.suffix.lstrip(".").upper(),
                "size_kb": round(f.stat().st_size / 1024, 1),
                "folder": f.parent.name,
            })

        return {
            "total_files": len(file_list),
            "total_chunks": len(self.vector_store.fallback_chunks) or self.vector_store.count(),
            "gdrive_resources_url": GDRIVE_RESOURCES_URL,
            "files": file_list,
        }


# Global singleton instance
rag_service = RAGService()
