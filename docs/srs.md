# Software Requirements Specification

Implementation status: Sprints 0–6 are implemented. Sprint 5 is **PASSED WITH
EXTERNAL PROVIDER LIMITATION** and Sprint 6 is **PASSED**. Authentication, OCR, and
autonomous quality decisions remain outside assignment scope.

## AI-Powered Pharmaceutical Customer Complaint Management System

**Repository:** `ai-pharma-complaint-qms`  
**Document status:** Final requirements baseline  
**Primary user:** Pharmaceutical Quality Assurance (QA) personnel

## 1. Purpose

This document specifies an AI-assisted customer-complaint intake module for pharmaceutical companies manufacturing Active Pharmaceutical Ingredients (APIs) and Finished Dosage Forms (FDFs). It defines the product scope, functional and non-functional requirements, data rules, safety boundaries, and acceptance criteria.

The application is an assignment/demo system inspired by pharmaceutical Quality Management System (QMS) practices. It is not a validated regulated QMS and does not claim regulatory certification or compliance.

## 2. Problem statement

Pharmaceutical complaints frequently arrive as unstructured emails, pasted text, or PDF reports. QA personnel must manually identify the customer, product, batch, quantity, dates, defect, and potential quality impact before recording a complaint. Manual intake is slow, inconsistent, and susceptible to transcription errors.

## 3. Proposed solution

The system accepts complaint text/email or a text-based PDF, extracts structured information using a Groq-hosted LLM orchestrated with LangGraph, populates a complaint form, produces an initial AI-assisted risk assessment, accepts conversational corrections, and saves the QA-reviewed complaint to a PostgreSQL QMS ledger.

## 4. Objectives

1. Reduce manual complaint-entry effort.
2. Preserve product and batch traceability.
3. Standardize initial complaint categorization and triage.
4. Make missing information visible before commitment.
5. Support both API and FDF complaint contexts.
6. Keep authorised QA personnel responsible for final decisions.
7. Maintain a clear, testable, and extensible implementation.

## 5. Definitions

| Term | Meaning |
|---|---|
| QMS/PQS | Pharmaceutical Quality Management/Quality System |
| GMP | Good Manufacturing Practice |
| API | Active Pharmaceutical Ingredient |
| FDF | Finished Dosage Form |
| QA | Quality Assurance |
| CAPA | Corrective and Preventive Action |
| OCR | Optical Character Recognition |
| Complaint draft | Extracted or manually entered data not yet committed |
| QMS ledger | PostgreSQL record of the reviewed complaint |

## 6. Product scope

### Included

- Manual complaint entry and review
- Text/email complaint processing
- Text-based PDF processing
- API and FDF field extraction
- Automatic form population
- Complaint classification and initial risk assessment
- Conversational field correction
- Completeness checking
- Possible duplicate detection
- Root-cause and CAPA recommendations
- PostgreSQL commitment, listing, and retrieval
- Loading, validation, and failure states

### Excluded

- Authentication and role-based access control
- A complete enterprise QMS
- Production-grade OCR or layout reconstruction
- Electronic signatures and validated audit trails
- Regulatory submissions
- Autonomous batch disposition or product recall
- Final investigation, confirmed root cause, or CAPA approval
- Mobile application and microservices

## 7. Technology constraints

| Layer | Required technology |
|---|---|
| Frontend | React, TypeScript, Vite |
| State | Redux Toolkit |
| Backend | Python and FastAPI |
| AI orchestration | LangGraph |
| LLM provider | Groq |
| Database | PostgreSQL |
| UI font | Google Inter |

The Groq model is configured through `GROQ_MODEL`; the baseline default is `openai/gpt-oss-120b`. Secrets must remain in backend environment configuration.

## 8. User and operating assumptions

- The primary user understands pharmaceutical complaint intake and reviews AI suggestions.
- The user supplies complaint text or a readable text-based PDF.
- Missing information may legitimately remain unknown during intake.
- The application must not invent absent batch numbers, quantities, dates, customers, or sites.
- Final quality decisions remain with authorised personnel.

## 9. Functional requirements

