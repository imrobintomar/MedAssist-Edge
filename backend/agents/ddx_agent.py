"""
Differential Diagnosis Reasoning Agent
───────────────────────────────────────
Role: Reason over structured SOAP data and propose a ranked DDx list.

MedGemma 1.5 API: messages dict format via processor.apply_chat_template().

Safety constraints:
  - Max 5 entries to prevent cognitive overload.
  - Explicitly hedged — possibilities, never confirmed diagnoses.
  - No treatment recommendations, no dosages.
"""

from __future__ import annotations
import json
import logging
import re
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from schemas import ClinicalInput, SOAPNote, DifferentialDiagnosis

logger = logging.getLogger(__name__)

_SYSTEM = (
    "You are a clinical reasoning assistant supporting differential diagnosis.\n\n"
    "STRICT RULES:\n"
    "1. Generate a RANKED differential diagnosis list (1 = most likely). Maximum 5 conditions.\n"
    "2. For each condition provide: condition name, likelihood (High/Moderate/Low), "
    "supporting_features (from input), against_features (arguing against it).\n"
    "3. Base reasoning ONLY on the provided clinical information. Do not invent findings.\n"
    "4. Use hedged language: 'may suggest', 'could be consistent with', 'warrants consideration'.\n"
    "5. Do NOT confirm any diagnosis. Do NOT recommend treatments, procedures, or medications.\n"
    "6. If input is insufficient for meaningful reasoning, state this in reasoning_summary.\n"
    "7. Output ONLY valid JSON. No prose before or after.\n\n"
    "OUTPUT SCHEMA:\n"
    "{\"diagnoses\": [{\"rank\": 1, \"condition\": \"...\", \"likelihood\": \"High|Moderate|Low\", "
    "\"supporting_features\": \"...\", \"against_features\": \"...\"}], "
    "\"reasoning_summary\": \"...\"}"
)


def build_messages(soap: "SOAPNote", data: "ClinicalInput") -> List[dict]:
    user_text = (
        f"Generate a ranked differential diagnosis based on the structured clinical data below.\n\n"
        f"SUBJECTIVE:\n{soap.subjective}\n\n"
        f"OBJECTIVE:\n{soap.objective}\n\n"
        f"ASSESSMENT (clinician's stated impressions):\n{soap.assessment}\n\n"
        f"PATIENT DEMOGRAPHICS:\nAge: {data.patient_age or 'N/A'}  "
        f"Sex: {data.patient_sex or 'N/A'}\n\n"
        "Remember: suggestions only, no confirmed diagnoses, no treatments."
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
    text = _strip_thinking_blocks(raw)
    text = re.sub(r"```(?:json)?\s*", "", text).strip().rstrip("`").strip()
    logger.debug("DDx raw output: %s", raw)
    # Try direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # Balanced-brace extraction (handles trailing prose with {} chars)
    candidate = _extract_json_object(text)
    if candidate:
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass
    # Dump raw output to file for inspection
    import pathlib, time
    _dump = pathlib.Path("/tmp/ddx_raw_output.txt")
    _dump.write_text(f"[{time.strftime('%H:%M:%S')}]\n{raw}\n")
    logger.warning("DDx parse failed. Raw output dumped to %s", _dump)
    return {"diagnoses": [], "reasoning_summary": "Parsing failed — review raw output."}


def run(soap: "SOAPNote", data: "ClinicalInput", engine) -> "DifferentialDiagnosis":
    from schemas import DifferentialDiagnosis, DiagnosisEntry

    from config import AGENT_MAX_TOKENS
    messages = build_messages(soap, data)
    raw = engine.generate(messages, max_new_tokens=AGENT_MAX_TOKENS["ddx"])
    parsed = parse_response(raw)

    def _to_str(val) -> str:
        if isinstance(val, list):
            return "; ".join(str(v) for v in val)
        return str(val) if val else ""

    entries: List[DiagnosisEntry] = []
    for item in parsed.get("diagnoses", [])[:5]:   # hard cap at 5
        entries.append(DiagnosisEntry(
            rank=item.get("rank", len(entries) + 1),
            condition=item.get("condition", "Unknown"),
            likelihood=item.get("likelihood", "Low"),
            supporting_features=_to_str(item.get("supporting_features", "")),
            against_features=_to_str(item.get("against_features", "")),
        ))

    return DifferentialDiagnosis(
        diagnoses=entries,
        reasoning_summary=parsed.get("reasoning_summary", "Unavailable."),
        raw=raw,
    )
