"""
RAG Pipeline Tests
───────────────────
Tests ingestion and retrieval WITHOUT a running model.
Requires: faiss-cpu, sentence-transformers (both small, CPU-only)

Run:
    pytest tests/test_rag.py -v
"""

import sys
import json
import pytest
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


@pytest.fixture(scope="module")
def tmp_dirs():
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        yield {
            "guidelines": root / "guidelines",
            "vector_store": root / "vector_store",
            "embed_cache": root / "embed_cache",
        }


@pytest.fixture(scope="module")
def indexed_store(tmp_dirs):
    """Build a small FAISS index from sample text, return paths + retriever."""
    from rag.ingestion import ingest

    # Write two small guideline files
    tmp_dirs["guidelines"].mkdir(parents=True)
    (tmp_dirs["guidelines"] / "ild.txt").write_text(
        "Idiopathic Pulmonary Fibrosis diagnosis requires HRCT showing honeycombing. "
        "Antifibrotic therapy with nintedanib or pirfenidone slows FVC decline. "
        "Supplemental oxygen recommended if SpO2 below 88 percent."
    )
    (tmp_dirs["guidelines"] / "pneumonia.txt").write_text(
        "Community Acquired Pneumonia diagnosis: new infiltrate plus fever or cough. "
        "CURB65 score guides hospitalisation decision. "
        "Blood cultures before antibiotics in severe pneumonia."
    )

    n = ingest(
        guidelines_dir=tmp_dirs["guidelines"],
        vector_store_dir=tmp_dirs["vector_store"],
        embed_model_name=EMBED_MODEL,
        embed_cache_dir=tmp_dirs["embed_cache"],
        chunk_size=200,
        overlap=20,
    )
    assert n > 0, "Ingestion produced zero chunks"
    return tmp_dirs


class TestIngestion:
    def test_index_file_created(self, indexed_store):
        assert (indexed_store["vector_store"] / "guidelines.faiss").exists()

    def test_metadata_file_created(self, indexed_store):
        meta_path = indexed_store["vector_store"] / "metadata.json"
        assert meta_path.exists()
        with open(meta_path) as f:
            meta = json.load(f)
        assert len(meta) > 0
        assert "source" in meta[0]
        assert "text" in meta[0]

    def test_chunks_have_source_attribution(self, indexed_store):
        with open(indexed_store["vector_store"] / "metadata.json") as f:
            meta = json.load(f)
        sources = {m["source"] for m in meta}
        assert "ild.txt" in sources
        assert "pneumonia.txt" in sources


class TestRetrieval:
    def test_retriever_loads(self, indexed_store):
        from rag.retrieval import GuidelineRetriever
        r = GuidelineRetriever(
            vector_store_dir=indexed_store["vector_store"],
            embed_model_name=EMBED_MODEL,
            embed_cache_dir=indexed_store["embed_cache"],
            top_k=2,
        )
        r.load()
        assert r.doc_count > 0

    def test_ild_query_returns_ild_chunk(self, indexed_store):
        from rag.retrieval import GuidelineRetriever
        r = GuidelineRetriever(
            vector_store_dir=indexed_store["vector_store"],
            embed_model_name=EMBED_MODEL,
            embed_cache_dir=indexed_store["embed_cache"],
            top_k=2,
        )
        r.load()
        results = r.retrieve("pulmonary fibrosis honeycombing HRCT")
        assert len(results) > 0
        # Top result should come from ild.txt
        assert results[0]["source"] == "ild.txt"

    def test_pneumonia_query_returns_pneumonia_chunk(self, indexed_store):
        from rag.retrieval import GuidelineRetriever
        r = GuidelineRetriever(
            vector_store_dir=indexed_store["vector_store"],
            embed_model_name=EMBED_MODEL,
            embed_cache_dir=indexed_store["embed_cache"],
            top_k=2,
        )
        r.load()
        results = r.retrieve("community acquired pneumonia CURB65 fever cough")
        assert len(results) > 0
        top_sources = [res["source"] for res in results]
        assert "pneumonia.txt" in top_sources

    def test_empty_query_returns_empty(self, indexed_store):
        from rag.retrieval import GuidelineRetriever
        r = GuidelineRetriever(
            vector_store_dir=indexed_store["vector_store"],
            embed_model_name=EMBED_MODEL,
            embed_cache_dir=indexed_store["embed_cache"],
            top_k=2,
        )
        r.load()
        results = r.retrieve("")
        assert results == []

    def test_top_k_respected(self, indexed_store):
        from rag.retrieval import GuidelineRetriever
        r = GuidelineRetriever(
            vector_store_dir=indexed_store["vector_store"],
            embed_model_name=EMBED_MODEL,
            embed_cache_dir=indexed_store["embed_cache"],
            top_k=1,
        )
        r.load()
        results = r.retrieve("lung disease")
        assert len(results) <= 1
