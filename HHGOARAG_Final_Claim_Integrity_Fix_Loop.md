# HHGOARAG — Final Claim-Integrity Fix Loop

## Objective

Perform a final **evidence-only claim-integrity audit** of the current `HH_Goa-T2` repository before any commit or push.

**Do not push or commit.**

**Do not fabricate benchmark improvements.**

**Do not modify the core architecture merely to make the report pass.**

The purpose of this loop is to ensure that the final Task 2 report makes only claims directly supported by measured evidence and by the official Task 2 requirements.

---

## 1. Read the Current Evidence First

Read the current:

- `walkthrough.md`
- `README.md`
- `backend/scripts/audit_task2_compliance.py`
- relevant latency/benchmark scripts
- relevant retrieval evaluation scripts
- relevant Task 2 implementation files

Also read the official Task 2 requirement text available in the repository if present.

Do not assume that previous PASS/READY claims are correct.

---

## 2. Critical Latency Audit

The Task 2 requirement states that:

> The full process — chunking + vector DB retrieval + everything through to final output — should complete in under 200 ms.

Audit and separately report:

### A. Router
- P50
- P70
- P100

### B. Local retrieval / RAG
Include, where measurable:
- embedding
- FAISS retrieval
- BM25
- RRF
- reranking/cross-encoder
- grounding
- local generation

Report:
- P50
- P70
- P100

### C. Real STT
Report measured Sarvam latency separately.

### D. Real LLM
Report measured external LLM latency separately.

### E. Real E2E Voice
Report:
Voice input → STT → routing → retrieval → generation → TTS/final output.

Report:
- P50
- P70
- P100

---

## 3. Do NOT Misrepresent the <200 ms Requirement

The current evidence reports approximately:

- Router P50: `0.05 ms`
- Local Hybrid RAG P50: `379.37 ms`
- Real cloud STT: approximately `800–1200 ms`
- Real cloud LLM: approximately `350–600 ms`
- Full E2E voice: approximately `1.5–2.4 s`

If these values are still confirmed by the audit:

### DO NOT write:
- "Full Task 2 pipeline <200 ms"
- "Task 2 latency requirement PASS"
- "READY TO PUSH" solely on the basis of router latency
- "Local RAG <200 ms" if the measured full local RAG is >200 ms

Instead classify the requirement honestly as:

`NOT SATISFIED`

or

`PARTIAL / NOT VERIFIED`

depending strictly on what the measured evidence supports.

Do not change measured numbers simply to obtain PASS.

---

## 4. Retrieval Claim-Integrity Audit

The current evidence reports:

- Recall@1 = `0.1400`
- Recall@5 = `0.3567`
- Recall@10 = `0.4200`
- MRR = `0.2301`

The report also uses wording such as:

> 100% retrieval success across 300 queries.

Determine exactly what "retrieval success" means in the implementation.

If it only means that the pipeline returned a retrieval result, it must NOT be described as:

- 100% retrieval accuracy
- 100% correct retrieval
- 100% relevant retrieval
- 100% Recall

Keep the actual Recall@1/5/10 and MRR values prominent.

---

## 5. Dataset Grounding Audit

Verify that answers are actually traceable to:

`ai4bharat/MSMARCO-XI`

Check:

- `source_dataset`
- `query_id`
- chunk IDs
- retrieved passage text
- citation IDs
- answer grounding validation

Verify the existing 10 dataset-grounding traces.

Do not claim stronger provenance than the code and data demonstrate.

---

## 6. Multilingual Audit

Verify the 15-language evaluation.

Report separately:

- STT support/integration
- language detection
- retrieval
- grounded answer
- answer language correctness
- citations

Do not turn "pipeline executed successfully" into "100% language accuracy."

Preserve the actual language-level results from the evidence.

---

## 7. Guardrail Audit

Verify:

- unsupported-query refusal
- prompt-injection isolation
- grounding checks
- citation validation
- off-topic/safety handling where implemented

Only mark PASS when the implementation/test evidence supports it.

---

## 8. Security Audit

Verify:

- `.env` is ignored
- `.env` is not tracked
- no API keys are hardcoded
- `.env.example` contains placeholders only
- logs/reports do not expose credentials

Do not print or expose any secret values.

---

## 9. Required Updated Walkthrough

Update `walkthrough.md` so that it contains:

1. Executive Summary
2. Dataset Grounding Evidence
3. Multilingual Matrix
4. Retrieval Metrics
5. Guardrail Results
6. Latency Breakdown
7. Real vs Mock Matrix
8. Security Audit
9. Final Task 2 Compliance Matrix
10. Remaining Blockers
11. Final Verdict

---

## 10. Final Compliance Matrix

Use only these classifications:

- `PASS`
- `PARTIAL`
- `FAIL`
- `NOT VERIFIED`

For the latency requirement, use the evidence actually measured.

Do not use "PASS (Scoped)" to imply that the full requirement is satisfied when only a sub-stage meets the threshold.

---

## 11. Final Verdict Rules

If local full RAG remains above 200 ms:

`TASK 2 — LATENCY REQUIREMENT NOT SATISFIED`

If real cloud E2E remains above 200 ms:

Explicitly disclose that result.

If other requirements pass, preserve those PASS results.

The final report must distinguish:

- what is implemented,
- what is empirically verified,
- what partially satisfies the requirement,
- what does not satisfy the requirement.

---

## 12. Modification Rules

Allowed:
- correcting inaccurate claims
- correcting compliance classifications
- correcting benchmark descriptions
- improving documentation
- improving audit/report scripts if needed to measure existing behavior accurately

Not allowed:
- fake benchmark results
- deleting unfavorable results
- changing latency numbers without a genuine remeasurement
- changing requirements
- hiding cloud latency
- claiming 100% retrieval accuracy from a 100% execution-success rate
- committing or pushing

---

## 13. Required Output

After completing the audit:

### A. Modify `walkthrough.md` only where necessary to make claims evidence-accurate.

### B. Report:
- exact files modified
- exact tests/commands executed
- confirmed latency values
- confirmed retrieval metrics
- confirmed multilingual results
- confirmed dataset-grounding results
- confirmed security results
- remaining blockers

### C. Do NOT commit.

### D. Do NOT push.

### E. End with one of:

`READY TO PUSH`

or

`NOT READY TO PUSH`

based on the actual evidence.

---

## Most Important Rule

**Do not optimize the report to make the project look compliant. Optimize the report to make the project truthful.**
