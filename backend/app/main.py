from __future__ import annotations

import asyncio
import base64
import os
import sys
import time
import traceback
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, File, Form, HTTPException, Response, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

PROJECT_ROOT = Path(__file__).resolve().parents[2]

try:
    from dotenv import load_dotenv

    _root_env = PROJECT_ROOT / ".env"
    _backend_env = Path(__file__).resolve().parents[1] / ".env"
    if _root_env.exists():
        load_dotenv(_root_env)
    elif _backend_env.exists():
        load_dotenv(_backend_env)
except ImportError:
    pass

from app.domain import SpeechToText, TextToSpeech
from app.embeddings import SentenceTransformerEmbeddingProvider
from app.generation import GeminiGroundedLLM, OpenAIGroundedLLM
from app.ingestion import fixed_chunks, hierarchical_chunks, load_jsonl, sentence_chunks
from app.pipeline import ExtractiveGroundedGenerator, RAGPipeline
from app.query_normalizer import (extract_topic_from_query,
                                  generate_suggested_questions,
                                  normalize_spoken_query)
from app.retrieval import (BM25Retriever, CrossEncoderReranker, FAISSDenseRetriever,
                           HashingDenseRetriever, HashingEmbedder, HybridRetriever,
                           TransparentReranker)
from app.router import QueryIntent, classify_query
from app.stt import FasterWhisperSTT, MockSTT, OpenAIWhisperSTT, SarvamSTT, SpeechToTextError
from app.tts import EdgeTTS, MockTTS, TextToSpeechError
from app.vector_store import FaissVectorStore

_configured_corpus = os.getenv("NOVARON_CORPUS_PATH")
if _configured_corpus:
    _raw_path = Path(_configured_corpus.strip())
    DATA_PATH = _raw_path if _raw_path.is_absolute() else (PROJECT_ROOT / _raw_path)
    if not DATA_PATH.exists():
        _fallback = PROJECT_ROOT / "data" / "fixtures" / "sample_corpus.jsonl"
        if _fallback.exists():
            DATA_PATH = _fallback
else:
    DATA_PATH = PROJECT_ROOT / "data" / "fixtures" / "sample_corpus.jsonl"


class QueryRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2_000)
    top_k: int = Field(default=5, ge=1, le=20)
    chunking_strategy: Literal["fixed", "sentence", "hierarchical"] = "sentence"
    retrieval_mode: Literal["dense", "bm25", "hybrid", "hybrid_rerank"] = "hybrid_rerank"
    language: str | None = None
    previous_query: str | None = None


class SourceResponse(BaseModel):
    chunk_id: str
    document_id: str
    passage_id: str
    title: str | None
    language: str | None
    text: str
    relevance_score: float


class QueryResponse(BaseModel):
    answer: str
    refused: bool
    retrieval_strategy: str
    chunking_strategy: str
    sources: list[SourceResponse]
    latency_ms: dict[str, float]
    query_type: str | None = None
    normalized_query: str | None = None
    suggested_questions: list[str] = Field(default_factory=list)


class VoiceQueryResponse(BaseModel):
    query: str
    answer: str
    refused: bool
    retrieval_strategy: str
    chunking_strategy: str
    sources: list[SourceResponse]
    latency_ms: dict[str, float]
    audio_base64: str | None = None
    query_type: str | None = None
    normalized_query: str | None = None
    suggested_questions: list[str] = Field(default_factory=list)


class TTSRequest(BaseModel):
    text: str = Field(min_length=1, max_length=10_000)
    language: str | None = Field(default="en")


_STORE_CACHE: dict[str, FaissVectorStore] = {}
_EMBEDDER_INSTANCE: SentenceTransformerEmbeddingProvider | None = None


def _get_shared_embedder() -> SentenceTransformerEmbeddingProvider:
    global _EMBEDDER_INSTANCE
    if _EMBEDDER_INSTANCE is None:
        _EMBEDDER_INSTANCE = SentenceTransformerEmbeddingProvider()
    return _EMBEDDER_INSTANCE