| ID | Requirement |
|---|---|
| FR-001 | The system shall display a structured Log Customer Complaint form. |
| FR-002 | The system shall display the current workflow status. |
| FR-003 | The system shall accept manual complaint entry. |
| FR-004 | The system shall accept pasted complaint text or email. |
| FR-005 | The system shall accept a PDF within configured type and size limits. |
| FR-006 | The system shall extract selectable text from uploaded PDFs. |
| FR-007 | The system shall return a clear error when no readable PDF text exists. |
| FR-008 | The system shall process complaint text through a real LangGraph workflow. |
| FR-009 | The system shall use the configured Groq model for structured AI output. |
| FR-010 | The system shall distinguish API, FDF, and unknown product types. |
| FR-011 | The system shall extract only information supported by the source. |
| FR-012 | The system shall represent missing extracted information as null. |
| FR-013 | The system shall validate all AI output using Pydantic schemas. |
| FR-014 | The system shall populate the Redux-managed form from validated extraction. |
| FR-015 | Null extraction values shall not erase existing non-empty user values. |
| FR-016 | The user shall be able to review and manually edit all complaint fields. |
| FR-017 | The system shall produce a structured complaint description. |
| FR-018 | The system shall suggest a complaint category. |
| FR-019 | The system shall suggest Minor, Major, or Critical severity. |
| FR-020 | The system shall generate an initial risk assessment. |
| FR-021 | The system shall generate a suggested next action. |
| FR-022 | AI assessments shall display a human-review disclaimer. |
| FR-023 | The Copilot shall accept conversational correction instructions. |
| FR-024 | Corrections shall return and apply only allowed changed fields. |
| FR-025 | Corrections shall preserve all fields not mentioned by the user. |
| FR-026 | Dependent checks shall be recalculated after relevant corrections. |
| FR-027 | The system shall prevent simultaneous duplicate processing/commit actions. |
| FR-028 | The system shall commit only after explicit user action. |
| FR-029 | Server-side validation shall run before commitment. |
| FR-030 | The system shall generate a unique human-readable complaint number. |
| FR-031 | The system shall save committed complaints in PostgreSQL transactionally. |
| FR-032 | The system shall list complaints using deterministic pagination. |
| FR-033 | The system shall retrieve a complaint by UUID. |
| FR-034 | Failures shall preserve the draft and allow retry. |
| FR-035 | Health and PostgreSQL-backed readiness endpoints shall be available. |

## 10. Selected bonus requirements

| ID | Requirement |
|---|---|
| BR-001 | The system shall report missing required and recommended complaint information. |
| BR-002 | The completeness result shall update after manual or conversational corrections. |
| BR-003 | The system shall search committed complaints for possible duplicates. |
| BR-004 | Duplicate scoring shall consider product, batch, category, and description similarity. |
| BR-005 | Duplicate matches shall include score and match reasons and shall not be final determinations. |
| BR-006 | The system shall suggest potential root causes and investigation areas. |
| BR-007 | The system shall suggest corrective and preventive actions separately. |
| BR-008 | Root-cause and CAPA outputs shall be labelled as recommendations requiring QA review. |

## 11. Data requirements

| Group | Fields |
|---|---|
| Origin/customer | Complaint source, customer name |
| Product/batch | Product type, product name, strength/grade, batch/lot, quantity, manufacturing date, expiry/retest date |
| Facility/material | Originating site/block, impacted non-product materials |
| Defect | Complaint category, complaint description |
| AI assessment | Suggested severity, risk assessment, suggested action |
| System | UUID, complaint number, source type, status, raw input, timestamps |

Partial pharmaceutical dates such as `March 2026` and explicit values such as `Not Provided` are preserved as text. Fields must have bounded lengths and whitespace-only required values are invalid.

## 12. Business rules

| ID | Rule |
|---|---|
| BRULE-001 | Minimum manual commit data consists of customer, product, batch/lot, category, and description. |
| BRULE-002 | Complaint numbers must be unique and concurrency-safe. |
| BRULE-003 | A draft is not persisted by text, document, or correction processing alone. |
| BRULE-004 | Unknown request fields are rejected where schemas require strict input. |
| BRULE-005 | Missing source information must not be fabricated. |
| BRULE-006 | Only allowlisted complaint fields may be updated conversationally. |
| BRULE-007 | AI output is advisory and requires QA review. |
| BRULE-008 | Database transactions are committed or rolled back as one unit. |
| BRULE-009 | Potential duplicates are indicators, not final duplicate classifications. |
| BRULE-010 | API keys and database credentials must never reach frontend code or responses. |

## 13. External interfaces

### User interface

- Two-column complaint workspace and Copilot panel
- Accessible labels and inline validation
- Status, processing, success, and error states
- Responsive desktop layout using Inter

### Backend API

- JSON REST endpoints for text processing, correction, commitment, listing, and retrieval
- Multipart endpoint for PDF processing
- Standard error envelope

### Groq

- Backend-only authenticated request
- Environment-configured model
- Structured response validated before use

### PostgreSQL

