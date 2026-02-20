import React from "react";
import type { DifferentialDiagnosis, DiagnosisEntry } from "../types";
import { CopyButton } from "./CopyButton";
import { CheckCircle, XCircle, Lightbulb } from "lucide-react";

interface Props {
  ddx: DifferentialDiagnosis;
}

const LIKELIHOOD: Record<string, { bg: string; border: string; text: string; dot: string }> = {
  High:     { bg: "#fef2f2", border: "#ef4444", text: "#b91c1c", dot: "#ef4444" },
  Moderate: { bg: "#fffbeb", border: "#f59e0b", text: "#b45309", dot: "#f59e0b" },
  Low:      { bg: "#f0fdf4", border: "#22c55e", text: "#15803d", dot: "#22c55e" },
};

const RANK_COLORS = ["#2563eb", "#7c3aed", "#0d9488", "#d97706", "#dc2626"];

const DiagnosisCard: React.FC<{ entry: DiagnosisEntry }> = ({ entry }) => {
  const lh = LIKELIHOOD[entry.likelihood] ?? LIKELIHOOD.Low;
  const rankColor = RANK_COLORS[(entry.rank - 1) % RANK_COLORS.length];

  return (
    <div
      className="rounded-xl p-4 transition-all duration-200 hover:shadow-md"
      style={{
        background: "white",
        border: "1px solid #e2e8f0",
        boxShadow: "0 1px 3px rgba(0,0,0,0.04)",
      }}
    >
      {/* Header */}
      <div className="flex items-start justify-between gap-3 mb-3">
        <div className="flex items-center gap-2.5">
          <div
            className="w-7 h-7 rounded-lg flex items-center justify-center shrink-0 text-white text-xs font-bold"
            style={{ background: rankColor }}
          >
            {entry.rank}
          </div>
          <h4 className="font-semibold text-slate-800 text-sm leading-snug">{entry.condition}</h4>
        </div>
        <span
          className="text-xs font-semibold px-2.5 py-0.5 rounded-full shrink-0 flex items-center gap-1"
          style={{
            background: lh.bg,
            border: `1px solid ${lh.border}`,
            color: lh.text,
          }}
        >
          <span className="w-1.5 h-1.5 rounded-full" style={{ background: lh.dot }} />
          {entry.likelihood}
        </span>
      </div>

      {/* For / Against */}
      <div className="grid grid-cols-2 gap-3">
        <div className="rounded-lg p-3" style={{ background: "#f0fdf4" }}>
          <p className="text-[10px] font-bold uppercase tracking-wider text-green-700 mb-1.5 flex items-center gap-1">
            <CheckCircle size={10} /> Supporting
          </p>
          <p className="text-xs text-slate-600 leading-relaxed">
            {entry.supporting_features || "—"}
          </p>
        </div>
        <div className="rounded-lg p-3" style={{ background: "#fef2f2" }}>
          <p className="text-[10px] font-bold uppercase tracking-wider text-red-700 mb-1.5 flex items-center gap-1">
            <XCircle size={10} /> Against
          </p>
          <p className="text-xs text-slate-600 leading-relaxed">
            {entry.against_features || "—"}
          </p>
        </div>
      </div>
    </div>
  );
};

export const DifferentialDx: React.FC<Props> = ({ ddx }) => {
  const fullText = ddx.diagnoses
    .map(
      (d) =>
        `${d.rank}. ${d.condition} (${d.likelihood})\n  For: ${d.supporting_features}\n  Against: ${d.against_features}`
    )
    .join("\n\n");

  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-center justify-between mb-1">
        <p className="text-xs text-slate-400 italic max-w-md">
          Differential considerations only — not confirmed diagnoses · Clinician review required
        </p>
        <CopyButton text={fullText} label="Copy DDx" />
      </div>

      {ddx.diagnoses.length === 0 ? (
        <p className="text-sm text-slate-400 italic py-6 text-center">
          No differential entries generated.
        </p>
      ) : (
        ddx.diagnoses.map((entry) => (
          <DiagnosisCard key={entry.rank} entry={entry} />
        ))
      )}

      {ddx.reasoning_summary && (
        <div
          className="mt-1 rounded-xl p-4"
          style={{
            background: "linear-gradient(135deg, #eff6ff, #f5f3ff)",
            border: "1px solid #bfdbfe",
          }}
        >
          <p className="text-[10px] font-bold uppercase tracking-wider text-clinical-700 mb-2 flex items-center gap-1.5">
            <Lightbulb size={11} /> Clinical Reasoning Summary
          </p>
          <p className="text-sm text-slate-700 leading-relaxed">{ddx.reasoning_summary}</p>
        </div>
      )}
    </div>
  );
};
