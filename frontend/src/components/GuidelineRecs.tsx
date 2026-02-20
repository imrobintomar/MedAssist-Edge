import React from "react";
import type { GuidelineRecommendation, GuidelineEntry } from "../types";
import { CopyButton } from "./CopyButton";
import { BookOpen, FlaskConical, Pill, BarChart3, CalendarClock, FileQuestion } from "lucide-react";

interface Props {
  guidelines: GuidelineRecommendation;
}

const CATEGORY_CONFIG: Record<string, { icon: React.ElementType; bg: string; border: string; iconColor: string; labelColor: string }> = {
  Workup:      { icon: FlaskConical,  bg: "#f0fdfa", border: "#0d9488", iconColor: "#0d9488", labelColor: "#0f766e" },
  Management:  { icon: Pill,          bg: "#eff6ff", border: "#2563eb", iconColor: "#2563eb", labelColor: "#1e40af" },
  Monitoring:  { icon: BarChart3,     bg: "#f5f3ff", border: "#7c3aed", iconColor: "#7c3aed", labelColor: "#6d28d9" },
  "Follow-up": { icon: CalendarClock, bg: "#f0fdf4", border: "#16a34a", iconColor: "#16a34a", labelColor: "#15803d" },
};

const CONFIDENCE_CONFIG: Record<string, { bg: string; border: string; text: string }> = {
  Direct:         { bg: "#f0fdf4", border: "#22c55e", text: "#15803d" },
  Inferred:       { bg: "#fffbeb", border: "#f59e0b", text: "#b45309" },
  "Low-evidence": { bg: "#f8fafc", border: "#94a3b8", text: "#475569" },
};

const RecCard: React.FC<{ rec: GuidelineEntry }> = ({ rec }) => {
  const cat = CATEGORY_CONFIG[rec.category] ?? {
    icon: FileQuestion, bg: "#f8fafc", border: "#94a3b8", iconColor: "#64748b", labelColor: "#475569",
  };
  const conf = CONFIDENCE_CONFIG[rec.confidence] ?? CONFIDENCE_CONFIG["Low-evidence"];
  const CatIcon = cat.icon;

  return (
    <div
      className="rounded-xl overflow-hidden transition-all duration-200 hover:shadow-md"
      style={{ border: `1px solid ${cat.border}30`, background: "white" }}
    >
      {/* Category header strip */}
      <div
        className="flex items-center justify-between px-4 py-2.5"
        style={{ background: cat.bg, borderBottom: `1px solid ${cat.border}30` }}
      >
        <span
          className="text-[10px] font-bold uppercase tracking-wider flex items-center gap-1.5"
          style={{ color: cat.labelColor }}
        >
          <CatIcon size={11} style={{ color: cat.iconColor }} />
          {rec.category}
        </span>
        <span
          className="text-[10px] font-semibold px-2 py-0.5 rounded-full"
          style={{ background: conf.bg, border: `1px solid ${conf.border}`, color: conf.text }}
        >
          {rec.confidence}
        </span>
      </div>

      {/* Body */}
      <div className="px-4 py-3">
        <p className="text-sm text-slate-700 leading-relaxed mb-2.5">{rec.recommendation}</p>
        <div className="flex items-center gap-1.5 text-xs text-slate-400">
          <BookOpen size={11} />
          <span className="italic">{rec.source}</span>
        </div>
      </div>
    </div>
  );
};

export const GuidelineRecs: React.FC<Props> = ({ guidelines }) => {
  const fullText = guidelines.recommendations
    .map((r) => `[${r.category}] ${r.recommendation}\nSource: ${r.source}`)
    .join("\n\n");

  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-center justify-between mb-1">
        <p className="text-xs text-slate-400 italic">
          Retrieved from local guideline index
          {guidelines.retrieved_sources.length > 0 && (
            <> · {guidelines.retrieved_sources.slice(0, 2).join(", ")}
            {guidelines.retrieved_sources.length > 2 && " …"}</>
          )}
        </p>
        <CopyButton text={fullText} label="Copy Recs" />
      </div>

      {guidelines.recommendations.length === 0 ? (
        <div
          className="py-8 px-6 text-center rounded-xl"
          style={{ background: "#f8fafc", border: "1px dashed #cbd5e1" }}
        >
          <BookOpen size={28} className="text-slate-300 mx-auto mb-3" />
          <p className="text-sm text-slate-500 font-medium">No guideline recommendations retrieved</p>
          <p className="text-xs text-slate-400 mt-1">
            Add guidelines to the <code className="bg-slate-100 px-1 rounded">guidelines/</code> directory and run{" "}
            <code className="bg-slate-100 px-1 rounded">setup_rag.py</code>
          </p>
        </div>
      ) : (
        guidelines.recommendations.map((rec, i) => (
          <RecCard key={i} rec={rec} />
        ))
      )}
    </div>
  );
};