- Async SQLAlchemy access
- Alembic migrations
- Service-owned transaction boundary

## 14. Non-functional requirements

| ID | Requirement |
|---|---|
| NFR-001 | Source code shall maintain separation between UI, routes, services, repositories, AI, and document processing. |
| NFR-002 | Python and TypeScript static checks shall pass. |
| NFR-003 | Critical domain and API behaviour shall have automated tests. |
| NFR-004 | The system shall use PostgreSQL integration tests for persistence behaviour. |
| NFR-005 | Errors shall not expose secrets, prompts, stack traces, or provider internals. |
| NFR-006 | Groq and database credentials shall use environment variables. |
| NFR-007 | AI provider failures shall return controlled, retryable errors where appropriate. |
| NFR-008 | The form shall preserve user input after recoverable failures. |
| NFR-009 | Database changes shall use version-controlled migrations. |
| NFR-010 | The UI shall be keyboard accessible and use associated labels. |
| NFR-011 | The application shall build and run through Docker Compose. |
| NFR-012 | Health shall remain independent from database readiness. |
| NFR-013 | Logs shall contain operational context without secrets or unnecessary complaint content. |
| NFR-014 | Automated AI tests shall use a deterministic fake provider by default. |
| NFR-015 | Real Groq use shall be verified through separately controlled smoke tests. |

## 15. AI safety requirements

- Complaint content is untrusted data, not system instruction.
- Structured output is validated before reaching Redux or persistence.
- At most one controlled retry is permitted for malformed structured output.
- Authentication and permanent provider errors are not blindly retried.
- The system does not confirm root cause, CAPA effectiveness, batch disposition, or recall.
- The interface must state: **AI-generated intake and quality recommendations require review and approval by authorised QA personnel.**

## 16. Acceptance criteria

| ID | Acceptance criterion |
|---|---|
| AC-001 | A valid manually entered complaint can be committed and retrieved after restart. |
| AC-002 | Valid FDF text populates supported fields without inventing absent values. |
| AC-003 | Valid API text populates API name, grade, batch, and quantity when present. |
| AC-004 | A readable PDF follows the same processing path as pasted text. |
| AC-005 | An unreadable PDF returns a clear non-destructive error. |
| AC-006 | Risk category, severity, rationale, and next action validate and display. |
| AC-007 | A conversational batch/quantity correction changes only those fields. |
| AC-008 | Completeness warnings recalculate after correction. |
| AC-009 | A similar saved complaint appears as a possible duplicate with reasons. |
| AC-010 | Root-cause and CAPA recommendations are contextual and explicitly advisory. |
| AC-011 | Backend, frontend, integration, build, and Docker gates pass. |
| AC-012 | No secret is committed or returned to the client. |

## 17. Regulatory context

The workflow is informed by [ICH Q10 Pharmaceutical Quality System](https://database.ich.org/sites/default/files/Q10_Guideline.pdf), [ICH Q9(R1) Quality Risk Management](https://database.ich.org/sites/default/files/ICH_Q9%28R1%29_Guideline_Step4_2023_0126.pdf), [FDA/ICH Q7 API GMP guidance](https://www.fda.gov/regulatory-information/search-fda-guidance-documents/q7a-good-manufacturing-practice-guidance-active-pharmaceutical-ingredients), [21 CFR 211.198 complaint files](https://www.ecfr.gov/current/title-21/chapter-I/subchapter-C/part-211/subpart-J/section-211.198), and [EU GMP Chapter 8](https://health.ec.europa.eu/document/download/b1eb2292-cb0d-4e3f-aea9-e3fe79faf6e3_en?filename=2014-08_gmp_chap8.pdf). Applicability depends on organisation and jurisdiction.

## 18. Delivery status

- Sprint 0 foundation: implemented and verified
- Sprint 1 manual QMS ledger: implemented and verified
- Text/email AI intake, PDF intake, and initial quality assessment: implemented and verified
- Conversational corrections and bonus capabilities: planned for subsequent controlled sprints

This SRS is the final scope baseline; implementation status is maintained in `testing-and-sprints.md`.
## Sprint 6 functional requirements

The system shall calculate deterministic complaint completeness, return up to five
bounded deterministic possible duplicate matches, and provide strictly validated
AI-assisted investigation/root-cause/CAPA recommendations. It shall recalculate these
results after processing and relevant corrections, preserve applicable results after
unrelated corrections, and identify potentially stale results after relevant manual
edits. None of these functions shall automatically persist, merge, suppress, approve,
close, release, reject, recall, or dispose of a complaint or batch.
