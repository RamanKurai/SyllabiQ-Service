# SyllabiQ Implementation Plan

> Phased implementation plan for pending work with full frontend–backend compatibility.

---

## Executive Summary

SyllabiQ is a syllabus-aware educational AI platform with a **React + Vite** frontend and **FastAPI** backend. This plan addresses integration gaps, streaming support, and production readiness across both layers.

---

## Current State

| Layer | Tech | Status |
|-------|------|--------|
| Frontend | React 18, TypeScript, Vite 6, Tailwind v4, Radix UI | Functional with mock data |
| Backend | FastAPI, SQLModel, ChromaDB, LangChain, OpenAI | RAG, auth, admin, content CRUD |
| Integration | REST API | **Mismatches** (see Phase 1) |

### Known Gaps

1. **API path mismatch**: Frontend calls `/v1/subjects` and `/v1/subjects/{id}/topics`; backend exposes `/api/content/subjects` and `/api/content/topics?syllabus_id=`.
2. **Subject/topic wiring**: App uses hardcoded `SUBJECTS`/`TOPICS`; Chat sends display names; backend expects UUIDs for RAG filtering.
3. **Streaming**: Frontend supports SSE; backend returns full JSON only.
4. **Auth header**: `getSubjects`, `getTopics`, `getInstitutions` omit `authHeader()`; some endpoints may require auth.

---

## Phase 1: Core Frontend–Backend Integration

**Goal**: Align API contracts and wire real content hierarchy end-to-end.

### 1.1 Backend: Content API Alignment

| Task | Description | Files |
|------|-------------|-------|
| Add convenience routes | `GET /api/content/subjects` (existing) + `GET /api/content/subjects/{subject_id}/topics` | `app/content/subjects.py`, `app/content/topics.py` |
| Add `/api/v1` alias | Mount content read endpoints under `/api/v1` for frontend compatibility, or document canonical paths | `app/main.py` |
| Response shape | Ensure subjects: `{id, name}`; topics: `{id, name}` (or map existing models) | `app/content/*.py`, schemas |

**Backend changes**:
- Add `GET /api/content/subjects/{subject_id}/topics` → list topics for syllabi under that subject.
- Optionally add Pydantic response schemas for `{id, name}` to match frontend expectations.

### 1.2 Frontend: API Client & Data Wiring

| Task | Description | Files |
|------|-------------|-------|
| Fix API paths | `getSubjects()` → `/content/subjects`; `getTopics(subjectId)` → `/content/subjects/{subjectId}/topics` | `src/lib/api.ts` |
| Add auth header | Include `authHeader()` in `getSubjects`, `getTopics`, `getInstitutions` | `src/lib/api.ts` |
| Remove mock data | Replace `SUBJECTS` and `TOPICS` in `App.tsx` with API-fetched data | `src/app/App.tsx` |
| Loading/error states | Handle loading and error for subject/topic fetch | `App.tsx`, `Header.tsx`, `Sidebar.tsx` |

**Data flow**:
```
App.tsx → useEffect → getSubjects() → setSubjects()
         → getTopics(selectedSubjectId) when subject selected
Header → subjects (from API)
Sidebar → topics (from API)
ChatInterface → subject_id, topic_id (UUIDs) in QueryRequest
```

### 1.3 Chat: Subject/Topic IDs

| Task | Description | Files |
|------|-------------|-------|
| Pass UUIDs | `selectedSubject` and `selectedTopic` must be UUIDs when calling `postQuery`/`streamQuery` | `ChatInterface.tsx`, `App.tsx` |
| Fallback | When no subject/topic selected, send `null` or omit; backend handles unscoped retrieval | `ChatInterface.tsx` |

### 1.4 Institutions & Departments

| Task | Description | Files |
|------|-------------|-------|
| Fix `getInstitutions` | Path: `/institutions` vs `/api/institutions` (verify mount) | `api.ts`, `main.py` |
| Ensure cascade | `getDepartments(institutionId)` already uses `/content/departments?institution_id=` | `api.ts` |

---

## Phase 2: Streaming & UX Improvements

**Goal**: Token-by-token streaming for chat and better loading/error UX.

### 2.1 Backend: Streaming Endpoint

| Task | Description | Files |
|------|-------------|-------|
| Add streaming route | `POST /api/v1/query/stream` returning `StreamingResponse` (SSE or NDJSON) | `app/api.py` |
| Stream generation | Use LangChain `stream()` or equivalent; yield `{"delta": "chunk"}` or `data: {...}` | `app/agents/core.py` |
| Error handling | On stream failure, send error event and close stream | `app/api.py` |

**Contract** (SSE):
```
data: {"delta": "chunk1"}
data: {"delta": "chunk2"}
...
data: {"done": true, "citations": [...]}
```

### 2.2 Frontend: Streaming UX

