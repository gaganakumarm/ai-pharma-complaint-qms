# AI-Powered Pharmaceutical Customer Complaint Management System

Sprint 0 provides a production-oriented full-stack foundation: React and TypeScript
on Vite, FastAPI with an async SQLAlchemy PostgreSQL adapter, Docker Compose, tests,
linting, type checks, formatting, migrations, and CI. Complaint processing and AI
features are intentionally not implemented yet.

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

No domain tables exist in Sprint 0, so the initial versions directory is empty.

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
