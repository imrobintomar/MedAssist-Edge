"""
MedGemma 1.5 Inference Engine — singleton, CPU-first, quantization-aware.

Key difference from MedGemma 1:
  - Model class : AutoModelForImageTextToText  (NOT AutoModelForCausalLM)
  - Tokenizer   : AutoProcessor                (NOT AutoTokenizer)
  - Chat format : processor.apply_chat_template() with messages dict
  - Native dtype: bfloat16 (GPU) / float32 (CPU)
  - Text-only   : pass messages with {"type":"text"} content only — no image required

Official recommendation (Jan 23 2026 update):
  do_sample=False by default (greedy decoding — deterministic, matches our safety needs).

Design:
  - Single model load at startup; all agents share one InferenceEngine instance.
  - generate() accepts a messages list (OpenAI-style), handles encoding internally.
  - Thread-safe for reads after init (FastAPI single-worker).
"""

from __future__ import annotations
import logging
import time
from pathlib import Path
from typing import List, Optional

import torch
from transformers import AutoProcessor, AutoModelForImageTextToText, BitsAndBytesConfig

logger = logging.getLogger(__name__)


class InferenceEngine:
    """MedGemma 1.5 wrapper: load once, generate many."""

    def __init__(
        self,
        model_id: str,
        cache_dir: Path,
        quantization: str = "int8",
        generation_config: Optional[dict] = None,
        force_cpu: bool = False,
    ) -> None:
        self.model_id = model_id
        self.cache_dir = Path(cache_dir)
        self.quantization = quantization
        self.force_cpu = force_cpu
        self._gen_cfg = generation_config or {}
        self.model = None
        self.processor = None
        self._loaded = False

    # ── Public API ────────────────────────────────────────────────────────────

    def load(self) -> None:
        """Load processor + model. Call once at startup."""
        if self._loaded:
            return

        local_only = self._is_cached()
        logger.info("Loading MedGemma 1.5 processor (local_only=%s) …", local_only)
        proc_kwargs: dict = {"local_files_only": local_only}
        if not self._is_local_dir():
            proc_kwargs["cache_dir"] = str(self.cache_dir)
        self.processor = AutoProcessor.from_pretrained(self.model_id, **proc_kwargs)

        logger.info("Loading MedGemma 1.5 model (quantization=%s) …", self.quantization)
        t0 = time.time()
        self.model = self._load_model(local_only)
        logger.info(
            "Model loaded in %.1f s on device: %s",
            time.time() - t0,
            self.model.device,
        )
        self._loaded = True

    def generate(self, messages: List[dict], max_new_tokens: Optional[int] = None) -> str:
        """
        Run a single text-only generation pass.

        Args:
            messages: List of role/content dicts.
            max_new_tokens: Override the default token budget for this call.
                            Pass per-agent limits from AGENT_MAX_TOKENS in config.

        Returns:
            Assistant response text (stripped, no special tokens).
        """
        if not self._loaded:
            raise RuntimeError("Call load() before generate()")

        # bfloat16 on GPU, float32 on CPU
        dtype = (
            torch.bfloat16
            if self.model.device.type != "cpu"
            else torch.float32
        )

        inputs = self.processor.apply_chat_template(
            messages,
            add_generation_prompt=True,
            tokenize=True,
            return_dict=True,
            return_tensors="pt",
        ).to(self.model.device, dtype=dtype)

        input_len = inputs["input_ids"].shape[-1]
        tokens = max_new_tokens or self._gen_cfg.get("max_new_tokens", 768)

        with torch.inference_mode():
            output_ids = self.model.generate(
                **inputs,
                max_new_tokens=tokens,
                do_sample=self._gen_cfg.get("do_sample", False),
                repetition_penalty=self._gen_cfg.get("repetition_penalty", 1.15),
            )

        # Decode only newly generated tokens (exclude the prompt)
        new_tokens = output_ids[0][input_len:]
        return self.processor.decode(new_tokens, skip_special_tokens=True).strip()

    # ── Private helpers ───────────────────────────────────────────────────────

    def _is_local_dir(self) -> bool:
        """True when model_id is an absolute local path (from --local-dir download)."""
        p = Path(self.model_id)
        return p.is_absolute() and p.exists()

    def _is_cached(self) -> bool:
        if self._is_local_dir():
            return True   # already a local directory
        return self.cache_dir.exists() and any(self.cache_dir.iterdir())

    def _load_model(self, local_only: bool) -> AutoModelForImageTextToText:
        if self._is_local_dir():
            # Downloaded with: hf download ... --local-dir /path/to/weights
            # Pass the path directly; no cache_dir needed
            kwargs: dict = {"local_files_only": True}
        else:
            # Downloaded with snapshot_download (HF cache structure)
            kwargs: dict = {
                "cache_dir": str(self.cache_dir),
                "local_files_only": local_only,
            }

        # GPU path — bfloat16, auto device placement
        if torch.cuda.is_available() and not self.force_cpu:
            kwargs["dtype"] = torch.bfloat16
            kwargs["device_map"] = "auto"
            logger.info("GPU detected — bfloat16 + device_map=auto")

        # CPU + BitsAndBytes quantization
        elif self.quantization in ("int8", "int4") and _bnb_available():
            bnb_cfg = BitsAndBytesConfig(
                load_in_8bit=(self.quantization == "int8"),
                load_in_4bit=(self.quantization == "int4"),
                bnb_4bit_compute_dtype=torch.float32,
            )
            kwargs["quantization_config"] = bnb_cfg
            kwargs["low_cpu_mem_usage"] = True
            logger.info("CPU + BitsAndBytes %s quantization", self.quantization)

        # CPU fallback — full float32
        else:
            kwargs["dtype"] = torch.float32
            kwargs["device_map"] = "cpu"
            kwargs["low_cpu_mem_usage"] = True
            logger.info("CPU float32 (no quantization)")

        return AutoModelForImageTextToText.from_pretrained(self.model_id, **kwargs)


def _bnb_available() -> bool:
    try:
        import bitsandbytes  # noqa: F401
        return True
    except ImportError:
        return False


# ── Module-level singleton ────────────────────────────────────────────────────

_engine: Optional[InferenceEngine] = None


def get_engine() -> InferenceEngine:
    if _engine is None or not _engine._loaded:
        raise RuntimeError("Engine not initialised. Call init_engine() at startup.")
    return _engine


def init_engine(
    model_id: str,
    cache_dir: Path,
    quantization: str = "int8",
    generation_config: Optional[dict] = None,
    force_cpu: bool = False,
) -> InferenceEngine:
    global _engine
    _engine = InferenceEngine(model_id, cache_dir, quantization, generation_config, force_cpu)
    _engine.load()
    return _engine
