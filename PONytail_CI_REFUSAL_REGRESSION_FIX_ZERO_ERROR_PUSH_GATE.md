# PONytail — CI Refusal Regression Fix & Zero-Error Push Gate

## Objective

Fix the current GitHub Actions regression where unsupported queries are incorrectly answered because dense retrieval accepts an irrelevant high-scoring passage.

**Do not push or commit automatically.**

## Current CI Failure

Two tests are failing:

1. `test_grounding_refusal_on_unsupported_questions`
2. `test_api_query_unsupported_refusal`

Failure example:

```text
Query:
"What is the exact secret recipe for Martian cosmic space cake?"

Incorrect result:
refused=False

Top retrieved evidence:
novaron-sys-overview-1:sentence:0
score ≈ 0.233858
```

The retrieved NOVARON system-overview passage is clearly unrelated to the question, yet it is being accepted as evidence.

Current CI result:

```text
2 failed
136 passed
18 skipped
```

## Required Fix

### 1. Find the Root Cause

Inspect:

- `backend/app/pipeline.py`
- `backend/app/retrieval.py`
- `backend/app/main.py`
- `backend/app/generation.py`
- reranker / grounding validation code
- existing refusal tests

Determine why an irrelevant dense result with a score around `0.234` is accepted as valid evidence.

### 2. Implement a General Evidence-Relevance Gate

Fix the **production evidence acceptance boundary**.

The system must refuse when retrieved passages are semantically unrelated to the user's query, even if dense retrieval gives them a misleadingly high score.

**Do not:**

- Hard-code the five test questions.
- Modify or delete the tests.
- Bypass the RAG pipeline.
- Disable grounding.
- Lower the refusal threshold simply to make tests pass.
- Remove citation validation.
- Sacrifice supported-query answers.
- Sacrifice multilingual support.
- Add a cloud/API call to the local relevance gate.
- Break the Ponytail latency optimization.

Prefer an existing lightweight local reranker/relevance mechanism if one already exists.

### 3. Preserve Supported Queries

These must continue to work:

```text
"What is a corporation?"
"What is photosynthesis?"
```

They must return `refused=False` when valid evidence exists.

Also preserve:

- Python knowledge queries
- AI knowledge queries
- Hindi queries
- other supported multilingual queries
- valid citations

### 4. Preserve Guardrails

Verify that the fix preserves:

- Unsupported queries → `refused=True`
- Prompt injection isolation
- Citation validation

Every citation must exist in retrieved evidence, match the cited chunk, and not be fabricated.

### 5. Preserve Multilingual Support

Do not regress the existing 15-language support. Verify representative supported queries across Indic languages and English.

### 6. Preserve Ponytail Latency

The local RAG pipeline must remain under:

```text
P50 < 200 ms
P70 < 200 ms
P100 < 200 ms
```

Do not introduce a slow external service into the local evidence gate.

## Regression Tests

Add or strengthen tests for:

### Unsupported English Query

```text
What is the exact secret recipe for Martian cosmic space cake?
```

Expected: `refused=True`

### High-Scoring Irrelevant Passage

A query retrieving a high-scoring but semantically unrelated NOVARON system document must still result in `refused=True`.

### Supported Corporation Query

```text
What is a corporation?
```

Expected: `refused=False`

### Supported Photosynthesis Query

```text
What is photosynthesis?
```

Expected: `refused=False`

### Multilingual Supported Query

Expected: grounded answer, valid citation, correct response language.

### Prompt Injection

Expected: grounding policy preserved and no fabricated answer.

## Complete Verification

Run all of the following after the fix.

### Backend Tests

```powershell
cd D:\HH_Goa-T2\backend
python -m pytest tests -v
```

Required: `0 failed`.

### Ponytail Latency

```powershell
python scripts/benchmark_ponytail.py
```

Required: P50, P70, and P100 all below 200 ms.

### Retrieval Quality

```powershell
python scripts/verify_retrieval_quality.py
```

Verify that retrieval quality does not regress.

### Frontend Build

```powershell
cd ..\frontend
npm run build
```

Required: 0 errors.

### Git Diff Validation

```powershell
cd ..
git diff --check
```

Required: no output / exit code 0.

### Secret Scan

```powershell
git grep -n -E "sk-[A-Za-z0-9]{20,}|AIzaSy[A-Za-z0-9_-]{33}|ghp_[A-Za-z0-9]{36}|xox[baprs]-[A-Za-z0-9-]+" -- ':!.env.example' ':!*.jsonl' ':!*.json'
```

Required: exit code 1 and zero credential matches.

## Final Diff Audit

Before declaring success:

- Inspect `git diff`.
- Remove temporary/debug code.
- Remove unnecessary changes.
- Ensure tests were not weakened.
- Ensure no secrets are present.
- Ensure no hard-coded unsupported-query list was added.
- Ensure Ponytail optimizations remain intact.
- Ensure no core RAG functionality was removed.

## Final Acceptance Criteria

Do **not** declare success unless all conditions below are satisfied:

```text
Backend tests:
0 failed

Frontend:
Build succeeds

Secret scan:
0 credential matches

Retrieval quality:
Passes quality gate

Ponytail latency:
P50 < 200 ms
P70 < 200 ms
P100 < 200 ms

Unsupported-query refusal:
PASS

Supported-query grounding:
PASS

Multilingual support:
PASS

Prompt-injection safety:
PASS

Citation validation:
PASS
```

Expected final state:

```text
READY TO PUSH
```

If anything fails:

```text
NOT READY
```

**Do not push or commit automatically.**
