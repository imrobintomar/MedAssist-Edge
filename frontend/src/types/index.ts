// ── Input ─────────────────────────────────────────────────────────────────────

export interface ClinicalInput {
  clinical_notes: string;
  lab_results?: string;
  radiology_text?: string;
  patient_age?: number;
  patient_sex?: "male" | "female" | "other";
}

// ── Agent outputs ─────────────────────────────────────────────────────────────

export interface SOAPNote {
  subjective: string;
  objective: string;
  assessment: string;
  plan_suggestions: string;
  raw: string;
}

export interface DiagnosisEntry {
  rank: number;
  condition: string;
  likelihood: "High" | "Moderate" | "Low";
  supporting_features: string;
  against_features: string;
}

export interface DifferentialDiagnosis {
  diagnoses: DiagnosisEntry[];
  reasoning_summary: string;
  raw: string;
}

export interface GuidelineEntry {
  category: "Workup" | "Management" | "Monitoring" | "Follow-up" | string;
  recommendation: string;
  source: string;
  confidence: "Direct" | "Inferred" | "Low-evidence";
}

export interface GuidelineRecommendation {
  recommendations: GuidelineEntry[];
  retrieved_sources: string[];
  raw: string;
}

export interface PatientExplanation {
  summary: string;
  key_points: string[];
  next_steps_suggestion: string;
  raw: string;
}

// ── Aggregate ─────────────────────────────────────────────────────────────────

export interface AnalysisResponse {
  soap: SOAPNote;
  ddx: DifferentialDiagnosis;
  guidelines: GuidelineRecommendation;
  patient_explanation: PatientExplanation;
  disclaimer: string;
  model_id: string;
  processing_time_seconds: number;
}

// ── UI state ──────────────────────────────────────────────────────────────────

export type TabId = "soap" | "ddx" | "guidelines" | "patient";

export type AnalysisStatus = "idle" | "loading" | "success" | "error";

export interface AppState {
  status: AnalysisStatus;
  result: AnalysisResponse | null;
  error: string | null;
  activeTab: TabId;
}
