import { useState, useCallback } from "react";
import { analyze } from "../api/client";
import type { ClinicalInput, AnalysisResponse, AnalysisStatus, TabId } from "../types";

export function useAnalysis() {
  const [status, setStatus] = useState<AnalysisStatus>("idle");
  const [result, setResult] = useState<AnalysisResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<TabId>("soap");

  const run = useCallback(async (input: ClinicalInput) => {
    setStatus("loading");
    setResult(null);
    setError(null);

    try {
      const data = await analyze(input);
      setResult(data);
      setStatus("success");
      setActiveTab("soap");
    } catch (err: any) {
      const message =
        err?.response?.data?.detail ||
        err?.message ||
        "Analysis failed. Is the backend running?";
      setError(message);
      setStatus("error");
    }
  }, []);

  const reset = useCallback(() => {
    setStatus("idle");
    setResult(null);
    setError(null);
  }, []);

  return { status, result, error, activeTab, setActiveTab, run, reset };
}