| Task | Description | Files |
|------|-------------|-------|
| Use stream by default | Prefer `streamQuery` over `postQuery` when backend supports it | `ChatInterface.tsx` |
| Progressive render | Append chunks to AI message as they arrive | `ChatInterface.tsx` |
| Fallback | If stream fails or returns non-stream, use full response | `ChatInterface.tsx` (already has fallback) |
| Debounce | Debounce query input (300–600ms) before send | `ChatInterface.tsx` |
| Skeleton | Accessible skeleton (`aria-busy`, `role="status"`) while loading | `ChatInterface.tsx` |

### 2.3 Caching & Performance

| Task | Description |
|------|-------------|
| Client cache | Cache recent queries (sessionStorage) keyed by query + marks + workflow |
| Static metadata | Consider ETag for subjects/topics (future) |

---

## Phase 3: Production Readiness

**Goal**: Security, observability, and deployment readiness.

### 3.1 Auth & Security

| Task | Description |
|------|-------------|
| `/auth/me` | Implement `GET /api/auth/me` for token validation and user info |
| Protected content | Ensure content mutations require auth; verify CORS in production |
| JWT refresh | Optional: refresh token flow |
| Rate limiting | Add rate limits on `/api/v1/query` |

### 3.2 Error Handling & Observability

| Task | Description |
|------|-------------|
| Structured errors | Consistent error response shape `{error, code, details}` |
| Logging | Structured logs (request ID, user, duration) |
| Health | Extend `/health` with DB and ChromaDB connectivity checks |

### 3.3 Deployment

| Task | Description |
|------|-------------|
| Env validation | Fail fast if `OPENAI_API_KEY` missing when RAG is used |
| Docker | Dockerfile for backend and frontend (if not present) |
| Migrations | Document DB migration path for schema changes |

---

## Phase 4: Future Enhancements

**Backend** (from README):
- Adaptive learning paths
- Analytics on student queries
- Voice-based interaction
- Multi-language support

**Frontend** (from README):
- PDF export for summaries and practice questions
- Progress tracking
- Personalized learning recommendations
- Study schedule planner
- Collaborative study groups

---

## API Contract Reference

### Canonical Paths (Backend)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| POST | `/api/v1/query` | RAG query (full response) |
| POST | `/api/v1/query/stream` | RAG query (streaming) — Phase 2 |
| POST | `/api/auth/signup` | Signup |
| POST | `/api/auth/login` | Login |
| GET | `/api/auth/me` | Current user — Phase 3 |
| GET | `/api/content/departments?institution_id=` | Departments |
| GET | `/api/content/subjects?course_id=` | Subjects |
| GET | `/api/content/subjects/{id}/topics` | Topics for subject — Phase 1 |
| GET | `/api/content/syllabi?subject_id=` | Syllabi |
| GET | `/api/content/topics?syllabus_id=` | Topics |
| POST | `/api/content/topics/{id}/upload` | Upload topic content |
| GET | `/api/dashboard/me` | Student dashboard |
| GET | `/api/admin/*` | Admin CRUD |

### Query Request (RAG)

```json
{
  "query": "string",
  "workflow": "qa|summarize|generate",
  "marks": 2|5|10,
  "top_k": 5,
  "format": "bullets|paragraph",
  "subject": "uuid",  // subject_id for RAG filter
  "topic": "uuid"     // topic_id for RAG filter
}
```

---

## Dependency Graph

```
Phase 1.1 (Backend routes) ──┬──► Phase 1.2 (Frontend API)
                             └──► Phase 1.3 (Chat IDs)
Phase 2.1 (Backend stream) ──────► Phase 2.2 (Frontend stream UX)
Phase 3 ─────────────────────────► Independent
Phase 4 ─────────────────────────► After Phase 3
```

---

## Checklist Summary

### Phase 1
- [ ] Backend: `GET /api/content/subjects/{subject_id}/topics`
- [ ] Frontend: Update `getSubjects`, `getTopics` paths and add auth
- [ ] Frontend: Replace mock SUBJECTS/TOPICS with API data
- [ ] Chat: Pass subject_id, topic_id (UUIDs) to query

### Phase 2
- [ ] Backend: Streaming endpoint
- [ ] Frontend: Prefer streamQuery, debounce, skeleton

### Phase 3
- [ ] Backend: `/auth/me`, rate limiting, health checks
- [ ] Both: Structured errors, logging

### Phase 4
- [ ] Per enhancement (separate tickets)

---

---

## Quick Start for AI Agents

Cursor rules in `.cursor/rules/` enable fast context loading:

| Rule | Scope | Purpose |
|------|-------|---------|
| `syllabiq-core.mdc` | Always | Project overview, hierarchy, conventions |
| `syllabiq-backend.mdc` | `SyllabiQ-service/**/*.py` | FastAPI, models, RAG patterns |
| `syllabiq-frontend.mdc` | `SyllabiQ-frontend/**/*.{ts,tsx}` | React, API client, accessibility |
| `syllabiq-api.mdc` | API files | Request/response contracts, integration |

**Agent init**: Open any project file; the core rule loads automatically. Backend/frontend/API rules activate when editing matching files.

---

*Last updated: 2025-02-20*
