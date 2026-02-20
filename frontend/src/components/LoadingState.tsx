import React, { useEffect, useState } from "react";
import { FileText, Brain, BookOpen, User } from "lucide-react";

const STEPS = [
  { icon: FileText,  label: "SOAP Structuring",       sub: "Organising clinical notes into structured format…",  color: "#2563eb", bg: "#eff6ff" },
  { icon: Brain,     label: "Differential Diagnosis",  sub: "Reasoning over findings to generate DDx list…",      color: "#7c3aed", bg: "#f5f3ff" },
  { icon: BookOpen,  label: "Guideline Retrieval",     sub: "Searching local clinical guideline index (RAG)…",    color: "#0d9488", bg: "#f0fdfa" },
  { icon: User,      label: "Patient Explanation",     sub: "Generating plain-language summary for patient…",     color: "#d97706", bg: "#fffbeb" },
];

export const LoadingState: React.FC = () => {
  const [active, setActive] = useState(0);

  useEffect(() => {
    const id = setInterval(() => setActive(a => (a + 1) % STEPS.length), 2800);
    return () => clearInterval(id);
  }, []);

  return (
    <div className="flex flex-col items-center justify-center flex-1 py-14 gap-8 px-6">
      {/* Spinner */}
      <div className="relative">
        <div className="w-16 h-16 rounded-full border-4 border-clinical-100 border-t-clinical-500 animate-spin" />
        <div className="absolute inset-0 flex items-center justify-center">
          <Brain size={20} className="text-clinical-400" />
        </div>
      </div>

      <div className="text-center">
        <p className="font-bold text-slate-700 text-lg">Running 4-Agent Pipeline</p>
        <p className="text-xs text-slate-400 mt-1">All inference runs locally · No data leaves this machine</p>
      </div>

      {/* Steps */}
      <div className="w-full max-w-md flex flex-col gap-2.5">
        {STEPS.map((step, i) => {
          const Icon = step.icon;
          const isActive = active === i;
          const isDone   = i < active;
          return (
            <div
              key={i}
              className="flex items-center gap-3 rounded-xl px-4 py-3 transition-all duration-500"
              style={{
                background:  isActive ? step.bg : isDone ? "#f8fafc" : "white",
                border:      `1px solid ${isActive ? step.color + "40" : "#e2e8f0"}`,
                opacity:     isDone ? 0.55 : 1,
                boxShadow:   isActive ? `0 2px 12px ${step.color}20` : "none",
              }}
            >
              <div className="w-8 h-8 rounded-lg flex items-center justify-center shrink-0"
                style={{ background: isActive ? step.color : isDone ? "#e2e8f0" : "#f1f5f9" }}>
                <Icon size={14} style={{ color: isActive ? "white" : isDone ? "#94a3b8" : "#94a3b8" }} />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-xs font-semibold text-slate-700">{step.label}</p>
                <p className="text-xs text-slate-400 truncate">{step.sub}</p>
              </div>
              {isActive && (
                <div className="flex gap-0.5 shrink-0">
                  {[0,1,2].map(d => (
                    <div key={d} className="w-1 h-1 rounded-full"
                      style={{ background: step.color, animation: `pulse 1s ease-in-out ${d*0.25}s infinite` }} />
                  ))}
                </div>
              )}
              {isDone && (
                <span className="text-xs font-medium shrink-0" style={{ color: step.color }}>✓</span>
              )}
            </div>
          );
        })}
      </div>

      <p className="text-xs text-slate-400 italic text-center max-w-xs">
        GPU inference ~30 s · CPU inference may take 2–5 min
      </p>
    </div>
  );
};
