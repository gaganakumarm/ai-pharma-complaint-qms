# AI-Powered Pharmaceutical Customer Complaint Management System

An assignment-scale complaint-intake and decision-support application for pharmaceutical QA teams working with Active Pharmaceutical Ingredients (APIs) and Finished Dosage Forms (FDFs).

## Problem and solution

Complaint evidence commonly arrives as email-style text or PDF reports. Manual transcription is slow and inconsistent. This application extracts a reviewable draft, highlights missing information and possible duplicates, provides advisory quality/RCA/CAPA support, accepts conversational corrections, and commits only after explicit human action.

It is a demonstration system, not a validated production QMS. Authorised QA personnel remain responsible for investigation, severity, CAPA, disposition, recall, and regulatory decisions.

## Main capabilities

- Manual, text/email-style, and selectable-text PDF intake
- API, FDF, and unknown-product contexts
- Structured extraction into an editable React form
- Category, severity, risk, and next-action recommendations
- Allowlisted conversational corrections with atomic reassessment
- Deterministic completeness and possible-duplicate checks
- Advisory root-cause and corrective/preventive action recommendations
- Explicit PostgreSQL commit, pagination, and UUID retrieval
- Controlled errors, retry-safe drafts, Docker health checks, and CI

## Architecture and stack

The React/TypeScript frontend uses Redux Toolkit, React Hook Form, Zod, Axios, Tailwind CSS, and Inter. FastAPI coordinates strict Pydantic contracts, services, async SQLAlchemy repositories, PostgreSQL, and Alembic. LangGraph sequences normalization, Groq extraction, validation, quality assessment, deterministic completeness, RCA/CAPA generation, and response preparation. PDF and text intake share this graph; corrections use a separate allowlisted patch graph.

Groq SDK behavior stays in the provider adapter, repositories contain only database access, and routes contain HTTP concerns. Processing never persists automatically.

```text
backend/app/
  ai/                 LangGraph workflows, prompts, Groq adapter
  api/                Routes and dependencies
  schemas/            Strict request/response contracts
  services/           Processing and deterministic business logic
  repositories/       PostgreSQL access
  infrastructure/     SQLAlchemy engine, sessions, models
frontend/src/
  app/                 Redux store and hooks
  features/complaints Intake workflow, API adapter, panels, tests
docs/                  Architecture, SRS, API, testing, submission
sample-data/           Fictional FDF, API, and textless PDFs
```

See [architecture.md](docs/architecture.md) and [requirements traceability](docs/requirements-traceability.md).

## Prerequisites

- Docker Desktop with Docker Compose, or
- Python 3.11+, Node.js 22+, npm, and PostgreSQL 16

## Environment setup

```powershell
Copy-Item .env.example .env
```

Configure the ignored local file:

```env
GROQ_API_KEY=replace_with_your_groq_api_key
GROQ_MODEL=openai/gpt-oss-120b
```

Retired assignment model identifiers were replaced by this configurable supported model. Change `GROQ_MODEL` when provider availability changes; never commit `.env`.

## Docker startup

```powershell
docker compose config --quiet
docker compose up --build -d
docker compose ps
```

- Frontend: <http://localhost:5173>
- API docs: <http://localhost:8000/docs>
- Liveness: <http://localhost:8000/health>
- PostgreSQL readiness: <http://localhost:8000/ready>

Docker database credentials are development-only defaults.

## Local development

Backend PowerShell session:

```powershell
Set-Location backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload
```

Frontend PowerShell session:

```powershell
Set-Location frontend
npm install
npm run dev
```

## Database migrations

```powershell
Set-Location backend
.\.venv\Scripts\alembic.exe upgrade head
```

The backend container runs this before startup. The complaints table uses a sequence-backed complaint number and indexes for complaint number, batch, lowercased product name, and creation time.

## API summary

