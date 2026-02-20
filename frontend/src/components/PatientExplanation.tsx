import React from "react";
import type { PatientExplanation as PatientExplanationType } from "../types";
import { CopyButton } from "./CopyButton";
import { User, ArrowRight, CheckCircle2, Heart } from "lucide-react";

interface Props {
  explanation: PatientExplanationType;
}

export const PatientExplanation: React.FC<Props> = ({ explanation }) => {
  const fullText = [
    explanation.summary,
    "\nKey Points:",
    ...explanation.key_points.map((p) => `• ${p}`),
    `\nNext Steps: ${explanation.next_steps_suggestion}`,
  ].join("\n");

  return (
    <div className="flex flex-col gap-4">
      {/* Header */}
      <div className="flex items-center justify-between mb-1">
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 rounded-full bg-amber-100 flex items-center justify-center">
            <User size={12} className="text-amber-600" />
          </div>
          <p className="text-xs text-slate-400 italic">
            Plain-language summary for the patient · Not a medical document
          </p>
        </div>
        <CopyButton text={fullText} label="Copy for Patient" />
      </div>

      {/* Summary card */}
      <div
        className="rounded-xl p-5"
        style={{
          background: "linear-gradient(135deg, #fffbeb, #fff7ed)",
          border: "1px solid #fcd34d50",
        }}
      >
        <div className="flex items-center gap-2 mb-3">
          <Heart size={14} className="text-amber-500" />
          <span className="text-xs font-bold uppercase tracking-wider text-amber-700">
            Your Health Summary
          </span>
        </div>
        <p className="text-sm text-slate-700 leading-relaxed whitespace-pre-wrap">
          {explanation.summary}
        </p>
      </div>

      {/* Key points */}
      {explanation.key_points.length > 0 && (
        <div>
          <h4 className="text-[10px] font-bold uppercase tracking-wider text-slate-500 mb-2.5 flex items-center gap-1.5">
            <CheckCircle2 size={11} className="text-teal-500" />
            Key Points to Remember
          </h4>
          <div className="flex flex-col gap-2">
            {explanation.key_points.map((point, i) => (
              <div
                key={i}
                className="flex items-start gap-3 rounded-lg p-3 transition-colors"
                style={{ background: "#f8fafc", border: "1px solid #e2e8f0" }}
              >
                <div
                  className="w-5 h-5 rounded-full flex items-center justify-center shrink-0 text-white text-[10px] font-bold mt-0.5"
                  style={{ background: "linear-gradient(135deg, #2563eb, #0d9488)" }}
                >
                  {i + 1}
                </div>
                <p className="text-sm text-slate-700 leading-relaxed">{point}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Next steps */}
      <div
        className="flex items-start gap-3 rounded-xl p-4"
        style={{
          background: "linear-gradient(135deg, #f0fdf4, #f0fdfa)",
          border: "1px solid #86efac50",
        }}
      >
        <div className="w-7 h-7 rounded-lg bg-green-100 flex items-center justify-center shrink-0">
          <ArrowRight size={14} className="text-green-700" />
        </div>
        <div>
          <p className="text-[10px] font-bold uppercase tracking-wider text-green-700 mb-1">
            Next Steps
          </p>
          <p className="text-sm text-green-800 leading-relaxed">
            {explanation.next_steps_suggestion}
          </p>
        </div>
      </div>
    </div>
  );
};
