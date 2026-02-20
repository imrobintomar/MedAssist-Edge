"""
Guideline Retrieval & Recommendation Agent (RAG)
─────────────────────────────────────────────────
Retrieves relevant chunks from the local FAISS vector store and parses
them directly into structured GuidelineEntry objects.

This agent does NOT call the LLM for extraction — MedGemma 4B reliably
returns empty recommendations[] when asked to extract from chunks.
Direct rule-based parsing is faster, more reliable, and fully grounded
in the actual guideline content.
"""

from __future__ import annotations
import re
import logging
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from schemas import ClinicalInput, SOAPNote, DifferentialDiagnosis, GuidelineRecommendation

logger = logging.getLogger(__name__)


# ── Filename → human-readable citation ───────────────────────────────────────

_SOURCE_LABELS: dict[str, str] = {
    "sample_respiratory_guidelines.txt":       "ATS/ERS/JRS/ALAT IPF & Respiratory Guidelines (2022)",
    "connective_tissue_ild_guidelines.txt":    "ATS/ERS CTD-ILD · BTS ILD Guidelines (2022–2024)",
}

def _label(filename: str) -> str:
    """Return a human-readable citation for a guideline filename."""
    base = filename.rsplit("/", 1)[-1]   # strip any path prefix
    return _SOURCE_LABELS.get(base, base.replace("_", " ").replace(".txt", "").replace(".pdf", ""))


# ── Category detection from section headers ───────────────────────────────────

_HEADER_CATEGORY: list[tuple[re.Pattern, str]] = [
    (re.compile(r"workup|investigation|serolog|screen|biopsy|broncho|echocard", re.I), "Workup"),
    (re.compile(r"management|treatment|therapy|therapeut|antifibrotic|anti-fibrotic|pharmacolog|prescri", re.I), "Management"),
    (re.compile(r"monitor|surveillance|serial|repeat pft|dlco every|fvc every", re.I), "Monitoring"),
    (re.compile(r"follow.?up|referral|refer all|review appointment", re.I), "Follow-up"),
]

# Sections whose bullets are purely diagnostic criteria — skip them
_SKIP_SECTION = re.compile(r"\bdiagnos[ie]|diagnostic criteria|definition\b|key hrct features", re.I)

_CONFIDENCE_DIRECT   = re.compile(r"\brecommend|indicated|should\b|required|must\b|standard of care", re.I)
_CONFIDENCE_INFERRED = re.compile(r"\bsuggest|consider|may\b|conditional|optional|could\b", re.I)

# Entries that are clearly truncated mid-sentence
_INCOMPLETE = re.compile(r"[a-z,]$")   # ends with lowercase letter or comma → truncated chunk edge


def _category_from_context(line: str, fallback: str) -> str:
    for pattern, cat in _HEADER_CATEGORY:
        if pattern.search(line):
            return cat
    return fallback


def _confidence(text: str) -> str:
    if _CONFIDENCE_DIRECT.search(text):
        return "Direct"
    if _CONFIDENCE_INFERRED.search(text):
        return "Inferred"
    return "Low-evidence"


