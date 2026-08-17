# Testing Strategy and Sprint Record

Final status: Sprints 0–4 and Sprint 6 are **PASSED**. Sprint 5 remains **PASSED WITH
EXTERNAL PROVIDER LIMITATION**.

## 1. Purpose

This document defines the project’s testing approach, quality gates, sprint sequence, and evolving verification record. The strategy remains stable; sprint status and exact results are updated after each accepted sprint.

## 2. Testing principles

- Test behaviour and contracts, not internal implementation details.
- Use real PostgreSQL for persistence integration tests.
- Use a deterministic fake Groq provider for automated AI tests.
- Test AI schema validity rather than exact generated wording.
- Keep each sprint independently testable and reviewable.
- Do not advance while the current acceptance gate is failed.
- Preserve user input during recoverable failures.

## 3. Toolset

| Area | Tools |
|---|---|
| Backend unit/API | Pytest, pytest-asyncio, HTTPX |
| Database integration | Dedicated PostgreSQL test service/container |
| AI automation | Fake provider, LangGraph node/graph tests |
| Real AI verification | Controlled Groq smoke tests |
| Frontend | Vitest, React Testing Library, user-event |
| Frontend API mocking | MSW when introduced |
| Browser acceptance | Automated Microsoft Edge/Playwright-style flow as configured |
| Manual API | Thunder Client, Swagger UI |
| Python quality | Ruff, strict MyPy |
| Frontend quality | ESLint, Prettier, TypeScript compiler |
| Security/dependencies | `npm audit`, production-only audit |
| Runtime | Docker Compose health and readiness |
| CI | GitHub Actions |

## 4. Test levels

### Unit tests

Cover pure validation, normalization, completeness, correction merge, duplicate scoring, schemas, reducers, and utilities.

### Integration tests

Cover FastAPI routes, service/repository collaboration, PostgreSQL constraints, transactions, migrations, LangGraph composition, and frontend API-state integration.

### End-to-end tests

Cover the critical user workflows through the running frontend, backend, and PostgreSQL stack.

### Manual smoke tests

Thunder Client verifies individual endpoints. Real Groq smoke tests verify live model/schema compatibility without making CI depend on credentials or rate limits.

## 5. Critical test inventory

### Ledger and database

- Schema trimming and blank rejection
- Enum and unknown-field validation
- Concurrency-safe unique complaint numbers
- Insert, retrieve, pagination, and ordering
- Partial pharmaceutical date preservation
- Constraint enforcement
- Transaction rollback without partial rows
- Migration on empty database
- Persistence after backend restart

### Text and PDF intake

- Valid API and FDF extraction contracts
- Incomplete complaint retains null values
- Batch identifiers are preserved exactly
- Blank/oversized input rejection
- Valid multipage text PDF
- Unsupported, oversized, corrupt, and textless PDF errors
- Processing does not create a ledger row

### LangGraph and Groq

- Expected node execution
- Valid state transitions
- Pydantic structured-output validation
- One controlled malformed-output retry
- No inappropriate retry for authentication failure
- Timeout and rate-limit mapping
- Prompt-injection text treated as complaint data
- Fake-provider automated tests
- Separate live-model smoke tests

### Assessment and corrections

- Severity enum validation
- Risk contract and disclaimer
- One-field and multi-field correction
- Unrelated fields remain unchanged
- Unknown/protected fields are rejected
- Relevant analysis recalculates after corrections
- Failed correction preserves the draft

### Selected bonuses

- Required/recommended missing fields
- Completeness recalculation
- Duplicate score range, ranking, and reasons
- Self-match exclusion
- Root-cause/CAPA schema and disclaimer

### Frontend

- Complete accessible form rendering
- Required validation
- Redux draft updates
- Status transitions
- Automatic population
- Null results do not erase values
- Loading, error, retry, and reset behaviour
- Duplicate-submit prevention
- Commit success and complaint number
- Responsive, unclipped layout

## 6. Real Groq smoke scenarios

