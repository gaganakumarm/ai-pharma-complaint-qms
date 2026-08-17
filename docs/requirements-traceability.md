# Requirements Traceability

Status reflects the final assignment implementation. “Advisory” means authorised QA review remains mandatory.

| Requirement | Status | Backend | Frontend | Endpoint | Test evidence | Limitation |
|---|---|---|---|---|---|---|
| Text/email-style intake | Implemented | `ai/graph.py`, `services/text_processing.py` | `ComplaintWorkspace.tsx`, Redux slice | `POST /api/complaints/process-text` | `test_text_processing.py`, workspace tests | Pasted content; no mailbox integration |
| PDF intake | Implemented | `services/documents.py` | PDF picker/drop zone | `POST /api/complaints/process-document` | document/API tests, fake browser | Selectable text only; no OCR |
| Structured extraction | Implemented | `schemas/extraction.py`, Groq adapter | Typed API mapping | Processing endpoints | Groq-provider and processing tests | Source-supported fields only |
| API and FDF support | Implemented | Product-type domain/schema and prompts | Product-type selector | Processing/correction endpoints | API/FDF graph and browser cases | Unknown remains valid when evidence is absent |
| Editable complaint form | Implemented | Commit validation | React Hook Form, Zod, Redux | `POST /api/complaints` | workspace and schema tests | No collaborative editing |
| Category/quality assessment | Implemented, advisory | `schemas/assessment.py`, LangGraph | Quality assessment panel | Processing/correction endpoints | quality-assessment tests | Not a regulatory determination |
| Severity recommendation | Implemented, advisory | Assessment schema | Severity control/panel | Processing/correction endpoints | MINOR/MAJOR/CRITICAL tests | Human approval required |
| Initial risk assessment | Implemented, advisory | Assessment graph/provider | Editable risk field | Processing/correction endpoints | assessment and browser tests | Preliminary only |
| Suggested next action | Implemented, advisory | Assessment schema/provider | Editable next-action field | Processing/correction endpoints | assessment tests | Does not authorize action |
| Conversational corrections | Implemented | `ai/correction_graph.py`, correction service | Copilot correction mode | `POST /api/complaints/correct` | correction API/graph/UI/browser tests | Allowlisted complaint fields only |
| Explicit QMS commit | Implemented | Complaint service transaction | Commit button | `POST /api/complaints` | service, PostgreSQL, browser tests | No electronic signature |
| PostgreSQL persistence | Implemented | SQLAlchemy model/repository, Alembic | Committed-record summary | POST/list/detail endpoints | 115 PostgreSQL-enabled passes | One assignment-scale ledger table |
| LangGraph orchestration | Implemented | Extraction and correction graphs | Consumes validated results | Processing/correction endpoints | execution-trace graph tests | In-process orchestration |
| Groq integration | Implemented | `ai/providers.py` | No secret/provider access | Processing/correction endpoints | controlled smoke/provider tests | External quota and availability |
| Completeness checker | Implemented, deterministic | `services/completeness.py` | Completeness panel/local recalculation | Processing/correction responses | Sprint 6 unit/UI/browser tests | Guidance does not block commit |
| Duplicate detection | Implemented, deterministic | Repository plus `services/duplicates.py` | Possible-match panel | `POST /api/complaints/check-duplicates` and processing | scoring/PostgreSQL/UI/browser tests | Lexical, not semantic; never confirms duplicates |
| RCA/CAPA recommendations | Implemented, advisory | Strict schema, prompt, provider, graph | RCA/CAPA panel | Processing/correction responses | safety tests and FDF/API smoke | Not approved or implemented CAPA |
| Human-review controls | Implemented | Trusted schemas/disclaimers | Explicit review wording | All AI processing responses | safety schema and UI tests | Organisational review occurs outside app |
| OCR | Not required/not implemented | Textless PDF controlled error | Preserved-draft error UI | PDF endpoint returns controlled 422 | PDF/textless browser tests | Production OCR explicitly out of scope |

The system does not claim authentication, regulatory approval, autonomous recall, batch disposition, investigation closure, confirmed root cause, semantic duplicate detection, or production-grade OCR.
