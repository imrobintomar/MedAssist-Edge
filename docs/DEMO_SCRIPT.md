# MedAssist-Edge — 3-Minute Demo Script

## Setup (before recording)
- Backend running: `python backend/main.py`
- Frontend running: `npm start` in `frontend/`
- Browser at `http://localhost:3000`
- Terminal visible in split-screen (to show no network calls)
- Use the sample case below

---

## Sample Clinical Case

```
Clinical Notes:
45-year-old female presenting with a 3-week history of progressive
dyspnea on exertion, dry cough, and fatigue. No fever, no chest pain,
no haemoptysis. Non-smoker. No recent travel. Works in a textile factory.
Physical exam: RR 22/min, SpO2 91% on room air, bilateral fine
inspiratory crackles at lung bases. No clubbing, no peripheral oedema.

Lab Results:
CBC: WBC 8.2, Hgb 11.4 g/dL, Plt 310
LDH 280 U/L (ref <225), ESR 68 mm/hr, CRP 2.1 mg/dL
Spirometry: FVC 68% predicted, FEV1/FVC 0.81 (restrictive pattern)

Radiology Text:
HRCT Chest: Bilateral ground-glass opacities predominating in the lower
lobes with subtle honeycombing pattern and traction bronchiectasis.
No pleural effusion. No mediastinal lymphadenopathy.
```

---

## Script

### 0:00 — Introduction (20 seconds)

> "This is MedAssist-Edge — a fully offline, agentic clinical decision support system running locally on a laptop. Every line of inference happens on this CPU. Nothing leaves this machine."

*[Point to the "Offline" badge and disclaimer banner]*

> "Notice the persistent disclaimer. This is clinical decision support — not diagnosis. The clinician is always in the loop."

---

### 0:20 — Input (30 seconds)

> "I'll paste a realistic case — a 45-year-old woman with progressive dyspnea, restrictive spirometry, and HRCT findings. Age 45, female."

*[Fill in the fields, paste the case data]*

> "Three separate input panels: clinical notes, lab results, radiology text. The system accepts exactly what a clinician already has — no reformatting required."

*[Click Analyse]*

---

### 0:50 — Loading / Agentic Pipeline (40 seconds)

> "The system runs four specialised agents in sequence — each with a different role."

*[Point to the loading cards]*

> "First: the SOAP Agent reorganises the raw notes into structured format. Second: the Differential Diagnosis Agent reasons over those findings. Third: the Guideline Agent searches our local FAISS index of clinical guidelines — no internet. Fourth: the Patient Explanation Agent translates everything into plain language."

> "Each agent uses the same MedGemma model but a completely different prompt — different role, different output schema, different safety constraints."

*[Terminal split: show no network calls, just CPU activity]*

---

### 1:30 — SOAP Output (25 seconds)

*[Result appears — click SOAP tab]*

> "The SOAP Note tab. The model has reorganised the free-text into Subjective, Objective, Assessment, and Plan Suggestions. Notice 'suggestions only' — no orders, no prescriptions."

*[Click copy button]*

> "One click to copy the structured note for the EMR."

---

### 1:55 — Differential Diagnosis (25 seconds)

*[Click DDx tab]*

> "The Differential Diagnosis tab. Five ranked conditions with likelihood ratings. For each one — supporting features and features arguing against. IPF is ranked first given the HRCT honeycombing and restrictive pattern."

> "Critically, nothing is confirmed. Everything is a 'possibility to consider'. The reasoning summary explains the clinical logic."

---

### 2:20 — Guidelines (20 seconds)

*[Click Guidelines tab]*

> "The Guideline Recommendations tab. These are retrieved from our local PDF index of clinical guidelines — in this case, the ATS/ERS IPF guidelines. Each recommendation cites its source. Direct, Inferred, or Low-evidence confidence labels."

> "The model synthesised, not invented. Every recommendation traces to a real document chunk."

---

### 2:40 — Patient Summary (15 seconds)

*[Click Patient Summary tab]*

> "Finally — a plain-language summary for the patient. Sixth-grade reading level. No jargon, no alarming language, and a clear 'speak to your doctor about next steps' message."

---

### 2:55 — Closing (5 seconds)

> "Fully offline. Four agents. One model. Zero cloud dependency. MedAssist-Edge."

---

## Key Demo Talking Points

1. **Offline evidence**: Show `ping google.com` failing while the system still works
2. **Agentic design**: Each agent has a named, auditable role — not a black box
3. **Safety first**: Point to every disclaimer, hedge, and refusal built into the system
4. **RAG citation**: Show that guideline text comes from a local file, not model memory
5. **Edge feasibility**: Show CPU usage, no GPU, reasonable latency