1. FDF discoloration complaint
2. API foreign-matter complaint
3. Incomplete complaint
4. Conversational batch/quantity correction
5. Embedded instruction attempting to alter extraction

Assertions focus on schema validity, evidence preservation, null handling, safe errors, and identifier accuracy—not exact prose.

## 7. Sprint acceptance process

1. Inspect repository and Git status.
2. Implement only the sprint scope.
3. Add or update relevant tests.
4. Run Python lint, format, typing, and tests.
5. Run frontend lint, format, typing, tests, audit, and build.
6. Validate migrations and PostgreSQL integration.
7. Rebuild and start Docker Compose.
8. Verify health, readiness, and container logs.
9. Run Thunder Client and browser acceptance.
10. Fix all failures and rerun affected gates.
11. Report exact evidence and known limitations.
12. Mark PASSED or FAILED.
13. Commit only after PASS.

## 8. Sprint record

### Sprint 0 — Foundation — PASSED

Delivered React/Redux, FastAPI, PostgreSQL, Docker Compose, settings, health/readiness, CI, linting, typing, and baseline tests. Docker build contexts were reduced to exclude dependencies and artifacts. Dependency audits reported zero vulnerabilities. PostgreSQL-backed readiness was verified.

### Sprint 1 — Complaint domain and QMS ledger — PASSED

Delivered the complete manual form, Redux draft, Zod/React Hook Form validation, API/service/repository layers, SQLAlchemy model, Alembic migration, sequence-based complaint numbers, commit/list/detail endpoints, Thunder Client collection, and browser acceptance.

Recorded evidence:

- Backend: 16 tests passed
- Frontend: 3 test files and 6 tests passed
- Migration upgrade, downgrade, and re-upgrade passed
- PostgreSQL integration and rollback passed
- Browser status flow: Pending Triage → Ready to Commit → COMMITTED
- `CMP-2026-000002` remained retrievable after backend restart
- Static checks, production build, audits, and Docker health passed

### Sprint 2 — Text/email AI intake — PASSED

**Objective:** LangGraph + Groq structured extraction and form population.

Recorded evidence: backend Ruff/format/MyPy passed; 37 tests passed and 4 live tests
were skipped by default; all 4 real Groq smoke cases passed; frontend lint, format,
typing, 10 tests, build, and both npm audits passed; Docker health/readiness and browser
commit/restart verification passed; ledger count was unchanged by text processing.

### Sprint 3 — PDF intake — PASSED

**Objective:** File validation and basic selectable-text extraction using the same graph.

Recorded evidence: Ruff and format passed; strict MyPy passed for all 46 backend source
and test files; 58 tests passed with 7 credential-gated live tests skipped; all 3 real
PDF/Groq smoke tests passed. Frontend lint, format, typing, 14 tests, production build,
and both npm audits passed. FDF/API browser extraction, controlled textless failure,
explicit PDF commit, backend restart retrieval, Docker health, and PostgreSQL readiness
passed. PDF processing was proven not to change the ledger count. Production OCR was
not added.

### Sprint 4 — Mandatory quality assessment — PASSED

**Objective:** Category, severity, initial risk assessment, and suggested next action.

Recorded evidence: Ruff and format passed; strict MyPy passed for 49 backend source and
test files; 80 PostgreSQL-backed tests passed with 13 credential-gated live tests
skipped; migrations passed. Nine real assessment/PDF Groq scenarios passed and the four
text/Groq regression scenarios passed. Frontend lint, format, typing, 16 tests, build,
and both npm audits passed. Browser acceptance verified assessed FDF/API inputs,
NEEDS_INFORMATION handling, trusted disclaimer, editable fields, textless-PDF draft
preservation, explicit commit, non-persistence before commit, and restart retrieval.
Docker health, PostgreSQL readiness, frontend HTTP, and logs passed.

### Sprint 5 — Conversational corrections — PASSED WITH EXTERNAL PROVIDER LIMITATION

**Objective:** Allowlisted field patches that preserve unrelated data.

