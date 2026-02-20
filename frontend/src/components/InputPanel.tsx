import React, { useState, useRef, useEffect } from "react";
import { Send, RotateCcw, WifiOff, FlaskConical, User, Microscope, Scan, FileText, ChevronDown } from "lucide-react";
import type { ClinicalInput } from "../types";

// ── Example cases ─────────────────────────────────────────────────────────────

const EXAMPLES = {
  ipf: {
    label: "Case 1 · IPF / UIP",
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
  },

  copd: {
    label: "Case 2 · COPD Exacerbation",
    age: "67",
    sex: "male" as const,
    notes: `Chief complaint: Worsening breathlessness and productive cough for 5 days.

HPI: Mr. J.K. is a 67-year-old retired construction worker with a 20 pack-year smoking history (quit 8 years ago) and known COPD (GOLD Stage III, last FEV1 38% predicted). He presents with a 5-day history of markedly worsening dyspnoea at rest, increased cough frequency, and change in sputum from white to yellow-green with increased volume. He reports a low-grade fever (37.9°C at home) and reduced exercise tolerance — previously able to walk 100m on flat ground, now dyspnoeic at rest. No chest pain or haemoptysis. No recent travel or sick contacts. He missed his last 3 clinic appointments. He is on triple inhaler therapy (ICS/LABA/LAMA) but admits to poor adherence due to cost.

Past medical history: COPD (diagnosed 2018, GOLD III, FEV1/FVC 0.58), hypertension, type 2 diabetes mellitus. Previous acute exacerbation of COPD requiring hospitalisation ×2 (2022, 2024).

Allergies: Penicillin (rash).

Examination: Temp 37.8°C, HR 108 bpm (sinus tachycardia), RR 26/min, SpO2 84% on room air (improved to 90% on 28% Venturi mask). BP 148/90 mmHg. Accessory muscle use, pursed-lip breathing. Barrel chest, hyperinflation; percussion bilateral hyperresonance. Auscultation: prolonged expiratory phase, widespread expiratory wheeze, coarse crackles bilateral bases right > left, no pleural rub. JVP not elevated; no peripheral oedema; no cyanosis.`,
    labs: `ABG (on 28% O2): pH 7.32, PaO2 8.1 kPa, PaCO2 6.9 kPa, HCO3 26 mmol/L (type II respiratory failure with partial metabolic compensation)
WBC 14.2 × 10⁹/L (neutrophilia 11.8), CRP 87 mg/L, PCT 0.8 ng/mL
Blood cultures ×2 pending; sputum sent for MC&S
BNP 210 pg/mL (mildly elevated)
Creatinine 1.3 mg/dL (baseline 1.1), eGFR 55 mL/min`,
    radiology: `CXR: Hyperinflated lungs, flattened diaphragms, right lower zone patchy consolidation consistent with infective change. No pleural effusion. No pneumothorax.

ECG: Sinus tachycardia 108 bpm. No acute ischaemic changes. Right axis deviation consistent with COPD.`,
  },

  ctdild: {
    label: "Case 3 · RA-ILD (CTD-ILD)",
    age: "54",
    sex: "female" as const,
    notes: `Chief complaint: Progressive breathlessness and dry cough — 4 months duration.

HPI: Mrs. A.P. is a 54-year-old schoolteacher with a 9-year history of seropositive rheumatoid arthritis (anti-CCP positive 320 U/mL, RF 180 IU/mL), currently on methotrexate 15mg weekly and hydroxychloroquine 200mg BD. Over the past 4 months she has developed insidious-onset exertional dyspnoea now limiting her to slow walking on flat ground (MRC dyspnoea scale 3), accompanied by a persistent dry cough. She denies haemoptysis, fever, or weight loss. No new drug exposures or environmental changes (no birds, no significant mould exposure). She reports her RA joint disease has been reasonably controlled (DAS28 2.8 at last review) but notes increasing morning hand stiffness (~45 minutes). She was started on methotrexate 3 years ago; no prior lung toxicity workup documented.

Past medical history: Seropositive RA (2016), Sjögren's syndrome overlap (dry eyes, positive anti-SSA), hypothyroidism (on levothyroxine 75mcg). No previous lung disease; non-smoker.

Allergies: NSAID-induced gastritis (not a true allergy).

Examination: Temp 36.6°C, HR 84 bpm regular, RR 20/min, SpO2 93% at rest (drops to 87% on 6-minute walk test — test stopped at 3 minutes due to desaturation). BP 128/78 mmHg. RA changes: symmetric MCP/PIP joint swelling bilateral, ulnar deviation, Z-deformity right thumb; no active synovitis. Respiratory: reduced chest expansion bilaterally; velcro-like fine end-inspiratory crackles bilateral bases; no clubbing; no wheeze. No lymphadenopathy; mild sicca features confirmed.`,
    labs: `ANA positive 1:320 (homogeneous), anti-SSA/Ro positive, anti-dsDNA negative
Anti-CCP 320 U/mL, RF 180 IU/mL
CRP 28 mg/L, ESR 54 mm/hr
FBC: Hb 11.8 g/dL (normocytic anaemia of chronic disease), WBC 7.2 × 10⁹/L, Platelets 380
LFTs: ALT 42 IU/L (mildly elevated, likely methotrexate effect); ALP, bilirubin normal
Creatinine 0.9 mg/dL, eGFR >60 mL/min`,
    radiology: `HRCT chest: Bilateral subpleural basal-predominant ground-glass opacities with reticulation; honeycombing absent; no traction bronchiectasis. Radiologist reports pattern consistent with NSIP (nonspecific interstitial pneumonia); UIP pattern less likely. No pleural effusion.

Pulmonary function tests: FVC 61% predicted, FEV1/FVC 0.82 (no obstruction); DLCO 48% predicted — moderately-severely impaired gas transfer; restrictive defect.

Echocardiogram: RVSP 38 mmHg (borderline pulmonary hypertension); preserved LV function; no pericardial effusion.`,
  },
} as const;

