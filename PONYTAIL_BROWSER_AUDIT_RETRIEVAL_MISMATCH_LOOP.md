# PONYTAIL — CRITICAL BROWSER-vs-AUDIT RETRIEVAL MISMATCH DEBUG LOOP

## Problem

The automated/live audit successfully answered:

> "What is a corporation?"

But when I personally use the browser UI and type or speak the same question, the UI returns:

> "I don't have enough information in the indexed knowledge base to answer that reliably."

Do **not** lower grounding thresholds, disable guardrails, bypass retrieval, add hardcoded answers, or weaken citation validation.

Investigate the actual discrepancy.

---

## 1. Reproduce the Problem

From the actual browser UI, test the exact typed query:

> What is a corporation?

Then separately test the spoken version:

> What is a corporation?

---

## 2. Capture the Actual Browser Pipeline

For the typed request, capture:

- Exact request payload sent by frontend
- Exact query received by backend
- Normalized query
- Detected language
- Corpus path
- Corpus document count
- Index path
- Retriever implementation
- Top-10 retrieved chunk IDs
- Top-10 retrieval scores
- RRF scores
- Evidence / grounding score
- Grounding threshold
- Final refusal decision
- LLM provider/model
- Fallback state

For the spoken request, additionally capture:

- Audio input
- Sarvam STT transcript
- Normalized transcript
- Detected language
- Then all retrieval/grounding fields above

---

## 3. Compare Against the Audit Path

Run exactly:

> What is a corporation?

through both:

### A. Existing audit/evaluation path

### B. Actual browser API path

The two paths must be compared stage-by-stage.

---

## 4. Verify Runtime Configuration

Confirm that the browser/backend runtime is actually using:

```text
data/novaron_corpus.jsonl
```

and **NOT**:

```text
data/fixtures/sample_corpus.jsonl
```

Also verify:

- Same corpus document count
- Same FAISS index
- Same BM25 index
- Same RRF configuration
- Same retrieval implementation
- Same optimized NumPy retrieval implementation from the Ponytail optimization
- Same grounding threshold
- Same LLM configuration

---

## 5. Test Three Browser Cases

Run all three through the **actual browser UI**:

1. Typed:
   `What is a corporation?`

2. Spoken:
   `What is a corporation?`

3. Typed:
   `Which is a corporation?`

Record the exact transcript/query and result for every case.

---

## 6. Find the Root Cause

Determine exactly where the browser and audit paths diverge.

Possible areas to investigate:

- Frontend request payload
- Backend endpoint
- Query normalization
- Language detection
- STT transcript
- Corpus configuration
- Index loading
- Retriever selection
- Query embedding
- Retrieval scores
- RRF fusion
- Grounding threshold
- LLM request
- Citation validation
- Environment variables

Do **not** assume the cause.

---

## 7. Fix Rules

Fix the **root cause only**.

Do NOT:

- Lower the grounding threshold merely to make the answer pass
- Disable guardrails
- Bypass retrieval
- Hardcode an answer for "What is a corporation?"
- Add fake citations
- Replace MSMARCO-XI with unrelated data
- Hide retrieval failures
- Modify benchmark results

If the threshold is genuinely misconfigured, prove it with evidence before changing it.

---

## 8. Required Verification After Fix

Run:

- Browser typed test
- Browser spoken test
- Audit test
- Dataset-grounding verification
- Citation verification
- Retrieval benchmark
- Full regression/unit test suite

The browser result must be grounded in the indexed dataset with valid citations.

---

## 9. Required Final Report

Produce this table:

| Stage | Audit | Browser Typed | Browser Speech |
|---|---|---|---|
| Raw query | | | |
| STT transcript | N/A | N/A | |
| Normalized query | | | |
| Language | | | |
| Corpus | | | |
| Index | | | |
| Retriever | | | |
| Top result | | | |
| Top score | | | |
| Evidence score | | | |
| Threshold | | | |
| Refused | | | |
| Citations | | | |

Then report:

```text
ROOT CAUSE:
FIX:
FILES CHANGED:
REGRESSION RESULTS:
BROWSER TYPED RESULT:
BROWSER SPEECH RESULT:
AUDIT RESULT:
DATASET CITATION VERIFIED:
```

## Final Acceptance Condition

Do not declare PASS until the **actual browser UI** can answer:

> What is a corporation?

with a valid citation to the indexed `ai4bharat/MSMARCO-XI` dataset.
