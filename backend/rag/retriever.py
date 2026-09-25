import re
from typing import List, Tuple
from .vector_store import VectorStore


class HybridRetriever:
    def __init__(self, vector_store: VectorStore):
        self.vector_store = vector_store

    def retrieve(self, query: str, top_k: int = 4) -> List[str]:
        """Hybrid search combining vector similarity and agronomic keyword weighting."""
        if not query or not query.strip():
            return []

        # 1. Primary vector search via ChromaDB
        vector_results = self.vector_store.query(query, top_k=top_k)
        if vector_results:
            return vector_results

        # 2. Resilient scoring fallback across in-memory chunks
        chunks = self.vector_store.fallback_chunks
        if not chunks:
            return []

        tokens = [t.lower() for t in re.findall(r"\w+", query) if len(t) > 2]
        if not tokens:
            tokens = [query.lower().strip()]

        scored_chunks: List[Tuple[float, str]] = []
        query_lower = query.lower()

        for chunk in chunks:
            chunk_lower = chunk.lower()
            score = 0.0

            # Exact phrase match bonus
            if query_lower in chunk_lower:
                score += 10.0

            # Token matches with frequency weighting
            for token in tokens:
                if token in chunk_lower:
                    freq = chunk_lower.count(token)
                    score += 1.0 + min(freq * 0.5, 3.0)

            # High priority agronomic domain boosts
            if any("table" in token for token in tokens):
                if "[agronomic table" in chunk_lower or "kc mid" in chunk_lower:
                    score += 5.0
            if "water balance" in chunk_lower or "fao-56" in chunk_lower:
                if any(t in tokens for t in ["water", "irrigation", "moisture"]):
                    score += 4.0
            if any(t in tokens for t in ["yellow", "yellowing", "leaf", "leaves", "fertilizer", "urea", "nitrogen"]):
                if "deficiency" in chunk_lower or "nitrogen" in chunk_lower or "remedy" in chunk_lower:
                    score += 4.0

            if score > 0:
                scored_chunks.append((score, chunk))

        scored_chunks.sort(key=lambda x: x[0], reverse=True)
        return [chunk for _, chunk in scored_chunks[:top_k]]
