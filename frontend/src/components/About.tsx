import React from "react";
import {
  FileText, GitBranch, BookOpen, User,
  ChevronDown, Database, Cpu, ArrowRight,
} from "lucide-react";

// ── Shared primitives ────────────────────────────────────────────────────────

const BRAND = "#080345";
const BRAND_LIGHT = "#f0effe";

const Arrow: React.FC<{ vertical?: boolean }> = ({ vertical }) =>
  vertical ? (
    <div className="flex flex-col items-center py-1">
      <div className="w-0.5 h-6 bg-slate-300" />
      <ChevronDown size={14} className="text-slate-400 -mt-1" />
    </div>
  ) : (
    <div className="flex items-center px-1">
      <div className="h-0.5 w-6 bg-slate-300" />
      <ArrowRight size={14} className="text-slate-400 -ml-1" />
    </div>
  );

interface BoxProps {
  icon: React.ElementType;
  label: string;
  sublabel?: string;
  accent?: string;
  dim?: boolean;
}

const Box: React.FC<BoxProps> = ({ icon: Icon, label, sublabel, accent = BRAND, dim }) => (
  <div
    className="flex flex-col items-center gap-2 px-5 py-4 rounded-2xl border text-center select-none"
    style={{
      background: dim ? "#f8fafc" : "#fff",
      border: `1.5px solid ${dim ? "#e2e8f0" : accent + "33"}`,
      minWidth: 160,
    }}
  >
    <div
      className="w-10 h-10 rounded-xl flex items-center justify-center"
      style={{ background: dim ? "#f1f5f9" : accent + "15" }}
    >
      <Icon size={20} style={{ color: dim ? "#94a3b8" : accent }} />
    </div>
    <div>
      <p className="text-sm font-semibold" style={{ color: dim ? "#94a3b8" : "#1e293b" }}>{label}</p>
      {sublabel && <p className="text-[11px] text-slate-400 mt-0.5 leading-tight">{sublabel}</p>}
    </div>
  </div>
);

const AgentBadge: React.FC<{ n: string; label: string; icon: React.ElementType; sub: string }> = ({
  n, label, icon: Icon, sub,
}) => (
  <div
    className="flex flex-col items-center gap-2 px-6 py-5 rounded-2xl text-center"
    style={{ background: "#fff", border: `1.5px solid ${BRAND}22`, minWidth: 180 }}
  >
    <span
      className="text-[10px] font-bold uppercase tracking-widest px-2 py-0.5 rounded-full"
      style={{ background: BRAND, color: "#fff" }}
    >
      Agent {n}
    </span>
    <div
      className="w-11 h-11 rounded-xl flex items-center justify-center"
      style={{ background: BRAND_LIGHT }}
    >
      <Icon size={22} style={{ color: BRAND }} />
    </div>
    <div>
      <p className="text-sm font-bold text-slate-800">{label}</p>
      <p className="text-[11px] text-slate-400 mt-0.5 leading-snug max-w-[160px]">{sub}</p>
    </div>
  </div>
);

// ── Stat pill ─────────────────────────────────────────────────────────────────

const Pill: React.FC<{ label: string; value: string }> = ({ label, value }) => (
  <div className="flex flex-col items-center gap-0.5 px-5 py-3 rounded-xl"
    style={{ background: BRAND_LIGHT, border: `1px solid ${BRAND}22` }}>
    <span className="text-lg font-extrabold" style={{ color: BRAND }}>{value}</span>
    <span className="text-[11px] text-slate-500 font-medium">{label}</span>
  </div>
);

// ── Main component ────────────────────────────────────────────────────────────

