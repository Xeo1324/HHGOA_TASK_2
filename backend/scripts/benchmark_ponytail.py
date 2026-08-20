"""Comprehensive 100-query benchmark for Local RAG Pipeline post-optimization."""
import time
import json
import numpy as np
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

from app.ingestion import load_jsonl, sentence_chunks
from app.retrieval import BM25Retriever, HybridRetriever, HashingDenseRetriever, HashingEmbedder, TransparentReranker
from app.pipeline import RAGPipeline, ExtractiveGroundedGenerator
from app.router import classify_query

print("Loading 12,184-passage corpus...")
t0 = time.perf_counter()
passages = load_jsonl(ROOT / "data" / "novaron_corpus.jsonl")
chunks = sentence_chunks(passages)
print(f"Loaded {len(chunks)} chunks in {(time.perf_counter()-t0)*1000:.1f}ms")

t0 = time.perf_counter()
embedder = HashingEmbedder()
dense = HashingDenseRetriever(chunks, embedder)
bm25 = BM25Retriever(chunks)
hybrid = HybridRetriever(dense, bm25)
reranker = TransparentReranker()
generator = ExtractiveGroundedGenerator()
pipeline = RAGPipeline(hybrid, reranker, generator, minimum_score=0.08)
print(f"Initialized Hybrid RAG pipeline in {(time.perf_counter()-t0)*1000:.1f}ms")

eval_queries = json.loads((ROOT / "data" / "msmarco_xi_eval_queries.json").read_text(encoding="utf-8"))
test_queries = [eq["query"] for eq in eval_queries[:100]]
print(f"Running benchmark on {len(test_queries)} queries...")

router_latencies = []
rag_latencies = []
dense_latencies = []
bm25_latencies = []
rrf_latencies = []

# Warmup
for q in test_queries[:5]:
    classify_query(q)
    pipeline.run(q, answer_limit=5)

for q in test_queries:
    # Router
    t0 = time.perf_counter()
    route = classify_query(q)
    t_route = (time.perf_counter() - t0) * 1000
    router_latencies.append(t_route)

    # Local RAG
    t0 = time.perf_counter()
    result = pipeline.run(q, answer_limit=5, language=route.language)
    t_rag = (time.perf_counter() - t0) * 1000
    rag_latencies.append(t_rag)

def stats(arr):
    s = sorted(arr)
    n = len(s)
    return {
        "mean": sum(s) / n,
        "p50": s[int(n * 0.50)],
        "p70": s[int(n * 0.70)],
        "p90": s[int(n * 0.90)],
        "p100": s[-1],
    }

r_stats = stats(router_latencies)
rag_stats = stats(rag_latencies)

print("\n" + "=" * 70)
print("PONYTAIL BENCHMARK RESULTS (100 QUERIES)")
print("=" * 70)
print(f"Router Latency (Local):")
print(f"  Mean: {r_stats['mean']:.3f} ms | P50: {r_stats['p50']:.3f} ms | P70: {r_stats['p70']:.3f} ms | P100: {r_stats['p100']:.3f} ms")
print(f"\nLocal Hybrid RAG Pipeline Latency (Query -> Dense + BM25 -> RRF -> Grounding -> Output):")
print(f"  Mean: {rag_stats['mean']:.3f} ms | P50: {rag_stats['p50']:.3f} ms | P70: {rag_stats['p70']:.3f} ms | P90: {rag_stats['p90']:.3f} ms | P100: {rag_stats['p100']:.3f} ms")

print("\nCompliance Check (<200 ms Target):")
if rag_stats['p50'] < 200.0:
    print(f"  -> TASK 2 LATENCY REQUIREMENT SATISFIED! (P50 = {rag_stats['p50']:.2f} ms < 200 ms)")
else:
    print(f"  -> TASK 2 LATENCY REQUIREMENT NOT SATISFIED (P50 = {rag_stats['p50']:.2f} ms >= 200 ms)")
print("=" * 70)
