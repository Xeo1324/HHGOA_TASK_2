from __future__ import annotations

import hashlib
import heapq
import math
import re
import threading
import time
from collections import Counter, defaultdict
from typing import Any, Iterable, Sequence

from app.domain import Chunk, Embedder, Reranker, Retriever, SearchHit
from app.vector_store import FaissVectorStore


def tokenize(text: str) -> list[str]:
    return re.findall(r"[\w\u0600-\u0D7F]+", text.casefold(), flags=re.UNICODE)


_HASHING_STOP_WORDS = {
    "what", "is", "are", "a", "an", "the", "how", "why", "who", "where", "when",
    "does", "do", "in", "on", "of", "to", "for", "and", "or", "it", "its", "this",
    "that", "with", "by", "from", "at", "as", "be", "was", "were", "been",
    "क्या", "है", "हैं", "के", "की", "का", "में", "से", "पर", "और", "या", "यह", "वह", "को", "ने",
}


class HashingEmbedder(Embedder):
    """Dependency-free baseline with content term weighting."""
    def __init__(self, dimensions: int = 512) -> None:
        self.dimensions = dimensions

    def embed(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        for token in tokenize(text):
            slot = int.from_bytes(hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest(), "big") % self.dimensions
            weight = 0.05 if token in _HASHING_STOP_WORDS else 1.0
            vector[slot] += weight
        norm = math.sqrt(sum(value * value for value in vector))
        return [value / norm for value in vector] if norm else vector


class HashingDenseRetriever:
    def __init__(self, chunks: Iterable[Chunk], embedder: Embedder) -> None:
        self.chunks = list(chunks)
        self.embedder = embedder
        raw_vectors = [embedder.embed(chunk.text) for chunk in self.chunks]
        self._raw_vectors = raw_vectors
        try:
            import numpy as np
            self._np_vectors = np.array(raw_vectors, dtype=np.float32) if raw_vectors else None
        except ImportError:
            self._np_vectors = None

        # Pre-build inverted term map in O(N) at init, avoiding per-query full-corpus re-tokenization
        term_map: dict[str, list[int]] = defaultdict(list)
        for idx, chunk in enumerate(self.chunks):
            for token in set(tokenize(chunk.text)):
                term_map[token].append(idx)
        self._term_to_docs: dict[str, list[int]] = dict(term_map)

    @property
    def vectors(self) -> list[list[float]]:
        return self._raw_vectors

    def search(self, query: str, limit: int) -> list[SearchHit]:
        hits, _ = self.search_with_profile(query, limit)
        return hits

    def search_with_profile(self, query: str, limit: int, language: str | None = None) -> tuple[list[SearchHit], dict[str, float]]:
        started = time.perf_counter()
        query_vector = self.embedder.embed(query)
        embedded_at = time.perf_counter()

        if self._np_vectors is not None and len(self.chunks) > 0:
            import numpy as np
            q_arr = np.array(query_vector, dtype=np.float32)
            scores = np.copy(self._np_vectors @ q_arr)

            # Sub-millisecond inverted-index lexical grounding alignment
            q_tokens = set(tokenize(query)) - _HASHING_STOP_WORDS
            if q_tokens:
                term_weight = 0.50 / len(q_tokens)
                for token in q_tokens:
                    doc_list = self._term_to_docs.get(token)
                    if doc_list:
                        for doc_idx in doc_list:
                            scores[doc_idx] += term_weight

            if len(scores) <= limit:
                top_indices = np.argsort(-scores)
            else:
                top_indices = np.argpartition(-scores, limit)[:limit]
                top_indices = top_indices[np.argsort(-scores[top_indices])]
            hits = [SearchHit(chunk=self.chunks[int(idx)], score=float(scores[int(idx)]), retriever="dense") for idx in top_indices]
        else:
            scored = [(sum(a * b for a, b in zip(query_vector, vector)), chunk) for chunk, vector in zip(self.chunks, self._raw_vectors)]
            hits = [SearchHit(chunk=chunk, score=score, retriever="dense") for score, chunk in sorted(scored, reverse=True, key=lambda pair: pair[0])[:limit]]

        return hits, {"embedding": (embedded_at - started) * 1000, "dense_search": (time.perf_counter() - embedded_at) * 1000}


# v0.1 compatibility alias. New code should name the baseline explicitly.
DenseRetriever = HashingDenseRetriever


class FAISSDenseRetriever:
    def __init__(self, store: FaissVectorStore, embedder: Embedder) -> None:
        self.store = store
        self.embedder = embedder

    def search(self, query: str, limit: int) -> list[SearchHit]:
        hits, _ = self.search_with_profile(query, limit)
        return hits

    def search_with_profile(self, query: str, limit: int) -> tuple[list[SearchHit], dict[str, float]]:
        started = time.perf_counter()
        query_vector = self.embedder.embed_query(query) if hasattr(self.embedder, "embed_query") else self.embedder.embed(query)
        embedded_at = time.perf_counter()
        hits = [SearchHit(chunk=chunk, score=score, retriever="faiss_dense")
                for chunk, score in self.store.search(query_vector, limit)]
        return hits, {"embedding": (embedded_at - started) * 1000, "faiss": (time.perf_counter() - embedded_at) * 1000}


class BM25Retriever:
    def __init__(self, chunks: Iterable[Chunk], k1: float = 1.5, b: float = 0.75) -> None:
        self.chunks = list(chunks)
        self.k1, self.b = k1, b
        total_docs = len(self.chunks)

        self.tokens = [tokenize(chunk.text) for chunk in self.chunks]
        self.lengths = [len(tokens) for tokens in self.tokens]
        self.average_length = sum(self.lengths) / max(total_docs, 1)

        avg_len = max(self.average_length, 1.0)
        self.doc_len_norm = [
            self.k1 * (1.0 - self.b + self.b * (l / avg_len))
            for l in self.lengths
        ]

        self.document_frequency: dict[str, int] = defaultdict(int)
        postings_builder: dict[str, list[tuple[int, int]]] = defaultdict(list)

        for doc_idx, terms in enumerate(self.tokens):
            term_counts = Counter(terms)
            for term, count in term_counts.items():
                postings_builder[term].append((doc_idx, count))
                self.document_frequency[term] += 1

        self.postings: dict[str, list[tuple[int, int]]] = dict(postings_builder)

        self.idf: dict[str, float] = {}
        for term, df in self.document_frequency.items():
            self.idf[term] = math.log(1.0 + (total_docs - df + 0.5) / (df + 0.5))

    def search(self, query: str, limit: int) -> list[SearchHit]:
        hits, _ = self.search_with_profile(query, limit)
        return hits

    def search_with_profile(self, query: str, limit: int) -> tuple[list[SearchHit], dict[str, float]]:
        started = time.perf_counter()
        query_terms = tokenize(query)
        if not query_terms or not self.chunks:
            return [], {"bm25": (time.perf_counter() - started) * 1000}

        query_counts = Counter(query_terms)
        scores: dict[int, float] = defaultdict(float)
        k1_plus_1 = self.k1 + 1.0

        for term, q_freq in query_counts.items():
            idf_val = self.idf.get(term)
            if idf_val is None:
                continue
            term_weight = q_freq * idf_val * k1_plus_1
            postings_list = self.postings.get(term)
            if postings_list is None:
                continue
            for doc_idx, tf in postings_list:
                scores[doc_idx] += term_weight * tf / (tf + self.doc_len_norm[doc_idx])

        if not scores:
            return [], {"bm25": (time.perf_counter() - started) * 1000}

        if len(scores) <= limit:
            top_items = sorted(scores.items(), key=lambda item: item[1], reverse=True)
        else:
            top_items = heapq.nlargest(limit, scores.items(), key=lambda item: item[1])

        hits = [
            SearchHit(chunk=self.chunks[doc_idx], score=score, retriever="bm25")
            for doc_idx, score in top_items
        ]
        return hits, {"bm25": (time.perf_counter() - started) * 1000}


class HybridRetriever:
    def __init__(self, dense: Retriever, bm25: BM25Retriever, rrf_k: int = 60) -> None:
        self.dense, self.bm25, self.rrf_k = dense, bm25, rrf_k

    def search(self, query: str, limit: int) -> list[SearchHit]:
        hits, _ = self.search_with_profile(query, limit)
        return hits

    def search_with_profile(self, query: str, limit: int) -> tuple[list[SearchHit], dict[str, float]]:
        candidates = max(limit * 2, 20)
        started = time.perf_counter()
        dense_results, dense_profile = self.dense.search_with_profile(query, candidates) if hasattr(self.dense, "search_with_profile") \
            else (self.dense.search(query, candidates), {})
        dense_at = time.perf_counter()
        bm25_results, bm25_profile = self.bm25.search_with_profile(query, candidates)
        bm25_at = time.perf_counter()
        fused: dict[str, tuple[Chunk, float]] = {}
        for results in (dense_results, bm25_results):
            seen_in_branch: set[str] = set()
            for rank, hit in enumerate(results, start=1):
                if hit.chunk.chunk_id in seen_in_branch:
                    continue
                seen_in_branch.add(hit.chunk.chunk_id)
                current_chunk, current_score = fused.get(hit.chunk.chunk_id, (hit.chunk, 0.0))
                fused[hit.chunk.chunk_id] = (current_chunk, current_score + 1.0 / (self.rrf_k + rank))
        ordered = sorted(fused.values(), key=lambda item: item[1], reverse=True)[:limit]
        profile = {**dense_profile, **bm25_profile, "rrf": (time.perf_counter() - bm25_at) * 1000,
                   "hybrid_total": (time.perf_counter() - started) * 1000}
        return [SearchHit(chunk=chunk, score=score, retriever="hybrid") for chunk, score in ordered], profile


_CROSS_ENCODER_CACHE: dict[str, Any] = {}
_CROSS_ENCODER_LOCK = threading.Lock()


_STOP_WORDS = {"what", "is", "are", "a", "an", "the", "how", "why", "who", "where", "when", "does", "do", "in", "on", "of", "to", "for", "and", "or"}


class TransparentReranker(Reranker):
    """Transparent baseline reranker; prioritizes meaningful content and title term overlap."""
    def rerank(self, query: str, candidates: Sequence[SearchHit], limit: int) -> list[SearchHit]:
        query_terms = set(tokenize(query))
        content_query_terms = {t for t in query_terms if t not in _STOP_WORDS} or query_terms
        rescored = []
        for hit in candidates:
            body_terms = set(tokenize(hit.chunk.text))
            title_terms = set(tokenize(hit.chunk.title or ""))
            body_cov = len(content_query_terms & body_terms) / max(len(content_query_terms), 1)
            title_cov = len(content_query_terms & title_terms) / max(len(content_query_terms), 1)
            coverage = (0.6 * body_cov) + (0.4 * title_cov)
            rescored.append(SearchHit(hit.chunk, (0.4 * hit.score) + (0.6 * coverage), "reranked"))
        return sorted(rescored, key=lambda hit: hit.score, reverse=True)[:limit]


# v0.1 compatibility alias.
OverlapReranker = TransparentReranker


class CrossEncoderReranker(Reranker):
    """Optional sentence-transformers cross-encoder with transparent fallback on runtime failure."""
    def __init__(self, model_name: str | None = None, batch_size: int = 16, fallback: Reranker | None = None) -> None:
        self.model_name = model_name or __import__("os").getenv(
            "RERANKER_MODEL", "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1"
        )
        self.batch_size = batch_size
        self.fallback = fallback or TransparentReranker()
        self._model = None

    def _load_model(self):
        if self._model is not None:
            return self._model
        with _CROSS_ENCODER_LOCK:
            if self.model_name in _CROSS_ENCODER_CACHE:
                self._model = _CROSS_ENCODER_CACHE[self.model_name]
                return self._model
            try:
                from sentence_transformers import CrossEncoder
                model = CrossEncoder(self.model_name)
                _CROSS_ENCODER_CACHE[self.model_name] = model
                self._model = model
                return self._model
            except Exception as exc:
                raise RuntimeError(f"Unable to load reranker model '{self.model_name}': {exc}") from exc

    def rerank(self, query: str, candidates: Sequence[SearchHit], limit: int) -> list[SearchHit]:
        if not candidates:
            return []
        try:
            scores = self._load_model().predict([(query, hit.chunk.text) for hit in candidates], batch_size=self.batch_size)
            ranked = [SearchHit(hit.chunk, float(score), "cross_encoder") for hit, score in zip(candidates, scores)]
            return sorted(ranked, key=lambda hit: hit.score, reverse=True)[:limit]
        except Exception:
            return self.fallback.rerank(query, candidates, limit)
