# SyllabiQ Changelog

## Recent Updates (Department, RAG, Topic Content Upload)

### Backend (SyllabiQ-service)

**New features:**
- **Department model & API** — Departments (e.g., Computer Science, Finance) per institution; courses link to departments
- **Student–department binding** — Signup requires department selection when institution is selected
- **Topic content upload** — PDF, CSV, DOCX upload per topic; text extraction and storage in DB
- **RAG integration** — ChromaDB vector store + OpenAI embeddings; real retrieval and generation (LangChain + GPT-4o-mini)
- **Indexer** — Chunks topic content, embeds, and indexes into ChromaDB on upload

**New endpoints:**
- `GET/POST/PUT/DELETE /api/content/departments`
- `POST /api/content/topics/{topic_id}/upload` (multipart)
- `GET /api/content/topics/{topic_id}/content`

**Config:**
- `OPENAI_API_KEY` — Required for RAG
- `CHROMA_PERSIST_DIR` — ChromaDB persistence (default: `./chroma_data`)
- `UPLOAD_MAX_SIZE_MB` — Max upload size (default: 10)

**Schema changes:**
- New tables: `department`, `topic_content`
- New columns: `user.department_id`, `course.department_id`

### Frontend (SyllabiQ-frontend)

**New features:**
- **Signup** — Department dropdown (cascades from institution)
- **Admin** — Departments tab; course department selector; topic content upload (PDF/CSV/DOCX) per topic

**Updated:**
- Content manager default tab → Departments
- Course create/edit includes department selection
- Topics table shows uploaded content and upload button

### Migration

For existing databases, add new tables and columns. See `SyllabiQ-service/docs/SCHEMA.md` for schema details. Fresh installs will create all tables via `init_db()`.
