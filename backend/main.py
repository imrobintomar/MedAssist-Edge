"""
MedAssist-Edge — FastAPI Backend
─────────────────────────────────
Offline, CPU-first, single-process clinical decision support API.

Startup sequence:
  1. Load MedGemma model into RAM (once, shared by all agents)
  2. Load FAISS vector store for guideline RAG
  3. Register API routes
  4. Accept requests at 127.0.0.1:8000 (localhost only)
"""

from __future__ import annotations
import asyncio
import logging
import sys
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

import uvicorn
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# ── Add backend dir to path ───────────────────────────────────────────────────
sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import (
    MODEL_ID, MODEL_CACHE_DIR, QUANTIZATION, GENERATION_CONFIG, FORCE_CPU,
    API_HOST, API_PORT, DISCLAIMER, VECTOR_STORE_DIR, GUIDELINES_DIR,
    EMBED_MODEL_NAME, EMBED_CACHE_DIR, TOP_K_DOCS,
)
from models.inference import init_engine, get_engine, InferenceEngine
from rag.retrieval import GuidelineRetriever
from schemas import ClinicalInput, AnalysisResponse, ErrorResponse
from middleware.audit_log import init_audit_logger, get_audit_logger
import agents.soap_agent as soap_agent
import agents.ddx_agent as ddx_agent
import agents.guideline_agent as guideline_agent
import agents.patient_agent as patient_agent

AUDIT_LOG_PATH = Path(__file__).resolve().parent.parent / "logs" / "audit.jsonl"

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
# Suppress noisy third-party debug logs
for _noisy in ("httpx", "httpcore", "urllib3", "transformers", "sentence_transformers", "faiss"):
    logging.getLogger(_noisy).setLevel(logging.WARNING)
logger = logging.getLogger("medassist")

# ── Application state ─────────────────────────────────────────────────────────

class AppState:
    engine: Optional[InferenceEngine] = None
    retriever: Optional[GuidelineRetriever] = None

app_state = AppState()


# ── Lifespan (startup / shutdown) ─────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load heavy resources once at startup."""
    logger.info("=== MedAssist-Edge starting up ===")

    # 0. Initialise audit logger
    init_audit_logger(AUDIT_LOG_PATH)
    logger.info("Audit logger ready: %s", AUDIT_LOG_PATH)

    # 1. Load model
    logger.info("Initialising inference engine …")
    app_state.engine = init_engine(
        model_id=MODEL_ID,
        cache_dir=MODEL_CACHE_DIR,
        quantization=QUANTIZATION,
        generation_config=GENERATION_CONFIG,
        force_cpu=FORCE_CPU,
    )
    logger.info("Inference engine ready.")

    # 2. Load RAG retriever (optional — degrades gracefully if index missing)
    try:
        app_state.retriever = GuidelineRetriever(
            vector_store_dir=VECTOR_STORE_DIR,
            embed_model_name=EMBED_MODEL_NAME,
            embed_cache_dir=EMBED_CACHE_DIR,
            top_k=TOP_K_DOCS,
        )
        app_state.retriever.load()
        logger.info("Guideline retriever ready (%d sources).", app_state.retriever.doc_count)
    except Exception as exc:
        logger.warning("Guideline retriever failed to load (%s). RAG disabled.", exc)
        app_state.retriever = None

    logger.info("=== MedAssist-Edge ready — listening on %s:%d ===", API_HOST, API_PORT)
    yield
    logger.info("Shutting down.")


# ── FastAPI app ───────────────────────────────────────────────────────────────

app = FastAPI(
    title="MedAssist-Edge",
    description=(
        "Offline Agentic Clinical Co-Pilot — "
        "CLINICAL DECISION SUPPORT ONLY, not a diagnostic tool."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",          # only accessible locally
    redoc_url="/redoc",
)

# CORS: allow only the local React dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)


# ── Dependency: engine ────────────────────────────────────────────────────────

def get_active_engine() -> InferenceEngine:
    if app_state.engine is None:
        raise HTTPException(503, "Inference engine not ready.")
    return app_state.engine

def get_active_retriever() -> Optional[GuidelineRetriever]:
    return app_state.retriever   # may be None — agents handle gracefully


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {
        "status": "ok",
        "model_loaded": app_state.engine is not None and app_state.engine._loaded,
        "rag_enabled": app_state.retriever is not None,
        "disclaimer": DISCLAIMER,
    }


@app.post(
    "/analyze",
    response_model=AnalysisResponse,
    responses={422: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    summary="Run full agentic clinical analysis pipeline",
)
async def analyze(
    payload: ClinicalInput,
    engine: InferenceEngine = Depends(get_active_engine),
    retriever = Depends(get_active_retriever),
):
    """
    Execute the four-agent pipeline:
      1. SOAP Structuring Agent
      2. Differential Diagnosis Agent
      3. Guideline Retrieval Agent (RAG)
      4. Patient Explanation Agent

    All inference runs locally. No data leaves the machine.
    """
    t_start = time.time()
    logger.info("Analysis request received (notes_len=%d)", len(payload.clinical_notes))

    audit = get_audit_logger()
    record_id = audit.start(payload) if audit else None

    try:
        # ── Agent 1: SOAP ──────────────────────────────────────────────────
        logger.info("[1/4] SOAP Structuring Agent …")
        soap = soap_agent.run(payload, engine)
        logger.info("SOAP done.")

        # ── Agent 2: DDx ───────────────────────────────────────────────────
        logger.info("[2/4] Differential Diagnosis Agent …")
        ddx = ddx_agent.run(soap, payload, engine)
        logger.info("DDx done (%d entries).", len(ddx.diagnoses))

        # ── Agents 3 + 4 concurrently ──────────────────────────────────────
        # Guidelines uses no LLM (rule-based RAG parser) → runs instantly.
        # Patient uses the LLM but doesn't depend on Guidelines output.
        # Run both via asyncio.to_thread so they overlap in wall-clock time.
        logger.info("[3+4/4] Guidelines (RAG) + Patient Explanation — concurrent …")

        guidelines, explanation = await asyncio.gather(
            asyncio.to_thread(guideline_agent.run, soap, ddx, payload, retriever, engine),
            asyncio.to_thread(patient_agent.run, soap, ddx, engine),
        )
        logger.info(
            "Guidelines done (%d recommendations). Patient explanation done.",
            len(guidelines.recommendations),
        )

        elapsed = time.time() - t_start
        logger.info("Pipeline complete in %.1f s", elapsed)

        response = AnalysisResponse(
            soap=soap,
            ddx=ddx,
            guidelines=guidelines,
            patient_explanation=explanation,
            disclaimer=DISCLAIMER,
            model_id=MODEL_ID,
            processing_time_seconds=round(elapsed, 2),
        )

        if audit and record_id:
            audit.finish(record_id, response)

        return response

    except Exception as exc:
        if audit and record_id:
            audit.finish(record_id, error=str(exc)[:200])
        logger.exception("Pipeline error: %s", exc)
        raise HTTPException(
            status_code=500,
            detail=f"Analysis pipeline error: {str(exc)[:200]}",
        )


@app.post(
    "/analyze/soap",
    summary="SOAP Agent only (for incremental UI updates)",
)
async def analyze_soap(
    payload: ClinicalInput,
    engine: InferenceEngine = Depends(get_active_engine),
):
    return soap_agent.run(payload, engine)


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=API_HOST,
        port=API_PORT,
        workers=1,          # single worker — shared model in memory
        log_level="info",
        reload=False,       # no hot-reload in production
        timeout_keep_alive=1800,  # 30 min — CPU float32 inference is slow
    )
