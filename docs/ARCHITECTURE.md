# SyllabiQ-service — Architecture Overview

Brief overview of the backend architecture and main components.

- **Framework:** FastAPI with `SQLModel` (SQLAlchemy) for models and Pydantic-like schemas.
- **API mounting:** The main routers are mounted under the `/api` prefix (see `app/main.py`). The core query endpoint is exposed as `/api/v1/query`.
- **Database:** Postgres (UUIDs for content tables, integers for tenant/user tables).
- **Core pipeline (agents):** `IntentAgent` → `RetrievalAgent` → `GenerationAgent` → `ValidationAgent` (see `app/api.py`). Agents use LangChain + OpenAI for retrieval and generation.
- **Key modules:**
  - `app/models` — DB models (User, Role, RoleAssignment, Institution, Department, Course, Subject, Syllabus, Topic, TopicContent, UserContext, TopicVisit, AuditLog)
  - `app/agents` — Intent / Retrieval / Generation / Validation agents (`app/agents/core.py`)
  - `app/rag` — Vector store (ChromaDB), indexer, retriever
  - `app/content/uploads` — Topic content upload (PDF, CSV, DOCX) and text extraction
  - `app/api.py` — primary HTTP endpoints (mounted at `/api`)
  - `app/auth`, `app/admin` — authentication and admin-protected routes (JWT-based, expect `Authorization: Bearer <token>` header)

Content hierarchy:
- **Department** (per institution) → **Course** → **Subject** → **Syllabus** → **Topic** → **TopicContent**
- Students bind to a department during signup when an institution is selected.

RAG pipeline:
- **Upload:** PDF/CSV/DOCX files are parsed (PyPDF2, python-docx), text extracted, stored in `TopicContent`.
- **Indexing:** `app/rag/indexer.py` chunks text, embeds via OpenAI, upserts into ChromaDB with metadata (topic_id, subject_id, course_id, department_id).
- **Retrieval:** `app/rag/retriever.py` embeds query, queries ChromaDB with optional subject/topic filters.
- **Generation:** LangChain ChatOpenAI (GPT-4o-mini) with retrieved context.

Integration notes:
- The frontend may request streaming (SSE) but the current implementation returns a single JSON response; if you plan to support streaming, return chunked SSE/NDJSON from `/api/v1/query` and update `app/api.py` to stream the generation output.
- Set `OPENAI_API_KEY` in `.env` for RAG. Without it, retrieval and generation fall back to stub responses.

Deployment note: Minimal single-process service with room to scale agents or move them to separate workers.
