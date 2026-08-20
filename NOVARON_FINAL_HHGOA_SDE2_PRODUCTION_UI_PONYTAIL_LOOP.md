# NOVARON — HH GOA TASK 2 FINAL PRODUCTION + UI POLISH LOOP

## Mission

Upgrade the current NOVARON repository into a polished, production-style submission that feels like it was engineered by a strong SDE-2 engineer **without adding unnecessary infrastructure or architecture theater**.

This is still an HH Goa Task 2 project. Do not over-engineer it.

The priority order is:

1. Preserve every verified HH Goa Task 2 requirement.
2. Fix correctness/retrieval issues.
3. Remove unnecessary/dead/duplicate code using the **Ponytail** principle.
4. Make the application production-deployable.
5. Improve observability/reliability.
6. Redesign the UI with the requested visual language.
7. Keep the repository clean and easy to understand.

---

# PART A — NON-NEGOTIABLE HH GOA REQUIREMENTS

Audit and preserve all of these:

- Voice-enabled RAG
- Real Sarvam STT
- `ai4bharat/MSMARCO-XI` dataset
- Multi-strategy chunking
- FAISS + BM25 + RRF retrieval
- Grounded generation
- Citation validation
- Prompt-injection protection
- Unsupported-query refusal
- Model harness with structured output/error recovery
- P50/P70/P100 latency measurement
- Local full RAG under 200 ms
- Multilingual support across the currently supported 15 languages
- Secret protection
- Real browser voice flow

Do not weaken any of these to improve appearance or latency.

---

# PART B — PONYTAIL CODEBASE CLEANUP

## Objective

Remove unnecessary complexity.

Before changing code, audit:

- unused imports
- unused functions
- dead classes
- duplicate helpers
- duplicate provider logic
- duplicate normalization
- duplicate retrieval paths
- obsolete mock paths
- redundant configuration
- temporary scripts
- scratch files
- debug logging
- obsolete benchmark scripts
- duplicate test runners
- unused frontend components
- unused CSS
- repeated constants
- unreachable branches

Do not delete anything until repository-wide references have been checked.

## Ponytail rule

If two implementations perform the same job:

```text
keep one authoritative implementation
remove the redundant implementation
```

Do not remove valid fallback behavior unless it is demonstrably unnecessary.

Do not shorten code merely because it is long. Remove code only when it is unnecessary, duplicated, obsolete, or unreachable.

---

# PART C — FIX QUERY / SPEECH RETRIEVAL ROBUSTNESS

Investigate and fix the observed mismatch:

```text
What is a corporation?      → grounded
What is corporation?        → refused
What is corporation         → refused
```

Also test:

```text
What's a corporation?
Which is a corporation?
What is the corporation?
Tell me about corporation.
```

## Requirements

Implement general-purpose query normalization/retrieval robustness.

Possible techniques:

- Unicode normalization
- whitespace normalization
- punctuation normalization
- contraction normalization
- safe case normalization
- language-aware normalization
- original + normalized query retrieval
- candidate fusion

Do NOT hardcode corporation-specific substitutions.

Do NOT lower grounding thresholds simply to make the examples pass.

Do NOT bypass citation validation.

Do NOT fabricate evidence.

Then test the same variants through real Sarvam speech input.

---

# PART D — PRODUCTION ENGINEERING, BUT KEEP IT LEAN

Do NOT add Kubernetes, Kafka, service mesh, or unnecessary microservices.

The target stack should remain understandable.

## 1. Docker

Add or improve:

```text
Dockerfile
.dockerignore
docker-compose.yml
```

Use a multi-stage build where appropriate.

The application should be reproducible from:

```text
docker build
docker run
```

Do not put secrets into Dockerfiles or images.

---

## 2. GitHub Actions

Add:

```text
.github/workflows/ci.yml
```

CI should run:

- backend tests
- frontend tests
- lint
- type checking
- retrieval regression tests
- security/secret scan
- production build
- Docker build