def _get_vector_store(strategy: str) -> FaissVectorStore | None:
    if strategy in _STORE_CACHE:
        return _STORE_CACHE[strategy]
    configured_path = Path(os.getenv("VECTOR_INDEX_DIR", "data/indexes"))
    index_root = configured_path if configured_path.is_absolute() else PROJECT_ROOT / configured_path
    index_dir = index_root / strategy
    if FaissVectorStore.exists(index_dir):
        embedder = _get_shared_embedder()
        store = FaissVectorStore.load(
            index_dir,
            expected_model=embedder.model_name,
            expected_strategy=strategy,
            expected_normalized=True,
        )
        _STORE_CACHE[strategy] = store
        return store
    return None


def _build_dense_retriever(chunks: list, strategy: str):
    provider = os.getenv("DENSE_RETRIEVER", "faiss").lower()
    if provider == "faiss":
        store = _get_vector_store(strategy)
        if store is not None:
            return FAISSDenseRetriever(store, _get_shared_embedder())
        return HashingDenseRetriever(chunks, HashingEmbedder())
    if provider == "hashing":
        return HashingDenseRetriever(chunks, HashingEmbedder())
    raise ValueError("DENSE_RETRIEVER must be either 'hashing' or 'faiss'.")


def _build_reranker():
    provider = os.getenv("RERANKER_PROVIDER", "transparent").lower()
    if provider == "transparent":
        return TransparentReranker()
    if provider == "cross_encoder":
        return CrossEncoderReranker()
    raise ValueError("RERANKER_PROVIDER must be either 'transparent' or 'cross_encoder'.")


_GENERATOR_INSTANCE = None


def _build_generator():
    global _GENERATOR_INSTANCE
    if _GENERATOR_INSTANCE is not None:
        return _GENERATOR_INSTANCE
    provider = os.getenv("LLM_PROVIDER", "extractive").lower()
    if provider == "extractive":
        _GENERATOR_INSTANCE = ExtractiveGroundedGenerator()
        return _GENERATOR_INSTANCE
    if provider == "openai":
        _GENERATOR_INSTANCE = OpenAIGroundedLLM()
        return _GENERATOR_INSTANCE
    if provider == "gemini":
        _GENERATOR_INSTANCE = GeminiGroundedLLM()
        return _GENERATOR_INSTANCE
    raise ValueError("LLM_PROVIDER must be one of 'extractive', 'openai', or 'gemini'.")


def _build_stt() -> SpeechToText:
    provider = os.getenv("STT_PROVIDER", "local").lower()
    if provider in ("local", "faster-whisper", "faster_whisper", "whisper"):
        return FasterWhisperSTT()
    if provider in ("openai", "groq"):
        return OpenAIWhisperSTT()
    if provider == "sarvam":
        return SarvamSTT()
    if provider == "mock":
        return MockSTT()
    raise ValueError(f"STT_PROVIDER must be 'local', 'openai', 'groq', 'sarvam', or 'mock', got '{provider}'.")


def _build_tts() -> TextToSpeech:
    provider = os.getenv("TTS_PROVIDER", "edge").lower()
    if provider == "edge":
        return EdgeTTS()
    if provider == "mock":
        return MockTTS()
    raise ValueError(f"TTS_PROVIDER must be either 'edge' or 'mock', got '{provider}'.")


def build_pipeline(chunks: list, strategy: str = "sentence", mode: str = "dense", dense=None, bm25=None) -> RAGPipeline:
    dense_retriever = dense if dense is not None else _build_dense_retriever(chunks, strategy)
    bm25_retriever = bm25 if bm25 is not None else BM25Retriever(chunks)
    retriever = {
        "dense": dense_retriever,
        "bm25": bm25_retriever,
        "hybrid": HybridRetriever(dense_retriever, bm25_retriever),
        "hybrid_rerank": HybridRetriever(dense_retriever, bm25_retriever),
    }[mode]
    reranker = _build_reranker() if mode == "hybrid_rerank" else None
    if mode in ("hybrid", "hybrid_rerank"):
        threshold = float(os.getenv("MIN_HYBRID_SCORE", "0.01"))
    elif mode == "bm25":
        threshold = float(os.getenv("MIN_BM25_SCORE", "0.5"))
    else:
        threshold = float(os.getenv("MIN_RELEVANCE_SCORE", "0.08")) if reranker else float(
            os.getenv("MIN_UNRERANKED_RELEVANCE_SCORE", "0.65")
        )
    return RAGPipeline(retriever, reranker, _build_generator(), threshold)


