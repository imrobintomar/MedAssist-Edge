"""
Pydantic request / response schemas for MedAssist-Edge API.
Strict typing ensures safe, auditable data flow between agents.
"""

from __future__ import annotations
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator
from config import MAX_INPUT_CHARS, DISCLAIMER


# ── Inbound ───────────────────────────────────────────────────────────────────

class ClinicalInput(BaseModel):
    """Raw clinical data from the clinician UI."""
    clinical_notes: str = Field(
        ...,
        min_length=20,
        description="Free-text clinical notes (HPI, ROS, exam findings)"
    )
    lab_results: Optional[str] = Field(
        default="",
        description="Lab values as free text (e.g., 'Na 138, K 4.1, Hgb 9.2')"
    )
    radiology_text: Optional[str] = Field(
        default="",
        description="Radiology report text (plain text, de-identified)"
    )
    patient_age: Optional[int] = Field(
        default=None, ge=0, le=120,
        description="Patient age in years (optional, for context)"
    )
    patient_sex: Optional[str] = Field(
        default=None,
        description="Biological sex: 'male' | 'female' | 'other'"
    )

    @field_validator("clinical_notes", "lab_results", "radiology_text", mode="before")
    @classmethod
    def truncate_input(cls, v: str) -> str:
        if v and len(v) > MAX_INPUT_CHARS:
            return v[:MAX_INPUT_CHARS]
        return v or ""


# ── Per-agent outputs ─────────────────────────────────────────────────────────

class SOAPNote(BaseModel):
    subjective: str
    objective: str
    assessment: str
    plan_suggestions: str   # suggestions only, never orders
    raw: str                # full model output for audit log


class DifferentialDiagnosis(BaseModel):
    diagnoses: List[DiagnosisEntry]
    reasoning_summary: str
    raw: str

class DiagnosisEntry(BaseModel):
    rank: int
    condition: str
    likelihood: str         # High / Moderate / Low
    supporting_features: str
    against_features: str


class GuidelineRecommendation(BaseModel):
    recommendations: List[GuidelineEntry]
    retrieved_sources: List[str]
    raw: str

class GuidelineEntry(BaseModel):
    category: str           # e.g. "Workup", "Management", "Follow-up"
    recommendation: str
    source: str             # guideline name + section
    confidence: str         # Direct / Inferred / Low-evidence


class PatientExplanation(BaseModel):
    summary: str            # plain-language, 6th-grade reading level
    key_points: List[str]
    next_steps_suggestion: str
    raw: str


# ── Aggregate response ────────────────────────────────────────────────────────

class AnalysisResponse(BaseModel):
    soap: SOAPNote
    ddx: DifferentialDiagnosis
    guidelines: GuidelineRecommendation
    patient_explanation: PatientExplanation
    disclaimer: str = DISCLAIMER
    model_id: str
    processing_time_seconds: float


# ── Error response ────────────────────────────────────────────────────────────

class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
    safe_to_retry: bool = True
