# PONytail — CI Root-Cause Fix & Verification Loop

## Objective

Apply only the three fixes identified by the completed CI audit, then run the complete verification suite.

Do not make unrelated changes.

---

# 1. Fix Secret Scanner False Positive

File:

`.github/workflows/ci.yml`

Problem:

The current secret scanner uses a broad hexadecimal pattern:

```text
[a-f0-9]{32,64}
```

This incorrectly matches normal Git commit SHAs.

Required change:

Replace the broad hexadecimal credential pattern with specific credential/token patterns such as:

```text
sk-[A-Za-z0-9]{20,}
AIzaSy[A-Za-z0-9_-]{33}
ghp_[A-Za-z0-9]{36}
xox[baprs]-[A-Za-z0-9-]+
```

Do not disable the secret scanner.

Do not weaken detection of genuine API keys.

Git commit SHAs must not be treated as credentials.

---

# 2. Make Backend CI Deterministic

File:

`.github/workflows/ci.yml`

In the `backend-test` job, configure offline deterministic CI defaults:

```yaml
env:
  LLM_PROVIDER: extractive
  STT_PROVIDER: mock
  TTS_PROVIDER: mock
  DENSE_RETRIEVER: hashing
```

Purpose:

- CI tests must not require live Gemini credentials.
- CI tests must not require live Sarvam credentials.
- CI tests must remain deterministic.
- Production/local `.env` configuration must remain unchanged.

Do NOT replace the real providers in the application.

These values are only for the CI test environment.

---

# 3. Fix Retrieval Quality Gate Threshold

File:

`backend/scripts/verify_retrieval_quality.py`

Current problem:

```text
minimum_score = 0.08
```

The hybrid RRF score scale is calibrated around:

```text
minimum_score = 0.01
```

Change the quality-gate threshold from `0.08` to `0.01`.

Do not modify:

- FAISS retrieval
- BM25 retrieval
- RRF algorithm
- dataset
- embeddings
- evaluation queries
- retrieval ranking
- quality metrics

The purpose is to align the evaluation gate with the existing calibrated hybrid-RRF score scale.

---

# 4. STRICT SECURITY RULES

Never:

- print API keys
- commit `.env`
- modify `.gitignore` to allow `.env`
- disable secret scanning
- remove security checks
- fabricate test results
- weaken retrieval requirements
- replace real production providers with mocks

CI-only mocks/extractive generation are allowed because the CI environment must be deterministic.

---

# 5. Run Verification

After applying the three fixes, run:

## Secret scan

```bash
git grep -n -E 'sk-[A-Za-z0-9]{20,}|AIzaSy[A-Za-z0-9_-]{33}|ghp_[A-Za-z0-9]{36}|xox[baprs]-[A-Za-z0-9-]+' -- ':!.env.example'
```

Expected:

```text
No credential matches.
```

## Backend tests

From `backend`:

```bash
python -m pytest tests -v
```

Expected:

```text
138 passed
0 failed
```

If the actual test count differs because the repository has changed, report the real count rather than fabricating `138`.

## Ponytail latency

```bash
python scripts/benchmark_ponytail.py
```

Verify:

```text
P50 < 200 ms
P70 < 200 ms
P100 < 200 ms
```

Do not fake or reuse previous benchmark numbers.

## MSMARCO-XI retrieval quality

```bash
python scripts/verify_retrieval_quality.py
```

Verify that the evaluation runs against the real MSMARCO-XI-derived corpus and reports its actual:

- Recall@1
- Recall@5
- Recall@10
- MRR

## Frontend

```bash
cd ../frontend
npm run build
```

Expected:

```text
Build succeeds
```

---

# 6. Git Safety Verification

Run:

```bash
git status
git check-ignore -v .env
git ls-files .env
git diff --check
```

Confirm:

- `.env` is ignored.
- `.env` is not tracked.
- `.env.example` contains placeholders only.
- No actual credentials are present in tracked files.
- No whitespace/error issues are introduced.

---

# 7. Do Not Commit or Push Yet

After verification, inspect:

```bash
git diff
git status
```

Do NOT commit.

Do NOT push.

Do NOT deploy.

---

# 8. Final Report

Return ONLY:

## 1. FIXES APPLIED

List the three fixes and exact files changed.

## 2. BACKEND TEST RESULT

Actual test count and pass/fail result.

## 3. RETRIEVAL QUALITY RESULT

Actual Recall@1, Recall@5, Recall@10 and MRR.

## 4. PONytail LATENCY RESULT

Actual P50/P70/P100.

State clearly whether all are below 200 ms.

## 5. SECRET SCAN RESULT

PASS/FAIL.

Never print credentials.

## 6. FRONTEND BUILD RESULT

PASS/FAIL.

## 7. GIT SAFETY

State whether `.env` is ignored/untracked and whether tracked files contain credentials.

## 8. FINAL PUSH READINESS

Use exactly one:

```text
READY TO PUSH
```

or

```text
NOT READY
```

Use `READY TO PUSH` only if every required verification passes.

---

# FINAL INSTRUCTION

Apply only the three authorized fixes.

Use Ponytail principles to keep the implementation clean and avoid unnecessary code.

Do not commit or push automatically.
