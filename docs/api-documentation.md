# API Documentation

## 1. Overview

The FastAPI backend provides system health, complaint processing, conversational
correction, duplicate checking, and explicit QMS-ledger operations.

- Base URL: **http://localhost:8000**
- Swagger UI: **http://localhost:8000/docs**
- OpenAPI schema: **http://localhost:8000/openapi.json**

The assignment build does not implement authentication and should not be exposed
directly to an untrusted network.

## 2. Endpoint summary

| Method | Endpoint                         | Purpose                           | Persistence        |
| ------ | -------------------------------- | --------------------------------- | ------------------ |
| GET    | /health                          | Application liveness              | None               |
| GET    | /ready                           | PostgreSQL readiness              | Read-only check    |
| POST   | /api/complaints/process-text     | Process complaint text            | None               |
| POST   | /api/complaints/process-document | Process a text-based PDF          | None               |
| POST   | /api/complaints/correct          | Apply a conversational correction | None               |
| POST   | /api/complaints/check-duplicates | Find possible matches             | Read-only          |
| POST   | /api/complaints                  | Commit a reviewed complaint       | Inserts one record |
| GET    | /api/complaints                  | List committed complaints         | Read-only          |
| GET    | /api/complaints/{complaint_id}   | Retrieve one complaint            | Read-only          |

## 3. Common conventions

JSON endpoints use **application/json**. PDF processing uses
**multipart/form-data** with a field named **file**.

Product types are API, FDF, and UNKNOWN. Severities are MINOR, MAJOR, and CRITICAL.
Source types are MANUAL, TEXT, and PDF.

Errors use this envelope:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Safe user-facing message",
    "details": null
  }
}
```

Validation errors use VALIDATION_ERROR and may include safe field details. Provider
errors never intentionally expose keys, prompts, raw responses, or stack traces.

## 4. Health and readiness

### GET /health

Returns application liveness without querying PostgreSQL or Groq.

```json
{
  "status": "ok"
}
```

### GET /ready

Executes SELECT 1 through the PostgreSQL engine and never calls Groq.

```json
{
  "status": "ready"
}
```

A database connectivity failure returns **503 Service Unavailable**.

## 5. Text processing

### POST /api/complaints/process-text

Request:

```json
{
  "text": "Fictional FDF complaint: Amoxicillin Capsules 500 mg, batch FDF-100, 12 capsules showed discoloration."
}
```

The response contains:

- source_type and input_length
- extracted_complaint
- quality_assessment
- completeness_assessment
- possible_duplicate_matches
- rca_capa_recommendations
- warnings and assistant_message
- status and configured model

The operation does not persist the draft. Possible status codes are 200, 422, 429,
502, 503, and 504.

## 6. PDF processing

### POST /api/complaints/process-document

The endpoint accepts one text-based PDF. It validates filename, content type,
signature, size, encryption, page count, and extracted-text length.

PowerShell:

```powershell
curl.exe -X POST -F "file=@sample-data/fictional-fdf-complaint.pdf;type=application/pdf" http://localhost:8000/api/complaints/process-document
```

The response includes the same processing fields as text intake plus:

```json
{
  "document": {
    "filename": "fictional-fdf-complaint.pdf",
    "content_type": "application/pdf",
    "page_count": 1,
    "character_count": 500
  }
}
```

Possible status codes are 200, 413, 415, 422, 429, 502, 503, and 504. Production OCR
is not supported; scanned or textless PDFs return a controlled error.

## 7. Conversational correction

### POST /api/complaints/correct

The request contains:

- current_complaint
- instruction
- current_quality_assessment
- optional current_completeness_assessment
- up to five current_possible_duplicate_matches
- optional current_rca_capa_recommendations
- optional non-negative client_draft_revision

The response contains the patch, updated complaint, changed fields, warnings,
assessment, completeness, duplicates, RCA/CAPA, assistant message, correction status,
and model.

Correction statuses:

- APPLIED
- CLARIFICATION_REQUIRED
- NO_CHANGES

Only allowlisted complaint fields may change. UUID, complaint number, status, and
timestamps are protected. Correction never writes to PostgreSQL.

## 8. Duplicate check

### POST /api/complaints/check-duplicates

Request:

```json
{
  "current_complaint_id": null,
  "product_name": "Amoxicillin Capsules",
  "batch_lot_number": "FDF-101",
  "complaint_category": "Appearance",
  "complaint_description": "Fictional discoloration was reported.",
  "affected_quantity": "48 capsules",
  "manufacturing_date": null,
  "expiry_retest_date": null
}
```

Response:

```json
{
  "matches": [],
  "possible_match_threshold": 45,
  "strong_match_threshold": 75
}
```

At most five matches are returned. Match levels are POSSIBLE_MATCH and STRONG_MATCH.
The result is advisory and does not block commit.

## 9. Explicit commit

### POST /api/complaints

This is the only endpoint in the complaint-processing workflow that inserts a record.

Required fields:

- customer_name
- product_name
- batch_lot_number
- complaint_category
- complaint_description

Example:

```json
{
  "source_type": "TEXT",
  "complaint_source": "Fictional email",
  "customer_name": "Fictional Customer",
  "product_type": "FDF",
  "product_name": "Amoxicillin Capsules",
  "product_strength_grade": "500 mg",
  "batch_lot_number": "FDF-101",
  "affected_quantity": "48 capsules",
  "manufacturing_date": null,
  "expiry_retest_date": null,
  "originating_site_block": null,
  "impacted_non_product_materials": null,
  "complaint_category": "Appearance",
  "complaint_description": "Fictional discoloration was reported.",
  "suggested_severity": "MAJOR",
  "initial_risk_assessment": "Potential quality impact requires QA review.",
  "suggested_next_action": "Authorised QA should investigate.",
  "raw_input": null
}
```

Success returns **201 Created**, the reviewed fields, UUID, generated complaint number,
COMMITTED status, and timestamps.

## 10. List complaints

### GET /api/complaints

| Parameter | Default | Bounds    |
| --------- | ------: | --------- |
| page      |       1 | Minimum 1 |
| page_size |      20 | 1 to 100  |

Example:

```text
GET /api/complaints?page=1&page_size=5
```

Response:

```json
{
  "items": [],
  "page": 1,
  "page_size": 5,
  "total": 0,
  "total_pages": 0
}
```

Items are ordered by creation time and UUID, both descending.

## 11. Retrieve complaint

### GET /api/complaints/{complaint_id}

The identifier must be a UUID.

- **200** returns the complaint.
- **404** means the record was not found.
- **422** means the UUID failed validation.

## 12. Status-code reference

| Status | Meaning                                             |
| -----: | --------------------------------------------------- |
|    200 | Successful read or processing operation             |
|    201 | Complaint committed                                 |
|    413 | PDF exceeds configured size                         |
|    415 | Unsupported document type                           |
|    422 | Request, text, PDF, or UUID validation failure      |
|    429 | Groq rate limit reached                             |
|    502 | Provider authentication or malformed-output failure |
|    503 | Database/provider unavailable or AI not configured  |
|    504 | Provider timeout                                    |
