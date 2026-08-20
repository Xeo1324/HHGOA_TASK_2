# HHGOARAG — P0 Local RAG Latency Optimization & Compliance Verification LOOP

## Objective

Audit and optimize the **actual local RAG pipeline** in the current `HH_Goa-T2` repository.

The latest live audit reports:

- Local Router P50: **0.05 ms**
- Local Hybrid RAG P50: **378.82 ms**
- Local Hybrid RAG P70: **380.81 ms**
- Local Hybrid RAG P100: **534.75 ms**
- Full cloud voice E2E P50: **11.05 s**

The **378.82 ms local RAG P50 is the primary blocker** against the stated `<200 ms` Task 2 target.

Use **Ponytail** as the execution/audit pass identifier for this loop.

---

# CRITICAL RULES

1. **Do NOT fake, redefine, or selectively report the latency metric.**
2. The `<200 ms` target must be measured on the real local RAG path:
   **query → retrieval/index operations → ranking/fusion → grounding/citation preparation → final local RAG output**.
3. Do NOT exclude expensive stages merely to make the number pass.
4. Do NOT remove required Task 2 functionality just to reduce latency.
5. Do NOT replace MSMARCO-XI with fabricated, unrelated, or tiny mock data.
6. Do NOT disable grounding, citation validation, guardrails, multilingual routing, or required retrieval components merely for benchmarking.
7. Do NOT claim `<200 ms` unless the optimized implementation is empirically measured below 200 ms.
8. Cloud STT, cloud LLM, and cloud TTS latency must remain separately reported. Do not mix or hide cloud latency inside the local benchmark.
9. Preserve real Sarvam STT and real Gemini/LLM integrations.
10. Never expose API keys, `.env` contents, or secrets in logs, reports, commits, or generated files.
11. Do not make unrelated architectural changes.
12. Before changing code, inspect the current implementation and identify the actual bottleneck.
13. If `<200 ms` cannot honestly be achieved without violating requirements, report **NOT SATISFIED** instead of manipulating the benchmark.
14. Keep all working multilingual functionality intact.

---

# PHASE 1 — READ-ONLY AUDIT

Inspect the current repository before modifying anything.

Check at minimum:

- `backend/app/pipeline.py`
- `backend/app/retrieval.py`
- `backend/app/router.py`
- `backend/app/main.py`
- embedding/index initialization
- FAISS index implementation
- BM25 implementation
- RRF fusion
- cross-encoder/reranker if present
- chunking implementation
- grounding/citation validation
- dataset loading
- `backend/scripts/audit_task2_compliance.py`
- existing benchmark/evaluation scripts
- `.env.example`
- `.gitignore`

Determine exactly what contributes to the reported **378.82 ms P50**.

Instrument each local stage separately where necessary.

Measure at least:

1. Query normalization
2. Language detection/routing
3. Dense retrieval
4. Sparse/BM25 retrieval
5. RRF fusion
6. Cross-encoder/reranking, if present
7. Context assembly
8. Grounding validation
9. Citation validation
10. Final local pipeline

Do not assume the slow stage. Measure it.

---

# PHASE 2 — BOTTLENECK ANALYSIS

Produce a table like:

| Stage | P50 | P70 | P100 | % of Local RAG Time |
|---|---:|---:|---:|---:|
| Router | | | | |
| Dense Retrieval | | | | |
| BM25 | | | | |
| RRF | | | | |
| Reranker | | | | |
| Context Assembly | | | | |
| Grounding | | | | |
| Citation Validation | | | | |
| Total | | | | |

Identify the **top 1–3 contributors** to the 378.82 ms latency.

---

# PHASE 3 — OPTIMIZATION

Optimize only the measured bottlenecks.

Possible optimization areas include, but are not limited to:

### FAISS / Dense Retrieval

- Reuse initialized FAISS indexes.
- Avoid rebuilding indexes per request.
- Avoid repeated embedding-model initialization.
- Batch or cache embeddings where appropriate.
- Reduce unnecessary candidate counts while preserving retrieval quality.
- Use efficient FAISS search parameters.
- Avoid unnecessary vector conversions/copies.

### BM25

- Ensure the inverted index is built once.
- Avoid tokenizing the entire corpus per query.
- Avoid rebuilding BM25 structures per request.
- Restrict sparse candidate processing to realistic candidate sets.

### RRF

- Fuse only retrieved candidate sets.
- Avoid repeated full-corpus operations.
- Use efficient dictionary/set operations.

### Reranking

If a cross-encoder is responsible for most of the latency:

- Measure it separately.
- Reduce candidate count only if retrieval quality remains acceptable.
- Batch candidate scoring where possible.
- Reuse the loaded model.
- Do not remove reranking blindly.
- If removing or bypassing reranking materially changes retrieval quality, measure and report that trade-off.

### Context / Grounding

- Avoid repeated parsing of the same chunks.
- Reuse metadata already available in retrieval results.
- Avoid unnecessary serialization/deserialization.
- Keep citation and grounding checks intact.

---

# PHASE 4 — RETRIEVAL QUALITY SAFETY CHECK

Latency optimization must not silently destroy retrieval quality.

After every meaningful optimization, run the existing MSMARCO-XI evaluation.

Report:

