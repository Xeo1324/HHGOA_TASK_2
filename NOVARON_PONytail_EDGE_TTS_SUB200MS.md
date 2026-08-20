# NOVARON — Ponytail EdgeTTS Sub-200 ms Latency Optimization Loop

## Objective

Optimize the NOVARON EdgeTTS stage so that **measured local TTS processing/dispatch overhead is below 200 ms**, while preserving the existing voice output and multilingual support.

## Important Constraint

Do **not** fake or redefine network latency.

Microsoft Edge Neural TTS is an external cloud service, so the actual end-to-end audio-generation time can exceed 200 ms because of network RTT and remote synthesis.

Therefore:

- Measure **TTS request/stream startup latency** separately from full audio completion latency.
- Optimize the application-side TTS pipeline for `<200 ms`.
- Keep full external TTS latency disclosed in telemetry.
- Do not claim full cloud audio synthesis is `<200 ms` unless repeated real measurements prove it.

---

## 1. Ponytail Investigation

Inspect the current TTS implementation and remove unnecessary work from the hot path.

Focus on:

- `backend/app/tts.py`
- `backend/app/pipeline.py`
- `backend/app/main.py`
- TTS-related tests
- frontend audio handling
- latency telemetry

Profile these stages independently:

1. TTS preparation
2. voice selection
3. text normalization
4. EdgeTTS connection/setup
5. first audio chunk received
6. complete audio generation
7. response serialization/base64 conversion
8. frontend playback startup

Identify the actual bottleneck before changing architecture.

---

## 2. Required Optimizations

### A. Stream EdgeTTS instead of buffering the complete response

If the current implementation waits for the entire synthesized audio before returning it, change it to stream audio chunks whenever the existing API architecture permits.

Target metric:

```text
TTS time-to-first-audio < 200 ms
```

Do not wait for the full MP3/audio payload before beginning playback.

### B. Remove unnecessary audio transformations

Eliminate unnecessary:

- byte copies
- temporary conversions
- duplicate buffers
- base64 encode/decode cycles
- format conversions
- disk writes
- repeated text preprocessing

Keep audio in the most direct format supported by the current frontend/backend contract.

### C. Reuse HTTP/session resources where supported

Avoid recreating expensive client/session state for every request if the EdgeTTS library safely supports reuse.

Do not introduce unsafe global mutable state.

### D. Precompute static configuration

Voice maps and language configuration must be initialized once rather than rebuilt per request.

Voice selection should be effectively constant-time.

### E. Cache repeated synthesis

Add a bounded in-memory LRU cache for repeated identical:

```text
(language, voice, normalized_text)
```

requests.

Requirements:

- bounded maximum entries/bytes
- deterministic cache key
- no API keys or sensitive information in cache
- cache hit must bypass external TTS
- expose cache hit/miss telemetry

For repeated queries such as the same refusal message, this should reduce latency dramatically.

### F. Cache common refusal/system phrases

If the UI repeatedly speaks deterministic phrases such as:

```text
I don't have enough information in the indexed knowledge base to answer that reliably.
```

pre-generate/cache these phrases where practical.

Do not pre-generate arbitrary user content.

### G. Parallelize independent work

Inspect the pipeline for work that can happen concurrently with TTS preparation.

Do not block TTS on unrelated telemetry or UI metadata.

Do not introduce concurrency if it changes correctness or citation ordering.

---

## 3. Latency Telemetry

Extend the existing `latencies` object with explicit TTS measurements.

Required fields:

```text
tts_prepare_ms
tts_cache_lookup_ms
tts_connect_ms
tts_first_audio_ms
tts_complete_ms
tts_total_ms
tts_cache_hit
```

If streaming is used, expose:

```text
tts_time_to_first_audio_ms
```

as the primary user-perceived TTS latency.

Clearly distinguish:

```text
TTS application overhead
TTS time-to-first-audio
TTS full synthesis completion
```

from total voice E2E latency.

---

## 4. Performance Targets

### Primary target

```text
TTS time-to-first-audio P50 < 200 ms
```

### Secondary targets

```text
TTS application overhead P50 < 50 ms
TTS cache-hit P50 < 10 ms
```

### Full external synthesis

Do not impose an artificial `<200 ms` claim on full EdgeTTS cloud synthesis.

Report:

```text
P50 / P70 / P100
```

for full synthesis separately.

If full synthesis remains above 200 ms, mark it as:

```text
EXTERNAL CLOUD LATENCY — DISCLOSED
```

rather than falsely marking it as a local performance failure.

---

## 5. Ponytail Code Cleanup

While implementing the optimization:

- remove dead TTS code
- remove duplicated voice-selection logic
- remove unused imports
- remove redundant exception wrappers
- remove unnecessary conversions
- remove obsolete fallback paths only if they are genuinely unreachable
- keep the public API backward compatible
- do not add speculative abstractions
- do not duplicate telemetry logic

The final implementation should be smaller or cleaner where possible.

---

## 6. Correctness Requirements

After optimization, verify that:

- English EdgeTTS still works.
- Hindi EdgeTTS still works.
- all 15 configured language voices remain available.
- refusal responses can still be synthesized.
- empty text is still rejected.
- unsupported languages are still rejected.
- TTS provider failures are still surfaced correctly.
- voice-to-voice flow still works.
- existing API response shape remains compatible.
- cached audio is byte-valid and playable.
- no credentials are logged or cached.

---

## 7. Benchmark

Create or update:

```text
backend/scripts/benchmark_tts_ponytail.py
```

Benchmark at least:

- 20 cold EdgeTTS requests
- 20 repeated/cache-hit requests
- representative English text
- representative Hindi text
- refusal/system phrase

Report:

```text
P50
P70
P90
P100
```

for:

```text
time-to-first-audio
full synthesis
cache-hit latency
```

Do not use a mock provider for the live EdgeTTS latency claim.

---

## 8. Regression Tests

Run:

```bash
cd backend
python -m pytest tests -v
```

Then:

```bash
python scripts/benchmark_ponytail.py
```

Then:

```bash
python scripts/benchmark_tts_ponytail.py
```

Then:

```bash
cd ../frontend
npm run build
```

---

## 9. Acceptance Matrix

| Requirement | Target |
|---|---|
| Local TTS preparation | `<50 ms P50` |
| Cache-hit TTS | `<10 ms P50` |
| EdgeTTS time-to-first-audio | **`<200 ms P50`** |
| Full EdgeTTS cloud synthesis | Measure and disclose |
| 15-language voices | Preserved |
| Voice-to-voice pipeline | Preserved |
| Existing TTS tests | 0 failures |
| Backend tests | 0 failures |
| Frontend build | PASS |
| No secret leakage | PASS |
| Existing `<200 ms` Local RAG | Preserved |

---

## 10. Final Verdict Rules

Use exactly one of these:

### If the target is met

```text
EDGE TTS STARTUP LATENCY <200 MS — VERIFIED
```

Only claim this after real EdgeTTS measurements.

### If only cache/stream startup is under 200 ms

```text
EDGE TTS TIME-TO-FIRST-AUDIO <200 MS — VERIFIED
FULL CLOUD SYNTHESIS LATENCY — DISCLOSED
```

### If the target is not met

```text
EDGE TTS <200 MS — NOT YET SATISFIED
```

Include the measured P50/P70/P100 and identify the remaining bottleneck.

## Final Instruction

Use the **Ponytail loop**:

```text
PROFILE → IDENTIFY BOTTLENECK → REMOVE UNNECESSARY WORK → OPTIMIZE → BENCHMARK → REGRESSION TEST → REPEAT
```

Do not declare success from theoretical optimization. Only real measurements count.
