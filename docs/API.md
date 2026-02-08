# SyllabiQ Backend — API Reference

Base URL (dev): http://localhost:8000

Notes:
- API routes are mounted under the `/api` prefix (e.g. `/api/v1/query`).
- Health check is exposed at the application root `/health`.
- Use the interactive OpenAPI docs at `/docs` when the app is running.

Endpoints

- GET /health
  - Description: Service health check
  - Response: { "status": "ok", "service": "syllabiq-backend" }

- POST /api/v1/query
  - Description: Main query endpoint. Orchestrates intent detection, retrieval, generation and validation.
  - Request body (JSON):
    - query: string (required)
    - workflow: string (optional) - hint like "qa", "summarize", "generate"
    - marks: integer (optional) - 2,5,10 to control answer length
    - top_k: integer (optional) - how many retrieval chunks to fetch
    - format: string (optional) - "bullets" | "paragraph"
    - subject, topic: optional filters
  - Response:
    - answer: string
    - citations: array of citation objects {id, source, text}
    - metadata: object (intent, chunks_returned, etc)

Auth (public)
- POST /api/auth/signup
  - Description: Create a new user. Frontend signup should POST here.
  - Request body:
    - email: string (required)
    - password: string (required)
    - full_name: string (optional)
    - institution_id: integer (optional) — if the user belongs to an institution
  - Behavior: creates a user with status `pending`. Institution admins / SuperAdmin must approve.
  - Response: User object (see /schemas) with `status` field.

- POST /api/auth/login
  - Description: Login with email + password. Returns a JWT access token.
  - Request body: { email, password }
  - Response: { access_token: "<jwt>", token_type: "bearer" }
  - Usage: include header `Authorization: Bearer <token>` for protected admin endpoints.

Admin / Management (requires Authorization: Bearer token)
Notes: these endpoints are mounted under `/api/admin`. Authorization is enforced:
- SuperAdmin: can create institutions, create global roles, assign global roles.
- InstitutionAdmin (scoped): can manage users/assignments for their institution.

- POST /api/admin/institutions
  - Create institution (SuperAdmin only)
  - Body: { name, slug?, type? }

- GET /api/admin/institutions
  - List institutions

- POST /api/admin/roles
  - Create a canonical role (SuperAdmin only)
  - Body: { name, description?, is_system?: bool }

- GET /api/admin/roles
  - List roles

- POST /api/admin/role-assignments
  - Assign a role to a user, optionally scoped to an institution.
  - Body: { user_id, role_id, institution_id? }
  - Permissions:
    - assigning a global role (institution_id=null) requires SuperAdmin
    - assigning a role scoped to an institution requires SuperAdmin or InstitutionAdmin for that institution

- GET /api/admin/users/pending?institution_id={id}
  - List pending users (filtered by institution if provided). Requires InstitutionAdmin or SuperAdmin.

- POST /api/admin/users/{user_id}/approve
  - Approve a pending user. Body: { assign_role_id? } to optionally assign a role on approval.
  - Permissions: InstitutionAdmin for the user's institution or SuperAdmin.

- POST /api/admin/users/{user_id}/deny
  - Deny a pending user (sets status to `denied`).
  - Permissions: InstitutionAdmin for the user's institution or SuperAdmin.

Seeding / demo data
- On startup (dev) the app seeds a demo institution, a demo user and default roles if none exist.
  - Demo user: `demo@syllabiq.local` / `password`
  - Demo user is assigned the `SuperAdmin` role by the seed script.

Signup → Approval workflow
- Frontend: POST /api/auth/signup with `institution_id` (if applicable). User is created in `pending` status.
- InstitutionAdmin (or SuperAdmin) reviews pending users via `/api/admin/users/pending` and calls `/api/admin/users/{id}/approve` or `/deny`.
- On approve, the approver can optionally assign a role (e.g. Student or Teacher) to the user scoped to that institution.

See the live `/docs` for request/response schemas and try the endpoints interactively.