_PIPELINES_CACHE: dict[str, dict[str, RAGPipeline]] = {}
_CHUNKS_CACHE: dict[str, list] = {}
_RETRIEVER_CACHE: dict[str, tuple[Any, BM25Retriever]] = {}


def _get_or_build_strategy_pipelines(strategy: str) -> dict[str, RAGPipeline]:
    if strategy in _PIPELINES_CACHE:
        return _PIPELINES_CACHE[strategy]

    if strategy not in _CHUNKS_CACHE:
        passages = load_jsonl(DATA_PATH)
        if strategy == "fixed":
            chunks = fixed_chunks(passages)
        elif strategy == "hierarchical":
            chunks = hierarchical_chunks(passages)
        else:
            chunks = sentence_chunks(passages)
        _CHUNKS_CACHE[strategy] = chunks
        del passages

    chunks = _CHUNKS_CACHE[strategy]
    if strategy not in _RETRIEVER_CACHE:
        dense = _build_dense_retriever(chunks, strategy)
        bm25 = BM25Retriever(chunks)
        _RETRIEVER_CACHE[strategy] = (dense, bm25)
    else:
        dense, bm25 = _RETRIEVER_CACHE[strategy]

    strat_pipelines = {
        mode: build_pipeline(chunks, strategy, mode, dense=dense, bm25=bm25)
        for mode in ("dense", "bm25", "hybrid", "hybrid_rerank")
    }
    _PIPELINES_CACHE[strategy] = strat_pipelines
    return strat_pipelines


class LazyPipelineDict(dict):
    """Dictionary that automatically builds chunking strategies on demand while exposing keys."""
    def __getitem__(self, strategy: str) -> dict[str, RAGPipeline]:
        return _get_or_build_strategy_pipelines(strategy)

    def __contains__(self, strategy: object) -> bool:
        return strategy in ("sentence", "fixed", "hierarchical")

    def keys(self):
        return ["sentence", "fixed", "hierarchical"]


def build_pipelines() -> dict[str, dict[str, RAGPipeline]]:
    # Eagerly initialize only the primary 'sentence' strategy to maintain steady-state RAM < 400MB
    _get_or_build_strategy_pipelines("sentence")
    return LazyPipelineDict({"sentence": _PIPELINES_CACHE["sentence"]})


from contextlib import asynccontextmanager

from fastapi.middleware.cors import CORSMiddleware

# ---------------------------------------------------------------------------
# Global state & Diagnostic startup tracking
# ---------------------------------------------------------------------------
pipelines: dict | None = None
stt_adapter: SpeechToText | None = None
tts_adapter: TextToSpeech | None = None
_startup_complete: bool = False
_startup_error: str | None = None


def _get_memory_mb() -> float | None:
    """Read current process memory RSS in MB (cross-platform)."""
    try:
        import psutil
        return psutil.Process().memory_info().rss / (1024.0 * 1024.0)
    except Exception:
        pass
    try:
        import resource
        return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0
    except Exception:
        pass
    try:
        import ctypes
        from ctypes import wintypes
        class PROCESS_MEMORY_COUNTERS(ctypes.Structure):
            _fields_ = [
                ('cb', wintypes.DWORD),
                ('PageFaultCount', wintypes.DWORD),
                ('PeakWorkingSetSize', ctypes.c_size_t),
                ('WorkingSetSize', ctypes.c_size_t),
                ('QuotaPeakPagedPoolUsage', ctypes.c_size_t),
                ('QuotaPagedPoolUsage', ctypes.c_size_t),
                ('QuotaPeakNonPagedPoolUsage', ctypes.c_size_t),
                ('QuotaNonPagedPoolUsage', ctypes.c_size_t),
                ('PagefileUsage', ctypes.c_size_t),
                ('PeakPagefileUsage', ctypes.c_size_t),
            ]
        k32 = ctypes.windll.kernel32
        k32.K32GetProcessMemoryInfo.argtypes = [wintypes.HANDLE, ctypes.POINTER(PROCESS_MEMORY_COUNTERS), wintypes.DWORD]
        k32.K32GetProcessMemoryInfo.restype = wintypes.BOOL
        pmc = PROCESS_MEMORY_COUNTERS()
        pmc.cb = ctypes.sizeof(PROCESS_MEMORY_COUNTERS)
        res = k32.K32GetProcessMemoryInfo(k32.GetCurrentProcess(), ctypes.byref(pmc), pmc.cb)
        if res and pmc.WorkingSetSize > 0:
            return pmc.WorkingSetSize / (1024.0 * 1024.0)
    except Exception:
        pass
    return None