Do not deploy automatically until CI passes.

---

## 3. Render Deployment

Use **Render as the primary deployment platform**.

Do not deploy to both Render and Fly.io merely for appearance.

Create only the configuration actually required for this project.

Possible files:

```text
render.yaml
```

Use environment variables/secrets through Render's secret configuration.

Never commit:

```text
.env
API keys
credentials
tokens
```

---

## 4. Fly.io

Do NOT add Fly.io unless the audit finds a concrete technical reason.

If Fly.io is added, document exactly why.

Do not duplicate the same production service across Render and Fly just to make the README look impressive.

---

## 5. Health and Readiness

Add:

```text
GET /health
GET /ready
```

`/health` should verify process availability.

`/ready` should verify required runtime resources such as:

- configuration
- FAISS/index availability
- BM25 availability
- corpus/index metadata
- required model initialization

Do not make readiness depend on external APIs unless absolutely necessary.

---

## 6. External Provider Reliability

For:

```text
Sarvam
Gemini
Edge TTS
```

use:

- explicit timeout
- bounded retries
- exponential backoff where appropriate
- clear non-retryable vs retryable errors
- graceful failure
- telemetry for fallback/error state

Do not retry permanent `4xx` authentication/configuration failures unnecessarily.

Do not allow an external provider request to hang forever.

---

## 7. Structured Logging

Use structured logs.

Every request should expose, where applicable:

```text
request_id
language
STT provider
LLM provider
retrieval latency
generation latency
TTS latency
total latency
grounded
refused
citation_count
fallback_used
```

Never log:

```text
API keys
Authorization headers
secret values
raw credentials
```

---

# PART E — OBSERVABILITY

Keep this lightweight.

Implement:

- request IDs
- structured logging
- stage latency metrics
- provider failure telemetry

Use OpenTelemetry only if it can be integrated cleanly without unnecessary complexity.

Do not build a giant custom monitoring platform.

Sentry is optional. Add it only if it provides real value and does not complicate the submission.

---

# PART F — RAG INDEX ENGINEERING

Keep the existing:

```text
FAISS
+
BM25
+
RRF
```

architecture.

Preserve the Ponytail NumPy vectorization optimization.

Do not reintroduce Python O(N×D) dense similarity loops.

## Prefer versioned indexes

If practical, organize indexes like:

```text
indexes/
├── v001/
├── v002/
└── CURRENT
```

Each index should have a manifest containing:

```text
dataset
document_count
embedding_model
chunk_strategy
created_at
evaluation metrics
index version
```

Only implement this if it does not destabilize the current repository.

---

# PART G — EVALUATION AS A FIRST-CLASS FEATURE

Preserve and improve the current evaluation system.

Maintain:

```text
Recall@1
Recall@5
Recall@10
MRR
P50
P70
P100
grounding
citation validation
multilingual checks
guardrail checks
```

Create a clean evaluation structure if necessary:

```text
eval/
├── retrieval/
├── latency/
├── multilingual/
├── grounding/
└── guardrails/
```

Do not duplicate existing scripts unnecessarily.

Deployment must not be allowed to silently claim success if evaluation regresses.

---

# PART H — MULTILINGUAL REQUIREMENT

The UI and backend must continue supporting the current 15 languages.

Verify:

- STT language mapping
- query normalization
- retrieval
- LLM response language
- grounding
- citations
- TTS voice mapping

Do not let English-only normalization damage Indic languages.

---

# PART I — UI REDESIGN

## Visual direction

Completely move away from the generic:

```text
blue/purple AI dashboard
neon gradients
glowing cards
excessive rounded containers
```

Use:

> **Premium editorial research tool + serious engineering laboratory**

The interface should feel calm, intelligent, minimal, and deliberate.

---

# PART J — COLOR PALETTE

Primary palette:

```text
Background:       #F7F3EA
Surface:          #FBF9F4
Primary text:     #111111
Secondary text:   #4A4741
Borders:          #D8D2C7
Muted background: #EEE9DF
Accent:           #111111
```

Rules:

- cream/off-white dominates
- black is the primary visual accent
- use subtle beige/gray borders
- avoid blue/purple as primary UI colors
- avoid neon colors
- avoid gradients unless absolutely necessary
- use shadows sparingly

Dark mode should not be introduced unless the existing product already requires it.

---

# PART K — TYPOGRAPHY

Use:

### Inter

For:

- navigation
- buttons
- controls
- labels
- metadata
- timestamps
- system status
- small UI text

### Serif / Times New Roman

For:

- major headings
- answer presentation
- editorial-style content
- important question text

### Aparajita

Use for Indic-language content where it improves readability/rendering.

Do not blindly use all four fonts everywhere.

Create a clear hierarchy.

Example:

```text
NOVARON
Inter / uppercase / small

What is a corporation?
Times New Roman / large editorial heading

Retrieved Sources
Inter / small label

A corporation is...
Serif body text

प्रकाश संश्लेषण क्या है?
Aparajita for Indic rendering where appropriate
```

Use a robust fallback stack.

Do not break rendering if a particular font is unavailable.

---

# PART L — UI COMPONENT DESIGN

Redesign the existing UI without destroying functionality.

Prioritize:

## Header

Minimal:

```text
NOVARON
Voice RAG
```

Use typography and spacing rather than decorative graphics.

## Query area

Make the text and voice input the visual focus.

Include:

- text input
- microphone control
- recording state
- transcription state
- submit action
- clear state

Avoid giant glowing microphone buttons.

## Answer area

Use editorial presentation:

```text
QUESTION

What is a corporation?

ANSWER

A corporation is...

SOURCES

[1] ...
[2] ...
```

## Citations

Make citations clear and clickable where supported.

Do not make citations visually dominant.

## Retrieval evidence

Expose useful evidence in a restrained manner:

```text
Retrieved evidence
Source
Similarity
Chunk
Dataset
```

## Status

Show:

```text
Listening...
Transcribing...
Retrieving...
Generating...
Grounded
Refused
```

Use typography/borders rather than bright colored badges.

---

# PART M — RESPONSIVE DESIGN

The application must work cleanly on:

- desktop
- laptop
- tablet
- mobile

Do not simply shrink desktop UI.

Verify:

- microphone controls
- text input
- answer
- citations
- source evidence
- settings
- error states

---

# PART N — UI PERFORMANCE

Do not add heavy UI libraries unless necessary.

Avoid:

- unnecessary animations
- expensive rerenders
- giant image assets
- unnecessary dependencies

Keep the frontend fast.

---

# PART O — ERROR STATES

Design proper states for:

### STT failure

```text
Speech recognition unavailable.
Please try again or type your question.
```

### LLM failure

```text
The answer service is temporarily unavailable.
```

### No evidence

```text
I couldn't find enough evidence in the indexed knowledge base.
```

### Network failure

```text
Connection lost. Please retry.
```

Never expose stack traces to the user.

---

# PART P — SECURITY

Verify:

- `.env` ignored
- no API keys in Git
- no credentials in frontend bundle
- no credentials in logs
- no credentials in screenshots
- no secrets in README
- CORS configured intentionally
- upload limits configured
- request size limits configured
- rate limiting considered for public deployment

---

# PART Q — DOCUMENTATION

README should look like a real engineering project.

Include:

```text
1. Overview
2. Architecture
3. Features
4. Tech Stack
5. RAG Pipeline
6. Dataset
7. Multilingual Support
8. Grounding & Guardrails
9. Performance
10. Local Development
11. Environment Variables
12. Docker
13. Deployment
14. Testing
15. Evaluation
16. Known Limitations
```

Do not exaggerate performance.

Clearly distinguish:

```text
Local RAG latency
```

from:

```text
Real cloud voice E2E latency
```

---

