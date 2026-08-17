# Testing Strategy and Sprint Record

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

### Sprint 2 — Text/email AI intake

**Objective:** LangGraph + Groq structured extraction and form population.

**Gate:** API/FDF/incomplete real smoke tests pass; automated fake-provider graph/API/frontend tests pass; no draft is automatically persisted.

### Sprint 3 — PDF intake

**Objective:** File validation and basic selectable-text extraction using the same graph.

**Gate:** Valid sample PDFs populate the form; invalid and textless documents fail safely; production OCR is not added.

### Sprint 4 — Mandatory quality assessment

**Objective:** Category, severity, initial risk assessment, and suggested next action.

**Gate:** API and FDF assessment contracts validate and display with the QA-review disclaimer.

### Sprint 5 — Conversational corrections

**Objective:** Allowlisted field patches that preserve unrelated data.

**Gate:** Demo correction cases pass, relevant checks recalculate, and malformed corrections cannot damage the draft.

### Sprint 6 — Selected bonuses

**Objective:** Completeness, duplicate detection, and root-cause/CAPA recommendations.

**Gate:** All three features work in API/FDF scenarios and display appropriate uncertainty/review language.

### Sprint 7 — Hardening

**Objective:** Full regression, robustness, security, accessibility, and failure recovery.

**Gate:** All backend/frontend/integration/E2E/build/Docker checks pass with no secrets or critical dependency findings.

### Sprint 8 — Submission

**Objective:** Final README, screenshots, sample documents, product demo, and code walkthrough.

**Gate:** Clean-environment setup works and every submission link/file is verified before the deadline.

## 9. Requirement tracking

| Capability | Type | Sprint | Status |
|---|---|---:|---|
| React, Redux, Inter UI | Mandatory | 0–1 | Implemented |
| FastAPI and PostgreSQL | Mandatory | 0–1 | Implemented |
| Manual form and ledger | Mandatory workflow | 1 | Implemented |
| Groq and LangGraph | Mandatory | 2 | Update after Sprint 2 |
| Text/email intake | Mandatory | 2 | Update after Sprint 2 |
| PDF intake | Mandatory | 3 | Update after Sprint 3 |
| Category/risk/next action | Mandatory | 4 | Update after Sprint 4 |
| Conversational correction | Mandatory | 5 | Update after Sprint 5 |
| Completeness checker | Bonus | 6 | Update after Sprint 6 |
| Duplicate detection | Bonus | 6 | Update after Sprint 6 |
| Root-cause/CAPA | Bonus | 6 | Update after Sprint 6 |

## 10. Final submission checklist

- [ ] Repository is clean and pushed
- [ ] No credentials or private `.env` files are committed
- [ ] Migrations work on a fresh PostgreSQL database
- [ ] All automated and integration tests pass
- [ ] Docker Compose starts all healthy services
- [ ] API and FDF text scenarios pass with real Groq
- [ ] PDF scenario passes
- [ ] Corrections preserve unrelated fields
- [ ] All three bonus features pass
- [ ] README setup works from a clean environment
- [ ] Thunder Client collection contains no secrets
- [ ] Product demonstration video is recorded
- [ ] Code walkthrough video is recorded
- [ ] Submission form is completed before the deadline

## 11. Update policy

After each sprint, update only:

- Sprint status and exact verification evidence
- Requirement-tracking status
- Final checklist items when complete

Do not rewrite historical pass evidence without a documented reason.
