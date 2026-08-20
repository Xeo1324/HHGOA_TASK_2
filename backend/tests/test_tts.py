from __future__ import annotations

import asyncio
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.pipeline import ExtractiveGroundedGenerator, REFUSAL
from app.stt import MockSTT
from app.tts import EdgeTTS, MockTTS, TextToSpeechError


# 1. MockTTS returns deterministic bytes
def test_mock_tts_returns_deterministic_bytes():
    mock = MockTTS()
    result = asyncio.run(mock.synthesize("Hello world", language="en"))
    assert result.startswith(b"ID3") or b"MOCK_MP3" in result
    assert len(mock.recorded_calls) == 1
    assert mock.recorded_calls[0]["text"] == "Hello world"
    assert mock.recorded_calls[0]["language"] == "en"


# 2. English language routing
def test_edge_tts_selects_english_voice():
    tts = EdgeTTS(voice_en="custom-en-voice", voice_hi="custom-hi-voice")
    voice = tts._select_voice("en")
    assert voice == "custom-en-voice"


# 3. Hindi language routing
def test_edge_tts_selects_hindi_voice():
    tts = EdgeTTS(voice_en="custom-en-voice", voice_hi="custom-hi-voice")
    voice = tts._select_voice("hi")
    assert voice == "custom-hi-voice"


# 4. Default language behavior
def test_edge_tts_default_language_behavior():
    tts = EdgeTTS(voice_en="default-en-voice")
    voice = tts._select_voice(None)
    assert voice == "default-en-voice"


# 5. Empty text rejection
def test_tts_rejects_empty_text():
    mock = MockTTS()
    with pytest.raises(TextToSpeechError, match="empty text"):
        asyncio.run(mock.synthesize("   "))


# 6. Unsupported language rejection
def test_tts_rejects_unsupported_language():
    mock = MockTTS()
    with pytest.raises(TextToSpeechError, match="Unsupported language"):
        asyncio.run(mock.synthesize("Hello", language="klingon"))


# 7. Provider error handling
def test_edge_tts_provider_error_handling(monkeypatch):
    tts = EdgeTTS()

    async def failing_edge(*args, **kwargs):
        raise RuntimeError("Fake EdgeTTS connection timeout")

    async def failing_fallback(*args, **kwargs):
        raise RuntimeError("Fake fallback connection timeout")

    monkeypatch.setattr(tts, "_synthesize_edge", failing_edge)
    monkeypatch.setattr(tts, "_synthesize_fallback", failing_fallback)
    with pytest.raises(TextToSpeechError, match="Speech synthesis request failed"):
        asyncio.run(tts.synthesize("Testing error handling"))


# 8. POST /v1/tts returns HTTP 200
def test_post_tts_endpoint_returns_http_200(monkeypatch):
    from app import main

    monkeypatch.setattr(main, "tts_adapter", MockTTS(b"ID3-FAKE-MP3-STREAM-DATA"))
    client = TestClient(app)
    response = client.post("/v1/tts", json={"text": "What is photosynthesis?", "language": "en"})
    assert response.status_code == 200


# 9. Response MIME type is audio/mpeg
def test_post_tts_response_mime_type(monkeypatch):
    from app import main

    monkeypatch.setattr(main, "tts_adapter", MockTTS(b"ID3-FAKE-MP3-STREAM-DATA"))
    client = TestClient(app)
    response = client.post("/v1/tts", json={"text": "Photosynthesis is the process in plants.", "language": "en"})
    assert response.headers.get("content-type") == "audio/mpeg"


# 10. Response contains non-empty audio bytes
def test_post_tts_contains_audio_bytes(monkeypatch):
    from app import main

    fake_bytes = b"ID3\x04\x00\x00\x00\x00\x00\x00\xff\xfb\x90\x04SAMPLEAUDIO"
    monkeypatch.setattr(main, "tts_adapter", MockTTS(fake_bytes))
    client = TestClient(app)
    response = client.post("/v1/tts", json={"text": "Testing audio payload"})
    assert response.status_code == 200
    assert response.content == fake_bytes


# 11. Refusal text can be synthesized
def test_refusal_text_can_be_synthesized(monkeypatch):
    from app import main

    mock = MockTTS()
    monkeypatch.setattr(main, "tts_adapter", mock)
    client = TestClient(app)
    response = client.post("/v1/tts", json={"text": REFUSAL, "language": "en"})
    assert response.status_code == 200
    assert len(mock.recorded_calls) == 1
    assert mock.recorded_calls[0]["text"] == REFUSAL


# 12. Existing voice pipeline remains compatible
def test_voice_pipeline_compatibility():
    client = TestClient(app)
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


# 13. Existing /v1/query remains compatible
def test_v1_query_endpoint_compatibility(monkeypatch):
    from app import main

    monkeypatch.setattr(main.pipelines["sentence"]["dense"], "generator", ExtractiveGroundedGenerator())
    client = TestClient(app)
    response = client.post(
        "/v1/query",
        json={"query": "What is photosynthesis?", "top_k": 3, "chunking_strategy": "sentence", "retrieval_mode": "dense"},
    )
    assert response.status_code == 200
    data = response.json()
    assert not data["refused"]
    assert len(data["sources"]) > 0


# 14. Existing /v1/voice/query remains compatible
def test_v1_voice_query_compatibility(monkeypatch):
    from app import main

    monkeypatch.setattr(main, "stt_adapter", MockSTT("What is photosynthesis?"))
    monkeypatch.setattr(main.pipelines["sentence"]["dense"], "generator", ExtractiveGroundedGenerator())
    client = TestClient(app)
    response = client.post(
        "/v1/voice/query",
        files={"file": ("voice.wav", b"fake-audio-bytes", "audio/wav")},
        data={"chunking_strategy": "sentence", "retrieval_mode": "dense"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["query"] == "What is photosynthesis?"
    assert not data["refused"]
    assert "stt" in data["latency_ms"]
