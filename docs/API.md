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
    - department_id: uuid (optional) — required when institution_id is set; binds student to department
  - Behavior: creates a user with status `pending`. Institution admins / SuperAdmin must approve.
  - Validation: department_id must belong to the selected institution. .edu email required for institution signups.
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

Content (public read, auth for mutations)
- GET /api/content/departments?institution_id={id}
  - List departments (optionally filtered by institution). Used for signup department dropdown.

- GET /api/content/courses
- GET /api/content/subjects
- GET /api/content/syllabi
- GET /api/content/topics
  - List content entities.

- POST /api/content/topics/{topic_id}/upload (requires Authorization)
  - Upload PDF, CSV, or DOCX file for a topic. Extracts text, stores in DB, indexes into ChromaDB for RAG.
  - Request: multipart/form-data with `file` field.
  - Response: TopicContent object.

- GET /api/content/topics/{topic_id}/content (requires Authorization)
  - List uploaded content items for a topic.

Admin / Management (requires Authorization: Bearer token)
Notes: these endpoints are mounted under `/api/admin`. Authorization is enforced:
- SuperAdmin: can create institutions, departments, content; create global roles; assign global roles.
- InstitutionAdmin (scoped): can manage users/assignments for their institution.

- POST /api/admin/content/departments
  - Create department (SuperAdmin only)
  - Body: { name, institution_id?, slug? }

- PUT /api/admin/content/departments/{department_id}
- DELETE /api/admin/content/departments/{department_id}
  - Update/delete department.

- POST /api/admin/content/courses
  - Create course. Body: { course_name, description?, department_id? }

- PUT /api/admin/content/courses/{course_id}
  - Update course (includes department_id).

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
- Frontend: POST /api/auth/signup with `institution_id` and `department_id` (required when institution selected). User is created in `pending` status.
- InstitutionAdmin (or SuperAdmin) reviews pending users via `/api/admin/users/pending` and calls `/api/admin/users/{id}/approve` or `/deny`.
- On approve, the approver can optionally assign a role (e.g. Student or Teacher) to the user scoped to that institution.

RAG pipeline
- Topic content (PDF/CSV/DOCX) is uploaded via POST /api/content/topics/{topic_id}/upload.
- Text is extracted, chunked, embedded (OpenAI), and stored in ChromaDB.
- Query endpoint uses ChromaDB retrieval with optional subject/topic filters for scoped answers.

See the live `/docs` for request/response schemas and try the endpoints interactively.

