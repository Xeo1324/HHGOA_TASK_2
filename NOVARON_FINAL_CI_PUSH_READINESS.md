# NOVARON — Final CI Refusal Regression & Push Readiness

## Status

```text
READY TO PUSH
```

## Verification

| Check | Result |
|---|---|
| Backend tests | 138 passed, 0 failed, 18 skipped |
| Unsupported-query refusal | PASS |
| Supported-query grounding | PASS |
| Multilingual support | PASS |
| Prompt injection & citation validation | PASS |
| Local RAG P50 | 2.62 ms |
| Local RAG P70 | 2.84 ms |
| Local RAG P100 | 4.67 ms |
| `<200 ms` latency gate | PASS |
| MSMARCO-XI quality gate | PASS |
| Frontend production build | PASS |
| Git diff check | PASS |
| Secret leak scan | PASS |

## Root Cause Fixed

The previous refusal regression was caused by the unreranked dense retrieval threshold being too low (`0.08`). Unrelated queries could produce background dense scores around `0.23–0.40` and were therefore incorrectly accepted as evidence.

The threshold was raised to `0.65`, while supported queries were verified to retain relevance scores of approximately `0.697–0.997`.

## Final Checks

- Unsupported queries refuse with `refused=True` and no fabricated sources.
- Supported queries remain grounded with citations.
- Multilingual behavior remains functional.
- Prompt-injection protection remains active.
- Ponytail latency optimization remains intact.
- No credentials are present in tracked files.
- No automated commit or push was performed.

## Final Verdict

```text
TASK 2 CI REGRESSION FIXED
LATENCY GATE PASSED
QUALITY GATE PASSED
SECURITY GATE PASSED
READY TO PUSH
```
