# Sprint 0 architecture

The application is split into independently deployable frontend and backend services.

- `backend/app/api` owns HTTP routing and schemas.
- `backend/app/core` owns cross-cutting configuration and error contracts.
- `backend/app/infrastructure` owns database adapters and resource lifecycles.
- `frontend/src/app` owns global Redux configuration.
- `frontend/src/features` owns feature-facing UI.
- `frontend/src/shared` owns reusable integrations such as the Axios client.

The readiness endpoint executes `SELECT 1` through the application's async SQLAlchemy
engine. The health endpoint intentionally has no dependency on external services.
Complaint domain logic and AI integrations are deferred beyond Sprint 0.
