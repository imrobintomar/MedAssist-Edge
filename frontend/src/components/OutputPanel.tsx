import React from "react";
import type { AnalysisResponse, TabId } from "../types";
import { SOAPNote } from "./SOAPNote";
import { DifferentialDx } from "./DifferentialDx";
import { GuidelineRecs } from "./GuidelineRecs";
import { PatientExplanation } from "./PatientExplanation";
import { Clock, Cpu, FileText, GitBranch, BookOpen, User } from "lucide-react";

interface Props {
  result: AnalysisResponse;
  activeTab: TabId;
  onTabChange: (tab: TabId) => void;
}

const TABS: { id: TabId; label: string; icon: React.ElementType; color: string }[] = [
  { id: "soap",       label: "SOAP Note",       icon: FileText,   color: "#2563eb" },
  { id: "ddx",        label: "Differential Dx", icon: GitBranch,  color: "#7c3aed" },
  { id: "guidelines", label: "Guidelines",       icon: BookOpen,   color: "#0d9488" },
  { id: "patient",    label: "Patient Summary",  icon: User,       color: "#d97706" },
];

export const OutputPanel: React.FC<Props> = ({ result, activeTab, onTabChange }) => {
  return (
    <div className="flex flex-col gap-5">

      {/* Meta bar */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="flex items-center gap-1.5 text-xs font-medium px-2.5 py-1 rounded-lg bg-slate-100 text-slate-600 border border-slate-200">
            <Cpu size={11} className="text-clinical-500" />
            {result.model_id.split("/").pop()}
          </span>
        </div>
        <span className="flex items-center gap-1.5 text-xs font-medium px-2.5 py-1 rounded-lg bg-slate-100 text-slate-600 border border-slate-200">
          <Clock size={11} className="text-teal-500" />
          {result.processing_time_seconds}s
        </span>
      </div>

      {/* Tab bar */}
      <div className="flex items-center gap-1.5 p-1 rounded-xl bg-slate-100 border border-slate-200">
        {TABS.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => onTabChange(tab.id)}
              className={`flex items-center gap-1.5 px-3.5 py-2 rounded-lg text-xs font-semibold transition-all duration-200 flex-1 justify-center whitespace-nowrap ${
                isActive
                  ? "tab-active shadow-sm"
                  : "text-slate-500 hover:text-slate-700 hover:bg-white"
              }`}
            >
              <Icon size={12} />
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* Tab content */}
      <div className="output-scroll animate-fade-up">
        {activeTab === "soap"       && <SOAPNote soap={result.soap} />}
        {activeTab === "ddx"        && <DifferentialDx ddx={result.ddx} />}
        {activeTab === "guidelines" && <GuidelineRecs guidelines={result.guidelines} />}
        {activeTab === "patient"    && <PatientExplanation explanation={result.patient_explanation} />}
      </div>
    </div>
  );
};
