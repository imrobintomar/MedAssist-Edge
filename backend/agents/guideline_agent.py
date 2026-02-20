"""
Guideline Retrieval & Recommendation Agent (RAG)
─────────────────────────────────────────────────
Retrieves relevant chunks from the local FAISS vector store and parses
them directly into structured GuidelineEntry objects.

This agent does NOT call the LLM for extraction — MedGemma 4B reliably
returns empty recommendations when asked to extract from chunks.
Direct rule-based parsing of the retrieved text is faster, more reliable,
and fully grounded in the actual guideline content.
"""

from __future__ import annotations
import re
import logging
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from schemas import ClinicalInput, SOAPNote, DifferentialDiagnosis, GuidelineRecommendation

logger = logging.getLogger(__name__)


# ── Category detection from section headers ──────────────────────────────────

_HEADER_CATEGORY: list[tuple[re.Pattern, str]] = [
    (re.compile(r"workup|diagnostic|investigation|screen", re.I), "Workup"),
    (re.compile(r"management|treatment|therapy|therapeut|antifibrotic|anti-fibrotic|pharmacolog", re.I), "Management"),
    (re.compile(r"monitor|surveillance|follow.?up|serial|repeat", re.I), "Monitoring"),
    (re.compile(r"follow.?up|referral|refer all|review", re.I), "Follow-up"),
]

_CONFIDENCE_DIRECT   = re.compile(r"\brecommend|indicated|should\b|required|must\b|standard of care", re.I)
_CONFIDENCE_INFERRED = re.compile(r"\bsuggest|consider|may\b|conditional|optional|could\b", re.I)


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

    Strategy:
    - Walk lines looking for section headers (WORKUP, MANAGEMENT, MONITORING …)
    - Collect bullet lines (starting with '- ') under the active category
    - Multi-line bullets (indented continuation) are joined to the preceding line
    """
    text   = chunk.get("text", "")
    source = chunk.get("source", "Unknown")
    lines  = text.splitlines()

    current_category = "Management"   # sensible default
    pending_bullet   = None
    entries: List[dict] = []

    def _flush(bullet: str | None):
        if not bullet:
            return
        bullet = re.sub(r"\s+", " ", bullet).strip()
        if len(bullet) < 25:
            return
        entries.append({
            "category":       current_category,
            "recommendation": bullet,
            "source":         source,
            "confidence":     _confidence(bullet),
        })

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        # Section header detection: lines that are all-caps or contain known keywords
        # e.g. "1.3 MANAGEMENT (GUIDELINE RECOMMENDATIONS)" or "## Workup"
        is_header = (
            bool(re.match(r"^\d+[\.\d]* [A-Z]", stripped))     # numbered section
            or bool(re.match(r"^#+\s+\S", stripped))            # markdown heading
            or (stripped.isupper() and len(stripped) < 80)      # ALL CAPS header
        )
        if is_header:
            _flush(pending_bullet)
            pending_bullet = None
            current_category = _category_from_context(stripped, current_category)
            continue

        # Bullet line
        if stripped.startswith("- "):
            _flush(pending_bullet)
            pending_bullet = stripped[2:].strip()
            continue

        # Indented continuation of previous bullet
        if pending_bullet and line.startswith("  "):
            pending_bullet += " " + stripped
            continue

        # Otherwise just update category hint from paragraph text
        current_category = _category_from_context(stripped, current_category)

    _flush(pending_bullet)
    return entries


def _rag_query(soap: "SOAPNote", ddx: "DifferentialDiagnosis") -> str:
    conditions = " ".join(d.condition for d in ddx.diagnoses[:3])
    return (
        f"{conditions} management treatment monitoring guidelines recommend "
        f"anti-fibrotic immunosuppression workup follow-up"
    )


def _strip_thinking_blocks(text: str) -> str:
    text = re.sub(r"<unused\d+>thought\s*", "", text)
    text = re.sub(r"<unused\d+>", "", text)
    return text


def run(
    soap: "SOAPNote",
    ddx:  "DifferentialDiagnosis",
    data: "ClinicalInput",
    retriever,
    engine,
) -> "GuidelineRecommendation":
    from schemas import GuidelineRecommendation, GuidelineEntry

    # ── 1. Retrieve relevant chunks ───────────────────────────────────────────
    query: str  = _rag_query(soap, ddx)
    chunks: List[dict] = retriever.retrieve(query) if retriever else []
    sources = list({c.get("source", "") for c in chunks if c.get("source")})

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

    # De-duplicate by recommendation text (keep first occurrence)
    seen: set[str] = set()
    unique_entries: List[dict] = []
    for e in raw_entries:
        key = e["recommendation"][:80].lower()
        if key not in seen:
            seen.add(key)
            unique_entries.append(e)

    # Debug dump
    pathlib.Path("/tmp/guideline_raw_output.txt").write_text(
        f"[{_time.strftime('%H:%M:%S')}] Parsed {len(unique_entries)} entries (rule-based, no LLM)\n\n"
        + "\n".join(f"[{e['category']}] {e['recommendation']}" for e in unique_entries)
    )

    entries: List[GuidelineEntry] = [
        GuidelineEntry(
            category=e["category"],
            recommendation=e["recommendation"],
            source=e["source"],
            confidence=e["confidence"],
        )
        for e in unique_entries
    ]

    return GuidelineRecommendation(
        recommendations=entries,
        retrieved_sources=sources,
        raw="\n".join(e["recommendation"] for e in unique_entries),
    )
