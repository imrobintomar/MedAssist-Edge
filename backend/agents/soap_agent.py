"""
SOAP Structuring Agent
─────────────────────
Role: Convert unstructured clinical notes into a structured SOAP note.

MedGemma 1.5 API: uses processor.apply_chat_template() with messages dict.
Raw <start_of_turn> strings are NOT used — processor handles chat formatting.

Safety constraints:
  - Plan section: suggestions only, no orders or dosages.
  - Refuses to invent findings not present in input.
  - Returns {"error": ...} JSON on unsafe/non-clinical input.
"""

from __future__ import annotations
import json
import logging
import re
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from schemas import ClinicalInput, SOAPNote

logger = logging.getLogger(__name__)

_SYSTEM = (
    "You are a clinical documentation assistant. Your only function is to "
    "reorganise the clinician's raw notes into a structured SOAP format.\n\n"
    "STRICT RULES:\n"
    "1. Use ONLY information explicitly stated in the input. Do NOT add, infer, "
    "or assume any clinical finding, symptom, or result.\n"
    "2. The Plan section must contain SUGGESTIONS ONLY (e.g. 'Consider checking…', "
    "'May warrant…'). Never write orders, prescriptions, or specific dosages.\n"
    "3. If information for a SOAP section is absent, write 'Not documented.'\n"
    "4. Do NOT diagnose. Do NOT recommend treatments.\n"
    "5. If the input contains non-clinical content or appears unsafe, respond only "
    "with: {\"error\": \"Input not suitable for SOAP structuring.\"}\n"
    "6. Output ONLY valid JSON. No prose before or after.\n\n"
    "OUTPUT SCHEMA:\n"
    "{\"subjective\": \"...\", \"objective\": \"...\", "
    "\"assessment\": \"...\", \"plan_suggestions\": \"...\"}"
)


def build_messages(data: "ClinicalInput") -> List[dict]:
    user_text = (
        f"Organise the following clinical information into SOAP format.\n\n"
        f"CLINICAL NOTES:\n{data.clinical_notes}\n\n"
        f"LAB RESULTS:\n{data.lab_results or 'Not provided'}\n\n"
        f"RADIOLOGY TEXT:\n{data.radiology_text or 'Not provided'}\n\n"
        f"PATIENT DEMOGRAPHICS:\nAge: {data.patient_age or 'N/A'}  "
        f"Sex: {data.patient_sex or 'N/A'}\n\n"
        "Return only the JSON object."
    )
    return [
        {"role": "system", "content": [{"type": "text", "text": _SYSTEM}]},
        {"role": "user",   "content": [{"type": "text", "text": user_text}]},
    ]


def _strip_thinking_blocks(text: str) -> str:
    """Remove MedGemma thinking blocks including their content."""
    # Remove complete <unusedN>...<unusedN> blocks
    text = re.sub(r"<unused\d+>.*?<unused\d+>", "", text, flags=re.DOTALL)
    # Any remaining opening tag (unclosed) — strip to first '{'
    match = re.search(r"<unused\d+>", text)
    if match:
        brace = text.find("{", match.start())
        if brace != -1:
            text = text[brace:]
        else:
            text = text[: match.start()]
    return text


def _to_str(value) -> str:
    """Coerce a parsed JSON value to str (model sometimes returns list instead of string)."""
    if isinstance(value, list):
        return "\n".join(str(item).strip() for item in value if item)
    if isinstance(value, str):
        return value
    return str(value) if value is not None else "Not documented."


def parse_response(raw: str) -> dict:
    text = _strip_thinking_blocks(raw)
    text = re.sub(r"```(?:json)?", "", text).strip().rstrip("`").strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        m = re.search(r"\{[\s\S]+\}", text)
        if m:
            try:
                return json.loads(m.group())
            except json.JSONDecodeError:
                pass
    logger.warning("SOAP parse failed. Raw: %.200s", raw)
    return {
        "subjective": "Parse error — review raw output.",
        "objective":  "Parse error — review raw output.",
        "assessment": "Parse error — review raw output.",
        "plan_suggestions": "Parse error — review raw output.",
    }


def run(data: "ClinicalInput", engine) -> "SOAPNote":
    from schemas import SOAPNote

    from config import AGENT_MAX_TOKENS
    messages = build_messages(data)
    raw = engine.generate(messages, max_new_tokens=AGENT_MAX_TOKENS["soap"])
    parsed = parse_response(raw)

    if "error" in parsed:
        logger.warning("SOAP refusal: %s", parsed["error"])
        return SOAPNote(
            subjective="[Refused]", objective="[Refused]",
            assessment="[Refused]", plan_suggestions=parsed["error"],
            raw=raw,
        )

    return SOAPNote(
        subjective=_to_str(parsed.get("subjective", "Not documented.")),
        objective=_to_str(parsed.get("objective", "Not documented.")),
        assessment=_to_str(parsed.get("assessment", "Not documented.")),
        plan_suggestions=_to_str(parsed.get("plan_suggestions", "Not documented.")),
        raw=raw,
    )
