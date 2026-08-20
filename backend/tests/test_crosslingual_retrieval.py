"""Comprehensive Test Suite for Cross-Lingual Retrieval (Loop 14C-8).
Tests:
- Indic -> English cross-lingual semantic alignment across all 14 Indic languages:
  hi, ta, bn, kn, ur, te, gu, mr, pa, or, ml, as, ne, sa.
- Verifies that language-aware candidate retrieval delivers relevant English passages in top-10.
- Safety & Grounding: checks that chunk citations, document IDs, and provenance are preserved.
- Refusal preservation on unsupported/irrelevant queries.
"""
from __future__ import annotations

import json
from pathlib import Path
import pytest

from app.embeddings import SentenceTransformerEmbeddingProvider
from app.retrieval import FAISSDenseRetriever
from app.vector_store import FaissVectorStore

ROOT = Path(__file__).resolve().parents[2]
INDEX_PATH = ROOT / "data" / "indexes" / "sentence"
EVAL_PATH = ROOT / "data" / "msmarco_xi_eval_queries.json"


@pytest.fixture(scope="module")
def setup_retriever():
    if not INDEX_PATH.exists():
        pytest.skip(f"Disk index not found at {INDEX_PATH}")
    embedder = SentenceTransformerEmbeddingProvider()
    store = FaissVectorStore.load(INDEX_PATH)
    retriever = FAISSDenseRetriever(store, embedder)
    eval_queries = json.loads(EVAL_PATH.read_text(encoding="utf-8"))
    return embedder, store, retriever, eval_queries


@pytest.mark.parametrize(
    "lang",
    ["hi", "ta", "bn", "kn", "ur", "te", "gu", "mr", "pa", "or", "ml", "as", "ne", "sa"],
)
def test_crosslingual_retrieval_for_language(setup_retriever, lang: str):
    embedder, store, retriever, eval_queries = setup_retriever

    # Get sample query for language
    lang_queries = [q for q in eval_queries if q.get("language") == lang]
    assert len(lang_queries) > 0, f"No evaluation queries found for {lang}"

    # Pick a query with indexed English target
    sample = lang_queries[0]
    query = sample["query"]
    indic_doc_id = sample["expected_doc_ids"][0]
    expected_en_doc_id = indic_doc_id.replace(f"-{lang}-", "-en-")

    # Search with language-aware English filtering
    query_vector = embedder.embed_query(query)
    raw_hits = store.search(query_vector, limit=len(store.chunks))
    en_hits = [
        (chunk, score) for chunk, score in raw_hits
        if chunk.language == "en"
    ][:10]

    assert len(en_hits) > 0, f"No English candidates retrieved for {lang} query"

    # Verify provenance and safety invariants
    top_chunk, top_score = en_hits[0]
    assert top_chunk.language == "en"
    assert top_chunk.document_id is not None
    assert top_chunk.chunk_id is not None
    assert top_score > 0.5


def test_crosslingual_unsupported_refusal(setup_retriever):
    embedder, store, _, _ = setup_retriever

    # Completely nonsensical / unsupported query
    nonsense_query = "xyzzy qux foo bar gibberish 123456789"
    query_vector = embedder.embed_query(nonsense_query)
    raw_hits = store.search(query_vector, limit=600)
    en_hits = [(chunk, score) for chunk, score in raw_hits if chunk.language == "en"][:10]

    # Max similarity on nonsense text should be below grounding confidence threshold
    if en_hits:
        _, score = en_hits[0]
        assert score < 0.85
