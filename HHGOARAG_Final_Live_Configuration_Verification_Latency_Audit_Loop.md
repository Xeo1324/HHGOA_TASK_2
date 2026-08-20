# HHGOARAG — Final Live Configuration Verification & Latency Audit Loop

## Objective

The `.env` configuration has been updated to use:

- Gemini for LLM generation
- Sarvam for STT
- `saaras:v3`
- The full `data/novaron_corpus.jsonl` corpus

Perform a **verification-only audit** of the current repository.

Do not commit.
Do not push.
Do not expose API keys.
Do not modify the architecture.
Do not fabricate or alter benchmark results.

---

## 1. Environment Verification

Verify that the application actually loads:

```env
LLM_PROVIDER=gemini
GEMINI_MODEL=gemini-3.5-flash-lite
GEMINI_API_KEY=<configured>
STT_PROVIDER=sarvam
STT_MODEL=saaras:v3
SARVAM_API_KEY=<configured>
TTS_PROVIDER=edge
DENSE_RETRIEVER=faiss
VECTOR_INDEX_DIR=data/indexes
NOVARON_CORPUS_PATH=data/novaron_corpus.jsonl
```

Never print the actual API keys.

---

## 2. Live Sarvam Verification

Run a genuine live Sarvam STT request.

Verify:

- Provider is Sarvam
- Model is `saaras:v3`
- API request succeeds
- Transcript is non-empty
- `fallback=false`
- No mock/local STT was used

Record the actual latency.

---

## 3. Live Gemini Verification

Run a genuine Gemini generation request through the application.

Verify:

- Provider is Gemini
- Configured model is actually used
- API request succeeds
- Response is non-empty
- `fallback=false`
- Local/extractive fallback was not used

Record the actual latency.

---

## 4. Dataset Verification

Verify that the application loads:

```text
data/novaron_corpus.jsonl
```

and NOT:

```text
data/fixtures/sample_corpus.jsonl
```

Confirm the number of loaded passages/documents.

Verify that retrieved results contain MSMARCO-XI provenance such as:

- `source_dataset`
- `query_id`
- chunk ID
- original/target language metadata where available

---

## 5. End-to-End Voice RAG Test

Run real:

```text
Audio
→ Sarvam STT
→ Language Detection / Router
→ Chunk / Retrieval
→ FAISS + BM25 + RRF
→ Gemini
→ Grounding
→ Citation Validation
→ TTS / Final Output
```

Use at least 5 representative queries.

Include:

- English
- Hindi
- at least one additional Indic language
- dataset-supported question
- unsupported/out-of-domain question

For every run record:

- transcript
- detected language
- STT provider
- LLM provider
- fallback status
- retrieved source IDs
- grounded status
- refusal status
- STT latency
- retrieval latency
- LLM latency
- total latency

---

## 6. Latency Audit

Run the existing benchmark with a reasonable sample size.

Report:

| Stage | P50 | P70 | P100 |
|---|---:|---:|---:|
| Router | | | |
| Retrieval / Hybrid RAG | | | |
| Gemini | | | |
| Sarvam STT | | | |
| Full Voice E2E | | | |

Do not substitute router latency for full RAG latency.

The Task 2 requirement is:

> The full process — chunking + vector DB retrieval + everything through to final output — should complete in under 200 ms.

Therefore:

- If full local RAG P50 is >200 ms → mark **NOT SATISFIED**
- If full local RAG P50 is <200 ms → mark **PASS**, provided the measurement genuinely represents the required pipeline
- Do not hide cloud latency
- Do not claim cloud E2E <200 ms unless measured evidence proves it

---

## 7. Retrieval Verification

Run the existing MSMARCO-XI evaluation.

Report:

- Recall@1
- Recall@5
- Recall@10
- MRR

Do not call successful execution "100% retrieval accuracy."

Also verify that answers are actually grounded in retrieved MSMARCO-XI passages.

---

## 8. Multilingual Verification

Verify the existing 15-language support.

Report actual results for:

- STT
- retrieval execution
- grounded output
- answer language
- citations

Do not claim 100% language accuracy merely because every pipeline execution completed.

---

## 9. Guardrail Verification

Verify:

- unsupported-query refusal
- prompt-injection isolation
- grounding validation
- citation validation
- off-topic/safety handling where implemented

---

## 10. Security Verification

Confirm:

- `.env` is ignored
- `.env` is not tracked
- no API keys are hardcoded
- `.env.example` contains placeholders only
- logs do not expose credentials

Never print secret values.

---

## 11. Required Output

Update `walkthrough.md` with the verified results only.

Clearly distinguish:

- Real external execution
- Local execution
- Mock/fallback execution
- Not verified

Include a final Task 2 compliance matrix.

Use only:

- `PASS`
- `PARTIAL`
- `NOT SATISFIED`
- `NOT VERIFIED`

---

## 12. Final Verdict

If the only remaining requirement issue is the <200 ms latency target, explicitly state that.

If the new configuration resolves the previous Sarvam live-verification issue, mark Sarvam accordingly.

Do not claim Task 2 is fully compliant unless every mandatory requirement is actually supported by the measured evidence.

End the report with:

```text
READY TO PUSH
```

only if all mandatory requirements are satisfied.

Otherwise:

```text
NOT READY TO PUSH
```

Do not commit or push.