def _log_startup_step(step_desc: str, start_time: float | None = None) -> float:
    now = time.perf_counter()
    ram = _get_memory_mb()
    ram_tag = f" [RAM: {ram:.1f} MB]" if ram is not None else ""
    if start_time is not None:
        elapsed = (now - start_time) * 1000.0
        print(f"[STARTUP]{ram_tag} [DONE] {step_desc} ({elapsed:.1f} ms)", flush=True)
    else:
        print(f"[STARTUP]{ram_tag} -> {step_desc}...", flush=True)
    return now


def _initialize_all() -> None:
    """Build every heavy resource (model download, FAISS index, BM25, STT, TTS).
    Called from lifespan in background on production, or synchronously in test environments."""
    global pipelines, stt_adapter, tts_adapter, _startup_complete, _startup_error

    if _startup_complete and pipelines is not None:
        return

    import sys
    import traceback

    t_total = time.perf_counter()
    print("=" * 60, flush=True)
    _log_startup_step("NOVARON STARTUP SEQUENCE INITIATED")
    print(f"[STARTUP] PID: {os.getpid()} | Python: {sys.version.split()[0]} | Platform: {sys.platform}", flush=True)
    print(
        f"[STARTUP] Config: CORPUS='{DATA_PATH}' | "
        f"DENSE_RETRIEVER='{os.getenv('DENSE_RETRIEVER', 'faiss')}' | "
        f"STT='{os.getenv('STT_PROVIDER', 'local')}' | "
        f"TTS='{os.getenv('TTS_PROVIDER', 'edge')}' | "
        f"LLM='{os.getenv('LLM_PROVIDER', 'gemini')}'",
        flush=True,
    )
    print("=" * 60, flush=True)

    try:
        # Step 1: Pipelines (Corpus, Chunking, Index loading)
        t_step = _log_startup_step("Step 1/5: Loading corpus and building RAG pipelines")
        pipelines = build_pipelines()
        _log_startup_step("Step 1/5: RAG pipelines built", t_step)

        # Step 2: STT Adapter
        stt_provider = os.getenv("STT_PROVIDER", "local")
        t_step = _log_startup_step(f"Step 2/5: Initializing STT adapter (provider='{stt_provider}')")
        stt_adapter = _build_stt()
        _log_startup_step("Step 2/5: STT adapter initialized", t_step)

        # Step 3: TTS Adapter
        tts_provider = os.getenv("TTS_PROVIDER", "edge")
        t_step = _log_startup_step(f"Step 3/5: Initializing TTS adapter (provider='{tts_provider}')")
        tts_adapter = _build_tts()
        _log_startup_step("Step 3/5: TTS adapter initialized", t_step)

        # Step 4: Shared Embedder initialization
        t_step = _log_startup_step("Step 4/5: Instantiating shared embedding provider")
        embedder = _get_shared_embedder()
        _log_startup_step(f"Step 4/5: Shared embedder instantiated (model='{embedder.model_name}')", t_step)

        # Step 5: Embedder warmup (run if FAISS index is active or explicitly enabled)
        warmup_setting = os.getenv("WARMUP_EMBEDDINGS", "auto").lower()
        faiss_active = False
        if pipelines:
            for strat_modes in pipelines.values():
                for pipe in strat_modes.values():
                    ret = getattr(pipe, "retriever", None)
                    if isinstance(ret, FAISSDenseRetriever):
                        faiss_active = True
                        break
                    if hasattr(ret, "dense") and isinstance(ret.dense, FAISSDenseRetriever):
                        faiss_active = True
                        break

        should_warmup = (
            warmup_setting in ("1", "true", "yes")
            or (warmup_setting == "auto" and faiss_active)
        )

        if should_warmup:
            t_step = _log_startup_step(f"Step 5/5: Warming up embedder model '{embedder.model_name}'")
            embedder.warmup()
            _log_startup_step("Step 5/5: Embedder warmup finished", t_step)
        else:
            _log_startup_step("Step 5/5: Embedder warmup deferred (lazy loading or hashing retriever active)")

        _startup_complete = True
        _startup_error = None
        _log_startup_step("[READY] System ready -- all services initialized successfully", t_total)
        print("=" * 60, flush=True)

    except Exception as exc:
        _startup_complete = False
        _startup_error = f"{type(exc).__name__}: {exc}"
        print(f"\n[STARTUP ERROR] Initialization failed: {exc}", flush=True)
        print("[STARTUP ERROR] Full traceback:", flush=True)
        traceback.print_exc()
        print("=" * 60, flush=True)


