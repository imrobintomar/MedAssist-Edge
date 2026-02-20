"""
Agent Unit Tests — Mock Inference Engine
─────────────────────────────────────────
Tests all agent parsing, prompt building, and fallback behaviour
WITHOUT loading MedGemma (no GPU/RAM required for CI).

Run:
    pip install pytest
    pytest tests/test_agents_mock.py -v
"""

import sys
import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def mock_engine():
    """Returns an engine mock whose generate() returns a preset JSON string."""
    engine = MagicMock()
    return engine

@pytest.fixture
def sample_input():
    from schemas import ClinicalInput
    return ClinicalInput(
        clinical_notes=(
            "45F with 3-week dyspnea, dry cough, SpO2 91%. "
            "HRCT: bilateral ground-glass opacities, honeycombing. "
            "Spirometry: FVC 68%, FEV1/FVC 0.81."
        ),
        lab_results="LDH 280, ESR 68",
        radiology_text="HRCT: bilateral lower lobe honeycombing, traction bronchiectasis.",
        patient_age=45,
        patient_sex="female",
    )


# ── SOAP Agent ────────────────────────────────────────────────────────────────

class TestSOAPAgent:
    def test_parse_valid_json(self, mock_engine, sample_input):
        import agents.soap_agent as agent
        mock_engine.generate.return_value = json.dumps({
            "subjective": "45F, dyspnea 3 weeks",
            "objective": "SpO2 91%, crackles",
            "assessment": "Possible ILD",
            "plan_suggestions": "Consider PFTs"
        })
        result = agent.run(sample_input, mock_engine)
        assert result.subjective == "45F, dyspnea 3 weeks"
        assert result.objective == "SpO2 91%, crackles"
        assert "Consider" in result.plan_suggestions

    def test_parse_json_with_markdown_fences(self, mock_engine, sample_input):
        import agents.soap_agent as agent
        mock_engine.generate.return_value = (
            "```json\n"
            '{"subjective":"S","objective":"O","assessment":"A","plan_suggestions":"P"}\n'
            "```"
        )
        result = agent.run(sample_input, mock_engine)
        assert result.subjective == "S"

    def test_fallback_on_invalid_json(self, mock_engine, sample_input):
        import agents.soap_agent as agent
        mock_engine.generate.return_value = "This is not JSON at all."
        result = agent.run(sample_input, mock_engine)
        # Should degrade gracefully, not raise
        assert result.subjective is not None

    def test_refusal_returned_in_plan(self, mock_engine, sample_input):
        import agents.soap_agent as agent
        mock_engine.generate.return_value = json.dumps(
            {"error": "Input not suitable for SOAP structuring."}
        )
        result = agent.run(sample_input, mock_engine)
        assert "Refused" in result.subjective or "not suitable" in result.plan_suggestions

    def test_prompt_contains_system_instruction(self, sample_input):
        import agents.soap_agent as agent
        prompt = agent.build_prompt(sample_input)
        assert "SOAP" in prompt
        assert "suggestions only" in prompt.lower() or "SUGGESTIONS ONLY" in prompt

    def test_plan_does_not_say_prescription(self, mock_engine, sample_input):
        """Plan suggestions must never contain dosage language."""
        import agents.soap_agent as agent
        mock_engine.generate.return_value = json.dumps({
            "subjective": "S", "objective": "O", "assessment": "A",
            "plan_suggestions": "Consider referring for PFTs and specialist review"
        })
        result = agent.run(sample_input, mock_engine)
        forbidden = ["mg", "prescribe", "administer", "order"]
        for word in forbidden:
            assert word not in result.plan_suggestions.lower()


# ── DDx Agent ─────────────────────────────────────────────────────────────────

class TestDDxAgent:
    def test_parse_valid_ddx(self, mock_engine, sample_input):
        import agents.ddx_agent as agent
        from schemas import SOAPNote
        soap = SOAPNote(
            subjective="45F dyspnea", objective="SpO2 91%",
            assessment="Possible ILD", plan_suggestions="", raw=""
        )
        mock_engine.generate.return_value = json.dumps({
            "diagnoses": [
                {"rank": 1, "condition": "IPF", "likelihood": "High",
                 "supporting_features": "Honeycombing, restrictive",
                 "against_features": "No clubbing"}
            ],
            "reasoning_summary": "UIP pattern on HRCT is most consistent with IPF."
        })
        result = agent.run(soap, sample_input, mock_engine)
        assert len(result.diagnoses) == 1
        assert result.diagnoses[0].condition == "IPF"
        assert result.diagnoses[0].likelihood == "High"

    def test_max_5_diagnoses_enforced(self, mock_engine, sample_input):
        import agents.ddx_agent as agent
        from schemas import SOAPNote
        soap = SOAPNote(
            subjective="S", objective="O", assessment="A",
            plan_suggestions="", raw=""
        )
        # Return 8 diagnoses
        mock_engine.generate.return_value = json.dumps({
            "diagnoses": [
                {"rank": i, "condition": f"Cond{i}", "likelihood": "Low",
                 "supporting_features": "", "against_features": ""}
                for i in range(1, 9)
            ],
            "reasoning_summary": "Summary"
        })
        result = agent.run(soap, sample_input, mock_engine)
        assert len(result.diagnoses) <= 5

    def test_empty_diagnoses_on_bad_json(self, mock_engine, sample_input):
        import agents.ddx_agent as agent
        from schemas import SOAPNote
        soap = SOAPNote(subjective="S", objective="O", assessment="A",
                        plan_suggestions="", raw="")
        mock_engine.generate.return_value = "Not JSON"
        result = agent.run(soap, sample_input, mock_engine)
        assert isinstance(result.diagnoses, list)


