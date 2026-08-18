# AI-Powered Pharmaceutical Customer Complaint Management System

An assignment-scale quality-management workflow for receiving pharmaceutical customer
complaints, converting unstructured text or selectable-text PDFs into a reviewable
draft, assisting quality assessment, and explicitly committing an authorised record to
a PostgreSQL QMS ledger.

The application supports both active pharmaceutical ingredient (API) and finished
dosage form (FDF) complaint contexts. AI output is advisory: authorised quality
personnel must review every extracted field, assessment, correction, duplicate match,
and RCA/CAPA recommendation before committing a complaint.

> **Screenshot placeholder — main workspace:** Add
> `docs/screenshots/01-main-workspace.png` after capturing the application with only
> fictional data and no credentials or personal information visible.

## Problem and solution

Pharmaceutical complaints commonly arrive as inconsistent emails, narrative text, or
PDF documents. Important product, batch, quantity, defect, and site details can be
difficult to transfer consistently into a structured quality record.

This project provides one controlled workspace that:

- accepts manual, text/email-style, and selectable-text PDF input;
- extracts structured complaint fields through Groq and LangGraph;
- recommends an initial category, severity, risk, and next action;
- supports conversational correction of allowlisted fields;
- calculates completeness and possible duplicates deterministically;
- provides advisory root-cause and CAPA investigation suggestions; and
- writes to PostgreSQL only after an explicit reviewed commit.

It does not replace an approved QMS or make final regulatory, recall, batch-release,
batch-rejection, investigation-closure, root-cause, or CAPA decisions.

## Main capabilities

- Editable complaint form for API and FDF complaints
- Manual complaint entry without an AI call
- Structured extraction from pasted complaint text
- Selectable-text PDF extraction with bounded upload, page, and text limits
- Preliminary pharmaceutical quality and risk assessment
- Suggested `MINOR`, `MAJOR`, or `CRITICAL` severity
- Conversational correction with protected-field and explicit-clearing controls
- Deterministic five-field completeness calculation
- Bounded PostgreSQL-backed duplicate candidate retrieval and deterministic scoring
- Advisory RCA/CAPA hypotheses, evidence needs, and action suggestions
- Explicit QMS commit with a UUID and generated complaint number
- Pagination and retrieval of committed complaints
- Standard API error envelope, liveness, and PostgreSQL readiness endpoints

## Architecture

The system separates presentation, HTTP transport, application coordination, domain
rules, AI integration, document handling, repositories, and database infrastructure.
This provides practical dependency inversion and keeps transaction ownership outside
the repository and AI layers.

> **Diagram placeholder — system architecture:** Export the verified Mermaid component
> diagram from [docs/architecture.md](docs/architecture.md) as
> `docs/screenshots/system-architecture.png`, then replace this placeholder with the
> image.

Current logical flow:

```text
React UI → Redux Toolkit → FastAPI routes → Application services
                                      ├─→ LangGraph → Groq
                                      ├─→ Deterministic rules
                                      ├─→ PDF text extraction
                                      └─→ Complaint repository → Async SQLAlchemy → PostgreSQL
```

AI processing returns an in-memory draft. The persistence path is separate:

```text
Reviewed form → Complaint service → Complaint repository → PostgreSQL transaction
```

Detailed diagrams and boundaries are documented in
[System Architecture](docs/architecture.md) and
[LangGraph Workflows](docs/langgraph-workflows.md).

## LangGraph workflow

A complaint-processing request coordinates these stages:

1. Normalize input.
2. Extract complaint fields.
3. Validate extraction.
4. Assess pharmaceutical quality and risk.
5. Validate the assessment and trusted disclaimer.
6. Calculate deterministic completeness.
7. Generate advisory RCA/CAPA recommendations.
8. Validate RCA/CAPA safety rules.
9. Prepare the response.

A separate correction graph extracts an allowlisted patch, validates and merges it
atomically, recalculates warnings, and conditionally regenerates assessment and
RCA/CAPA results. Neither graph persists a complaint.

One processing request may use separate structured Groq calls for extraction,
quality/risk assessment, and RCA/CAPA generation. Provider authentication, quota,
latency, and token usage therefore apply per model call.

## Technology stack

