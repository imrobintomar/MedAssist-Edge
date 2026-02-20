import React from "react";
import { InputPanel } from "./components/InputPanel";
import { OutputPanel } from "./components/OutputPanel";
import { LoadingState } from "./components/LoadingState";
import { useAnalysis } from "./hooks/useAnalysis";
import { AlertCircle, Activity, Sparkles, RefreshCw, ShieldAlert } from "lucide-react";

export default function App() {
  const { status, result, error, activeTab, setActiveTab, run, reset } = useAnalysis();

  return (
    <div className="min-h-screen" style={{ background: "linear-gradient(160deg, #eef2ff 0%, #f0fdfa 60%, #f8fafc 100%)" }}>

      {/* ── Header ─────────────────────────────────────────────────────── */}
      <header className="header-gradient px-6 py-4 flex items-center justify-between shadow-lg">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-white/20 flex items-center justify-center">
            <Activity className="text-white" size={20} />
          </div>
          <div>
            <h1 className="font-bold text-white text-lg leading-none tracking-tight">
              MedAssist<span className="text-teal-400">-Edge</span>
            </h1>
            <p className="text-xs text-blue-200 leading-none mt-0.5 font-light">
              Offline Agentic Clinical Co-Pilot · Powered by MedGemma
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2 bg-white/10 rounded-full px-4 py-1.5 border border-white/20">
          <span className="w-2 h-2 rounded-full bg-teal-400 animate-pulse" />
          <span className="text-xs text-white/90 font-medium">Running locally — no data leaves this machine</span>
        </div>
      </header>

      {/* ── Main layout ────────────────────────────────────────────────── */}
      <main className="max-w-[1400px] mx-auto px-6 py-5 grid grid-cols-[440px_1fr] gap-5 items-start">

        {/* Left — Input */}
        <div className="glass-card rounded-2xl shadow-card overflow-hidden">
          <div className="h-1 w-full" style={{ background: "linear-gradient(90deg, #2563eb, #14b8a6)" }} />
          <div className="p-6">
            <InputPanel onSubmit={run} onReset={reset} isLoading={status === "loading"} />
          </div>
        </div>

        {/* Right — Output */}
        <div className="glass-card rounded-2xl shadow-card overflow-hidden min-h-[560px] flex flex-col">
          <div className="h-1 w-full" style={{ background: "linear-gradient(90deg, #7c3aed, #2563eb, #14b8a6)" }} />

          {status === "idle" && (
            <div className="flex flex-col items-center justify-center flex-1 py-20 text-center gap-4 px-8">
              <div className="w-16 h-16 rounded-2xl flex items-center justify-center mb-1"
                style={{ background: "linear-gradient(135deg, #eff6ff, #f0fdfa)" }}>
                <Sparkles size={28} className="text-clinical-400" />
              </div>
              <p className="text-lg font-semibold text-slate-700">Ready for analysis</p>
              <p className="text-sm text-slate-400 max-w-xs leading-relaxed">
                Enter clinical notes on the left and click <strong className="text-slate-600">Analyse</strong> to run the 4-agent AI pipeline.
              </p>
              <div className="flex flex-wrap gap-2 mt-2 justify-center">
                {["SOAP Note", "Differential Dx", "Guidelines", "Patient Summary"].map(t => (
                  <span key={t} className="text-xs px-3 py-1 rounded-full bg-clinical-50 text-clinical-600 border border-clinical-100 font-medium">
                    {t}
                  </span>
                ))}
              </div>
            </div>
          )}

          {status === "loading" && <LoadingState />}

          {status === "error" && (
            <div className="flex flex-col items-center justify-center flex-1 py-16 gap-4 px-8">
              <div className="w-14 h-14 rounded-2xl bg-danger-50 flex items-center justify-center">
                <AlertCircle size={28} className="text-danger-500" />
              </div>
              <div className="text-center">
                <p className="font-semibold text-slate-700 text-base">Analysis Failed</p>
                <p className="text-sm text-slate-500 mt-1 max-w-sm leading-relaxed">{error}</p>
              </div>
              <button
                onClick={reset}
                className="flex items-center gap-2 text-sm text-clinical-600 hover:text-clinical-700 font-medium bg-clinical-50 hover:bg-clinical-100 px-4 py-2 rounded-lg transition-colors"
              >
                <RefreshCw size={14} />
                Try again
              </button>
            </div>
          )}

          {status === "success" && result && (
            <div className="p-6 flex-1">
              <OutputPanel result={result} activeTab={activeTab} onTabChange={setActiveTab} />
            </div>
          )}
        </div>
      </main>

      {/* ── Footer disclaimer ───────────────────────────────────────────── */}
      <footer className="mt-4 px-6 pb-6">
        <div className="max-w-[1400px] mx-auto flex items-start gap-3 px-4 py-3 rounded-xl"
          style={{ background: "rgba(255,255,255,0.6)", border: "1px solid #e2e8f0" }}>
          <ShieldAlert size={14} className="shrink-0 mt-0.5 text-amber-600" />
          <p className="text-xs text-slate-500 leading-snug">
            <span className="font-semibold text-slate-700">Clinical Decision Support Only.</span>{" "}
            All AI-generated output must be reviewed by a qualified clinician before any clinical
            action is taken. This system does not diagnose, prescribe, or issue medical orders.
            The clinician retains full clinical responsibility.
          </p>
        </div>
      </footer>
    </div>
  );
}
