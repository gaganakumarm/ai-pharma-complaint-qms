# Final Test Report

## 1. Scope and status

This report consolidates the accepted verification evidence for the AI-Powered
Pharmaceutical Customer Complaint Management System at six testing levels. It records
previously completed release gates; real Groq tests were not repeated for this
documentation-only update because they consume external quota.

- Sprints 0–4: **PASSED**
- Sprint 5: **PASSED WITH EXTERNAL PROVIDER LIMITATION**
- Sprint 6: **PASSED**

Only fictional API and FDF complaint data is authorised for testing and demonstrations.

## 2. Test environment

| Area            | Tools and configuration                                       |
| --------------- | ------------------------------------------------------------- |
| Backend         | Python 3.11+, FastAPI, Pydantic, LangGraph                    |
| Database        | PostgreSQL 16, async SQLAlchemy, asyncpg, Alembic             |
| Frontend        | React, TypeScript, Vite, Redux Toolkit                        |
| Backend tests   | Pytest, pytest-asyncio, HTTPX                                 |
| Frontend tests  | Vitest, React Testing Library, user-event                     |
| Static analysis | Ruff, strict MyPy, ESLint, Prettier, TypeScript               |
| Runtime         | Docker Compose: PostgreSQL, FastAPI, Nginx frontend           |
| AI              | Groq in production; deterministic fake provider in tests only |

## 3. Level 1 — Backend static checks

Run from `backend`:

```powershell
ruff check .
ruff format --check .
mypy app
```

| Check       | Recorded result                        |
| ----------- | -------------------------------------- |
| Ruff lint   | Passed with no violations              |
| Ruff format | Passed                                 |
| Strict MyPy | Passed for 39 application source files |

The strict gate covers application source. Tests are excluded because test-double
typing noise is not part of the accepted application gate.

## 4. Level 2 — Backend automated tests

### Default unit and API suite

```powershell
pytest
```

Recorded result:

```text
107 passed, 28 skipped
```

Skips are expected for credential- and PostgreSQL-gated cases when their flags or
database URL are absent. Coverage includes schemas, service/repository boundaries,
text and PDF workflows, quality/risk assessment, completeness, duplicate scoring,
corrections, RCA/CAPA safety, error mapping, retry behavior, prompt-injection
resistance, trusted human-review controls, and processing non-persistence.

### Isolated PostgreSQL integration suite

```powershell
Set-Location ..
docker compose --profile test up -d postgres_test
$env:TEST_DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5433/pharma_qms_test"
Set-Location backend
pytest
Remove-Item Env:TEST_DATABASE_URL
```

Recorded result:

```text
115 passed, 20 skipped
```

The remaining skips are credential-gated provider tests. PostgreSQL coverage includes
inserts and retrieval, complaint-number uniqueness, rollback, pagination, ordering,
enum constraints, bounded duplicate queries, self-exclusion, processing
non-persistence, and explicit commit.

## 5. Level 3 — Database migration tests

Migration verification used only the isolated test database. The development ledger
containing 21 complaint records was not downgraded.

Verified sequence:

1. Upgrade an empty test database to Alembic head.
2. Downgrade the isolated database to base.
3. Upgrade it to head again.
4. Re-run the head upgrade to verify current-state behavior.
5. Restart the backend normally and retrieve an existing record.

Recorded result: **PASSED**. The PostgreSQL enums, complaint-number sequence, table,
constraints, and indexes match [database-design.md](database-design.md).

## 6. Level 4 — Frontend tests

Run from `frontend`:

```powershell
npm audit
npm audit --omit=dev
npm run lint
npm run format
npm run typecheck
npm test
npm run build
```

`npm run format` invokes the non-mutating `prettier --check .` script.

Recorded results:

```text
21 tests passed across 4 files
0 npm vulnerabilities
Production build passed
```

ESLint, Prettier, and TypeScript also passed. Tests cover form validation, Redux draft
state, text/PDF population, assessment and correction states, completeness,
duplicates, RCA/CAPA, stale-result and failure handling, duplicate-submission
prevention, and explicit commit behavior.

## 7. Level 5 — API and infrastructure tests

```powershell
docker compose config --quiet
docker compose up --build -d
docker compose ps
curl.exe http://localhost:5173
curl.exe http://localhost:8000/health
curl.exe http://localhost:8000/ready
curl.exe "http://localhost:8000/api/complaints?page=1&page_size=5"
curl.exe "http://localhost:8000/api/complaints/7f94a4c6-d200-459f-acb3-bf0e3c02d44f"
```