# Synchronous initialization for test suites and offline harnesses
if "pytest" in sys.modules or os.getenv("PYTEST_CURRENT_TEST"):
    _initialize_all()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Uvicorn binds its port only AFTER this function yields.
    We yield immediately so Render's port scan succeeds, then run
    heavy initialization (model download, FAISS, BM25) in the background."""
    if not _startup_complete:
        asyncio.get_event_loop().run_in_executor(None, _initialize_all)
    yield


app = FastAPI(title="NOVARON Voice RAG", version="0.5.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    """Process liveness probe."""
    return {
        "status": "ok",
        "service": "novaron-rag-core",
        "uptime": True,
        "ready": True if _startup_complete and pipelines is not None else False,
    }


@app.get("/ready")
def ready() -> dict:
    """Resource readiness probe — verifies indexed corpus, pipelines, and provider adapters."""
    if _startup_error is not None:
        raise HTTPException(status_code=500, detail=f"Startup failed: {_startup_error}")
    if not _startup_complete or pipelines is None:
        raise HTTPException(status_code=503, detail="Service starting up")
    return {
        "status": "ready",
        "service": "novaron-rag-core",
        "ready": True,
        "corpus_loaded": True,
        "active_strategies": list(pipelines.keys()) if pipelines else [],
    }


def _require_ready():
    """Raise HTTP 500 if startup failed, or 503 if still starting up."""
    if _startup_error is not None:
        raise HTTPException(
            status_code=500,
            detail=f"Service initialization failed: {_startup_error}",
        )
    if not _startup_complete or pipelines is None:
        if "pytest" in sys.modules or os.getenv("PYTEST_CURRENT_TEST"):
            _initialize_all()
            if _startup_complete:
                return
        raise HTTPException(
            status_code=503,
            detail="Service is starting up — please retry in a few seconds.",
        )


@app.post("/v1/query", response_model=QueryResponse)
def query(request: QueryRequest) -> QueryResponse:
    _require_ready()
    t_start = time.perf_counter()

    # 1. Deterministic Local Query Normalization & Anaphora Context
    prev_topic = extract_topic_from_query(request.previous_query) if request.previous_query else None
    normalized = normalize_spoken_query(request.query, previous_topic=prev_topic)
    norm_elapsed = round((time.perf_counter() - t_start) * 1000, 3)

    # 2. Route Query
    route = classify_query(normalized.normalized_query, preferred_language=request.language)

    # 3. Handle Conversational / System directly
    if route.intent in (QueryIntent.CONVERSATIONAL, QueryIntent.SYSTEM) and route.direct_answer:
        route_ms = round((time.perf_counter() - t_start) * 1000, 3)
        return QueryResponse(
            answer=route.direct_answer,
            refused=False,
            retrieval_strategy=f"direct_{route.intent.value}",
            chunking_strategy=request.chunking_strategy,
            query_type=route.intent.value,
            normalized_query=normalized.normalized_query,
            sources=[],
            latency_ms={"norm": norm_elapsed, "route": route_ms, "total": route_ms},
            suggested_questions=generate_suggested_questions(normalized.normalized_query, [], language=route.language),
        )

    # 4. Handle Knowledge Queries through Grounded RAG Pipeline
    result = pipelines[request.chunking_strategy][request.retrieval_mode].run(normalized.normalized_query, answer_limit=request.top_k, language=route.language)
    labels = {
        "dense": "dense",
        "bm25": "bm25",
        "hybrid": "hybrid_rrf",
        "hybrid_rerank": "hybrid_rrf + reranker",
    }
    source_titles = [hit.chunk.title for hit in result.sources if hit.chunk.title]
    suggestions = generate_suggested_questions(normalized.normalized_query, source_titles, language=route.language)

    latencies = {"norm": norm_elapsed, **result.latency_ms}
    latencies["total"] = round(norm_elapsed + result.latency_ms.get("rag_total", 0.0), 3)

    return QueryResponse(
        answer=result.answer,
        refused=result.refused,
        retrieval_strategy=labels[request.retrieval_mode],
        chunking_strategy=request.chunking_strategy,
        query_type="knowledge" if not result.refused else "refusal",
        normalized_query=normalized.normalized_query,
        latency_ms=latencies,
        suggested_questions=suggestions,
        sources=[
            SourceResponse(
                chunk_id=hit.chunk.chunk_id,
                document_id=hit.chunk.document_id,
                passage_id=hit.chunk.passage_id,
                title=hit.chunk.title,
                language=hit.chunk.language,
                text=hit.chunk.text,
                relevance_score=round(hit.score, 4),
            )
            for hit in result.sources
        ],
    )


@app.post("/v1/voice/query", response_model=VoiceQueryResponse)
async def voice_query(
    file: UploadFile = File(...),
    language: str | None = Form(default=None),
    top_k: int = Form(default=5),
    chunking_strategy: Literal["fixed", "sentence", "hierarchical"] = Form(default="sentence"),
    retrieval_mode: Literal["dense", "bm25", "hybrid", "hybrid_rerank"] = Form(default="dense"),
    synthesize_audio: bool = Form(default=False),
    previous_query: str | None = Form(default=None),
) -> VoiceQueryResponse:
    _require_ready()
    if not file or not file.filename:
        raise HTTPException(status_code=400, detail="Audio file is required.")

    audio_bytes = await file.read()
    if not audio_bytes or len(audio_bytes) == 0:
        raise HTTPException(status_code=400, detail="Uploaded audio file is empty.")

    if len(audio_bytes) > 25 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Audio file exceeds maximum size of 25MB.")

    stt_start = time.perf_counter()
    try:
        transcript = await stt_adapter.transcribe(
            audio=audio_bytes,
            language=language,
            filename=file.filename or "audio.wav",
        )
    except SpeechToTextError as exc:
        raise HTTPException(status_code=502, detail=f"Speech-to-text transcription error: {exc}") from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Internal error during voice transcription.") from exc

    stt_elapsed = round((time.perf_counter() - stt_start) * 1000, 3)

    if chunking_strategy not in pipelines or retrieval_mode not in pipelines[chunking_strategy]:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid chunking strategy '{chunking_strategy}' or retrieval mode '{retrieval_mode}'.",
        )

    # 1. Deterministic Local Query Normalization & Anaphora Context
    t_norm_start = time.perf_counter()
    prev_topic = extract_topic_from_query(previous_query) if previous_query else None
    normalized = normalize_spoken_query(transcript, previous_topic=prev_topic)
    norm_elapsed = round((time.perf_counter() - t_norm_start) * 1000, 3)

    # 2. Route Query
    route = classify_query(normalized.normalized_query, preferred_language=language)
    labels = {
        "dense": "dense",
        "bm25": "bm25",
        "hybrid": "hybrid_rrf",
        "hybrid_rerank": "hybrid_rrf + reranker",
    }

    if route.intent in (QueryIntent.CONVERSATIONAL, QueryIntent.SYSTEM) and route.direct_answer:
        answer = route.direct_answer
        refused = False
        strategy = f"direct_{route.intent.value}"
        sources: list[SourceResponse] = []
        latency_ms = {
            "stt": stt_elapsed,
            "norm": norm_elapsed,
            "route": 0.5,
            "total": round(stt_elapsed + norm_elapsed + 0.5, 3),
        }
        query_type = route.intent.value
        suggestions = generate_suggested_questions(normalized.normalized_query, [], language=route.language)
    else:
        loop = asyncio.get_running_loop()
        pipeline_instance = pipelines[chunking_strategy][retrieval_mode]
        result = await loop.run_in_executor(
            None,
            lambda: pipeline_instance.run(normalized.normalized_query, answer_limit=top_k, language=route.language),
        )
        answer = result.answer
        refused = result.refused
        strategy = labels[retrieval_mode]
        sources = [
            SourceResponse(
                chunk_id=hit.chunk.chunk_id,
                document_id=hit.chunk.document_id,
                passage_id=hit.chunk.passage_id,
                title=hit.chunk.title,
                language=hit.chunk.language,
                text=hit.chunk.text,
                relevance_score=round(hit.score, 4),
            )
            for hit in result.sources
        ]
        source_titles = [hit.chunk.title for hit in result.sources if hit.chunk.title]
        suggestions = generate_suggested_questions(normalized.normalized_query, source_titles, language=route.language)
        latency_ms = {
            "stt": stt_elapsed,
            "norm": norm_elapsed,
            **result.latency_ms,
            "total": round(stt_elapsed + norm_elapsed + result.latency_ms.get("rag_total", 0.0), 3),
        }
        query_type = "knowledge" if not refused else "refusal"

    audio_b64 = None
    if synthesize_audio and answer:
        tts_start = time.perf_counter()
        try:
            if hasattr(tts_adapter, "synthesize_with_telemetry"):
                tts_audio, tts_telem = await tts_adapter.synthesize_with_telemetry(
                    answer, language=language or route.language
                )
                tts_elapsed = tts_telem.get("tts_total_ms", round((time.perf_counter() - tts_start) * 1000, 3))
                latency_ms["tts"] = tts_elapsed
                latency_ms["tts_first_audio_ms"] = tts_telem.get("tts_first_audio_ms")
                latency_ms["tts_cache_hit"] = tts_telem.get("tts_cache_hit", False)
                latency_ms["time_to_first_audio_ms"] = tts_telem.get("time_to_first_audio_ms")
            else:
                tts_audio = await tts_adapter.synthesize(answer, language=language or route.language)
                tts_elapsed = round((time.perf_counter() - tts_start) * 1000, 3)
                latency_ms["tts"] = tts_elapsed
            latency_ms["total"] = round(latency_ms["total"] + tts_elapsed, 3)
            audio_b64 = base64.b64encode(tts_audio).decode("ascii")
        except Exception as exc:
            raise HTTPException(status_code=502, detail=f"Speech synthesis error: {exc}") from exc

    return VoiceQueryResponse(
        query=transcript,
        normalized_query=normalized.normalized_query,
        answer=answer,
        refused=refused,
        retrieval_strategy=strategy,
        chunking_strategy=chunking_strategy,
        query_type=query_type,
        latency_ms=latency_ms,
        audio_base64=audio_b64,
        suggested_questions=suggestions,
        sources=sources,
    )


@app.post("/v1/tts")
async def synthesize_speech(request: TTSRequest) -> Response:
    _require_ready()
    if not request.text or not request.text.strip():
        raise HTTPException(status_code=400, detail="Text to synthesize cannot be empty.")
    try:
        audio_bytes = await tts_adapter.synthesize(request.text, language=request.language)
        return Response(content=audio_bytes, media_type="audio/mpeg")
    except TextToSpeechError as exc:
        msg = str(exc)
        status = 400 if "Unsupported language" in msg or "Cannot synthesize empty" in msg else 502
        raise HTTPException(status_code=status, detail=msg) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Internal error during speech synthesis.") from exc


@app.post("/v1/tts/stream")
async def stream_synthesize_speech(request: TTSRequest) -> StreamingResponse:
    _require_ready()
    if not request.text or not request.text.strip():
        raise HTTPException(status_code=400, detail="Text to synthesize cannot be empty.")
    if not hasattr(tts_adapter, "stream_chunks"):
        raise HTTPException(status_code=501, detail="Configured TTS adapter does not support streaming.")
    try:
        return StreamingResponse(
            tts_adapter.stream_chunks(request.text, language=request.language),
            media_type="audio/mpeg",
        )
    except TextToSpeechError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Streaming error: {exc}") from exc
