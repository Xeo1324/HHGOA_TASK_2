import asyncio
import io
import os
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

from app.domain import SpeechToText
import threading


class SpeechToTextError(RuntimeError):
    """Raised when audio transcription fails."""
    pass


_WHISPER_MODEL_CACHE: dict[str, Any] = {}
_WHISPER_MODEL_LOCK = threading.Lock()


class FasterWhisperSTT(SpeechToText):
    """Local, offline Speech-to-Text adapter using faster-whisper on CPU."""

    def __init__(
        self,
        model_size: str | None = None,
        device: str = "cpu",
        compute_type: str = "int8",
        model_instance: Any | None = None,
    ) -> None:
        self.model_size = model_size or os.getenv("STT_MODEL", "tiny")
        self.device = device
        self.compute_type = compute_type
        self._model = model_instance

    def _get_model(self) -> Any:
        if self._model is not None:
            return self._model
        with _WHISPER_MODEL_LOCK:
            if self.model_size in _WHISPER_MODEL_CACHE:
                self._model = _WHISPER_MODEL_CACHE[self.model_size]
                return self._model
            try:
                from faster_whisper import WhisperModel
            except ImportError as exc:
                raise SpeechToTextError(
                    "faster-whisper package is required for FasterWhisperSTT. "
                    "Install it with: pip install faster-whisper"
                ) from exc
            try:
                model = WhisperModel(
                    self.model_size,
                    device=self.device,
                    compute_type=self.compute_type,
                )
                _WHISPER_MODEL_CACHE[self.model_size] = model
                self._model = model
                return self._model
            except Exception as exc:
                raise SpeechToTextError(
                    f"Failed to initialize faster-whisper model '{self.model_size}': {exc}"
                ) from exc

    def _transcribe_sync(self, audio: bytes, language: str | None) -> str:
        model = self._get_model()
        audio_stream = io.BytesIO(audio)
        kwargs: dict[str, Any] = {"beam_size": 5}
        if language and language != "auto":
            kwargs["language"] = language

        segments, info = model.transcribe(audio_stream, **kwargs)
        text_segments = [segment.text for segment in segments]
        transcript = " ".join(text_segments).strip()
        if not transcript:
            raise SpeechToTextError("Transcribed audio yielded an empty transcript.")
        return transcript

    async def transcribe(
        self,
        audio: bytes,
        language: str | None = None,
        filename: str = "audio.wav",
    ) -> str:
        if not audio or len(audio) == 0:
            raise SpeechToTextError("Audio payload cannot be empty.")

        try:
            loop = asyncio.get_running_loop()
            return await loop.run_in_executor(None, self._transcribe_sync, audio, language)
        except SpeechToTextError:
            raise
        except Exception as exc:
            raise SpeechToTextError(f"STT transcription request failed: {exc}") from exc


class OpenAIWhisperSTT(SpeechToText):
    """OpenAI-compatible speech-to-text adapter supporting Groq and standard OpenAI Whisper endpoints."""

    def __init__(
        self,
        model: str | None = None,
        api_key: str | None = None,
        base_url: str | None = None,
        client: Any | None = None,
    ) -> None:
        self.model = model or os.getenv("STT_MODEL", "whisper-large-v3-turbo")
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.base_url = base_url or os.getenv("LLM_BASE_URL")
        self._client = client

    def _client_instance(self):
        if self._client is not None:
            return self._client
        if not self.api_key:
            raise SpeechToTextError("OPENAI_API_KEY is required for OpenAI/Groq STT transcription.")
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise SpeechToTextError("openai package is required for OpenAIWhisperSTT.") from exc
        kwargs: dict[str, Any] = {"api_key": self.api_key}
        if self.base_url:
            kwargs["base_url"] = self.base_url
        self._client = OpenAI(**kwargs)
        return self._client

    async def transcribe(
        self,
        audio: bytes,
        language: str | None = None,
        filename: str = "audio.wav",
    ) -> str:
        if not audio or len(audio) == 0:
            raise SpeechToTextError("Audio payload cannot be empty.")

        file_tuple = (filename, io.BytesIO(audio), "audio/wav")
        kwargs: dict[str, Any] = {
            "model": self.model,
            "file": file_tuple,
        }
        if language:
            kwargs["language"] = language

        try:
            client = self._client_instance()
            response = client.audio.transcriptions.create(**kwargs)
            # Response may be a pydantic model with `.text` or a dict
            transcript = getattr(response, "text", None) or (response.get("text") if isinstance(response, dict) else str(response))
            cleaned = str(transcript).strip()
            if not cleaned:
                raise SpeechToTextError("Transcribed audio yielded an empty transcript.")
            return cleaned
        except SpeechToTextError:
            raise
        except Exception as exc:
            raise SpeechToTextError(f"STT transcription request failed: {exc}") from exc


