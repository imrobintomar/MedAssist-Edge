"""
MedAssist-Edge Configuration
All paths, model settings, and runtime parameters.
Fully offline — no external URLs or API keys.
"""

from pathlib import Path
import os

# ── Project root ─────────────────────────────────────────────────────────────
ROOT_DIR = Path(__file__).resolve().parent.parent

# ── Model settings ────────────────────────────────────────────────────────────
# If you used:  hf download ... --local-dir /path/to/model_cache/medgemma-1.5-4b-it
#   → set MODEL_ID to that local path string, e.g. str(MODEL_CACHE_DIR)
# If you used:  huggingface-cli login + snapshot_download (HF cache structure)
#   → keep MODEL_ID as the repo ID and set MODEL_CACHE_DIR to your cache root
MODEL_ID = str(ROOT_DIR / "model" / "medgemma-1.5-4b-it")  # local --local-dir path
MODEL_CACHE_DIR = ROOT_DIR / "model"  # parent dir

# Quantization: "none" | "int8" | "int4"
# int8  → ~4 GB RAM (from ~8 GB bf16), slight quality loss, 2× faster on CPU
# int4  → ~2 GB RAM, moderate quality loss, 3–4× faster
# NOTE: MedGemma 1.5 uses bfloat16 natively; quantization via BitsAndBytes
QUANTIZATION = os.getenv("QUANTIZATION", "int8")
FORCE_CPU = False  # always use CPU; set False to allow GPU if available

# Generation defaults — greedy decoding per official Jan 23 2026 update
# (model card: "Updated generation config to use greedy decoding by default")
GENERATION_CONFIG = {
    "max_new_tokens": 2048,      # Guidelines with 4 categories can exceed 1536 tokens
    "do_sample": False,          # greedy decoding — deterministic, safer
    "repetition_penalty": 1.15,
}

# ── RAG settings ──────────────────────────────────────────────────────────────
GUIDELINES_DIR = ROOT_DIR / "guidelines"        # raw PDFs / .txt files
VECTOR_STORE_DIR = ROOT_DIR / "vector_store"    # FAISS index lives here
EMBED_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"  # tiny, CPU-fast
EMBED_CACHE_DIR = ROOT_DIR / "embed_cache"

CHUNK_SIZE = 512       # characters per chunk
CHUNK_OVERLAP = 64     # overlap for context continuity
TOP_K_DOCS = 4         # chunks retrieved per query

# ── API server ────────────────────────────────────────────────────────────────
API_HOST = "127.0.0.1"   # localhost only — no external exposure
API_PORT = 8000
API_WORKERS = 1          # single worker shares the loaded model

# ── Safety ────────────────────────────────────────────────────────────────────
MAX_INPUT_CHARS = 8000   # prevent prompt injection via oversized inputs
DISCLAIMER = (
    "⚠️  CLINICAL DECISION SUPPORT ONLY — This output is AI-generated and "
    "must be reviewed by a qualified clinician. It does not constitute a "
    "diagnosis, prescription, or medical order. The clinician retains full "
    "clinical responsibility."
)
