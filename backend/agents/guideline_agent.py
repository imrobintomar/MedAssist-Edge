"""
Guideline Retrieval & Recommendation Agent (RAG)
─────────────────────────────────────────────────
Role: Retrieve relevant clinical guideline passages from the local FAISS
      vector store and synthesise citation-backed recommendations.

MedGemma 1.5 API: messages dict format via processor.apply_chat_template().

RAG design:
  - Query = top DDx conditions + chief complaint
  - Retrieved chunks injected verbatim into the prompt
  - Model synthesises, never invents, guideline content
  - Every recommendation attributed to its source chunk
"""

from __future__ import annotations
import json
import logging
import re
from typing import TYPE_CHECKING, List, Optional

if TYPE_CHECKING:
    from schemas import ClinicalInput, SOAPNote, DifferentialDiagnosis, GuidelineRecommendation

logger = logging.getLogger(__name__)

_SYSTEM = (
    "You are a clinical guideline synthesis assistant.\n\n"
    "You are given:\n"
    "1. A patient's structured clinical summary (SOAP + differential diagnosis).\n"
    "2. Excerpts retrieved from authoritative clinical guidelines.\n\n"
    "TASK: Extract every actionable recommendation from the provided guideline excerpts "
    "that is relevant to this patient. Organise them into JSON.\n\n"
    "RULES:\n"
    "1. Extract recommendations from the provided excerpts only. Do not invent guideline content.\n"
    "2. Attribute each recommendation to its source file and section.\n"
    "3. Assign each recommendation a category: choose one of "
    "Workup, Management, Monitoring, or Follow-up.\n"
    "4. Use hedged language: 'Guidelines suggest…', 'According to [source]…'.\n"
    "5. Do NOT recommend specific drug doses. Do NOT issue clinical orders.\n"
    "6. If the excerpts contain ANY relevant clinical content, produce recommendations. "
    "Only return empty recommendations if the excerpts are completely unrelated to the case.\n"
    "7. Output ONLY valid JSON — no prose, no markdown outside the JSON block.\n\n"
    "OUTPUT SCHEMA (populate recommendations array with all relevant items found):\n"
    "{\"recommendations\": ["
    "{\"category\": \"Workup\", \"recommendation\": \"...\", \"source\": \"...\", \"confidence\": \"Direct\"}, "
    "{\"category\": \"Management\", \"recommendation\": \"...\", \"source\": \"...\", \"confidence\": \"Direct\"}, "
    "{\"category\": \"Monitoring\", \"recommendation\": \"...\", \"source\": \"...\", \"confidence\": \"Direct\"}"
    "], "
    "\"retrieved_sources\": [\"source1\", \"source2\"]}"
)


def _format_chunks(chunks: List[dict]) -> str:
    if not chunks:
        return "No guideline excerpts retrieved."
    import re as _re
    parts = []
    for i, chunk in enumerate(chunks, 1):
        text = chunk.get("text", "")
        # Remove section separator lines (===, ---, >>>)
        text = _re.sub(r"^[=\-]{4,}\s*$", "", text, flags=_re.MULTILINE)
        # Collapse multiple blank lines
        text = _re.sub(r"\n{3,}", "\n\n", text).strip()
        parts.append(f"[{i}] SOURCE: {chunk.get('source', 'Unknown')}\n{text}")
    return "\n\n---\n\n".join(parts)


def _rag_query(soap: "SOAPNote", ddx: "DifferentialDiagnosis") -> str:
    conditions = " ".join(d.condition for d in ddx.diagnoses[:3])
    # Bias toward management/treatment/monitoring chunks not just diagnostic definitions
    return (
        f"{conditions} management treatment monitoring guidelines recommend "
        f"anti-fibrotic immunosuppression workup follow-up"
    )


def build_messages(
    soap: "SOAPNote",
    ddx: "DifferentialDiagnosis",
    chunks: List[dict],
) -> List[dict]:
    ddx_list = ", ".join(
        f"{d.condition} ({d.likelihood})" for d in ddx.diagnoses[:3]
    ) or "Not available"

    user_text = (
        f"CLINICAL SUMMARY:\n"
        f"Assessment: {soap.assessment}\n"
        f"Top DDx: {ddx_list}\n\n"
        f"RETRIEVED GUIDELINE EXCERPTS:\n"
        f"{_format_chunks(chunks)}\n\n"
        "Synthesise recommendations based ONLY on the excerpts above."
    )
    return [
        {"role": "system", "content": [{"type": "text", "text": _SYSTEM}]},
        {"role": "user",   "content": [{"type": "text", "text": user_text}]},
    ]


def _extract_json_object(text: str) -> str | None:
    """Extract first complete JSON object using balanced-brace matching."""
    start = text.find("{")
    if start == -1:
        return None
    depth = 0
    in_string = False
    escape_next = False
    for i, ch in enumerate(text[start:], start):
        if escape_next:
            escape_next = False
            continue
        if ch == "\\" and in_string:
            escape_next = True
            continue
        if ch == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[start : i + 1]
    return None


def _strip_thinking_blocks(text: str) -> str:
    """Remove MedGemma <unusedXX>thought...</unusedXX> thinking blocks."""
    text = re.sub(r"<unused\d+>thought\s*", "", text)
    text = re.sub(r"<unused\d+>", "", text)
    return text


def parse_response(raw: str) -> dict:
    import pathlib, time
    _dump = pathlib.Path("/tmp/guideline_raw_output.txt")
    _dump.write_text(f"[{time.strftime('%H:%M:%S')}]\n{raw}\n")

    text = _strip_thinking_blocks(raw)
    text = re.sub(r"```(?:json)?\s*", "", text).strip().rstrip("`").strip()
    logger.debug("Guideline raw output: %s", raw)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    candidate = _extract_json_object(text)
    if candidate:
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass
    logger.warning("Guideline parse failed. Raw output:\n%s", raw)
    return {"recommendations": [], "retrieved_sources": []}


def run(
    soap: "SOAPNote",
    ddx: "DifferentialDiagnosis",
    data: "ClinicalInput",
    retriever,
    engine,
) -> "GuidelineRecommendation":
    from schemas import GuidelineRecommendation, GuidelineEntry

    query = _rag_query(soap, ddx)
    chunks: List[dict] = retriever.retrieve(query) if retriever else []
    sources = list({c.get("source", "") for c in chunks if c.get("source")})

    # Debug: dump retrieved chunks to file
    import pathlib, time as _time
    _cdump = pathlib.Path("/tmp/guideline_chunks.txt")
    _cdump.write_text(
        f"[{_time.strftime('%H:%M:%S')}] Query: {query}\n\n"
        + "\n\n---\n\n".join(
            f"Score={c.get('score', 0):.3f} Source={c.get('source')}\n{c.get('text', '')}"
            for c in chunks
        )
    )

    messages = build_messages(soap, ddx, chunks)
    raw = engine.generate(messages)
    parsed = parse_response(raw)

    entries: List[GuidelineEntry] = [
        GuidelineEntry(
            category=item.get("category", "General"),
            recommendation=item.get("recommendation", ""),
            source=item.get("source", "Unknown"),
            confidence=item.get("confidence", "Low-evidence"),
        )
        for item in parsed.get("recommendations", [])
    ]

    return GuidelineRecommendation(
        recommendations=entries,
        retrieved_sources=parsed.get("retrieved_sources", sources),
        raw=raw,
    )
