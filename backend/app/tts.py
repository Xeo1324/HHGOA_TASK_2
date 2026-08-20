from __future__ import annotations

import asyncio
import io
import os
import re
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

try:
    from dotenv import load_dotenv

    _project_root = Path(__file__).resolve().parents[2]
    _root_env = _project_root / ".env"
    _backend_env = Path(__file__).resolve().parents[1] / ".env"
    if _root_env.exists():
        load_dotenv(_root_env)
    elif _backend_env.exists():
        load_dotenv(_backend_env)
except ImportError:
    pass

from app.domain import TextToSpeech


class TextToSpeechError(RuntimeError):
    """Raised when text-to-speech synthesis fails."""
    pass


class EdgeTTS(TextToSpeech):
    """Microsoft Edge Neural Text-to-Speech adapter with multilingual Indic voice support.

    Supports all 15 MSMARCO-XI languages (14 Indic + English) with automatic voice selection.
    Languages without a dedicated Edge Neural voice fall back to a related language voice.
    """

    # Comprehensive voice mapping for all 15 supported languages.
    # Languages without dedicated Edge TTS voices use the closest available voice.
    _VOICE_MAP: dict[str, str] = {
        "en": "en-US-JennyNeural",
        "hi": "hi-IN-SwaraNeural",
        "as": "bn-IN-TanishaaNeural",   # Assamese → Bengali voice (closest script)
        "bn": "bn-IN-TanishaaNeural",   # Bengali
        "gu": "gu-IN-DhwaniNeural",     # Gujarati
        "kn": "kn-IN-SapnaNeural",      # Kannada
        "ml": "ml-IN-SobhanaNeural",    # Malayalam
        "mr": "mr-IN-AarohiNeural",     # Marathi
        "ne": "hi-IN-SwaraNeural",      # Nepali → Hindi voice (Devanagari)
        "or": "hi-IN-SwaraNeural",      # Odia → Hindi voice (no Edge TTS Odia)
        "pa": "hi-IN-SwaraNeural",      # Punjabi → Hindi voice (limited Edge support)
        "sa": "hi-IN-SwaraNeural",      # Sanskrit → Hindi voice (Devanagari)
        "ta": "ta-IN-PallaviNeural",    # Tamil
        "te": "te-IN-ShrutiNeural",     # Telugu
        "ur": "ur-PK-UzmaNeural",       # Urdu
    }

    def __init__(
        self,
        voice_en: str | None = None,
        voice_hi: str | None = None,
    ) -> None:
        self.voice_en = voice_en or os.getenv("TTS_VOICE_EN", "en-US-JennyNeural")
        self.voice_hi = voice_hi or os.getenv("TTS_VOICE_HI", "hi-IN-SwaraNeural")
        # Override defaults with env-configured voices
        self._VOICE_MAP["en"] = self.voice_en
        self._VOICE_MAP["hi"] = self.voice_hi

    def _select_voice(self, language: str | None) -> str:
        if language is None:
            return self.voice_en
        lang = language.lower().strip()
        # Handle full language names
        lang_name_map = {
            "eng": "en", "english": "en", "hin": "hi", "hindi": "hi",
            "assamese": "as", "bengali": "bn", "gujarati": "gu",
            "kannada": "kn", "malayalam": "ml", "marathi": "mr",
            "nepali": "ne", "odia": "or", "punjabi": "pa",
            "sanskrit": "sa", "tamil": "ta", "telugu": "te", "urdu": "ur",
        }
        lang = lang_name_map.get(lang, lang)
        voice = self._VOICE_MAP.get(lang)
        if voice:
            return voice
        # Graceful fallback to English for truly unknown languages
        return self.voice_en

    @staticmethod
    def _clean_text(text: str) -> str:
        # Strip citation brackets such as [chunk-id] or [msmarco-xi:en:1:2:sentence:0]
        cleaned = re.sub(r"\[[a-zA-Z0-9_\-:]+\]", "", text)
        return " ".join(cleaned.split())

    async def _synthesize_edge(self, text: str, voice: str) -> bytes:
        import edge_tts

        communicate = edge_tts.Communicate(text, voice)
        audio_buffer = bytearray()
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_buffer.extend(chunk["data"])

        if not audio_buffer:
            raise TextToSpeechError("EdgeTTS produced empty audio stream.")
        return bytes(audio_buffer)

    async def _synthesize_fallback(self, text: str, language: str | None) -> bytes:
        lang = "hi" if language and language.lower() in ("hi", "hin", "hindi") else "en"
        # Split text into <= 180 char segments at word boundaries to respect endpoint limitations
        words = text.split()
        chunks: list[str] = []
        curr: list[str] = []
        curr_len = 0
        for w in words:
            if curr_len + len(w) + 1 > 180:
                if curr:
                    chunks.append(" ".join(curr))
                curr = [w]
                curr_len = len(w)
            else:
                curr.append(w)
                curr_len += len(w) + 1
        if curr:
            chunks.append(" ".join(curr))

        def _fetch_all():
            buffer = bytearray()
            for chunk in chunks:
                url = f"https://translate.google.com/translate_tts?ie=UTF-8&tl={lang}&client=tw-ob&q=" + urllib.parse.quote(chunk)
                req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
                with urllib.request.urlopen(req, timeout=10) as resp:
                    buffer.extend(resp.read())
            return bytes(buffer)

        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, _fetch_all)

    async def synthesize(
        self,
        text: str,
        language: str | None = None,
    ) -> bytes:
        if not text or not text.strip():
            raise TextToSpeechError("Cannot synthesize empty text.")

        voice = self._select_voice(language)
        cleaned_text = self._clean_text(text)
        if not cleaned_text:
            raise TextToSpeechError("Cannot synthesize empty text after removing citations.")

        # Attempt EdgeTTS first; if blocked or handshake fails, use resilient chunked fallback
        try:
            return await self._synthesize_edge(cleaned_text, voice)
        except Exception:
            try:
                return await self._synthesize_fallback(cleaned_text, language)
            except Exception as exc:
                raise TextToSpeechError(f"Speech synthesis request failed: {exc}") from exc


class MockTTS(TextToSpeech):
    """Deterministic mock TTS adapter for testing and offline environments."""

    _SUPPORTED_LANGS = {
        "en", "hi", "as", "bn", "gu", "kn", "ml", "mr", "ne", "or", "pa", "sa", "ta", "te", "ur",
        "eng", "hin", "english", "hindi", "assamese", "bengali", "gujarati",
        "kannada", "malayalam", "marathi", "nepali", "odia", "punjabi",
        "sanskrit", "tamil", "telugu", "urdu",
    }

    def __init__(self, mock_bytes: bytes | None = None) -> None:
        self.mock_bytes = mock_bytes or (b"ID3\x04\x00\x00\x00\x00\x00\x00\xff\xfb\x90\x04" + b"MOCK_MP3_AUDIO_DATA_FOR_TESTS")
        self.recorded_calls: list[dict[str, Any]] = []

    async def synthesize(
        self,
        text: str,
        language: str | None = None,
    ) -> bytes:
        if not text or not text.strip():
            raise TextToSpeechError("Cannot synthesize empty text.")

        if language and language.lower() not in self._SUPPORTED_LANGS:
            raise TextToSpeechError(f"Unsupported language '{language}' for speech synthesis.")

        self.recorded_calls.append({"text": text, "language": language})
        return self.mock_bytes
