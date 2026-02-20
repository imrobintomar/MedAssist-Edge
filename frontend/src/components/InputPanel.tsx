import React, { useState } from "react";
import { Send, RotateCcw, WifiOff, FlaskConical, User, Microscope, Scan, FileText } from "lucide-react";
import type { ClinicalInput } from "../types";

const EXAMPLE_CASE = {
  age: "67",
  sex: "male" as const,
  notes: `Chief complaint: Progressive shortness of breath and dry cough for 3 months.

HPI: 67-year-old male non-smoker presenting with worsening exertional dyspnoea over 3 months. Dry, non-productive cough. No fever, chills, or night sweats. No haemoptysis. Reports fatigue and 3 kg unintentional weight loss. Never smoked. Works as a retired farmer. No known asbestos or silica exposure. No sick contacts.

ROS: Negative for orthopnoea, PND, leg swelling. No joint pains or skin changes. No GORD symptoms.

Examination: RR 20/min, SpO2 94% on air (drops to 88% on exertion). Chest: bilateral fine end-inspiratory crackles at both bases, worse on right. No wheeze. No clubbing. No lymphadenopathy. Cardiovascular: normal HS, no JVD.`,
  labs: `FBC: Hb 13.2 g/dL, WBC 7.8 x10^9/L (normal differential), Platelets 310
CRP: 18 mg/L
LDH: 280 U/L (mildly elevated)
ANA: positive 1:80 (speckled)
Anti-Scl-70: negative
RF: negative
ABG on air: pH 7.44, PaO2 68 mmHg, PaCO2 36 mmHg`,
  radiology: `CXR PA: Bilateral peripheral reticular infiltrates predominantly at the lung bases. Mild honeycombing pattern at right base. No pleural effusion. Heart size normal.

HRCT Chest: Bilateral subpleural, basal-predominant reticulation with honeycombing and traction bronchiectasis. Subpleural sparing relatively preserved. Mild ground-glass opacity. No consolidation. Pattern consistent with Usual Interstitial Pneumonia (UIP). No mediastinal lymphadenopathy.

Pulmonary function tests: FVC 61% predicted, FEV1/FVC 0.84, TLC 58% predicted, DLCO 48% predicted. Restrictive ventilatory defect with severely impaired gas transfer.`,
};

interface Props {
  onSubmit: (data: ClinicalInput) => void;
  onReset: () => void;
  isLoading: boolean;
}

const inp = "w-full rounded-xl px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-clinical-400 transition-all bg-slate-50 border border-slate-200 hover:border-slate-300 focus:bg-white focus:border-clinical-300";
const lbl = "block text-xs font-semibold text-slate-600 mb-1.5";

