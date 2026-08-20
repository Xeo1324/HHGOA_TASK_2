"""Corpus and Index Integrity Test Suite for NOVARON (Loop 14).
Validates corpus completeness, metadata preservation, index count alignment, and retrieval sanity.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.ingestion import fixed_chunks, hierarchical_chunks, load_jsonl, sentence_chunks
from app.vector_store import FaissVectorStore

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
CORPUS_PATH = DATA_DIR / "novaron_corpus.jsonl"


def test_corpus_file_exists_and_non_empty():
    assert CORPUS_PATH.exists(), f"Missing corpus file at {CORPUS_PATH}"
    docs = load_jsonl(CORPUS_PATH)
    assert len(docs) >= 1500, f"Expected at least 1500 documents, got {len(docs)}"


def test_corpus_schema_and_uniqueness():
    docs = load_jsonl(CORPUS_PATH)
    seen_passage_ids = set()

    for d in docs:
        pid = d.passage_id
        did = d.document_id
        text = d.text
        lang = d.language

        assert pid, f"Missing passage_id in {d}"
        assert did, f"Missing document_id in {d}"
        valid_langs = {"as", "bn", "gu", "hi", "kn", "ml", "mr", "ne", "or", "pa", "sa", "ta", "te", "ur", "en"}
        assert lang in valid_langs, f"Invalid language {lang} in {pid}"

        assert pid not in seen_passage_ids, f"Duplicate passage_id found: {pid}"
        seen_passage_ids.add(pid)


def test_manifest_and_vector_count_alignment():
    pytest.importorskip("faiss")
    docs = load_jsonl(CORPUS_PATH)

    strategies = {
        "sentence": sentence_chunks(docs),
        "fixed": fixed_chunks(docs),
        "hierarchical": hierarchical_chunks(docs),
    }

    for strat, chunks in strategies.items():
        idx_dir = DATA_DIR / "indexes" / strat
        manifest_file = idx_dir / "manifest.json"
        if not manifest_file.exists():
            pytest.skip(f"Pre-built FAISS index not present at {idx_dir}")
            return

        manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
        store = FaissVectorStore.load(idx_dir)

        # 1. Corpus chunks count equals manifest chunk count
        assert len(chunks) == manifest["chunk_count"], (
            f"Strategy {strat}: chunks ({len(chunks)}) != manifest count ({manifest['chunk_count']})"
        )

        # 2. Manifest chunk count equals FAISS loaded chunks
        assert manifest["chunk_count"] == len(store.chunks), (
            f"Strategy {strat}: manifest count ({manifest['chunk_count']}) != FAISS store chunks ({len(store.chunks)})"
        )

        # 3. Embedding dimension matches 384
        assert store.dimensions == 384, f"Expected 384 dimensions, got {store.dimensions}"


def test_multilingual_semantic_retrieval_hindi():
    from app.main import pipelines

    hindi_pipe = pipelines["sentence"]["hybrid"] if "hybrid" in pipelines["sentence"] else pipelines["sentence"]["dense"]

    # Test Hindi queries map to relevant technical concepts
    queries_to_verify = [
        ("प्रकाश संश्लेषण क्या है?", ["photosynthesis", "science-photosynthesis", "प्रकाश"]),
        ("गुरुत्वाकर्षण क्या है?", ["gravity", "science-gravity", "गुरुत्वाकर्षण"]),
        ("पायथन क्या है?", ["python", "tech-python", "पायथन"]),
        ("कृत्रिम बुद्धिमत्ता क्या है?", ["ai", "tech-ai", "artificial", "बुद्धिमत्ता"]),
    ]

    for q, expected_keywords in queries_to_verify:
        hits = hindi_pipe.retriever.search(q, 3)
        assert len(hits) > 0, f"No hits returned for Hindi query '{q}'"
        top_text = " ".join((h.chunk.text + " " + h.chunk.document_id).lower() for h in hits[:3])
        assert any(kw in top_text for kw in expected_keywords), (
            f"Top hits for '{q}' were not semantically relevant: {[h.chunk.document_id for h in hits[:3]]}"
        )


def test_grounding_refusal_on_unsupported_questions():
    from app.main import pipelines

    pipe = pipelines["sentence"]["dense"]

    impossible_queries = [
        "What is the exact secret recipe for Martian cosmic space cake?",
        "How many invisible purple dragons live inside Mount Olympus?",
        "What was the winning lottery number in the Andromeda galaxy last week?",
        "How do you convert fairy dust into quantum gravity engines?",
        "What is the phone number of the emperor of Atlantis?",
    ]

    for q in impossible_queries:
        res = pipe.run(q)
        assert res.refused is True, f"Expected refusal for impossible query: '{q}'"
        assert len(res.sources) == 0, f"Refused query should have 0 sources, got {len(res.sources)}"
