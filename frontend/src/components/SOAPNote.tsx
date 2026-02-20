import React from "react";
import type { SOAPNote as SOAPNoteType } from "../types";
import { CopyButton } from "./CopyButton";
import { MessageSquare, Activity, Brain, ClipboardList } from "lucide-react";

interface Props {
  soap: SOAPNoteType;
}

interface SectionConfig {
  key: keyof SOAPNoteType;
  label: string;
  icon: React.ElementType;
  accent: string;
  bg: string;
  iconColor: string;
  labelColor: string;
}

const SECTIONS: SectionConfig[] = [
  {
    key: "subjective",
    label: "S — Subjective",
    icon: MessageSquare,
    accent: "#2563eb",
    bg: "#eff6ff",
    iconColor: "#2563eb",
    labelColor: "#1e40af",
  },
  {
    key: "objective",
    label: "O — Objective",
    icon: Activity,
    accent: "#0d9488",
    bg: "#f0fdfa",
    iconColor: "#0d9488",
    labelColor: "#0f766e",
  },
  {
    key: "assessment",
    label: "A — Assessment",
    icon: Brain,
    accent: "#d97706",
    bg: "#fffbeb",
    iconColor: "#d97706",
    labelColor: "#b45309",
  },
  {
    key: "plan_suggestions",
    label: "P — Plan",
    icon: ClipboardList,
    accent: "#7c3aed",
    bg: "#f5f3ff",
    iconColor: "#7c3aed",
    labelColor: "#6d28d9",
  },
];

const Section: React.FC<{ cfg: SectionConfig; content: string }> = ({ cfg, content }) => {
  const Icon = cfg.icon;
  return (
    <div
      className="rounded-xl p-4 transition-shadow hover:shadow-md"
      style={{
        background: cfg.bg,
        borderLeft: `4px solid ${cfg.accent}`,
        border: `1px solid ${cfg.accent}22`,
        borderLeftWidth: "4px",
        borderLeftColor: cfg.accent,
      }}
    >
      <div className="flex items-center gap-2 mb-2.5">
        <div
          className="w-6 h-6 rounded-md flex items-center justify-center shrink-0"
          style={{ background: cfg.accent + "20" }}
        >
          <Icon size={13} style={{ color: cfg.iconColor }} />
        </div>
        <h4
          className="text-xs font-bold uppercase tracking-wider"
          style={{ color: cfg.labelColor }}
        >
          {cfg.label}
        </h4>
      </div>
      <p className="text-sm text-slate-700 whitespace-pre-wrap leading-relaxed font-mono text-[13px]">
        {content}
      </p>
    </div>
  );
};

export const SOAPNote: React.FC<Props> = ({ soap }) => {
  const fullText = [
    `SUBJECTIVE:\n${soap.subjective}`,
    `\nOBJECTIVE:\n${soap.objective}`,
    `\nASSESSMENT:\n${soap.assessment}`,
    `\nPLAN SUGGESTIONS:\n${soap.plan_suggestions}`,
  ].join("\n");

  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-center justify-between mb-1">
        <p className="text-xs text-slate-400 italic">
          AI-structured from your clinical notes · Verify before use
        </p>
        <CopyButton text={fullText} label="Copy SOAP" />
      </div>

      {SECTIONS.map((cfg) => (
        <Section key={cfg.key} cfg={cfg} content={String(soap[cfg.key] ?? "")} />
      ))}
    </div>
  );
};
