"""
Guideline Ingestion Pipeline
────────────────────────────
Converts local guideline documents (PDF, TXT, MD) into a FAISS
vector index for offline semantic retrieval.

Usage:
  python -m rag.ingestion           # processes guidelines/ directory
  python scripts/setup_rag.py       # convenience wrapper

Design decisions:
  - Fixed-size chunking with overlap preserves context at boundaries
  - Source metadata (filename + chunk index) enables citations
  - Embedding model (all-MiniLM-L6-v2) is tiny (~22 MB), CPU-fast
  - FAISS flat index = exact nearest-neighbour, no approximation error
"""

from __future__ import annotations
import json
import logging
import sys
from pathlib import Path
from typing import List

logger = logging.getLogger(__name__)

# Optional PDF extraction
try:
    import fitz  # PyMuPDF
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    logger.warning("PyMuPDF not installed — PDF ingestion disabled. Install: pip install pymupdf")


def extract_text_from_pdf(path: Path) -> str:
    if not PDF_AVAILABLE:
        return ""
    doc = fitz.open(str(path))
    pages = [page.get_text() for page in doc]
    doc.close()
    return "\n".join(pages)


def extract_text_from_txt(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def load_documents(guidelines_dir: Path) -> List[dict]:
    """
    Load all supported documents from the guidelines directory.

    Returns:
        List of {"source": str, "text": str} dicts.
    """
    docs = []
    supported = {".pdf", ".txt", ".md"}
    files = [f for f in guidelines_dir.rglob("*") if f.suffix.lower() in supported]
    logger.info("Found %d guideline files in %s", len(files), guidelines_dir)

    for f in files:
        try:
            if f.suffix.lower() == ".pdf":
                text = extract_text_from_pdf(f)
            else:
                text = extract_text_from_txt(f)
            if text.strip():
                docs.append({"source": f.name, "text": text})
                logger.debug("Loaded: %s (%d chars)", f.name, len(text))
        except Exception as exc:
            logger.warning("Failed to load %s: %s", f.name, exc)

    logger.info("Loaded %d documents successfully.", len(docs))
    return docs


def chunk_document(doc: dict, chunk_size: int = 512, overlap: int = 64) -> List[dict]:
    """
    Split a document into overlapping fixed-size character chunks.

    Args:
        doc: {"source": str, "text": str}
        chunk_size: Characters per chunk
        overlap: Character overlap between consecutive chunks

    Returns:
        List of {"source": str, "chunk_id": int, "text": str}
    """
    text = doc["text"]
    source = doc["source"]
    chunks = []
    start = 0
    chunk_id = 0

    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunk_text = text[start:end].strip()
        if chunk_text:
            chunks.append({
                "source": source,
                "chunk_id": chunk_id,
                "text": chunk_text,
            })
            chunk_id += 1
        start += chunk_size - overlap

    return chunks


def ingest(
    guidelines_dir: Path,
    vector_store_dir: Path,
    embed_model_name: str,
    embed_cache_dir: Path,
    chunk_size: int = 512,
    overlap: int = 64,
) -> int:
    """
    Full ingestion pipeline: load → chunk → embed → save FAISS index.

    Returns:
        Number of chunks indexed.
    """
    import numpy as np
    import faiss
    from sentence_transformers import SentenceTransformer

    vector_store_dir.mkdir(parents=True, exist_ok=True)
    embed_cache_dir.mkdir(parents=True, exist_ok=True)

    # 1. Load documents
    docs = load_documents(guidelines_dir)
    if not docs:
        logger.error("No documents found in %s. Aborting.", guidelines_dir)
        return 0

    # 2. Chunk
    all_chunks: List[dict] = []
    for doc in docs:
        all_chunks.extend(chunk_document(doc, chunk_size, overlap))
    logger.info("Total chunks: %d", len(all_chunks))

    # 3. Embed
    logger.info("Loading embedding model: %s …", embed_model_name)
    model = SentenceTransformer(
        embed_model_name,
        cache_folder=str(embed_cache_dir),
    )
    texts = [c["text"] for c in all_chunks]
    logger.info("Embedding %d chunks …", len(texts))
    embeddings = model.encode(
        texts,
        batch_size=32,
        show_progress_bar=True,
        normalize_embeddings=True,   # cosine similarity via dot product
    )
    embeddings = np.array(embeddings, dtype=np.float32)

    # 4. Build FAISS index
    dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)   # Inner product = cosine (normalised vectors)
    index.add(embeddings)
    logger.info("FAISS index built: %d vectors, dim=%d", index.ntotal, dim)

    # 5. Save
    faiss.write_index(index, str(vector_store_dir / "guidelines.faiss"))
    with open(vector_store_dir / "metadata.json", "w") as f:
        json.dump(all_chunks, f, ensure_ascii=False)
    logger.info("Saved index to %s", vector_store_dir)

    return len(all_chunks)


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from config import GUIDELINES_DIR, VECTOR_STORE_DIR, EMBED_MODEL_NAME, EMBED_CACHE_DIR
    logging.basicConfig(level=logging.INFO)
    n = ingest(GUIDELINES_DIR, VECTOR_STORE_DIR, EMBED_MODEL_NAME, EMBED_CACHE_DIR)
    print(f"Ingestion complete: {n} chunks indexed.")
