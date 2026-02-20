"""
Patient-Friendly Explanation Agent
───────────────────────────────────
Role: Translate complex clinical findings into plain-language summaries
      (6th-grade reading level) for patient communication.

MedGemma 1.5 API: messages dict format via processor.apply_chat_template().

Safety constraints:
  - Does NOT confirm diagnoses, prescribe, or predict outcomes.
  - Emphasises "speak to your doctor" at every step.
  - Avoids alarming language; focuses on next steps, not prognosis.
"""

from __future__ import annotations
import json
import logging
import re
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from schemas import SOAPNote, DifferentialDiagnosis, PatientExplanation

logger = logging.getLogger(__name__)

_SYSTEM = (
    "You are a patient communication assistant. Your role is to translate a "
    "clinical summary into clear, simple language that a patient can understand.\n\n"
    "STRICT RULES:\n"
    "1. Write at a 6th-grade reading level. Avoid medical jargon. Where medical "
    "terms are needed, explain them in brackets.\n"
    "2. Do NOT confirm any diagnosis. Do NOT state what the patient 'has.' "
    "Use language like 'your doctor is considering…' or 'one possibility being "
    "looked at is…'\n"
    "3. Do NOT mention medications, dosages, or specific procedures.\n"
    "4. Always end with a clear, reassuring next-steps statement encouraging the "
    "patient to speak with their doctor.\n"
    "5. Be warm, empathetic, and non-alarming in tone.\n"
    "6. Base content ONLY on the provided clinical summary. Do not add information "
    "not present.\n"
    "7. Output ONLY valid JSON. No prose before or after.\n\n"
    "OUTPUT SCHEMA:\n"
    "{\"summary\": \"...\", \"key_points\": [\"...\"], "
    "\"next_steps_suggestion\": \"...\"}"
)


def build_messages(soap: "SOAPNote", ddx: "DifferentialDiagnosis") -> List[dict]:
    ddx_summary = "\n".join(
        f"- {d.condition} is being considered as a possibility ({d.likelihood} likelihood)"
        for d in ddx.diagnoses[:3]
    ) or "No specific conditions documented yet."

    user_text = (
        f"Translate the following clinical summary into simple, patient-friendly language.\n\n"
        f"WHAT WAS RECORDED (Symptoms & Findings):\n"
        f"{soap.subjective}\n{soap.objective}\n\n"
        f"WHAT THE DOCTOR IS THINKING (Working Assessment):\n{soap.assessment}\n\n"
        f"POSSIBILITIES BEING CONSIDERED (NOT confirmed diagnoses):\n{ddx_summary}\n\n"
        "Write a summary the patient can understand. Never confirm a diagnosis."
    )
    return [
        {"role": "system", "content": [{"type": "text", "text": _SYSTEM}]},
        {"role": "user",   "content": [{"type": "text", "text": user_text}]},
    ]


def _extract_json_object(text: str) -> str | None:
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
    """Remove MedGemma thinking blocks including their content.

    MedGemma 1.5 thinking format:
      <unused94>thought\\n...chain-of-thought content...\\n<unused95>\\n{JSON}

    Strategy: if a closing <unusedXX> tag exists, remove everything from the
    first <unusedXX> up to and including the closing tag.  If there is no
    closing tag (output was cut off mid-thought), strip from the opening tag
    to the first '{' so we preserve any JSON that follows.
    """
    # Pattern for a complete block: <unusedN>...<unusedN>
    text = re.sub(r"<unused\d+>.*?<unused\d+>", "", text, flags=re.DOTALL)
    # Any remaining opening tag (unclosed thinking block) — strip to first '{'
    match = re.search(r"<unused\d+>", text)
    if match:
        brace = text.find("{", match.start())
        if brace != -1:
            text = text[brace:]
        else:
            text = text[: match.start()]   # no JSON found after tag
    return text


def _extract_json_from_last_brace(text: str) -> str | None:
    """Find the last top-level { that starts a valid JSON object."""
    positions = [i for i, ch in enumerate(text) if ch == "{"]
    for start in reversed(positions):
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


def _repair_truncated_json(text: str) -> str | None:
    """Attempt to close a truncated JSON object by appending missing brackets/braces.

    Only tries if the text contains an opening '{' — avoids false positives.
    Returns a repaired string or None if repair isn't possible / doesn't help.
    """
    start = text.find("{")
    if start == -1:
        return None
    snippet = text[start:]
    # Walk the snippet counting open braces/brackets and open strings
    depth_brace = 0
    depth_bracket = 0
    in_string = False
    escape_next = False
    for ch in snippet:
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
            depth_brace += 1
        elif ch == "}":
            depth_brace -= 1
        elif ch == "[":
            depth_bracket += 1
        elif ch == "]":
            depth_bracket -= 1
    if depth_brace == 0 and depth_bracket == 0:
        return None  # Already balanced — other parsers would have handled it
    # Close the in-progress string if needed
    closing = ""
    if in_string:
        closing += '"'
    closing += "]" * max(depth_bracket, 0)
    closing += "}" * max(depth_brace, 0)
    return snippet + closing


def parse_response(raw: str) -> dict:
    import pathlib, time
    _dump = pathlib.Path("/tmp/patient_raw_output.txt")
    _dump.write_text(f"[{time.strftime('%H:%M:%S')}]\n{raw}\n")

    # Strip MedGemma thinking blocks before any other processing
    text = _strip_thinking_blocks(raw)
    # Strip code fences
    text = re.sub(r"```(?:json)?\s*", "", text).strip().rstrip("`").strip()
    logger.debug("Patient raw output: %s", raw)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # Try the last { first (JSON comes after thinking content)
    candidate = _extract_json_from_last_brace(text)
    if candidate:
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass
    # Fall back to first { extractor
    candidate = _extract_json_object(text)
    if candidate:
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass
    # Last resort: try to repair a truncated JSON object by closing open brackets
    candidate = _repair_truncated_json(text)
    if candidate:
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass
    logger.warning("Patient agent parse failed. Raw output:\n%s", raw)
    return {
        "summary": "A summary could not be generated. Please speak directly with your doctor.",
        "key_points": ["Please consult your healthcare provider for further information."],
        "next_steps_suggestion": "Please discuss your results and next steps with your doctor.",
    }


def run(soap: "SOAPNote", ddx: "DifferentialDiagnosis", engine) -> "PatientExplanation":
    from schemas import PatientExplanation

    from config import AGENT_MAX_TOKENS
    messages = build_messages(soap, ddx)
    raw = engine.generate(messages, max_new_tokens=AGENT_MAX_TOKENS["patient"])
    parsed = parse_response(raw)

    key_points: List[str] = parsed.get("key_points", [])
    if not isinstance(key_points, list):
        key_points = [str(key_points)]

    return PatientExplanation(
        summary=parsed.get("summary", "Summary unavailable."),
        key_points=key_points[:5],
        next_steps_suggestion=parsed.get(
            "next_steps_suggestion",
            "Please speak with your doctor about your results and next steps.",
        ),
        raw=raw,
    )
