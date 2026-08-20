# PONytail CI FAILURE AUDIT LOOP

## Objective

Audit the latest GitHub Actions CI failures before making any fixes or pushing/deploying again.

Latest CI result:
- Frontend Typecheck & Build — PASSED
- Backend Test Suite & Retrieval Quality Gate — FAILED
- Secret & Credential Leak Scan — FAILED

## STRICT RULE

**DO NOT MODIFY CODE YET.**

This is a read-only root-cause investigation.

Do not:
- delete or weaken tests
- lower retrieval-quality thresholds
- disable CI checks or secret scanning
- replace real retrieval/provider integrations with mocks
- expose or print API keys/secrets
- commit or push anything
- make unrelated UI changes

Use Ponytail principles only after the actual root cause is established: remove unnecessary code/paths without reducing required functionality.

---

# 1. Read the Latest CI Run

Inspect the complete logs for:

1. `CI / Quality & Regression Gate / Backend Test Suite & Retrieval Quality Gate`
2. `CI / Quality & Regression Gate / Secret & Credential Leak Scan`

The frontend job has already passed, so do not investigate or modify frontend code unless the logs explicitly show a dependency.

---

# 2. Backend Test & Retrieval Quality Audit

Identify:
- exact failing test
- exact failing command
- exact assertion
- exact file and line
- retrieval metric that failed
- expected threshold
- measured value
- whether the failure is deterministic

Classify the root cause as:
- genuine code defect
- stale/incorrect CI expectation
- retrieval-quality regression
- environment/dependency issue
- dataset/index mismatch
- false-positive test
- other, with explanation

Verify that retrieval evaluation still uses:
- `ai4bharat/MSMARCO-XI`
- actual indexed corpus
- real FAISS/BM25/RRF retrieval
- real multilingual retrieval path
- existing evaluation queries

Do not substitute mocks or fabricated metrics.

---

# 3. Secret & Credential Leak Audit

Inspect the complete secret-scan failure.

Check:
- tracked files
- Git history relevant to the scanner
- `.env`
- `.env.example`
- README/documentation
- Markdown audit reports
- test fixtures
- generated artifacts
- logs
- scripts
- source code
- workflow files

Determine whether the scanner detected:
1. an actual credential
2. a credential accidentally committed in Git history
3. a test/example placeholder resembling a credential
4. a false positive
5. another secret-like value

## SECURITY RULE

NEVER print actual secret values.

If a secret is found, report only:
- filename
- line number if available
- secret type/category
- whether it is tracked
- whether it exists in Git history
- required remediation

Do not expose the key itself.

---

# 4. Git Safety Audit

Run and inspect:

```bash
git status
git ls-files
git check-ignore -v .env
git diff -- .gitignore .env.example
```

Also inspect relevant Git history if the scanner indicates historical exposure.

Confirm:
- `.env` is ignored
- `.env` is not tracked
- `.env.example` contains placeholders only
- no API key is hardcoded in source
- no API key is present in documentation
- no generated artifact contains credentials

Do not rewrite Git history yet.

---

# 5. Determine Required Fixes

For every failure, produce:

| Failure | Root Cause | File | Required Fix | Risk |
|---|---|---|---|---|
| Backend/Quality | ... | ... | ... | ... |
| Secret Scan | ... | ... | ... | ... |

Separate mandatory fixes from optional improvements.

Do not make optional improvements during this pass.

---

# 6. Ponytail Optimization Rule

If unnecessary code is contributing to the CI failure:
- remove redundant paths only when safe
- preserve required Task 2 functionality
- preserve real Sarvam STT
- preserve Gemini/LLM integration
- preserve MSMARCO-XI grounding
- preserve FAISS/BM25/RRF retrieval
- preserve multilingual support
- preserve guardrails
- preserve citation validation
- preserve latency telemetry

Never optimize by weakening correctness checks.

---

# 7. Required Final Report

Return ONLY this structure:

## 1. ROOT CAUSE

Explain the actual cause of each failed CI job.

## 2. FAILED CHECKS

List every failed test/check with:
- command
- test/check name
- expected result
- actual result

## 3. EXACT FILES INVOLVED

List only files directly responsible for the failures.

## 4. REQUIRED FIXES

Give precise fixes, without implementing them yet.

## 5. SECURITY RISK

State whether an actual credential exposure exists.

Never print any credential value.

## 6. CAN THE FIX BE MADE SAFELY?

Answer `YES` or `NO` with a short reason.

## 7. POST-FIX VERIFICATION COMMANDS

Give exact commands that should be run after implementation.

Include relevant backend tests, retrieval evaluation, secret scan, and frontend verification where applicable.

## 8. FINAL PUSH READINESS

Use exactly one:
`READY`
or
`NOT READY`

A failed CI job means **NOT READY** until the root cause is fixed and the relevant checks pass.

---

# FINAL INSTRUCTION

Do not implement, commit, or push anything during this audit.

First identify the root causes and return the report.