def _parse_chunk(chunk: dict) -> List[dict]:
    """
    Extract actionable recommendation bullets from a single retrieved chunk.

    - Walk lines, update active category when a section header is found
    - Skip bullets in DIAGNOSIS / DEFINITION sections
    - Collect bullet lines (starting with '- ') with multi-line continuation
    - Filter truncated bullets (end mid-word at chunk boundary)
    """
    text    = chunk.get("text", "")
    source  = chunk.get("source", "Unknown")
    label   = _label(source)
    lines   = text.splitlines()

    current_category   = "Management"
    skip_section       = False
    pending_bullet: str | None = None
    entries: List[dict] = []

    def _flush(bullet: str | None):
        if not bullet:
            return
        bullet = re.sub(r"\s+", " ", bullet).strip()
        # Skip too-short, truncated, or diagnostic-criteria bullets
        if len(bullet) < 25:
            return
        if _INCOMPLETE.search(bullet):
            return
        if skip_section:
            return
        entries.append({
            "category":       current_category,
            "recommendation": bullet,
            "source":         label,
            "confidence":     _confidence(bullet),
        })

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        # Section header detection
        is_header = (
            bool(re.match(r"^\d+[\.\d]* [A-Z]", stripped))
            or bool(re.match(r"^#+\s+\S", stripped))
            or (stripped.isupper() and 4 < len(stripped) < 80)
        )
        if is_header:
            _flush(pending_bullet)
            pending_bullet = None
            skip_section = bool(_SKIP_SECTION.search(stripped))
            if not skip_section:
                current_category = _category_from_context(stripped, current_category)
            continue

        # Bullet line
        if stripped.startswith("- "):
            _flush(pending_bullet)
            pending_bullet = stripped[2:].strip()
            continue

        # Indented continuation
        if pending_bullet and line.startswith("  "):
            pending_bullet += " " + stripped
            continue

        # Paragraph: update category hint (but don't disrupt pending bullet)
        if not pending_bullet:
            current_category = _category_from_context(stripped, current_category)

    _flush(pending_bullet)
    return entries


def _rag_query(soap: "SOAPNote", ddx: "DifferentialDiagnosis") -> str:
    conditions = " ".join(d.condition for d in ddx.diagnoses[:3])
    return (
        f"{conditions} management treatment monitoring guidelines recommend "
        f"anti-fibrotic immunosuppression workup follow-up"
    )


def run(
    soap:      "SOAPNote",
    ddx:       "DifferentialDiagnosis",
    data:      "ClinicalInput",
    retriever,
    engine,
) -> "GuidelineRecommendation":
    from schemas import GuidelineRecommendation, GuidelineEntry

    # ── 1. Retrieve ──────────────────────────────────────────────────────────
    query: str       = _rag_query(soap, ddx)
    chunks: List[dict] = retriever.retrieve(query) if retriever else []
    sources = list({_label(c.get("source", "")) for c in chunks if c.get("source")})

    # Debug dump
    import pathlib, time as _time
    pathlib.Path("/tmp/guideline_chunks.txt").write_text(
        f"[{_time.strftime('%H:%M:%S')}] Query: {query}\n\n"
        + "\n\n---\n\n".join(
            f"Score={c.get('score', 0):.3f} Source={c.get('source')}\n{c.get('text', '')}"
            for c in chunks
        )
    )

    if not chunks:
        logger.warning("No guideline chunks retrieved.")
        return GuidelineRecommendation(recommendations=[], retrieved_sources=[], raw="")

    # ── 2. Parse chunks directly (no LLM) ────────────────────────────────────
    raw_entries: List[dict] = []
    for chunk in chunks:
        raw_entries.extend(_parse_chunk(chunk))

    # De-duplicate on recommendation text (keep first occurrence)
    seen: set[str] = set()
    unique: List[dict] = []
    for e in raw_entries:
        key = e["recommendation"][:80].lower()
        if key not in seen:
            seen.add(key)
            unique.append(e)

    pathlib.Path("/tmp/guideline_raw_output.txt").write_text(
        f"[{_time.strftime('%H:%M:%S')}] {len(unique)} entries (rule-based)\n\n"
        + "\n".join(f"[{e['category']}] ({e['confidence']}) {e['recommendation']}" for e in unique)
    )

    entries: List[GuidelineEntry] = [
        GuidelineEntry(
            category       = e["category"],
            recommendation = e["recommendation"],
            source         = e["source"],
            confidence     = e["confidence"],
        )
        for e in unique
    ]

    return GuidelineRecommendation(
        recommendations  = entries,
        retrieved_sources = sources,
        raw              = "\n".join(e["recommendation"] for e in unique),
    )
