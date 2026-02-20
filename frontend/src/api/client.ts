import axios from "axios";
import type { ClinicalInput, AnalysisResponse } from "../types";

// Proxied via package.json "proxy" → http://127.0.0.1:8000
const api = axios.create({
  baseURL: "/",
  timeout: 1_800_000,  // 30-minute timeout — CPU float32 inference is slow
  headers: { "Content-Type": "application/json" },
});

export async function analyze(input: ClinicalInput): Promise<AnalysisResponse> {
  const { data } = await api.post<AnalysisResponse>("/analyze", input);
  return data;
}

export async function healthCheck(): Promise<boolean> {
  try {
    const { data } = await api.get("/health");
    return data?.status === "ok";
  } catch {
    return false;
  }
}
