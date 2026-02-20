# MedAssist-Edge — Safety & Governance Design

## 1. Core Safety Philosophy

MedAssist-Edge is **clinical decision support**, not a diagnostic or prescriptive system. Every design decision flows from this distinction.

| Claim | General LLM chatbot | MedAssist-Edge |
|---|---|---|
| Confirms diagnoses | Possible | Explicitly prohibited in every prompt |
| Prescribes medication | Possible | Explicitly prohibited; dosages refused |
| Invents clinical facts | Possible | Each agent restricted to input data only |
| Cites sources | Rarely | Guideline agent cites source + section |
| Auditable | No | Every agent output logged with raw text |
| Consistent | No | Temperature=0.1, deterministic decoding |

---

## 2. Per-Agent Safety Constraints

### SOAP Agent
- **Prohibited**: Adding findings not present in input, making assessments, suggesting diagnoses
- **Required**: Faithfully re-organise only what was documented; say "Not documented" if absent
- **Refusal trigger**: Non-clinical or potentially harmful input → returns `{"error": "..."}` JSON

### DDx Agent
- **Prohibited**: Confirming any diagnosis, recommending treatments, inventing symptoms
- **Required**: Ranked possibilities with explicit supporting/against evidence; hedged language mandatory ("may suggest", "could be consistent with")
- **Cap**: Maximum 5 entries to prevent cognitive overwhelm

### Guideline Agent
- **Prohibited**: Using training-time knowledge for guideline content; recommending specific drug doses
- **Required**: Cite every recommendation to a local guideline source; only synthesise retrieved chunks
- **Graceful degradation**: If no relevant chunk retrieved, returns "No relevant guideline excerpt available" rather than hallucinating

### Patient Agent
- **Prohibited**: Confirming diagnoses, mentioning medications, alarming language
- **Required**: 6th-grade reading level; emphasise "speak to your doctor"; base only on prior agent outputs
- **Tone constraint**: Warm, empathetic, non-alarming

---

## 3. System-Level Safeguards

### Input validation
- Maximum 8,000 characters per field (prevents prompt injection via oversized inputs)
- Pydantic schema validation on all fields
- Age range enforcement (0–120)

### Output schema enforcement
- All agents return JSON with explicit schemas
- JSON parse failure falls back to a safe default rather than exposing raw model output
- Raw model output is preserved in `raw` field for audit log

### Persistent disclaimer
- Displayed in the UI on every page load (cannot be dismissed)
- Included in every API response
- Prepended to any copy-to-clipboard export

### Network isolation
- API server binds to `127.0.0.1` only (localhost)
- CORS restricted to `localhost:3000` only
- No outbound connections; model weights loaded from local disk
- `HF_HUB_OFFLINE` mode supported

---

## 4. Human-in-the-Loop Design

```
AI Output
    │
    ▼
┌─────────────────────────────────────────────────────┐
│  Clinician reviews each of the 4 output sections    │
│  • SOAP Note: edit/approve before filing            │
│  • DDx: validate against clinical judgement         │
│  • Guidelines: check against local protocols        │
│  • Patient summary: review before giving to patient │
└────────────────────────┬────────────────────────────┘
                         │  Clinician approves
                         ▼
                   Clinical action
```

The system intentionally has no "one-click action" button. Every output requires manual copy-and-paste or deliberate clinician review.

---

## 5. Auditability

Every `AnalysisResponse` includes:
- `model_id`: exact model version used
- `processing_time_seconds`: for performance monitoring
- `raw` field on every agent output: full unprocessed model text
- Structured parsed output: for downstream audit comparison

Logs written by FastAPI (stdout) include:
- Timestamp of each request
- Agent completion events
- Any parse failures or refusals

---

## 6. Why This Is Safer Than General LLM Chatbots

1. **Explicit prohibition at the prompt level** — each agent's system prompt contains hard prohibitions, not general suggestions
2. **Input restriction** — agents only reason over provided clinical data, not general web knowledge
3. **Source grounding** — guideline recommendations are traceable to specific documents
4. **Deterministic outputs** — temperature≈0, greedy decoding → same input produces same output
5. **No user persona** — system does not roleplay as a doctor; it is explicitly a co-pilot
6. **Auditability by design** — raw outputs preserved for review

---

## 7. Known Limitations

- MedGemma-4b-it is a 4B parameter model; it may make errors on complex or rare presentations
- Guideline RAG quality depends on the documents loaded by the institution
- The system has not undergone clinical validation or regulatory review
- Not intended for emergency or acute clinical decision-making without immediate clinician supervision
- Output accuracy degrades for highly specialised sub-specialties

**These limitations must be disclosed to all users before deployment.**