- Recall@1
- Recall@5
- Recall@10
- MRR

Compare against the current baseline:

- Recall@1 = **0.1400**
- Recall@5 = **0.3567**
- Recall@10 = **0.4200**
- MRR = **0.2301**

Do not claim the optimization is successful if latency improves only because retrieval quality was severely degraded.

Prefer optimizations that improve or preserve retrieval quality.

---

# PHASE 5 — MULTILINGUAL VERIFICATION

The system must continue supporting all currently claimed languages.

Verify at minimum:

- English
- Hindi
- Bengali
- Gujarati
- Kannada
- Malayalam
- Marathi
- Nepali
- Odia
- Punjabi
- Sanskrit
- Tamil
- Telugu
- Urdu
- Assamese

For representative queries, verify:

1. Language detection
2. Correct retrieval path
3. MSMARCO-XI provenance
4. Grounded answer
5. Citation IDs
6. Answer language

Do not mark multilingual support as PASS merely because the code contains language mappings.

---

# PHASE 6 — DATASET PROVENANCE VERIFICATION

Confirm that retrieval actually comes from:

`ai4bharat/MSMARCO-XI`

Verify that returned chunks retain appropriate provenance such as:

- `source_dataset`
- `query_id`
- language metadata
- document/chunk ID

Explicitly test at least:

- one English query
- one Hindi query
- one additional Indic-language query

Inspect the actual retrieved chunk metadata.

---

# PHASE 7 — GUARDRAIL REGRESSION TEST

Ensure optimization has not weakened:

- off-topic refusal
- unsafe/inappropriate-input handling
- prompt-injection isolation
- ungrounded-answer refusal
- citation validation

Run the existing guardrail tests and add tests only if a regression is discovered.

---

# PHASE 8 — REAL PROVIDER REGRESSION

Do not replace the existing real providers.

Confirm configuration supports:

- Sarvam `saaras:v3`
- Gemini configured model
- Edge TTS

Cloud latency must remain separately measured.

Do NOT use cloud latency to claim local `<200 ms`.

---

# PHASE 9 — FINAL BENCHMARK

Run a sufficiently large benchmark, preferably **100+ queries**, using the same benchmark methodology before and after optimization.

Report:

### Local RAG

- P50
- P70
- P100
- Mean

### Cloud stages separately

- Sarvam STT P50/P70/P100
- Gemini P50/P70/P100
- TTS P50/P70/P100
- Full voice E2E P50/P70/P100

The local benchmark must use the complete defined local RAG path.

---

# PHASE 10 — COMPLIANCE DECISION

Use exactly one of:

### `TASK 2 LATENCY REQUIREMENT SATISFIED`

Only if the measured complete local RAG pipeline is genuinely `<200 ms`.

OR:

### `TASK 2 LATENCY REQUIREMENT NOT SATISFIED`

If the complete local RAG pipeline remains ≥200 ms.

Do not call the project fully compliant merely because the router is below 200 ms.

---

# REQUIRED FINAL REPORT

Create/update a Markdown report containing:

## 1. Baseline

Current measured:

- Local RAG P50 = 378.82 ms
- Local RAG P70 = 380.81 ms
- Local RAG P100 = 534.75 ms

## 2. Bottleneck Breakdown

Show measured latency for every major stage.

## 3. Changes Made

For every modification:

- File
- Change
- Reason
- Expected effect

## 4. Before vs After

| Metric | Before | After | Change |
|---|---:|---:|---:|
| P50 | | | |
| P70 | | | |
| P100 | | | |
| Recall@1 | | | |
| Recall@5 | | | |
| Recall@10 | | | |
| MRR | | | |

## 5. Multilingual Verification

Report actual tested languages and results.

## 6. Dataset Grounding

Show actual retrieved MSMARCO-XI provenance for representative queries.

## 7. Guardrail Verification

Report pass/fail results.

## 8. Cloud Provider Verification

Clearly separate:

- Sarvam
- Gemini
- TTS
- Full cloud E2E

## 9. Final Task 2 Matrix

| Requirement | Status |
|---|---|
| Voice RAG | |
| Sarvam/ElevenLabs STT | |
| MSMARCO-XI | |
| Vast chunking | |
| `<200 ms` local full pipeline | |
| P50/P70/P100 | |
| Model harness | |
| Guardrails | |
| Grounding | |
| Citation validation | |
| Multilingual support | |
| Secret security | |

## 10. Final Verdict

Use an honest verdict based strictly on measured evidence.

---

# GIT SAFETY

Before suggesting a push:

1. Run `git status`.
2. Run a diff inspection.
3. Confirm `.env` is ignored.
4. Confirm no API keys appear in tracked files.
5. Confirm no temporary recordings, generated credentials, caches, or scratch files are staged.
6. Run the relevant test suite.
7. Do NOT commit or push automatically.

Only state `SAFE TO PUSH` after the above checks pass.

---

# IMPORTANT

The objective is **not** to manufacture a `<200 ms` number.

The objective is to make the real implementation as fast as possible while preserving:

**Real MSMARCO-XI → real retrieval → real grounding → real citations → real multilingual support → real Sarvam STT → real model harness → real guardrails.**

If the honest result remains above 200 ms, report that clearly and identify the remaining bottleneck and the next technically valid optimization.
