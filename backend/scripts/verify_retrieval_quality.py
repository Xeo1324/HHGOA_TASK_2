"""Verification of Retrieval Quality and Guardrails post-optimization."""
import json
import time
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

from app.ingestion import load_jsonl, sentence_chunks
from app.retrieval import BM25Retriever, HybridRetriever, HashingDenseRetriever, HashingEmbedder, TransparentReranker
from app.pipeline import RAGPipeline, ExtractiveGroundedGenerator, REFUSAL

passages = load_jsonl(ROOT / "data" / "novaron_corpus.jsonl")
chunks = sentence_chunks(passages)
embedder = HashingEmbedder()
dense = HashingDenseRetriever(chunks, embedder)
bm25 = BM25Retriever(chunks)
hybrid = HybridRetriever(dense, bm25)
reranker = TransparentReranker()
generator = ExtractiveGroundedGenerator()
pipeline = RAGPipeline(hybrid, reranker, generator, minimum_score=0.01)

eval_queries = json.loads((ROOT / "data" / "msmarco_xi_eval_queries.json").read_text(encoding="utf-8"))
total = len(eval_queries)

recall_1 = 0
recall_5 = 0
recall_10 = 0
mrr_sum = 0.0

for eq in eval_queries:
    q_text = eq["query"]
    expected_docs = eq.get("expected_doc_ids", [])
    if not expected_docs:
        continue

    res = pipeline.run(q_text, retrieval_limit=10, answer_limit=10)
    retrieved_doc_ids = [h.chunk.document_id for h in res.sources]

    h1 = any(any(exp in d for exp in expected_docs) for d in retrieved_doc_ids[:1])
    h5 = any(any(exp in d for exp in expected_docs) for d in retrieved_doc_ids[:5])
    h10 = any(any(exp in d for exp in expected_docs) for d in retrieved_doc_ids[:10])

    if h1:
        recall_1 += 1
    if h5:
        recall_5 += 1
    if h10:
        recall_10 += 1

    for rank, doc_id in enumerate(retrieved_doc_ids, 1):
        if any(exp in doc_id for exp in expected_docs):
            mrr_sum += 1.0 / rank
            break

r1 = round(recall_1 / total, 4)
r5 = round(recall_5 / total, 4)
r10 = round(recall_10 / total, 4)
mrr = round(mrr_sum / total, 4)

print("=" * 60)
print("RETRIEVAL QUALITY EVALUATION (300 MSMARCO-XI QUERIES)")
print("=" * 60)
print(f"Recall@1:  {r1:.4f} (Baseline: 0.1400)")
print(f"Recall@5:  {r5:.4f} (Baseline: 0.3567)")
print(f"Recall@10: {r10:.4f} (Baseline: 0.4200)")
print(f"MRR:       {mrr:.4f} (Baseline: 0.2301)")
print("=" * 60)
