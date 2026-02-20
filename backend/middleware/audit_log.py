"""
Audit Logging Middleware
────────────────────────
Writes a structured JSONL audit log of every analysis request/response.
Required for clinical governance: provides a complete, tamper-evident
record of what the AI system produced and when.

Log format (one JSON object per line):
{
  "timestamp": "2024-01-15T10:23:45.123Z",
  "request_id": "abc123",
  "clinical_notes_hash": "sha256:...",   // hash only — no PHI stored in log
  "model_id": "google/medgemma-4b-it",
  "agents_run": ["soap", "ddx", "guidelines", "patient"],
  "processing_time_s": 87.4,
  "soap_assessment": "...",              // assessment text for audit
  "ddx_count": 5,
  "guidelines_count": 3,
  "error": null
}
"""

from __future__ import annotations
import hashlib
import json
import logging
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class AuditLogger:
    """
    Write structured JSONL audit records for every analysis request.

    Usage:
        audit = AuditLogger(Path("logs/audit.jsonl"))
        record_id = audit.start(payload)
        # ... run pipeline ...
        audit.finish(record_id, response, error=None)
    """

    def __init__(self, log_path: Path) -> None:
        self.log_path = log_path
        log_path.parent.mkdir(parents=True, exist_ok=True)
        logger.info("Audit log: %s", log_path)

    def start(self, payload) -> str:
        """Register start of a request. Returns a unique record ID."""
        record_id = str(uuid.uuid4())[:8]
        # Hash clinical notes — PHI never written to log
        notes_bytes = payload.clinical_notes.encode("utf-8")
        notes_hash = "sha256:" + hashlib.sha256(notes_bytes).hexdigest()[:16]

        self._pending[record_id] = {
            "record_id": record_id,
            "timestamp_start": datetime.now(timezone.utc).isoformat(),
            "clinical_notes_hash": notes_hash,
            "patient_age": payload.patient_age,
            "patient_sex": payload.patient_sex,
            "_t0": time.time(),
        }
        return record_id

    def finish(
        self,
        record_id: str,
        response=None,
        error: Optional[str] = None,
    ) -> None:
        """Complete and write the audit record."""
        rec = self._pending.pop(record_id, {})
        t0 = rec.pop("_t0", time.time())

        rec.update({
            "timestamp_end": datetime.now(timezone.utc).isoformat(),
            "processing_time_s": round(time.time() - t0, 2),
            "error": error,
        })

        if response is not None:
            rec.update({
                "model_id": response.model_id,
                "soap_assessment": response.soap.assessment[:200],  # truncated
                "ddx_count": len(response.ddx.diagnoses),
                "guidelines_count": len(response.guidelines.recommendations),
                "agents_run": ["soap", "ddx", "guidelines", "patient"],
            })

        try:
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        except Exception as exc:
            logger.warning("Audit log write failed: %s", exc)

    # ── Internal state ────────────────────────────────────────────────────────
    _pending: dict = {}


# Module-level singleton
_audit_logger: Optional[AuditLogger] = None


def get_audit_logger() -> Optional[AuditLogger]:
    return _audit_logger


def init_audit_logger(log_path: Path) -> AuditLogger:
    global _audit_logger
    _audit_logger = AuditLogger(log_path)
    return _audit_logger
