# Test Report

## 1. Scope and status

This report lists what was rerun in the current workspace and which results come from
earlier project testing. Live Groq tests were not repeated because they use external
quota.

Documentation review date: **August 18, 2026**. Add the final Git commit SHA after the
submission commit is created.

Tests and demonstrations use only fictional API and FDF complaint data.

## 2. Test environment

| Area            | Tools and configuration                             |
| --------------- | --------------------------------------------------- |
| Backend         | Python 3.11+, FastAPI, Pydantic, LangGraph          |
| Database        | PostgreSQL 16, async SQLAlchemy, asyncpg, Alembic   |
| Frontend        | React, TypeScript, Vite, Redux Toolkit              |
| Backend tests   | Pytest, pytest-asyncio, HTTPX                       |
| Frontend tests  | Vitest, React Testing Library, user-event           |
| Static analysis | Ruff, strict MyPy, ESLint, Prettier, TypeScript     |
| Runtime         | Docker Compose: PostgreSQL, FastAPI, Nginx frontend |
| AI              | Groq at runtime; predictable fake provider in tests |

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

MyPy covers the application source. Test files are not part of this type-check command.

## 4. Level 2 — Backend automated tests

### Default unit and API suite

```powershell
pytest
```

Rerun result from the project `backend/.venv` on August 18, 2026:

```text
107 passed, 28 skipped
```

Skips are expected for credential- and PostgreSQL-gated cases when their flags or
database URL are absent. Coverage includes schemas, service/repository boundaries,
text and PDF workflows, quality/risk assessment, completeness, duplicate scoring,
corrections, RCA/CAPA safety, error mapping, retry behavior, prompt-injection
resistance, frontend review behavior, and confirmation that processing does not write
to the database. The current application does not authenticate or authorize a QA
reviewer at the API boundary.

### Isolated PostgreSQL integration suite

```powershell
Set-Location ..
docker compose --profile test up -d postgres_test
$env:TEST_DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5433/pharma_qms_test"
Set-Location backend
pytest
Remove-Item Env:TEST_DATABASE_URL
```

Recorded release result; requires the isolated PostgreSQL test profile to reproduce:

```text
115 passed, 20 skipped
```

The remaining skips are credential-gated provider tests. PostgreSQL coverage includes
inserts and retrieval, complaint-number uniqueness, rollback, pagination, ordering,
enum constraints, bounded duplicate queries, self-exclusion, no database writes during
processing, and complaint commit.

## 5. Level 3 — Database migration tests

Migration verification used only the isolated test database. No development database
was downgraded.

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
22 tests passed across 4 files
0 npm vulnerabilities
Production build passed
```

ESLint, Prettier, and TypeScript also passed. Tests cover form validation, Redux draft
state, text/PDF population, assessment and correction states, completeness,
duplicates, RCA/CAPA, stale-result and failure handling, duplicate-submission
prevention, and commit behavior.

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

These infrastructure results come from an earlier full-stack run. Complaint identifiers
and row counts are omitted because they depend on the local database.

## 8. Level 6 — Manual end-to-end test

An earlier browser run used fictional samples and the fake test provider. It verified:

1. FDF PDF extraction into editable fields.
2. API/FDF classification and quality/risk assessment.
3. Completeness, duplicate, and RCA/CAPA panels.
4. Conversational batch and quantity correction with recalculation.
5. Preservation of unrelated values, protected fields, and field clearing.
6. No ledger change during processing or correction.
7. Exactly one new database record after commit.
8. Retrieval of the newly committed complaint by UUID.
9. API PDF assessment without automatic persistence.
10. Text-intake regression.
11. Controlled textless-PDF failure with draft preservation.
12. Backend restart and successful retrieval of the committed record.

Earlier result: **Passed**.

## 9. Real Groq compatibility evidence

Credential-gated checks previously validated FDF/API extraction, quality/risk
assessment, corrections, RCA/CAPA, null preservation, prompt-injection protection,
and application-supplied review disclaimers. Earlier smoke tests also covered fictional
FDF and API RCA/CAPA responses. These tests do not imply authenticated QA approval.

```env
GROQ_MODEL=openai/gpt-oss-120b
```

The live-provider suite was not rerun for this documentation change. HTTP 429 means the
Groq quota was exhausted; the application does not retry that response or write a
complaint. Earlier correction scenarios passed, while a later complete browser rerun
was stopped by HTTP 429. GPT-OSS 20B did not satisfy the response schemas, and the
Gemini experiment is not part of the current code or configuration.

## 10. Security and repository checks

Release checks:

```powershell
git diff --check
git status
git check-ignore .env
git grep -n -E "gsk_[A-Za-z0-9]|GEMINI_API_KEY=.{10,}|GROQ_API_KEY=.{10,}"
```

An earlier repository check confirmed that `.env` was ignored, no API key was tracked,
and generated caches, builds, and local databases were not tracked.

For the August 18, 2026 documentation update, the default backend suite, Ruff lint,
Ruff format, strict application MyPy, frontend tests, ESLint, and the TypeScript
production build were rerun. PostgreSQL, Compose, browser, migration, vulnerability
audit, and real-provider checks were not rerun.

## 11. Final summary

| Check                                            | Result                            |
| ------------------------------------------------ | --------------------------------- |
| Ruff, format, strict application MyPy            | Passed on August 18, 2026         |
| Default Pytest: 107 passed, 28 expected skips    | Passed on August 18, 2026         |
| Frontend lint, 22 tests, and production build    | Passed on August 18, 2026         |
| PostgreSQL Pytest: 115 passed, 20 expected skips | Earlier result; not rerun         |
| Isolated Alembic downgrade/upgrade/re-upgrade    | Earlier result; not rerun         |
| Compose, health, readiness, retrieval, and logs  | Earlier result; not rerun         |
| Fictional browser workflow                       | Earlier result; not rerun         |
| Live Groq workflow                               | Earlier partial result; quota hit |

The default backend suite and static checks plus the frontend test, lint, and build
checks were rerun on August 18, 2026. Other rows record earlier release evidence and
do not claim a new PostgreSQL, Compose, browser, migration, vulnerability-audit, or
real-provider run.