| Area                 | Technology                                                   |
| -------------------- | ------------------------------------------------------------ |
| Frontend             | React, TypeScript, Vite, Redux Toolkit, React Redux          |
| Forms and validation | React Hook Form, Zod                                         |
| Styling              | Tailwind CSS, Inter                                          |
| HTTP client          | Axios                                                        |
| Backend              | Python 3.11+, FastAPI, Uvicorn, Pydantic Settings            |
| AI orchestration     | LangGraph, Groq SDK, strict Pydantic schemas                 |
| PDF handling         | PyMuPDF                                                      |
| Persistence          | PostgreSQL 16, SQLAlchemy 2 async, asyncpg, Alembic          |
| Testing              | Pytest, pytest-asyncio, HTTPX, Vitest, React Testing Library |
| Quality              | Ruff, strict MyPy, ESLint, Prettier, TypeScript              |
| Delivery             | Docker Compose, Nginx, GitHub Actions                        |

## Project structure

```text
backend/
  app/
    ai/                 Provider contract, Groq adapter, prompts, graphs
    api/routes/         FastAPI HTTP endpoints
    core/               Settings and error handling
    domain/             Complaint enums and domain concepts
    infrastructure/     Async database engine, sessions, models
    repositories/       Complaint persistence operations
    schemas/            Strict API and AI data contracts
    services/           Application use cases and deterministic rules
  alembic/              Database migrations
  tests/                Unit, API, provider, PDF, and PostgreSQL tests
frontend/
  src/
    app/                 Redux store and typed hooks
    features/complaints/ Complaint workspace, state, API, schemas
    shared/api/          Shared Axios client
    styles/              Tailwind and Inter styles
  scripts/               Deterministic manual acceptance runner
docs/                     Architecture, SRS, database, API, AI, and workflow docs
sample-data/              Fictional FDF, API, and textless PDF samples
```

## Prerequisites

- Docker Desktop with Docker Compose, or:
  - Python 3.11 or newer
  - Node.js 22 and npm
  - PostgreSQL 16
- A Groq API key only when exercising real AI processing

All commands below are written for Windows PowerShell and run from the repository
root unless a section changes directory.

## Environment setup

Create the ignored local environment file:

```powershell
Copy-Item .env.example .env
```

For real Groq processing, edit `.env` locally without committing or displaying its
contents:

```env
GROQ_API_KEY=replace_with_your_groq_api_key
GROQ_MODEL=openai/gpt-oss-120b
```

`GROQ_MODEL` remains configurable. Retired models referenced in the original
assignment were replaced by the currently configured supported default. Groq is the
only production AI provider in the stable source; there is no automatic Gemini
fallback. Manual entry and review remain available when AI processing cannot run.

Never commit `.env`, credentials, complaint personal information, prompts, or raw
provider responses.

## Start with Docker Compose

```powershell
docker compose config --quiet
docker compose up --build -d
docker compose ps
```

Open:

- Frontend: <http://localhost:5173>
- Swagger UI: <http://localhost:8000/docs>
- Health: <http://localhost:8000/health>
- Readiness: <http://localhost:8000/ready>

Inspect or stop the stack:

```powershell
docker compose logs --tail 100 backend frontend postgres
docker compose down
```

`docker compose down` preserves the named PostgreSQL volume. Do not add `--volumes`
unless deleting local ledger data is intentional.

## Local development

Start PostgreSQL:

```powershell
docker compose up -d postgres
```

Backend terminal:

