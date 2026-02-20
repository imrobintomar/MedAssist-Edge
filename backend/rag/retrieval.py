"""
Guideline Retriever
────────────────────
Semantic retrieval from the local FAISS vector store.

Thread-safety: read-only after load() — safe for concurrent FastAPI requests.
"""

from __future__ import annotations
import json
import logging
from pathlib import Path
from typing import List, Optional

import numpy as np

logger = logging.getLogger(__name__)


class GuidelineRetriever:
    """
    Load a pre-built FAISS index and serve top-K guideline chunks
    for a given clinical query.
    """

    def __init__(
        self,
        vector_store_dir: Path,
        embed_model_name: str,
        embed_cache_dir: Path,
        top_k: int = 4,
    ) -> None:
        self.vector_store_dir = Path(vector_store_dir)
        self.embed_model_name = embed_model_name
        self.embed_cache_dir = Path(embed_cache_dir)
        self.top_k = top_k
        self._index = None
        self._metadata: List[dict] = []
        self._embed_model = None
        self._loaded = False

    @property
    def doc_count(self) -> int:
        return len(self._metadata)

    def load(self) -> None:
        """Load FAISS index + metadata from disk. Call once at startup."""
        import faiss
        from sentence_transformers import SentenceTransformer

        index_path = self.vector_store_dir / "guidelines.faiss"
        meta_path = self.vector_store_dir / "metadata.json"

        if not index_path.exists():
            raise FileNotFoundError(
                f"FAISS index not found at {index_path}. "
                "Run: python scripts/setup_rag.py"
            )

        self._index = faiss.read_index(str(index_path))
        with open(meta_path, "r") as f:
            self._metadata = json.load(f)

        logger.info(
            "FAISS index loaded: %d vectors from %d unique sources",
            self._index.ntotal,
            len({m["source"] for m in self._metadata}),
        )

        local_only = self.embed_cache_dir.exists() and any(self.embed_cache_dir.iterdir())
        self._embed_model = SentenceTransformer(
            self.embed_model_name,
            cache_folder=str(self.embed_cache_dir),
            local_files_only=local_only,
        )
        self._loaded = True

    def retrieve(self, query: str) -> List[dict]:
        """
        Retrieve the top-K most relevant guideline chunks.

        Args:
            query: Clinical query string (e.g. chief complaint + DDx terms)

        Returns:
            List of {"source": str, "text": str, "score": float}
        """
        if not self._loaded:
            raise RuntimeError("Call load() before retrieve()")
        if not query.strip():
            return []

        # Embed query
        q_vec = self._embed_model.encode(
            [query],
            normalize_embeddings=True,
        ).astype(np.float32)

        # Search
        scores, indices = self._index.search(q_vec, self.top_k)

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0 or idx >= len(self._metadata):
                continue
            meta = self._metadata[idx]
            results.append({
                "source": meta["source"],
                "text": meta["text"],
                "score": float(score),
            })

        logger.debug(
            "Retrieved %d chunks for query '%s...' (top score=%.3f)",
            len(results),
            query[:50],
            results[0]["score"] if results else 0,
        )
        return results
