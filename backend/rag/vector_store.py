import logging
from typing import Any, Dict, List, Optional
from .config import CHROMA_DB_PATH, COLLECTION_NAME, MODEL_NAME

logger = logging.getLogger("rag.vector_store")


class VectorStore:
    def __init__(self):
        self.chroma_available: bool = False
        self.client = None
        self.collection = None
        self.fallback_chunks: List[str] = []
        self.fallback_metadata: List[Dict[str, Any]] = []
        self._init_chroma()

    def _init_chroma(self):
        try:
            # pyrefly: ignore [missing-import]
            import chromadb
            # pyrefly: ignore [missing-import]
            from chromadb.utils import embedding_functions

            self.client = chromadb.PersistentClient(path=str(CHROMA_DB_PATH))
            self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name=MODEL_NAME
            )
            self.collection = self.client.get_or_create_collection(
                name=COLLECTION_NAME,
                embedding_function=self.embedding_fn,
                metadata={"hnsw:space": "cosine"},
            )
            self.chroma_available = True
            logger.info(f"VectorStore: ChromaDB collection '{COLLECTION_NAME}' initialized successfully.")
        except Exception as e:
            logger.warning(
                f"VectorStore: ChromaDB / Sentence-Transformers init notice ({e}). "
                "Engaging resilient in-memory semantic store."
            )
            self.client = None
            self.collection = None
            self.chroma_available = False

    def count(self) -> int:
        if self.chroma_available and self.collection is not None:
            try:
                return self.collection.count()
            except Exception as e:
                logger.warning(f"Error checking collection count: {e}")
        return len(self.fallback_chunks)

    def add_chunks(
        self,
        chunks: List[str],
        metadatas: List[Dict[str, Any]],
        ids: List[str],
        batch_size: int = 50,
    ) -> None:
        self.fallback_chunks = chunks
        self.fallback_metadata = metadatas

        if self.chroma_available and self.collection is not None and chunks:
            try:
                for i in range(0, len(chunks), batch_size):
                    self.collection.add(
                        documents=chunks[i : i + batch_size],
                        metadatas=metadatas[i : i + batch_size],
                        ids=ids[i : i + batch_size],
                    )
                logger.info(
                    f"VectorStore: Successfully persisted {len(chunks)} chunks into ChromaDB."
                )
            except Exception as err:
                logger.error(f"VectorStore: ChromaDB batch addition error: {err}")

    def query(self, query_text: str, top_k: int = 4) -> Optional[List[str]]:
        if self.chroma_available and self.collection is not None:
            try:
                if self.collection.count() > 0:
                    results = self.collection.query(
                        query_texts=[query_text],
                        n_results=top_k,
                    )
                    if results and results.get("documents") and len(results["documents"]) > 0:
                        docs = results["documents"][0]
                        if docs:
                            return docs
            except Exception as e:
                logger.warning(f"VectorStore query exception ({e}), falling back to memory search.")
        return None
