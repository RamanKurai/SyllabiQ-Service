# SyllabiQ-service — Architecture Overview

Brief overview of the backend architecture and main components.

- **Framework:** FastAPI with `SQLModel` (SQLAlchemy) for models and Pydantic-like schemas.
- **Database:** Postgres (UUIDs for content tables, integers for tenant/user tables).
- **Core pipeline (agents):** `IntentAgent` → `RetrievalAgent` → `GenerationAgent` → `ValidationAgent` (see `app/api.py`).
- **Key modules:**
  - `app/models` — DB models (User, Role, Institution, Course, Subject, Syllabus, Topic, UserContext)
  - `app/agents`, `app/rag` — retrieval and generation helpers
  - `app/api.py` — primary HTTP endpoints (e.g. `/v1/query`)

Deployment note: Minimal single-process service with room to scale agents or move them to separate workers.
