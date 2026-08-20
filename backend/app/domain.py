from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, Sequence


@dataclass(frozen=True)
class Passage:
    document_id: str
    passage_id: str
    text: str
    title: str | None = None
    language: str | None = None
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class Chunk:
    chunk_id: str
    document_id: str
    passage_id: str
    text: str
    chunk_index: int
    strategy: str
    title: str | None = None
    language: str | None = None
    parent_chunk_id: str | None = None


@dataclass(frozen=True)
class SearchHit:
    chunk: Chunk
    score: float
    retriever: str


class Embedder(Protocol):
    def embed(self, text: str) -> Sequence[float]: ...


class EmbeddingProvider(Embedder, Protocol):
    """Provider-neutral embedding contract used by in-memory and persisted stores."""
    def embed_many(self, texts: Sequence[str], batch_size: int | None = None) -> Sequence[Sequence[float]]: ...


class Retriever(Protocol):
    def search(self, query: str, limit: int) -> list[SearchHit]: ...


class Reranker(Protocol):
    def rerank(self, query: str, candidates: Sequence[SearchHit], limit: int) -> list[SearchHit]: ...


class GroundedGenerator(Protocol):
    def answer(self, query: str, evidence: Sequence[SearchHit], language: str | None = None) -> str | "GeneratedAnswer": ...


class SpeechToText(Protocol):
    async def transcribe(self, audio: bytes, language: str | None = None) -> str: ...


class TextToSpeech(Protocol):
    async def synthesize(self, text: str, language: str | None = None) -> bytes: ...


@dataclass(frozen=True)
class GeneratedAnswer:
    answer: str
    citation_chunk_ids: tuple[str, ...]
    refused: bool = False
