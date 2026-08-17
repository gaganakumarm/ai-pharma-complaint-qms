# AI-Powered Pharmaceutical Customer Complaint Management System

Sprint 1 provides a non-AI complaint ledger vertical slice: a validated Redux-backed
React form, FastAPI use-case and repository layers, and PostgreSQL persistence with
concurrency-safe human-readable complaint numbers. AI features remain intentionally
unimplemented.

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
`GROQ_API_KEY` only when a later sprint introduces an approved integration; Sprint 0
does not read or transmit it. `GROQ_MODEL` remains environment-configurable and
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
