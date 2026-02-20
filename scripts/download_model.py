#!/usr/bin/env python3
"""
Model Download Script — MedGemma 1.5
──────────────────────────────────────
Pre-download MedGemma 1.5 (google/medgemma-1.5-4b-it) weights to the local
cache so the application runs fully offline thereafter.

PREREQUISITES:
  1. Accept the Health AI Developer Foundations terms of use on HuggingFace:
     https://huggingface.co/google/medgemma-1.5-4b-it
  2. Log in with your HuggingFace token:
     huggingface-cli login
     OR: export HUGGING_FACE_HUB_TOKEN=hf_...

Run ONCE while you have internet access:
  python scripts/download_model.py

After download, the system runs 100% offline.
"""

import sys
import argparse
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))
from config import MODEL_ID, MODEL_CACHE_DIR, EMBED_MODEL_NAME, EMBED_CACHE_DIR

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")


def download_medgemma(model_id: str, cache_dir: Path) -> None:
    """Download MedGemma 1.5 processor + model weights."""
    from transformers import AutoProcessor, AutoModelForImageTextToText
    import torch

    cache_dir.mkdir(parents=True, exist_ok=True)

    print(f"\nDownloading processor: {model_id}")
    AutoProcessor.from_pretrained(model_id, cache_dir=str(cache_dir))
    print("  Processor cached.")

    print(f"Downloading model weights: {model_id}")
    print("  MedGemma 1.5 4B ≈ 8 GB (fp32) / 4 GB (bf16). This may take several minutes …")

    # Download in bfloat16 to halve disk usage; runtime quantization applied separately
    AutoModelForImageTextToText.from_pretrained(
        model_id,
        cache_dir=str(cache_dir),
        torch_dtype=torch.bfloat16,
        low_cpu_mem_usage=True,
    )
    print(f"  Model cached at: {cache_dir}")


def download_embedder(model_name: str, cache_dir: Path) -> None:
    from sentence_transformers import SentenceTransformer
    cache_dir.mkdir(parents=True, exist_ok=True)
    print(f"\nDownloading embedding model: {model_name}")
    SentenceTransformer(model_name, cache_folder=str(cache_dir))
    print(f"  Cached at: {cache_dir}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Download MedGemma 1.5 for offline use")
    parser.add_argument("--model", default=MODEL_ID, help=f"Model ID (default: {MODEL_ID})")
    parser.add_argument("--skip-embed", action="store_true", help="Skip embedding model")
    args = parser.parse_args()

    print("=" * 60)
    print("MedAssist-Edge — Model Download")
    print(f"Model  : {args.model}")
    print(f"Cache  : {MODEL_CACHE_DIR}")
    print("=" * 60)
    print("NOTE: Internet access required for this step only.")
    print("After download, disconnect and the system works fully offline.\n")

    download_medgemma(args.model, MODEL_CACHE_DIR)

    if not args.skip_embed:
        download_embedder(EMBED_MODEL_NAME, EMBED_CACHE_DIR)

    print("\n" + "=" * 60)
    print("✓ All models downloaded. System is ready for offline use.")
    print("\nNext steps:")
    print("  1. Add guidelines to:  guidelines/")
    print("  2. Build RAG index:    python scripts/setup_rag.py")
    print("  3. Start backend:      python backend/main.py")
    print("  4. Start frontend:     cd frontend && npm install && npm start")
    print("=" * 60)


if __name__ == "__main__":
    main()
