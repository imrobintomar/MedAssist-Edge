# MedAssist-Edge — Edge AI & Performance

## 1. Why MedGemma-4b-it for Edge?

| Property | Value | Why it matters |
|---|---|---|
| Parameter count | 4 billion | Fits in 8–16 GB RAM |
| Architecture | Gemma 2 (decoder-only) | Efficient inference, well-optimised kernels |
| Training | Medical instruction tuning by Google | Higher clinical language fidelity |
| Tokeniser | SentencePiece | Low memory overhead |
| Format | Instruction-following (IT) | Works with structured prompts without fine-tuning |
| License | Health AI Developer Foundations ToS | Research/non-commercial use |

---

## 2. Quantization Strategy

### Why quantize?
- fp32 MedGemma-4b ≈ 16 GB RAM → impractical on most clinical workstations
- int8 quantization ≈ 4 GB RAM with <2% accuracy loss on QA benchmarks
- int4 quantization ≈ 2 GB RAM with ~5% accuracy loss — acceptable for non-critical decision support

### Recommended tiers

| Hardware | Quantization | Expected latency per agent |
|---|---|---|
| 32 GB RAM, modern CPU | int8 (BitsAndBytes) | 20–40 seconds |
| 16 GB RAM, laptop CPU | int8 | 40–90 seconds |
| 8 GB RAM, edge device | int4 | 60–120 seconds |
| GPU available (optional) | fp16 (auto) | 5–15 seconds |

### Implementation
```python
BitsAndBytesConfig(
    load_in_8bit=True,
    bnb_4bit_compute_dtype=torch.float32,
)
```
No GPU required. BitsAndBytes supports CPU inference natively.

---

## 3. Embedding Model Choice

`sentence-transformers/all-MiniLM-L6-v2`:
- 22 MB download
- 384-dimensional embeddings
- ~50ms per query on CPU
- MIT license, no data sharing

This model is separate from MedGemma and loaded independently for RAG. Its small size has negligible RAM impact.

---

## 4. FAISS Index Performance

| Index type | Accuracy | RAM | Speed |
|---|---|---|---|
| `IndexFlatIP` (used) | Exact | O(n) | Fast for <100K chunks |
| `IndexIVFFlat` | ~99% | Lower | Better for >100K chunks |

For typical guideline libraries (50–500 documents → 2,000–20,000 chunks), `IndexFlatIP` is optimal.

---

## 5. Offline Guarantees

At runtime, MedAssist-Edge makes **zero outbound network calls**:

```python
# Enforced at model load time:
local_files_only=True           # HuggingFace cache only
# OR set environment variable:
HF_HUB_OFFLINE=1
```

FAISS index is a local binary file. Embedding model is cached locally. No telemetry, no cloud API.

---

## 6. Full System RAM Budget

| Component | int8 | int4 |
|---|---|---|
| MedGemma-4b-it | ~4 GB | ~2 GB |
| Embedding model (MiniLM) | ~100 MB | ~100 MB |
| FAISS index (10K chunks) | ~15 MB | ~15 MB |
| Python + FastAPI | ~200 MB | ~200 MB |
| React frontend | negligible | negligible |
| **Total** | **~4.5 GB** | **~2.5 GB** |

---

## 7. Inference Latency Breakdown (CPU, int8)

For a typical clinical case:

| Agent | Notes | Est. time |
|---|---|---|
| SOAP Agent | 768 max new tokens | 20–40s |
| DDx Agent | 512 max new tokens | 15–35s |
| Guideline Agent | 512 max new tokens | 15–30s |
| Patient Agent | 512 max new tokens | 15–30s |
| RAG retrieval | FAISS search | <1s |
| **Total pipeline** | | **65–140s** |

This is expected and acceptable for clinical workflows where quality matters more than speed.

---

## 8. Deployment Scenarios

| Scenario | Configuration |
|---|---|
| Hospital workstation (16 GB) | int8, single-user, localhost |
| Shared clinic server (32 GB) | int8, multiple users via nginx reverse proxy |
| Laptop, offline clinic visit | int4, battery-powered |
| Air-gapped network | Full offline, weights pre-loaded |
