# SyllabiQ-service — Architecture Overview

Brief overview of the backend architecture and main components.

- **Framework:** FastAPI with `SQLModel` (SQLAlchemy) for models and Pydantic-like schemas.
- **API mounting:** The main routers are mounted under the `/api` prefix (see `app/main.py`). The core query endpoint is exposed as `/api/v1/query`.
- **Database:** Postgres (UUIDs for content tables, integers for tenant/user tables).
- **Core pipeline (agents):** `IntentAgent` → `RetrievalAgent` → `GenerationAgent` → `ValidationAgent` (see `app/api.py`). Current agent implementations are synchronous placeholders that return a full JSON response (no SSE streaming at present).
- **Key modules:**
  - `app/models` — DB models (User, Role, Institution, Course, Subject, Syllabus, Topic, UserContext)
  - `app/agents` — Intent / Retrieval / Generation / Validation agent implementations (placeholders in `app/agents/core.py`)
  - `app/api.py` — primary HTTP endpoints (mounted at `/api`)
  - `app/auth`, `app/admin` — authentication and admin-protected routes (JWT-based, expect `Authorization: Bearer <token>` header)

Integration notes:
- The frontend may request streaming (SSE) but the current implementation returns a single JSON response; if you plan to support streaming, return chunked SSE/NDJSON from `/api/v1/query` and update `app/api.py` to stream the generation output.
- The retrieval agent is intended to be backed by an embeddings/vectorstore (FAISS/Chroma/etc.) in future; currently it returns stubbed chunks.

Deployment note: Minimal single-process service with room to scale agents or move them to separate workers.