# PART R — ARCHITECTURE DOCUMENTATION

Create an architecture diagram if one does not already exist.

Show:

```text
Browser
 ↓
FastAPI
 ↓
Sarvam
 ↓
Query Normalization
 ↓
FAISS + BM25
 ↓
RRF
 ↓
Grounding
 ↓
Gemini
 ↓
Citation Validation
 ↓
Edge TTS
 ↓
Browser
```

Also document failure paths.

---

# PART S — DO NOT OVER-ENGINEER

Do NOT add unless technically justified:

- Kubernetes
- Kafka
- service mesh
- GraphQL
- Terraform
- multiple cloud providers
- dozens of microservices
- PostgreSQL without a real persistence requirement
- Redis without a queue/cache requirement
- Celery without background-job requirements
- complex authentication for a local/demo-only endpoint

A smaller, well-engineered system is preferred over a fake enterprise architecture.

---

# PART T — REQUIRED VERIFICATION

Run all existing tests.

Then run:

```text
query robustness
speech E2E
retrieval evaluation
multilingual evaluation
grounding tests
guardrail tests
latency benchmark
security scan
frontend build
Docker build
```

Verify baseline preservation:

```text
Local RAG:
P50  = 5.16 ms
P70  = 5.65 ms
P100 = 14.92 ms
```

The local pipeline must remain below:

```text
200 ms
```

Do not claim that external Sarvam/Gemini/TTS network latency is under 200 ms.

---

# PART U — FINAL AUDIT REPORT

Produce a final report containing:

## 1. HH Goa Compliance

| Requirement | Status |
|---|---|
| Voice RAG | |
| Sarvam STT | |
| MSMARCO-XI | |
| Vast chunking | |
| FAISS/BM25/RRF | |
| <200 ms local RAG | |
| P50/P70/P100 | |
| Model harness | |
| Guardrails | |
| Grounding | |
| Citations | |
| Multilingual | |
| Security | |

## 2. Ponytail Cleanup

| File | Removed | Reason |
|---|---|---|
| | | |

## 3. Production Engineering

| Feature | Status |
|---|---|
| Docker | |
| GitHub Actions | |
| Render deployment | |
| Health endpoint | |
| Readiness endpoint | |
| Structured logging | |
| Timeouts | |
| Retry handling | |
| Error handling | |
| Security | |

## 4. UI

| Feature | Status |
|---|---|
| Cream/off-white palette | |
| Black primary accent | |
| Inter UI typography | |
| Serif/Times typography | |
| Aparajita Indic support | |
| Responsive layout | |
| Voice UX | |
| Citation UI | |
| Error states | |

## 5. Performance

| Metric | Before | After |
|---|---:|---:|
| P50 | 5.16 ms | |
| P70 | 5.65 ms | |
| P100 | 14.92 ms | |

## 6. Retrieval

| Metric | Before | After |
|---|---:|---:|
| Recall@1 | 0.1400 | |
| Recall@5 | 0.3567 | |
| Recall@10 | 0.4200 | |
| MRR | 0.2301 | |

## 7. Query Robustness

| Query | Result |
|---|---|
| What is a corporation? | |
| What is corporation? | |
| What is corporation | |
| What's a corporation? | |
| Which is a corporation? | |

## 8. Final Verdict

Return exactly one:

```text
TASK 2 READY
```

or

```text
TASK 2 READY WITH DISCLOSED LIMITATIONS
```

or

```text
NOT READY
```

Do not claim readiness if any mandatory requirement has failed.

---

# FINAL PRINCIPLE

The project should feel like:

```text
A serious, polished AI engineering product
```

not:

```text
A college project overloaded with infrastructure buzzwords.
```

Use **Ponytail** aggressively for unnecessary code and complexity, but conservatively for verified functionality.

Correctness > infrastructure quantity.

Reliability > visual effects.

Clarity > complexity.

HH Goa requirements > SDE-2 cosplay.
