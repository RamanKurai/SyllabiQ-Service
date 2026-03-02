# SyllabiQ Backend — API Reference

**Base URL (dev):** `http://localhost:8000`

**Interactive docs:** [http://localhost:8000/docs](http://localhost:8000/docs) (Swagger UI) — use **Authorize** with the JWT from `POST /api/auth/login` for protected endpoints.

---

## Table of contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Health](#health)
4. [Auth](#auth)
5. [Query & embeddings](#query--embeddings)
6. [Content](#content)
7. [Institutions (public)](#institutions-public)
8. [Dashboard](#dashboard)
9. [Admin APIs](#admin-apis) — *all admin endpoints in one place*
10. [Workflows](#workflows)

---

## Overview

- Routes are under the `/api` prefix (e.g. `/api/auth/login`, `/api/admin/...`).
- Health check: `GET /health`.
- Protected endpoints require header: `Authorization: Bearer <jwt>` (JWT from login).

---

## Authentication

- **Public:** `POST /api/auth/signup`, `POST /api/auth/login` (no token).
- **Protected:** All other auth, admin, dashboard, and some content endpoints require a valid JWT.
- Use the token in the `Authorization` header: `Bearer <access_token>`.

---

## Health

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Service health check. Response: `{ "status": "ok", "service": "syllabiq-backend" }`. |

---

## Auth

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/auth/signup` | No | Create a new user. Body: `email`, `password`, `full_name?`, `institution_id?`, `department_id?`. User is created with status `pending`; .edu required for institution signups. |
| POST | `/api/auth/login` | No | Login. Body: `{ "email", "password" }`. Returns `{ "access_token": "<jwt>", "token_type": "bearer", "roles": [...] }`. |
| GET | `/api/auth/me` | Yes | Current user profile and role assignments. |

---

## Query & embeddings

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/v1/query` | No | Main RAG query. Body: `query`, `workflow?`, `marks?`, `top_k?`, `format?`, `subject?`, `topic?`. Returns `answer`, `citations`, `metadata`. |
| POST | `/api/v1/embed` | No | Batch embed texts. |
| POST | `/api/v1/embed-query` | No | Embed a single query string. |

---

## Content

**Read (public):** List departments, courses, subjects, syllabi, topics (e.g. `GET /api/content/departments?institution_id=...`, `GET /api/content/courses`, etc.).

**Auth-required:**

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/content/topics/{topic_id}/upload` | Upload PDF/CSV/DOCX for a topic (multipart `file`). Extracts text, indexes for RAG. |
| GET | `/api/content/topics/{topic_id}/content` | List uploaded content items for a topic. |

Content CRUD (create/update/delete) for departments, courses, subjects, syllabi, topics is under **Admin APIs** below.

---

## Institutions (public)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/institutions/` | List institutions (e.g. for signup dropdown). |

---

## Dashboard

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/dashboard/me` | Yes | Aggregated dashboard for the current user (KPIs, context, activity). |

---

## Admin APIs

All admin endpoints are under `/api/admin` and require **`Authorization: Bearer <token>`**. Role requirements (SuperAdmin, InstitutionAdmin, etc.) are noted per group.

### Institutions

| Method | Path | Role | Description |
|--------|------|------|-------------|
| POST | `/api/admin/institutions` | SuperAdmin | Create institution. Body: `name`, `slug?`, `type?`, `institute_admin?`. |
| GET | `/api/admin/institutions` | Any auth | List institutions (paginated: `limit`, `offset`). |
| PUT | `/api/admin/institutions/{institution_id}` | SuperAdmin | Update institution. Body: `name?`, `slug?`, `type?`, `is_active?`. |
| DELETE | `/api/admin/institutions/{institution_id}` | SuperAdmin | Delete institution. |

### KPIs

| Method | Path | Role | Description |
|--------|------|------|-------------|
| GET | `/api/admin/kpis?days=7` | Admin (scoped) | Aggregated counts and time-series (signups, approvals). SuperAdmin: global; others: institution-scoped. |

### Roles

| Method | Path | Role | Description |
|--------|------|------|-------------|
| POST | `/api/admin/roles` | SuperAdmin | Create role. Body: `name`, `description?`, `is_system?`. |
| GET | `/api/admin/roles` | Any auth | List roles (paginated). |
| PUT | `/api/admin/roles/{role_id}` | SuperAdmin | Update role. Body: `name?`, `description?`, `is_active?`. |
| DELETE | `/api/admin/roles/{role_id}` | SuperAdmin | Delete role. |

### Content — Departments

| Method | Path | Role | Description |
|--------|------|------|-------------|
| POST | `/api/admin/content/departments` | SuperAdmin, InstitutionAdmin (assigned institutions) | Create department. Body: `name`, `institution_id?`, `slug?`. |
| PUT | `/api/admin/content/departments/{department_id}` | SuperAdmin, InstitutionAdmin (assigned institutions) | Update department. |
| DELETE | `/api/admin/content/departments/{department_id}` | SuperAdmin, InstitutionAdmin (assigned institutions) | Delete department. |

### Content — Courses

| Method | Path | Role | Description |
|--------|------|------|-------------|
| POST | `/api/admin/content/courses` | SuperAdmin, InstitutionAdmin (assigned institutions) | Create course. Body: `course_name`, `description?`, `department_id?`. |
| PUT | `/api/admin/content/courses/{course_id}` | SuperAdmin, InstitutionAdmin (assigned institutions) | Update course. |
| DELETE | `/api/admin/content/courses/{course_id}` | SuperAdmin, InstitutionAdmin (assigned institutions) | Delete course. |

### Content — Subjects

| Method | Path | Role | Description |
|--------|------|------|-------------|
| POST | `/api/admin/content/subjects` | SuperAdmin, InstitutionAdmin (assigned institutions) | Create subject. Body: as per schema. |
| PUT | `/api/admin/content/subjects/{subject_id}` | SuperAdmin, InstitutionAdmin (assigned institutions) | Update subject. |
| DELETE | `/api/admin/content/subjects/{subject_id}` | SuperAdmin, InstitutionAdmin (assigned institutions) | Delete subject. |

### Content — Syllabi

| Method | Path | Role | Description |
|--------|------|------|-------------|
| POST | `/api/admin/content/syllabi` | SuperAdmin, InstitutionAdmin (assigned institutions) | Create syllabus. Body: as per schema. |
| PUT | `/api/admin/content/syllabi/{syllabus_id}` | SuperAdmin, InstitutionAdmin (assigned institutions) | Update syllabus. |
| DELETE | `/api/admin/content/syllabi/{syllabus_id}` | SuperAdmin, InstitutionAdmin (assigned institutions) | Delete syllabus. |

### Content — Topics

| Method | Path | Role | Description |
|--------|------|------|-------------|
| POST | `/api/admin/content/topics` | SuperAdmin, InstitutionAdmin (assigned institutions) | Create topic. Body: as per schema. |
| PUT | `/api/admin/content/topics/{topic_id}` | SuperAdmin, InstitutionAdmin (assigned institutions) | Update topic. |
| DELETE | `/api/admin/content/topics/{topic_id}` | SuperAdmin, InstitutionAdmin (assigned institutions) | Delete topic. |

### Role assignments

| Method | Path | Role | Description |
|--------|------|------|-------------|
| POST | `/api/admin/role-assignments` | SuperAdmin / InstitutionAdmin | Assign role to user. Body: `user_id`, `role_id`, `institution_id?`. Global role (`institution_id` null): SuperAdmin only; scoped: SuperAdmin or InstitutionAdmin for that institution. |

### Users — Pending & list

| Method | Path | Role | Description |
|--------|------|------|-------------|
| GET | `/api/admin/users/pending?institution_id=&limit=&offset=` | InstitutionAdmin / SuperAdmin | List pending users (optionally by institution). |
| GET | `/api/admin/users?status=&institution_id=&role_name=&limit=&offset=` | Admin (scoped) | List users with filters and pagination. Principal/Teacher: institution-scoped. |

### Users — Approve / deny

| Method | Path | Role | Description |
|--------|------|------|-------------|
| POST | `/api/admin/users/{user_id}/approve` | InstitutionAdmin / SuperAdmin | Approve pending user. Body: `assign_role_id?` to assign role on approval. |
| POST | `/api/admin/users/{user_id}/deny` | InstitutionAdmin / SuperAdmin | Deny pending user (status → `denied`). |

### Users — CRUD & lifecycle

| Method | Path | Role | Description |
|--------|------|------|-------------|
| GET | `/api/admin/users/{user_id}` | Admin (scoped) | Get user by ID. |
| PUT | `/api/admin/users/{user_id}` | Admin (scoped) | Update user. Body: `full_name?`, `institution_id?`, `is_active?`, `status?`. Cannot change own status/institution/active. |
| POST | `/api/admin/users/{user_id}/suspend` | Admin (scoped) | Suspend user (status → `suspended`, `is_active` → false). |
| DELETE | `/api/admin/users/{user_id}` | SuperAdmin | Delete user. |

---

## Workflows

### Signup → approval

1. Frontend: `POST /api/auth/signup` with `institution_id` and `department_id` when applicable. User is created with status `pending`.
2. InstitutionAdmin (or SuperAdmin) lists pending users: `GET /api/admin/users/pending?institution_id=...`.
3. Approve: `POST /api/admin/users/{id}/approve` (optional `assign_role_id`). Deny: `POST /api/admin/users/{id}/deny`.

### RAG pipeline

- Topic content: upload via `POST /api/content/topics/{topic_id}/upload` (PDF/CSV/DOCX). Text is extracted, chunked, embedded, and stored in ChromaDB.
- Queries: `POST /api/v1/query` uses retrieval + LLM; subject/topic filters and model config via env (see `.env.example`).

### Demo data

- On startup (dev), the app may seed a demo institution, default roles, and a demo user: `demo@syllabiq.local` / `password` (SuperAdmin).

---

For request/response schemas and to try endpoints with a token, use the live **[/docs](http://localhost:8000/docs)** (Swagger UI). All **Admin APIs** appear under the **admin** tag there.

**Related:** [SOFT_DELETE.md](SOFT_DELETE.md) — design for soft delete (archive) and SuperAdmin-only permanent remove.