```powershell
Set-Location backend
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Frontend terminal:

```powershell
Set-Location frontend
npm ci
npm run dev
```

When the backend runs outside Compose, the root `.env.example` database URL points to
PostgreSQL at `localhost:5432`. The Compose backend uses the service hostname
`postgres` automatically.

## Database migrations

Run from `backend` with the virtual environment active:

```powershell
alembic current
alembic upgrade head
```

Migration history is in `backend/alembic/versions`. Do not downgrade a development or
shared database merely to verify the application.

## Quality and test commands

Backend checks, from `backend`:

```powershell
ruff check .
ruff format --check .
mypy app
pytest
```

PostgreSQL-enabled tests use the isolated test service:

```powershell
Set-Location ..
docker compose --profile test up -d postgres_test
$env:TEST_DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5433/pharma_qms_test"
Set-Location backend
pytest
Remove-Item Env:TEST_DATABASE_URL
```

Frontend checks, from `frontend`:

```powershell
npm audit
npm audit --omit=dev
npm run lint
npm run format
npm run typecheck
npm test
npm run build
```

Credential-gated real-provider smoke tests are intentionally separate from the
default deterministic suite. They consume external quota and must use only fictional
data.

## Example reviewer workflow

1. Open the complaint workspace.
2. Paste fictional complaint text or choose a fictional FDF/API PDF from
   `sample-data`.
3. Process the input and review the extracted editable fields.
4. Review category, severity, risk, next action, completeness, duplicates, and
   RCA/CAPA recommendations.
5. Correct an allowlisted value conversationally and verify reassessment behavior.
6. Manually edit any remaining field as needed.
7. Explicitly commit the reviewed complaint.
8. Record the generated complaint number and retrieve the committed UUID through the
   API.

Processing, correction, completeness, duplicate checking, and RCA/CAPA generation do
not insert ledger rows. Only `POST /api/complaints` commits a complaint.

## Fictional sample data

The repository includes:

- `sample-data/fictional-fdf-complaint.pdf`
- `sample-data/fictional-api-complaint.pdf`
- `sample-data/fictional-textless-complaint.pdf`
- `sample-data/generate_pdf_samples.py`

The textless document exercises the controlled no-readable-text failure path. The
samples are fictional and must not be replaced with real patient, customer, or
commercially sensitive complaint data in screenshots or demonstrations.

## Screenshots and diagrams

Do not fabricate screenshots or commit images containing keys, personal information,
absolute paths, developer tools, or raw provider responses.

> **Screenshot placeholder — populated FDF form:**
> `docs/screenshots/02-fdf-populated-form.png`

> **Screenshot placeholder — quality and risk assessment:**
> `docs/screenshots/03-quality-risk-panel.png`

> **Screenshot placeholder — conversational correction:**
> `docs/screenshots/04-conversational-correction.png`

> **Screenshot placeholder — completeness and duplicate results:**
> `docs/screenshots/05-completeness-panel.png` and
> `docs/screenshots/06-duplicate-panel.png`

> **Screenshot placeholder — RCA/CAPA recommendations:**
> `docs/screenshots/07-rca-capa-panel.png`

> **Screenshot placeholder — committed complaint:**
> `docs/screenshots/08-committed-complaint.png`

See the [screenshot capture checklist](docs/screenshots/README.md) for recommended
filenames and safe capture instructions.

## Documentation

- [System architecture](docs/architecture.md)
- [Software requirements specification](docs/srs.md)
- [LangGraph workflows](docs/langgraph-workflows.md)
- [LLM integration and safety](docs/llm-integration-and-safety.md)
- [Database design](docs/database-design.md)
- [API documentation](docs/api-documentation.md)
- [Testing and sprint report](docs/testing-and-sprints.md)
- [Requirements traceability](docs/requirements-traceability.md)
- [Submission summary](docs/submission.md)
- [Screenshot capture checklist](docs/screenshots/README.md)

## Security, privacy, and human review

- Keep credentials in the ignored local `.env` or deployment secret storage.
- Do not expose the application directly to an untrusted network; authentication and
  role-based access control are outside this assignment.
- Do not log complaint content, customer information, prompts, or raw model output.
- Treat uploaded files and complaint narratives as untrusted data.
- Treat every AI result, duplicate match, and RCA/CAPA suggestion as advisory.
- Require authorised pharmaceutical quality review before explicit commit or any
  downstream action.

## Known limitations

- This is not a validated production QMS and has no authentication, authorisation,
  electronic signatures, or formal audit-signature workflow.
- PDF intake supports selectable text only; production OCR is not implemented.
- Email-style intake means pasted narrative content; mailbox integration is not
  implemented.
- Duplicate detection is deterministic lexical matching, not semantic matching.
- External Groq availability, quota, latency, and model support are outside the
  application’s control.
- The application does not autonomously recall products, dispose batches, approve or
  close CAPA, confirm root cause, close investigations, or make regulatory decisions.

## Assignment status

The implemented assignment scope covers the full complaint intake, correction,
quality-support, deterministic enhancement, and explicit-persistence workflow. The
stable production AI integration is Groq; deterministic providers remain test-only.
Historical external-provider limitations do not weaken the deterministic safety or
manual-review boundaries.

## Demo video

> **Demo video placeholder:** Add a public or reviewer-accessible 3–5 minute demo link
> here after recording the fictional FDF/API workflow. Verify that no credential,
> personal information, local absolute path, or raw provider response is visible.