type ExampleKey = keyof typeof EXAMPLES;

// ── Component ─────────────────────────────────────────────────────────────────

interface Props {
  onSubmit: (data: ClinicalInput) => void;
  onReset: () => void;
  isLoading: boolean;
}

const inp = "w-full rounded-xl px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-clinical-400 transition-all bg-slate-50 border border-slate-200 hover:border-slate-300 focus:bg-white focus:border-clinical-300";
const lbl = "block text-xs font-semibold text-slate-600 mb-1.5";

export const InputPanel: React.FC<Props> = ({ onSubmit, onReset, isLoading }) => {
  const [notes, setNotes]         = useState("");
  const [labs, setLabs]           = useState("");
  const [radiology, setRadiology] = useState("");
  const [age, setAge]             = useState<string>("");
  const [sex, setSex]             = useState<"" | "male" | "female" | "other">("");
  const [menuOpen, setMenuOpen]   = useState(false);
  const menuRef                   = useRef<HTMLDivElement>(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setMenuOpen(false);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  const loadExample = (key: ExampleKey) => {
    const c = EXAMPLES[key];
    setAge(c.age);
    setSex(c.sex);
    setNotes(c.notes);
    setLabs(c.labs);
    setRadiology(c.radiology);
    setMenuOpen(false);
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

          {/* Load Example dropdown */}
          <div className="relative" ref={menuRef}>
            <button
              type="button"
              onClick={() => setMenuOpen(o => !o)}
              disabled={isLoading}
              className="flex items-center gap-1.5 text-xs font-medium px-3 py-1.5 rounded-lg border border-clinical-200 text-clinical-700 bg-clinical-50 hover:bg-clinical-100 transition-colors disabled:opacity-40"
            >
              <FlaskConical size={12} />
              Load Example
              <ChevronDown size={11} className={`transition-transform ${menuOpen ? "rotate-180" : ""}`} />
            </button>

            {menuOpen && (
              <div
                className="absolute right-0 mt-1.5 w-52 rounded-xl shadow-lg border border-slate-200 bg-white overflow-hidden z-50"
                style={{ top: "100%" }}
              >
                {(Object.keys(EXAMPLES) as ExampleKey[]).map((key, i) => (
                  <button
                    key={key}
                    type="button"
                    onClick={() => loadExample(key)}
                    className={`w-full text-left px-4 py-2.5 text-xs font-medium text-slate-700 hover:bg-clinical-50 hover:text-clinical-700 transition-colors flex items-center gap-2 ${
                      i < Object.keys(EXAMPLES).length - 1 ? "border-b border-slate-100" : ""
                    }`}
                  >
                    <FlaskConical size={11} className="text-clinical-400 shrink-0" />
                    {EXAMPLES[key].label}
                  </button>
                ))}
              </div>
            )}
          </div>

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