- `POST /api/complaints/process-text` — unsaved text draft
- `POST /api/complaints/process-document` — unsaved text-based PDF draft
- `POST /api/complaints/correct` — unsaved allowlisted correction
- `POST /api/complaints/check-duplicates` — non-persistent duplicate check
- `POST /api/complaints` — explicit commit
- `GET /api/complaints` — newest-first pagination
- `GET /api/complaints/{complaint_id}` — committed record
- `GET /health` and `GET /ready` — liveness and database readiness

Processing responses include quality assessment, completeness, possible duplicates, and advisory RCA/CAPA. They do not expose prompts, raw provider output, PDF bytes, full PDF text, credentials, or database internals.

## Example workflow and sample data

1. Upload `sample-data/fictional-fdf-complaint.pdf`.
2. Review extracted fields, quality guidance, completeness, duplicates, and RCA/CAPA.
3. Correct the fictional batch and quantity conversationally.
4. Review recalculated results and explicitly commit.
5. Retrieve the UUID-backed record.
6. Process `fictional-api-complaint.pdf` and confirm no automatic persistence.

All samples are fictional. Regenerate them with:

```powershell
python sample-data\generate_pdf_samples.py
```

`fictional-textless-complaint.pdf` tests the controlled no-readable-text path. OCR is intentionally not included or required.

## Testing

```powershell
Set-Location backend
.\.venv\Scripts\ruff.exe check app tests
.\.venv\Scripts\ruff.exe format --check app tests
.\.venv\Scripts\mypy.exe app
.\.venv\Scripts\pytest.exe -q
```

PostgreSQL integration:

```powershell
Set-Location ..
docker compose --profile test up -d postgres_test
Set-Location backend
$env:TEST_DATABASE_URL='postgresql+asyncpg://postgres:postgres@localhost:5433/pharma_qms_test'
$env:DATABASE_URL=$env:TEST_DATABASE_URL
.\.venv\Scripts\alembic.exe downgrade base
.\.venv\Scripts\alembic.exe upgrade head
.\.venv\Scripts\pytest.exe -q
```

Frontend:

```powershell
Set-Location ..\frontend
npm audit
npm audit --omit=dev
npm run lint
npm run format
npm run typecheck
npm test
npm run build
```

## Thunder Client, screenshots, and demo

Import collections under `docs/thunder-client/`; select PDF files manually for multipart requests. They contain fictional data and no credentials.

- [Screenshot capture checklist](docs/screenshots/README.md)
- [Submission summary](docs/submission.md)
- Demo video: **add a reviewer-accessible link before submission**

No binary screenshot placeholders are committed.

## Security, privacy, and human review

- Secrets remain in ignored environment files and backend variables.
- Inputs, corrections, uploads, and AI structures are bounded and validated.
- Complaint content is delimited as untrusted evidence.
- Authentication and rate-limit failures are not automatically retried.
- Duplicate results are possible matches, never confirmed duplicates.
- RCA/CAPA is unapproved investigation support with a trusted disclaimer.
- Use only fictional or appropriately controlled data in this assignment system.

## Known limitations

- No authentication, roles, electronic signatures, validated audit trail, or deployment
- No OCR, mailbox integration, embeddings, or semantic duplicate search
- No final regulatory approval, confirmed root cause, autonomous recall, batch disposition, release/rejection, investigation closure, or approved CAPA
- Lexical duplicate scoring and model recommendations require human QA review
- Groq availability and quota remain external dependencies

## Assignment status

- Sprint 0: PASSED
- Sprint 1: PASSED
- Sprint 2: PASSED
- Sprint 3: PASSED
- Sprint 4: PASSED
- Sprint 5: PASSED WITH EXTERNAL PROVIDER LIMITATION
- Sprint 6: PASSED

Sprint 5's deterministic workflow and earlier real correction scenarios passed. A later uninterrupted real-browser rerun was blocked by Groq HTTP 429 and was not represented as successful. Sprint 6's fictional FDF and API RCA/CAPA smoke checks passed.

No repository license is included.