export const InputPanel: React.FC<Props> = ({ onSubmit, onReset, isLoading }) => {
  const [notes, setNotes] = useState("");
  const [labs, setLabs] = useState("");
  const [radiology, setRadiology] = useState("");
  const [age, setAge] = useState<string>("");
  const [sex, setSex] = useState<"" | "male" | "female" | "other">("");

  const loadExample = () => {
    setAge(EXAMPLE_CASE.age);
    setSex(EXAMPLE_CASE.sex);
    setNotes(EXAMPLE_CASE.notes);
    setLabs(EXAMPLE_CASE.labs);
    setRadiology(EXAMPLE_CASE.radiology);
  };

  const canSubmit = notes.trim().length >= 20 && !isLoading;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!canSubmit) return;
    onSubmit({
      clinical_notes: notes.trim(),
      lab_results:    labs.trim()      || undefined,
      radiology_text: radiology.trim() || undefined,
      patient_age:    age ? parseInt(age, 10) : undefined,
      patient_sex:    sex || undefined,
    });
  };

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-5">

      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-base font-bold text-slate-800">Clinical Input</h2>
          <p className="text-xs text-slate-400 mt-0.5">Enter patient data for AI analysis</p>
        </div>
        <div className="flex items-center gap-2">
          <button type="button" onClick={loadExample} disabled={isLoading}
            className="flex items-center gap-1.5 text-xs font-medium px-3 py-1.5 rounded-lg border border-clinical-200 text-clinical-700 bg-clinical-50 hover:bg-clinical-100 transition-colors disabled:opacity-40">
            <FlaskConical size={12} /> Load Example
          </button>
          <span className="flex items-center gap-1.5 text-xs font-medium px-3 py-1.5 rounded-lg border border-teal-200 text-teal-700 bg-teal-50">
            <WifiOff size={12} /> Offline
          </span>
        </div>
      </div>

      {/* Demographics */}
      <div className="grid grid-cols-2 gap-3 p-4 rounded-xl bg-gradient-to-br from-slate-50 to-blue-50/60 border border-slate-100">
        <div>
          <label className={lbl}>
            <span className="flex items-center gap-1"><User size={10} className="text-slate-400" /> Age (years)</span>
          </label>
          <input type="number" min={0} max={120} value={age}
            onChange={(e) => setAge(e.target.value)}
            placeholder="e.g. 67" className={inp} />
        </div>
        <div>
          <label className={lbl}>
            <span className="flex items-center gap-1"><User size={10} className="text-slate-400" /> Biological Sex</span>
          </label>
          <select value={sex} onChange={(e) => setSex(e.target.value as any)}
            className={inp + " cursor-pointer"}>
            <option value="">Not specified</option>
            <option value="male">Male</option>
            <option value="female">Female</option>
            <option value="other">Other</option>
          </select>
        </div>
      </div>

      {/* Clinical Notes */}
      <div>
        <label className={lbl}>
          <span className="flex items-center gap-1">
            <FileText size={11} className="text-clinical-500" />
            Clinical Notes <span className="text-danger-500">*</span>
            <span className="text-slate-400 font-normal">(HPI, ROS, Exam)</span>
          </span>
        </label>
        <textarea value={notes} onChange={(e) => setNotes(e.target.value)}
          placeholder="Patient presents with…" rows={8} required
          className={inp + " font-mono resize-y leading-relaxed"} />
        <div className="flex justify-between mt-1">
          <span className="text-xs text-slate-400">Min 20 characters required</span>
          <span className={`text-xs font-medium ${notes.length > 7500 ? "text-danger-500" : "text-slate-400"}`}>
            {notes.length} / 8000
          </span>
        </div>
      </div>

      {/* Lab Results */}
      <div>
        <label className={lbl}>
          <span className="flex items-center gap-1">
            <Microscope size={11} className="text-teal-500" />
            Lab Results <span className="text-slate-400 font-normal">(optional)</span>
          </span>
        </label>
        <textarea value={labs} onChange={(e) => setLabs(e.target.value)}
          placeholder="Na 138, K 4.1, Hgb 13.2 g/dL, CRP 18…" rows={3}
          className={inp + " font-mono resize-y"} />
      </div>

      {/* Radiology */}
      <div>
        <label className={lbl}>
          <span className="flex items-center gap-1">
            <Scan size={11} className="text-violet-500" />
            Radiology Report <span className="text-slate-400 font-normal">(optional)</span>
          </span>
        </label>
        <textarea value={radiology} onChange={(e) => setRadiology(e.target.value)}
          placeholder="HRCT Chest: bilateral subpleural reticulation…" rows={3}
          className={inp + " font-mono resize-y"} />
      </div>

      {/* Actions */}
      <div className="flex gap-3 pt-1">
        <button type="submit" disabled={!canSubmit}
          className="btn-primary flex-1 flex items-center justify-center gap-2 text-white font-semibold py-3 px-5 rounded-xl">
          {isLoading ? (
            <><span className="w-4 h-4 border-2 border-white/40 border-t-white rounded-full animate-spin" /> Analysing…</>
          ) : (
            <><Send size={15} /> Analyse</>
          )}
        </button>
        <button type="button" onClick={onReset}
          className="flex items-center gap-1.5 border border-slate-200 text-slate-600 hover:bg-slate-50 hover:border-slate-300 py-3 px-4 rounded-xl transition-colors text-sm font-medium">
          <RotateCcw size={14} /> Reset
        </button>
      </div>
    </form>
  );
};
