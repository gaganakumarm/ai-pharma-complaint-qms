# Assignment Submission

## AI-Powered Pharmaceutical Customer Complaint Management System

- **Candidate:** `[Candidate name]`
- **Repository:** `[Repository URL]`
- **Demo video:** `[3–5 minute reviewer-accessible video URL]`

### Problem solved

Transforms fictional pharmaceutical complaint text or readable PDFs into an editable QA intake draft while keeping persistence and quality decisions under human control.

### Major features

- API/FDF text and PDF extraction
- Structured editable complaint form and conversational corrections
- Quality, severity, risk, and next-action guidance
- Deterministic completeness and possible-duplicate detection
- Advisory RCA/CAPA investigation support
- Explicit PostgreSQL ledger commitment and retrieval

### Technology

React, TypeScript, Vite, Redux Toolkit, Tailwind CSS, FastAPI, Pydantic, LangGraph, Groq, async SQLAlchemy, PostgreSQL, Alembic, Docker Compose, Vitest, Pytest, Ruff, MyPy, and GitHub Actions.

### Setup

```powershell
Copy-Item .env.example .env
docker compose up --build -d
```

Set `GROQ_API_KEY=replace_with_your_groq_api_key`; the configurable model is `openai/gpt-oss-120b`.

### Demo workflow

Process the fictional FDF PDF, review decision-support panels, correct batch/quantity, explicitly commit and retrieve the record, then process the fictional API PDF and demonstrate that processing does not persist automatically.

### Verification summary

- Backend default: 107 passed, 28 credential/environment-gated skips
- PostgreSQL-enabled: 115 passed, 20 credential-gated skips
- Frontend: 21 passed
- Ruff, format, MyPy, ESLint, Prettier, TypeScript, build, audits, Docker health/readiness, deterministic browser acceptance, and fictional FDF/API RCA-CAPA smoke checks passed

### Model and review note

Retired assignment model identifiers were replaced by the environment-configurable `openai/gpt-oss-120b`. AI output is advisory. Root causes are hypotheses, duplicate results are possible matches, and CAPA is not approved or implemented by this application. Authorised QA review is required.

### Limitations

No authentication, OCR, mailbox integration, semantic duplicate matching, regulatory approval, autonomous recall, batch disposition, investigation closure, or electronic signatures.

### Screenshots

- [Capture instructions](screenshots/README.md)
- `[Main workspace screenshot link]`
- `[Decision-support screenshot link]`
- `[Committed complaint screenshot link]`

### Reviewer notes

Use only the fictional files in `sample-data/`. Sprint 5 remains **PASSED WITH EXTERNAL PROVIDER LIMITATION**; Sprint 6 is **PASSED**. See [requirements traceability](requirements-traceability.md) for evidence and honest limitations.