The complete deterministic correction workflow passed, including clarification,
protected fields, clearing, controlled failure/retry, explicit commit, and restart
retrieval. Seven earlier real-Groq correction scenarios passed. Later attempts to run
one uninterrupted real-provider browser workflow were blocked by Groq HTTP 429, so
that later full browser run is not claimed as passed.

### Sprint 6 — Selected bonuses — PASSED

**Objective:** Completeness, duplicate detection, and root-cause/CAPA recommendations.

Completeness, deterministic duplicate detection, and advisory RCA/CAPA passed unit,
PostgreSQL, frontend, Docker, and complete deterministic browser verification. One
fictional FDF and one fictional API RCA/CAPA real-provider smoke check passed strict
schema and human-review validation.

## 9. Requirement tracking

| Capability | Type | Sprint | Status |
|---|---|---:|---|
| React, Redux, Inter UI | Mandatory | 0–1 | Implemented |
| FastAPI and PostgreSQL | Mandatory | 0–1 | Implemented |
| Manual form and ledger | Mandatory workflow | 1 | Implemented |
| Groq and LangGraph | Mandatory | 2 | Implemented |
| Text/email intake | Mandatory | 2 | Implemented |
| PDF intake | Mandatory | 3 | Implemented |
| Category/risk/next action | Mandatory | 4 | Implemented |
| Conversational correction | Mandatory | 5 | Passed with external provider limitation |
| Completeness checker | Bonus | 6 | Implemented and passed |
| Duplicate detection | Bonus | 6 | Implemented and passed |
| Root-cause/CAPA | Bonus | 6 | Implemented and passed |

## 10. Final submission checklist

- [ ] Repository is clean and pushed
- [ ] No credentials or private `.env` files are committed
- [x] Migrations work on a fresh PostgreSQL database
- [x] All automated and integration tests pass
- [x] Docker Compose starts all healthy services
- [x] Controlled API and FDF Groq smoke evidence is recorded
- [x] PDF scenario passes with deterministic acceptance
- [x] Corrections preserve unrelated fields
- [x] All three bonus features pass
- [x] README provides clean-environment PowerShell setup
- [x] Thunder Client collection contains no secrets
- [ ] Product demonstration video is recorded
- [ ] Code walkthrough video is recorded
- [ ] Submission form is completed before the deadline

## 11. Update policy

After each sprint, update only:

- Sprint status and exact verification evidence
- Requirement-tracking status
- Final checklist items when complete

Do not rewrite historical pass evidence without a documented reason.
## Sprint 6

Acceptance covers pure completeness and similarity boundaries, bounded PostgreSQL
candidate retrieval, strict RCA/CAPA schema and safety rejection, shared text/PDF
LangGraph behavior, correction recalculation/preservation, Redux reset/stale behavior,
accessible panels, non-persistence, and explicit commit/restart retrieval. The complete
browser workflow uses the deterministic fake provider. Real Groq verification is
limited to one fictional FDF and one fictional API smoke scenario when quota permits;
HTTP 429 is recorded as an external-provider limitation and is never looped.

Acceptance status: **PASSED**. The complete deterministic browser workflow and both
single-call fictional FDF/API RCA-CAPA provider smoke checks passed on 2026-08-18.

## Final release review

The 2026-08-18 release gate passed Ruff, Ruff formatting, strict MyPy (39
application source files), 107 default tests with 28 database/provider skips, and
115 isolated-PostgreSQL tests with 20 provider skips. Alembic downgrade to base,
upgrade to head, and an idempotent re-upgrade passed.

Frontend ESLint, Prettier, TypeScript, 21 Vitest tests, production build, and both
npm audit modes passed with zero vulnerabilities. Docker Compose validation and
rebuild passed; PostgreSQL and backend were healthy, the frontend returned HTTP
200, and both health endpoints returned HTTP 200.

One final deterministic browser workflow processed fictional FDF and API PDFs,
recalculated corrections, verified completeness, duplicate, and RCA/CAPA panels,
and committed exactly one FDF record: `CMP-2026-000021`. The ledger moved from
20 to 21 only at explicit commit. The committed record was retrieved after a
backend restart. No real-provider request was made during this release review.
