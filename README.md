# MedAssist-Edge: Offline Agentic Clinical Co-Pilot

> **Clinical Decision Support Only** — Not a diagnostic or prescriptive tool.
> All inference runs locally on your machine. No data leaves the device.

Built for the [Google — MedGemma Challenge](https://www.kaggle.com/competitions/medgemma) on Kaggle.

---

## What It Does

MedAssist-Edge takes unstructured clinical notes (HPI, exam findings, labs, radiology) and runs them through a 4-agent pipeline powered by **MedGemma 1.5 4B IT** entirely offline:

1. **SOAP Agent** — Structures free-text notes into Subjective / Objective / Assessment / Plan
2. **DDx Agent** — Generates a ranked differential diagnosis with supporting and against evidence
3. **Guidelines Agent** — Retrieves relevant excerpts from local clinical guidelines (RAG) and synthesises cited recommendations
4. **Patient Agent** — Produces a plain-language explanation suitable for the patient

**Key properties:**
- 100% offline after initial model download — no API calls, no cloud inference
- GPU (bfloat16) or CPU (int8 via BitsAndBytes) — adapts automatically
- Local FAISS vector store for guideline retrieval
- JSONL audit log for clinical governance
- React + TypeScript frontend, FastAPI backend

---

## System Requirements

| | Minimum | Recommended |
|---|---|---|
| RAM | 8 GB | 16 GB |
| Disk | 12 GB | 20 GB |
| GPU | None (CPU fallback) | CUDA GPU (4 GB+ VRAM) |
| Python | 3.10+ | 3.11+ |
| Node.js | 18+ | 20+ |

---

## Quick Start

### 1. Install Python dependencies

```bash
python3 -m pip install torch transformers accelerate bitsandbytes \
    fastapi uvicorn pydantic sentence-transformers faiss-cpu pymupdf pillow \
    huggingface_hub
```

### 2. Download model weights (once — requires internet + HuggingFace account)

Accept the [Health AI Developer Foundations Terms](https://huggingface.co/google/medgemma-1.5-4b-it) on HuggingFace first, then:

```bash
export HF_TOKEN=hf_...          # your HuggingFace token
python3 scripts/download_weights.py
```

Downloads ~8.6 GB to `model/medgemma-1.5-4b-it/`.

### 3. Build the RAG index

```bash
python3 scripts/setup_rag.py
```

Add your own `.pdf` or `.txt` guideline files to `guidelines/` first. A sample respiratory guidelines file is included.

### 4. Start the backend

```bash
python3 backend/main.py
# → http://127.0.0.1:8000
```

Model loads in ~5–30 seconds depending on GPU/CPU.

### 5. Start the frontend

```bash
cd frontend
npm install
npm start
# → http://localhost:3000
```

---

## Architecture

```
Browser (React + TypeScript)
        │  POST /analyze
        ▼
FastAPI Backend (single worker, localhost only)
        │
        ├─► [1] SOAP Agent      ─┐
        ├─► [2] DDx Agent         │  MedGemma 1.5 4B IT
        ├─► [3] Guidelines Agent ─┤  (bfloat16 GPU / int8 CPU)
        └─► [4] Patient Agent   ─┘
                    │
                    └─► FAISS Vector Store (local guidelines)
                             sentence-transformers/all-MiniLM-L6-v2
```

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for full system design.

---

## Agent Pipeline

| # | Agent | Input | Output |
|---|---|---|---|
| 1 | SOAP Structuring | Raw clinical notes + demographics | Structured SOAP note |
| 2 | Differential Diagnosis | SOAP note | Ranked DDx list (≤5) with evidence |
| 3 | Guideline Retrieval (RAG) | DDx + assessment | Cited recommendations by category |
| 4 | Patient Explanation | SOAP + DDx | Plain-language summary (6th-grade) |

---

## Configuration

`backend/config.py`:

```python
QUANTIZATION = os.getenv("QUANTIZATION", "int8")  # "none" | "int8" | "int4"
FORCE_CPU    = True     # False = use GPU if available (bfloat16, much faster)
TOP_K_DOCS   = 4        # Guideline chunks retrieved per query
MAX_NEW_TOKENS = 768    # Per-agent generation limit
```

**Performance by mode:**

| Mode | RAM | Time per agent |
|---|---|---|
| GPU bfloat16 | ~8 GB VRAM | ~25–30 s |
| CPU int8 (bitsandbytes) | ~4 GB RAM | ~2–4 min |
| CPU float32 (fallback) | ~16 GB RAM | ~8–10 min |

---

## Adding Clinical Guidelines

Drop `.pdf` or `.txt` files into `guidelines/` and re-run:

```bash
python3 scripts/setup_rag.py
```

The index rebuilds in seconds. Supported formats: PDF, plain text, Markdown.

---

## Project Structure

```
MedGemma/
├── backend/
│   ├── agents/          # SOAP, DDx, Guidelines, Patient agents
│   ├── models/          # MedGemma 1.5 inference engine (singleton)
│   ├── rag/             # FAISS ingestion + retrieval
│   ├── schemas/         # Pydantic v2 request/response models
│   ├── middleware/       # JSONL audit logger
│   ├── config.py        # All settings in one place
│   └── main.py          # FastAPI app + lifespan startup
├── frontend/
│   └── src/
│       ├── components/  # OutputPanel, SOAP, DDx, Guidelines, Patient
│       ├── hooks/       # useAnalysis state machine
│       └── api/         # axios client (30-min timeout for CPU)
├── guidelines/          # Your clinical guideline files (PDF/TXT)
├── model/               # Downloaded MedGemma 1.5 weights (~8.6 GB)
├── vector_store/        # Built FAISS index
├── logs/                # JSONL audit trail
├── scripts/
│   ├── download_weights.py   # Shard-by-shard weight downloader
│   ├── setup_rag.py          # Build/rebuild FAISS index
│   └── download_model.py     # Full model + embedder download
├── notebooks/
│   └── medassist_edge_kaggle.ipynb   # Kaggle submission notebook
├── tests/               # Unit tests (mocked engine, RAG integration)
└── docs/                # Architecture, safety, edge AI, demo script
```

---

## Documentation

| Document | Contents |
|---|---|
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | System design, data flow, component list |
| [docs/SAFETY.md](docs/SAFETY.md) | Safety constraints, governance, limitations |
| [docs/EDGE_AI.md](docs/EDGE_AI.md) | Quantization, latency, RAM budget |
| [docs/DEMO_SCRIPT.md](docs/DEMO_SCRIPT.md) | 3-minute demo walkthrough with sample case |
| [docs/KAGGLE_WRITEUP.md](docs/KAGGLE_WRITEUP.md) | Competition write-up and design rationale |

---

## Safety Notice

This system is **clinical decision support only**. It:
- Does not confirm diagnoses
- Does not prescribe medications or recommend dosages
- Does not replace clinician judgement
- Has not undergone clinical validation or regulatory review
- Must be reviewed by a qualified clinician before any clinical action

**The clinician retains full clinical responsibility for all decisions.**

---

## Model

**google/medgemma-1.5-4b-it** — Multimodal medical language model by Google.
Model weights are subject to the [Health AI Developer Foundations Terms of Use](https://developers.google.com/health-ai-developer-foundations/terms).
Requires acceptance of terms on HuggingFace before download.

---

## License

Code: MIT License.
Model weights: [Google Health AI Developer Foundations Terms](https://developers.google.com/health-ai-developer-foundations/terms).
For research and competition use only.