| Check                        | Recorded result                                       |
| ---------------------------- | ----------------------------------------------------- |
| Docker Compose configuration | Passed                                                |
| PostgreSQL                   | Healthy                                               |
| Backend                      | Healthy                                               |
| Frontend                     | HTTP 200                                              |
| `GET /health`                | HTTP 200, `{"status":"ok"}`                           |
| `GET /ready`                 | HTTP 200, `{"status":"ready"}` via Compose PostgreSQL |
| Complaint listing            | HTTP 200                                              |
| Recent service logs          | No release-blocking runtime errors                    |

Known-record read-only verification:

| Field            | Value                                  |
| ---------------- | -------------------------------------- |
| UUID             | `7f94a4c6-d200-459f-acb3-bf0e3c02d44f` |
| Complaint number | `CMP-2026-000021`                      |
| Batch            | `BMX240602`                            |
| Quantity         | `48 capsules`                          |

No record was created, updated, or deleted by this verification.

## 8. Level 6 — Manual end-to-end test

The final controlled browser workflow used fictional samples and the deterministic
test provider. It verified:

1. FDF PDF extraction into editable fields.
2. API/FDF classification and quality/risk assessment.
3. Completeness, duplicate, and advisory RCA/CAPA panels.
4. Conversational batch and quantity correction with recalculation.
5. Preservation of unrelated values, protected fields, and explicit clearing.
6. No ledger change during processing or correction.
7. Exactly one ledger increase, from 20 to 21, after explicit commit.
8. Retrieval of complaint `CMP-2026-000021` by UUID.
9. API PDF assessment without automatic persistence.
10. Text-intake regression.
11. Controlled textless-PDF failure with draft preservation.
12. Backend restart and successful retrieval of the committed record.

Recorded result: **PASSED**.

## 9. Real Groq compatibility evidence

Credential-gated checks previously validated FDF/API extraction, quality/risk
assessment, corrections, RCA/CAPA, null preservation, prompt-injection protection,
and human-review enforcement. Sprint 6 also recorded successful fictional FDF and API
RCA/CAPA smoke verification under strict schemas.

```env
GROQ_MODEL=openai/gpt-oss-120b
```

The suite was not rerun for this documentation change. HTTP 429 is an external quota
condition and is not automatically retried. It cannot modify the ledger. GPT-OSS 20B
failed strict compatibility; the rejected Gemini experiment is absent from stable
source and runtime configuration.

Sprint 5 remains **PASSED WITH EXTERNAL PROVIDER LIMITATION**: deterministic and
earlier real correction scenarios passed, while a later uninterrupted real-provider
browser rerun was blocked by HTTP 429.

## 10. Security and repository checks

Release checks:

```powershell
git diff --check
git status
git check-ignore .env
git grep -n -E "gsk_[A-Za-z0-9]|GEMINI_API_KEY=.{10,}|GROQ_API_KEY=.{10,}"
```

Recorded release verification confirmed that `.env` is ignored, no API key is
tracked, generated caches/builds/local databases are not tracked, and Gemini
experimental files are absent from stable source.

For this documentation-only update, only Prettier, relative Markdown links,
`git diff --check`, and working-tree status were rerun, as required.

## 11. Final summary

|    Level | Gate                                                   | Result                                   |
| -------: | ------------------------------------------------------ | ---------------------------------------- |
|        1 | Ruff, format, strict application MyPy                  | PASSED                                   |
|        2 | Default Pytest: 107 passed, 28 expected skips          | PASSED                                   |
|        2 | PostgreSQL Pytest: 115 passed, 20 expected skips       | PASSED                                   |
|        3 | Isolated Alembic downgrade/upgrade/re-upgrade          | PASSED                                   |
|        4 | Frontend checks, 21 tests, build, zero vulnerabilities | PASSED                                   |
|        5 | Compose, HTTP, health/readiness, retrieval, logs       | PASSED                                   |
|        6 | Deterministic fictional browser workflow               | PASSED                                   |
| External | Real Groq compatibility                                | PASSED WITH RECORDED EXTERNAL LIMITATION |

No application suite was rerun for this documentation-only change. This report records
the previously accepted release evidence and does not claim a new real-provider run.
