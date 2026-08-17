# AI-Powered Pharmaceutical Customer Complaint Management System

Sprint 1 provides the complaint ledger and explicit commit workflow. Sprint 2 adds
non-persistent text and email extraction through a compiled LangGraph
workflow and the official Groq SDK. Extracted values populate the editable Redux draft
but are never committed until the user explicitly selects **Commit to QMS Ledger**.
Sprint 3 adds bounded PDF upload and basic selectable-text extraction with PyMuPDF.
PDF and pasted-text intake converge on the same AI workflow. OCR and quality-risk
decisions remain out of scope.

## Prerequisites

- Docker Desktop with Docker Compose, or
- Python 3.11+, Node.js 22+, npm, and PostgreSQL 16

## Run with Docker

```bash
cp .env.example .env
docker compose up --build
```

Open the frontend at <http://localhost:5173>. Operational endpoints are available at
<http://localhost:8000/health> and <http://localhost:8000/ready>; API documentation is
at <http://localhost:8000/docs>.

The bundled Docker database credentials are development-only defaults. Set
`GROQ_API_KEY` to enable text or PDF extraction. `GROQ_MODEL` remains environment-configurable and
defaults to the supported Groq production model `openai/gpt-oss-120b`.

## Run locally

Start PostgreSQL and copy `.env.example` to `.env`. From `backend`:

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
uvicorn app.main:app --reload
```

From `frontend` in a second terminal:

```bash
npm install
npm run dev
```

## Database migrations

From `backend`, with `DATABASE_URL` configured:

```bash
alembic upgrade head
alembic revision --autogenerate -m "describe change"
```

The backend container runs `alembic upgrade head` before Uvicorn starts. This command
is idempotent, so restarts preserve the PostgreSQL volume and safely check migrations.

Manual commits require customer name, product name, batch/lot number, complaint
category, and complaint description. Pharmaceutical dates remain text so partial or
source-faithful values such as `March 2026` and `Not Provided` are preserved.

## API

- `POST /api/complaints` commits a complaint and returns HTTP 201.
- `GET /api/complaints?page=1&page_size=20` lists newest complaints first.
- `GET /api/complaints/{id}` retrieves a committed record.
- `POST /api/complaints/process-text` extracts a draft from pasted complaint text.
- `POST /api/complaints/process-document` accepts multipart field `file` containing
  a text-based PDF and returns an unsaved draft plus safe document metadata.

Text processing requires `GROQ_API_KEY`. `GROQ_MODEL` remains configurable and the
default uses Groq strict JSON Schema output. `MAX_TEXT_INPUT_LENGTH` defaults to 20,000.
PDF uploads default to 10 MB, 50 pages, and 20,000 extracted characters through
`MAX_UPLOAD_SIZE_MB`, `MAX_PDF_PAGES`, and `MAX_PDF_TEXT_LENGTH`. Files are checked by
extension, MIME type, `%PDF-` signature, readability, encryption state, page count, and
selectable text before AI processing. Scanned/textless PDFs return a controlled error;
OCR is not included.
Provider authentication, timeout, rate-limit, malformed-output, and availability
failures use the standard API error contract. The default test suite uses fake
providers; run real smoke tests explicitly with `RUN_GROQ_SMOKE=1`.

Recreate the fictional demonstration PDFs with:

```bash
python sample-data/generate_pdf_samples.py
```

The safe Thunder Client export is under `docs/thunder-client/`.

## PostgreSQL integration tests

```bash
docker compose --profile test up -d postgres_test
cd backend
set TEST_DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5433/pharma_qms_test
set DATABASE_URL=%TEST_DATABASE_URL%
alembic downgrade base
alembic upgrade head
pytest
```

The test database uses a separate temporary container and never touches development
data.

## Quality checks

```bash
cd backend
ruff check .
ruff format --check .
mypy app tests
pytest

cd ../frontend
npm run lint
npm run format
npm run typecheck
npm test
npm run build

cd ..
docker compose config
```

GitHub Actions runs these backend and frontend checks on every push and pull request.
See [docs/architecture.md](docs/architecture.md) for the package responsibilities.