export const About: React.FC = () => (
  <div className="max-w-[900px] mx-auto px-6 py-10 flex flex-col gap-12">

    {/* ── Hero ── */}
    <div className="text-center flex flex-col items-center gap-3">
      <div
        className="w-14 h-14 rounded-2xl flex items-center justify-center mb-1"
        style={{ background: BRAND }}
      >
        <Cpu size={28} className="text-white" />
      </div>
      <h2 className="text-2xl font-extrabold" style={{ color: BRAND }}>How MedAssist-Edge Works</h2>
      <p className="text-sm text-slate-500 max-w-lg leading-relaxed">
        A fully offline, 4-agent AI pipeline that transforms raw clinical notes into structured
        decision support — nothing leaves your machine.
      </p>

      {/* Stats row */}
      <div className="flex gap-3 mt-2 flex-wrap justify-center">
        <Pill value="4" label="AI Agents" />
        <Pill value="100%" label="Offline" />
        <Pill value="MedGemma" label="Model" />
        <Pill value="FAISS" label="Vector Store" />
      </div>
    </div>

    {/* ── Pipeline diagram ── */}
    <div
      className="rounded-3xl px-8 py-8 flex flex-col items-center gap-0"
      style={{ background: "#f8fafc", border: "1px solid #e2e8f0" }}
    >
      <p className="text-[11px] font-bold uppercase tracking-widest text-slate-400 mb-5">Pipeline</p>

      {/* Step 0 — Input */}
      <div className="flex items-center gap-3">
        <Box icon={FileText}   label="Clinical Notes" sublabel="HPI · ROS · Exam" dim />
        <Arrow />
        <Box icon={Database}   label="Lab Results"    sublabel="optional" dim />
        <Arrow />
        <Box icon={FileText}   label="Radiology"      sublabel="optional" dim />
      </div>

      {/* Down arrow */}
      <Arrow vertical />

      {/* Step 1 — SOAP */}
      <AgentBadge n="1" icon={FileText} label="SOAP Structuring" sub="Converts raw notes into Subjective · Objective · Assessment · Plan" />

      <Arrow vertical />

      {/* Step 2 — DDx */}
      <AgentBadge n="2" icon={GitBranch} label="Differential Diagnosis" sub="Ranks up to 5 possible conditions with supporting & against evidence" />

      <Arrow vertical />

      {/* Step 3 + 4 — concurrent */}
      <div
        className="flex items-stretch gap-4 w-full justify-center"
        style={{ position: "relative" }}
      >
        {/* left line */}
        <div className="flex flex-col items-center">
          <div className="flex-1 w-0.5 bg-slate-300" style={{ minHeight: 24 }} />
        </div>

        <div className="flex gap-6">
          <div className="flex flex-col items-center gap-0">
            <Arrow vertical />
            <AgentBadge n="3" icon={BookOpen} label="Guidelines RAG" sub="FAISS vector search + rule-based parser. No LLM — instant." />
          </div>

          {/* divider */}
          <div className="flex items-center">
            <div className="h-full w-px bg-slate-200" style={{ minHeight: 80 }} />
          </div>

          <div className="flex flex-col items-center gap-0">
            <Arrow vertical />
            <AgentBadge n="4" icon={User} label="Patient Summary" sub="Plain-language explanation at 6th-grade reading level." />
          </div>
        </div>
      </div>

      {/* Concurrent label */}
      <p className="text-[10px] font-semibold text-slate-400 mt-2 mb-1 tracking-wide">
        ↑ Agents 3 & 4 run concurrently
      </p>

      <Arrow vertical />

      {/* Output */}
      <div
        className="flex items-center gap-3 px-6 py-4 rounded-2xl text-center"
        style={{ background: BRAND, minWidth: 300 }}
      >
        <FileText size={20} className="text-white shrink-0" />
        <div className="text-left">
          <p className="text-sm font-bold text-white">Clinical Report</p>
          <p className="text-[11px] text-white/70">SOAP · DDx · Guidelines · Patient Summary</p>
        </div>
      </div>
    </div>

    {/* ── Tech stack ── */}
    <div className="grid grid-cols-2 gap-4">
      {[
        { label: "Inference", value: "MedGemma 1.5 4B IT", sub: "Google · bfloat16 GPU · greedy decoding" },
        { label: "Embeddings", value: "all-MiniLM-L6-v2", sub: "sentence-transformers · CPU-fast · 384-dim" },
        { label: "Vector Store", value: "FAISS", sub: "Local flat-index · top-4 chunk retrieval" },
        { label: "API", value: "FastAPI · uvicorn", sub: "Single worker · 127.0.0.1 only · no network" },
      ].map(({ label, value, sub }) => (
        <div key={label}
          className="px-5 py-4 rounded-2xl"
          style={{ background: "#fff", border: "1px solid #e2e8f0" }}
        >
          <p className="text-[10px] font-bold uppercase tracking-widest text-slate-400 mb-1">{label}</p>
          <p className="text-sm font-bold text-slate-800">{value}</p>
          <p className="text-[11px] text-slate-400 mt-0.5">{sub}</p>
        </div>
      ))}
    </div>

    {/* ── Privacy note ── */}
    <div
      className="flex items-start gap-3 px-5 py-4 rounded-2xl"
      style={{ background: BRAND_LIGHT, border: `1px solid ${BRAND}22` }}
    >
      <Cpu size={16} className="shrink-0 mt-0.5" style={{ color: BRAND }} />
      <p className="text-xs text-slate-600 leading-relaxed">
        <span className="font-semibold" style={{ color: BRAND }}>Fully air-gapped.</span>{" "}
        All inference runs locally on your hardware. No patient data is transmitted to any external
        server, cloud API, or third-party service at any point. Audit logs are written to disk only.
      </p>
    </div>

  </div>
);
