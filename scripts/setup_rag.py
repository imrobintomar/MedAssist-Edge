#!/usr/bin/env python3
"""
RAG Setup Script
────────────────
Run once to build the local FAISS guideline index.

Usage:
  python scripts/setup_rag.py

Prerequisites:
  - Place guideline files (.pdf, .txt, .md) in the guidelines/ directory
  - Install dependencies: pip install -r backend/requirements.txt
"""

import sys
import logging
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from config import (
    GUIDELINES_DIR,
    VECTOR_STORE_DIR,
    EMBED_MODEL_NAME,
    EMBED_CACHE_DIR,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
)
from rag.ingestion import ingest

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

def main():
    print("=" * 60)
    print("MedAssist-Edge — RAG Ingestion Pipeline")
    print("=" * 60)
    print(f"Guidelines directory : {GUIDELINES_DIR}")
    print(f"Vector store output  : {VECTOR_STORE_DIR}")
    print(f"Embedding model      : {EMBED_MODEL_NAME}")
    print(f"Chunk size           : {CHUNK_SIZE} chars")
    print(f"Chunk overlap        : {CHUNK_OVERLAP} chars")
    print()

    if not GUIDELINES_DIR.exists() or not any(GUIDELINES_DIR.iterdir()):
        print("ERROR: No guideline files found.")
        print(f"  → Place .pdf, .txt, or .md files in: {GUIDELINES_DIR}")
        print()
        print("Example sources:")
        print("  - WHO Essential Medicines List (PDF)")
        print("  - NICE Clinical Guidelines (PDF/TXT)")
        print("  - National TB Programme Guidelines (PDF)")
        sys.exit(1)

    n_chunks = ingest(
        guidelines_dir=GUIDELINES_DIR,
        vector_store_dir=VECTOR_STORE_DIR,
        embed_model_name=EMBED_MODEL_NAME,
        embed_cache_dir=EMBED_CACHE_DIR,
        chunk_size=CHUNK_SIZE,
        overlap=CHUNK_OVERLAP,
    )

    if n_chunks > 0:
        print(f"\n✓ Ingestion complete: {n_chunks} chunks indexed.")
        print(f"  Index saved to: {VECTOR_STORE_DIR}")
        print("\nYou can now start the API server:")
        print("  python backend/main.py")
    else:
        print("\n✗ Ingestion failed. Check logs above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