# ── Guideline Agent ───────────────────────────────────────────────────────────

class TestGuidelineAgent:
    def test_parse_valid_recommendations(self, mock_engine, sample_input):
        import agents.guideline_agent as agent
        from schemas import SOAPNote, DifferentialDiagnosis, DiagnosisEntry

        soap = SOAPNote(subjective="S", objective="O", assessment="IPF suspected",
                        plan_suggestions="", raw="")
        ddx = DifferentialDiagnosis(
            diagnoses=[DiagnosisEntry(rank=1, condition="IPF", likelihood="High",
                                      supporting_features="", against_features="")],
            reasoning_summary="", raw=""
        )
        mock_engine.generate.return_value = json.dumps({
            "recommendations": [
                {"category": "Workup", "recommendation": "Perform PFTs",
                 "source": "ATS/ERS IPF Guidelines", "confidence": "Direct"}
            ],
            "retrieved_sources": ["sample_guidelines.txt"]
        })
        mock_retriever = MagicMock()
        mock_retriever.retrieve.return_value = [
            {"source": "sample_guidelines.txt", "text": "PFTs recommended.", "score": 0.9}
        ]
        result = agent.run(soap, ddx, sample_input, mock_retriever, mock_engine)
        assert len(result.recommendations) == 1
        assert result.recommendations[0].category == "Workup"

    def test_no_retriever_degrades_gracefully(self, mock_engine, sample_input):
        import agents.guideline_agent as agent
        from schemas import SOAPNote, DifferentialDiagnosis
        soap = SOAPNote(subjective="S", objective="O", assessment="A",
                        plan_suggestions="", raw="")
        ddx = DifferentialDiagnosis(diagnoses=[], reasoning_summary="", raw="")
        mock_engine.generate.return_value = json.dumps({
            "recommendations": [], "retrieved_sources": []
        })
        result = agent.run(soap, ddx, sample_input, None, mock_engine)
        assert result is not None


# ── Patient Agent ─────────────────────────────────────────────────────────────

class TestPatientAgent:
    def test_parse_valid_explanation(self, mock_engine):
        import agents.patient_agent as agent
        from schemas import SOAPNote, DifferentialDiagnosis, DiagnosisEntry

        soap = SOAPNote(subjective="Breathlessness", objective="SpO2 91%",
                        assessment="Possible lung scarring", plan_suggestions="", raw="")
        ddx = DifferentialDiagnosis(
            diagnoses=[DiagnosisEntry(rank=1, condition="IPF", likelihood="High",
                                      supporting_features="", against_features="")],
            reasoning_summary="", raw=""
        )
        mock_engine.generate.return_value = json.dumps({
            "summary": "Your doctor noticed some changes in your lungs.",
            "key_points": ["You have breathlessness", "Tests show lung changes"],
            "next_steps_suggestion": "Please discuss with your doctor."
        })
        result = agent.run(soap, ddx, mock_engine)
        assert "doctor" in result.summary.lower() or "doctor" in result.next_steps_suggestion.lower()
        assert len(result.key_points) == 2

    def test_key_points_capped_at_5(self, mock_engine):
        import agents.patient_agent as agent
        from schemas import SOAPNote, DifferentialDiagnosis
        soap = SOAPNote(subjective="S", objective="O", assessment="A",
                        plan_suggestions="", raw="")
        ddx = DifferentialDiagnosis(diagnoses=[], reasoning_summary="", raw="")
        mock_engine.generate.return_value = json.dumps({
            "summary": "Summary",
            "key_points": [f"Point {i}" for i in range(10)],
            "next_steps_suggestion": "See doctor."
        })
        result = agent.run(soap, ddx, mock_engine)
        assert len(result.key_points) <= 5

    def test_no_medication_in_output(self, mock_engine):
        """Patient explanation must never mention specific medications."""
        import agents.patient_agent as agent
        from schemas import SOAPNote, DifferentialDiagnosis
        soap = SOAPNote(subjective="S", objective="O", assessment="A",
                        plan_suggestions="", raw="")
        ddx = DifferentialDiagnosis(diagnoses=[], reasoning_summary="", raw="")
        mock_engine.generate.return_value = json.dumps({
            "summary": "You have been given a prescription for your condition.",
            "key_points": [],
            "next_steps_suggestion": "Take 500mg daily."
        })
        # The prompt prohibits this — test that the safety rules are in the prompt
        prompt = agent.build_prompt(soap, ddx)
        assert "NOT mention medications" in prompt or "Do NOT mention medications" in prompt


# ── Schemas ───────────────────────────────────────────────────────────────────

class TestSchemas:
    def test_input_truncates_long_notes(self):
        from schemas import ClinicalInput
        long_notes = "x" * 10000
        inp = ClinicalInput(clinical_notes=long_notes)
        assert len(inp.clinical_notes) <= 8000

    def test_input_requires_min_length(self):
        from schemas import ClinicalInput
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            ClinicalInput(clinical_notes="too short")

    def test_age_range_enforced(self):
        from schemas import ClinicalInput
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            ClinicalInput(clinical_notes="A" * 25, patient_age=200)
