# MedAssist-Edge — System Architecture

## 1. Why Agentic Decomposition?

A monolithic "chat with your notes" approach has fundamental problems in clinical AI:

| Problem | Single LLM chatbot | Agentic decomposition |
|---|---|---|
| Auditability | Black-box answer | Each agent has a named, logged role |
| Safety | No boundaries | Each agent has explicit refusal rules |
| Specialisation | Generic reasoning | Each prompt is domain-optimised |
| Debuggability | Impossible to isolate errors | Failure pinpoints to one agent |
| Workflow fit | Conversation-shaped | Mirrors clinical documentation workflow |

Agentic systems are safer because each agent operates within a narrowly defined responsibility boundary. A SOAP agent cannot accidentally diagnose; a DDx agent cannot accidentally prescribe.

---

## 2. System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    CLINICIAN WORKSTATION                    │
│                                                             │
│  ┌──────────────┐           ┌──────────────────────────┐   │
│  │  React UI    │◄─────────►│  FastAPI Backend         │   │
│  │  (localhost) │  HTTP/    │  (localhost:8000)        │   │
│  │              │  JSON     │                          │   │
│  └──────────────┘           │  ┌────────────────────┐ │   │
│                             │  │ Inference Engine    │ │   │
│                             │  │ MedGemma-4b-it      │ │   │
│                             │  │ (CPU, int8 quant)   │ │   │
│                             │  └────────┬───────────┘ │   │
│                             │           │ shared       │   │
│                             │  ┌────────▼───────────┐ │   │
│                             │  │  Agent Router       │ │   │
│                             │  └────────┬───────────┘ │   │
│                             │           │              │   │
│                    ┌────────▼──┬────────▼──┬──────────▼──┐ │
│                    │SOAP Agent │ DDx Agent │Guide Agent  │ │
│                    │           │           │(RAG)        │ │
│                    └───────────┴────────┬──┴─────────────┘ │
│                                         │                   │
│                             │  ┌────────▼───────────┐ │   │
│                             │  │ Patient Agent       │ │   │
│                             │  └────────────────────┘ │   │
│                             │                          │   │
│                             │  ┌────────────────────┐ │   │
│                             │  │ FAISS Vector Store  │ │   │
│                             │  │ (local guidelines)  │ │   │
│                             │  └────────────────────┘ │   │
│                             └──────────────────────────┘   │
│                                                             │
│  ━━━━━━━━━━━━━━━━  NO NETWORK BOUNDARY  ━━━━━━━━━━━━━━━━   │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Data Flow

```
ClinicalInput (notes + labs + radiology)
        │
        ▼
[1] SOAP Agent ──────────────────► SOAPNote {S, O, A, P}
        │
        ▼
[2] DDx Agent (receives SOAPNote) ► DifferentialDiagnosis {5 entries}
        │
        ▼
[3] Guideline Agent ──────────────► GuidelineRecommendation
        │  ↑ FAISS retrieval
        │  └── query: assessment + DDx terms
        ▼
[4] Patient Agent (receives SOAP + DDx) ► PatientExplanation
        │
        ▼
AnalysisResponse (all 4 outputs + metadata + disclaimer)
```

---

## 4. Component Inventory

### Backend
| File | Purpose |
|---|---|
| `backend/main.py` | FastAPI application, startup, routing |
| `backend/config.py` | All configuration constants |
| `backend/models/inference.py` | MedGemma singleton loader, generate() |
| `backend/agents/soap_agent.py` | SOAP structuring prompt + parser |
| `backend/agents/ddx_agent.py` | Differential diagnosis prompt + parser |
| `backend/agents/guideline_agent.py` | RAG-injected guideline synthesis |
| `backend/agents/patient_agent.py` | Plain-language patient explanation |
| `backend/rag/ingestion.py` | PDF/TXT → FAISS index pipeline |
| `backend/rag/retrieval.py` | Semantic search over guideline index |
| `backend/schemas/models.py` | Pydantic request/response schemas |

### Frontend
| File | Purpose |
|---|---|
| `src/App.tsx` | Root layout, state orchestration |
| `src/hooks/useAnalysis.ts` | API call state machine |
| `src/api/client.ts` | Axios wrapper for backend |
| `src/components/InputPanel.tsx` | Clinical notes form |
| `src/components/OutputPanel.tsx` | Tabbed output container |
| `src/components/SOAPNote.tsx` | SOAP display |
| `src/components/DifferentialDx.tsx` | DDx ranked cards |
| `src/components/GuidelineRecs.tsx` | Guideline recommendation cards |
| `src/components/PatientExplanation.tsx` | Patient summary display |
| `src/components/DisclaimerBanner.tsx` | Persistent safety banner |

---

## 5. Model Sharing Strategy

One `InferenceEngine` instance is created at FastAPI startup and shared across all four agents via FastAPI's dependency injection system. This:

- Avoids loading 4 copies of the model (which would require ~8–32 GB RAM)
- Ensures deterministic sequential execution
- Simplifies memory management
- Is safe because agents execute sequentially (no concurrency)
