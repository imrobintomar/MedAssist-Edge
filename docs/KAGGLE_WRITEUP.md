# MedAssist-Edge: Kaggle MedGemma Competition Write-Up

---

### Project name

**MedAssist-Edge — Offline Agentic Clinical Co-Pilot**

---

### Your team

| Name | Speciality | Role |
|------|-----------|------|
| Prabudh | Clinical AI / Backend Engineering | System architecture, agent pipeline, RAG, safety design, full-stack implementation |

---

### Problem statement

**The problem:** Clinicians in low-resource, privacy-restricted, or air-gapped environments have no access to AI-assisted clinical decision support. Cloud-based tools are disqualified for sensitive patient data. General-purpose LLMs hallucinate clinical facts and cite non-existent guidelines. And physicians globally spend an estimated **2 hours on documentation for every 1 hour of direct patient care** — a burden that directly degrades care quality and clinician wellbeing.

**Why it matters:** In low-income countries and rural hospitals, a single physician may carry a caseload of hundreds of patients per week with no specialist support. In conflict zones, humanitarian settings, and underserved clinics worldwide, there is no reliable internet — and therefore no access to current clinical AI tools. The patients who need AI-assisted care the most are the ones locked out of it.

**The impact:** Even a tool that helps a clinician structure a SOAP note faster, surface a rare differential, or retrieve the local guideline recommendation for a condition they rarely see can directly improve clinical decision quality. Deployed offline, it does so without creating a data privacy risk, a regulatory burden, or a connectivity dependency.

---

### Overall solution

MedAssist-Edge is a **fully offline, four-agent clinical decision support system** powered by **MedGemma 1.5 4B IT** — running on a standard workstation CPU with no internet dependency after first download.

**Why MedGemma?** General-purpose LLMs are unreliable for clinical use: they confabulate drug names, invent guideline citations, and produce outputs that look correct to non-clinicians. MedGemma is trained on curated medical literature, clinical notes, and biomedical data — making it the right base model for a system where a hallucinated differential or a fabricated guideline could harm a patient.

**The four-agent pipeline mirrors the actual clinical workflow:**

| Agent | What it does | Why it's a separate agent |
|-------|-------------|--------------------------|
| SOAP Structuring | Converts free-text notes → structured Subjective / Objective / Assessment / Plan | Structured output = auditable; clinician can verify note before downstream agents see it |
| Differential Diagnosis | Ranked DDx list with supporting/against evidence for each condition | Bounded scope: cannot prescribe, cannot confirm — only reasons |
| Guideline Retrieval (RAG) | Retrieves relevant excerpts from *local* clinical guidelines; synthesises cited recommendations | Grounded in institution's own documents — not the model's training memory |
| Patient Explanation | Plain-language summary suitable for patient communication | Different register, different safety constraints from clinical agents |

**Agentic decomposition is a safety architecture, not a style choice.** Each agent has a bounded role, a separate system prompt with explicit prohibitions, and produces structured JSON output that is parsed and validated before passing downstream. An error in the guideline agent doesn't corrupt the DDx. A refusal by the patient agent doesn't drop the SOAP note. Partial results are still clinically useful.

---

### Technical details

**Inference stack:**
- Model: `google/medgemma-1.5-4b-it` — single instance loaded once at startup
- Quantization: BitsAndBytes int8 (~4 GB RAM); auto-detects GPU for bfloat16 if available
- Decoding: Temperature 0.1, greedy — deterministic output enables reproducibility and audit
- Backend: FastAPI (Python), single worker, bound to `127.0.0.1` only
- Frontend: React + TypeScript + Tailwind CSS — tab-based output, copy-to-clipboard on all outputs

**RAG pipeline:**
- Embedding: `all-MiniLM-L6-v2` (22 MB, CPU, offline-safe)
- Vector store: FAISS `IndexFlatIP` — exact cosine similarity
- Chunking: 512-character windows, 64-character overlap
- Retrieval: Top-4 chunks per query, injected verbatim into prompt
- Institutions add their own PDF/TXT guidelines; index rebuilds in seconds

**Performance:**

| Mode | RAM | Pipeline latency |
|------|-----|-----------------|
| CPU int8 | ~4.5 GB | ~90 s |
| GPU bfloat16 | ~8 GB VRAM | ~25 s |

**Safety by design:**
1. Prompt-level hard prohibitions on every agent (no diagnoses confirmed, no dosages, no invented findings)
2. Guideline agent explicitly forbidden from using training-time knowledge — only retrieved chunks
3. No execute button; all outputs require manual copy before any clinical action
4. JSONL audit log for governance and reproducibility
5. Network isolation: no outbound connections, no telemetry, CORS restricted to localhost
6. Persistent footer disclaimer on every screen

**Feasibility:** The system runs on a standard clinical workstation. No GPU, no cloud account, no data leaving the machine. Institutions can extend it by dropping PDF guidelines into a folder and running a single script. The architecture is modular — additional agents (radiology interpretation, drug interaction checking) slot in without changing the pipeline core.

---

*Clinical Decision Support Only — Not a diagnostic or prescriptive tool. All inference runs locally. No patient data leaves the device.*
*Submitted to the Google MedGemma Kaggle Competition. For research and competition use only.*