class SarvamSTT(SpeechToText):
    """Sarvam AI Saaras v3 Speech-to-Text adapter for multilingual Indic transcription.

    Required by HH Goa Task 2: voice-enabled RAG with Sarvam / ElevenLabs STT.
    Supports all 14 Indic languages + English with auto language detection.
    """

    # Sarvam language code mapping (ISO 639-1 → Sarvam language_code)
    _LANG_MAP: dict[str, str] = {
        "as": "as-IN", "bn": "bn-IN", "gu": "gu-IN", "hi": "hi-IN",
        "kn": "kn-IN", "ml": "ml-IN", "mr": "mr-IN", "ne": "ne-NP",
        "or": "or-IN", "pa": "pa-IN", "sa": "sa-IN", "ta": "ta-IN",
        "te": "te-IN", "ur": "ur-IN", "en": "en-IN",
    }

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "saaras:v3",
        client: Any | None = None,
    ) -> None:
        self.api_key = api_key or os.getenv("SARVAM_API_KEY")
        self.model = model
        self._client = client

    def _client_instance(self):
        if self._client is not None:
            return self._client
        if not self.api_key:
            raise SpeechToTextError(
                "SARVAM_API_KEY is required when STT_PROVIDER=sarvam. "
                "Set it in your .env file."
            )
        try:
            from sarvamai import SarvamAI
        except ImportError as exc:
            raise SpeechToTextError(
                "sarvamai package is required for Sarvam STT. "
                "Install it with: pip install sarvamai"
            ) from exc
        self._client = SarvamAI(api_subscription_key=self.api_key)
        return self._client

    def _transcribe_sync(self, audio: bytes, language: str | None, filename: str) -> str:
        client = self._client_instance()
        audio_stream = io.BytesIO(audio)
        audio_stream.name = filename  # sarvamai SDK may use the name attribute

        # Map language code or use "unknown" for auto-detection
        lang_code = "unknown"
        if language and language != "auto":
            lang_code = self._LANG_MAP.get(language, language)

        response = client.speech_to_text.transcribe(
            file=audio_stream,
            model=self.model,
            language_code=lang_code,
            mode="transcribe",
        )

        transcript = getattr(response, "transcript", None)
        if not transcript or not str(transcript).strip():
            raise SpeechToTextError("Sarvam STT returned an empty transcript.")
        return str(transcript).strip()

    async def transcribe(
        self,
        audio: bytes,
        language: str | None = None,
        filename: str = "audio.wav",
    ) -> str:
        if not audio or len(audio) == 0:
            raise SpeechToTextError("Audio payload cannot be empty.")

        try:
            loop = asyncio.get_running_loop()
            return await loop.run_in_executor(
                None, self._transcribe_sync, audio, language, filename
            )
        except SpeechToTextError:
            raise
        except Exception as exc:
            raise SpeechToTextError(
                f"Sarvam STT transcription failed: {exc}"
            ) from exc


class MockSTT(SpeechToText):
    """Deterministic mock STT adapter for testing and offline environments."""

    def __init__(self, transcript: str = "What is photosynthesis?") -> None:
        self.transcript = transcript
        self.recorded_calls: list[dict[str, Any]] = []

    async def transcribe(
        self,
        audio: bytes,
        language: str | None = None,
        filename: str = "audio.wav",
    ) -> str:
        if not audio or len(audio) == 0:
            raise SpeechToTextError("Audio payload cannot be empty.")
        self.recorded_calls.append({
            "audio_len": len(audio),
            "language": language,
            "filename": filename,
        })
        return self.transcript
