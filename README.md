# SyllabiQ – Backend Service
**Syllabus-Aware Educational AI using RAG & Multi-Agent Architecture**

> 📌 **This is the backend service.** For the frontend UI, see [SyllabiQ Frontend](../SyllabiQ/README.md).

---

## 📌 Overview

SyllabiQ is a backend service for a syllabus-aware educational AI platform designed to help college students with:
- Syllabus-aligned Q&A
- Exam-oriented explanations
- Notes summarization
- Practice question generation

**Frontend**: The [SyllabiQ React frontend](../SyllabiQ/README.md) provides the user interface for these features.

The backend is built using **FastAPI**, **LangChain**, and **Retrieval-Augmented Generation (RAG)** with a **multi-agent orchestration layer** to ensure accuracy, control, and scalability.

The system does **not train or fine-tune** any language model.  
All intelligence is controlled using **retrieval, prompt orchestration, and guardrails at runtime**.

---

## 🚀 Key Features

### 1. Syllabus-Aware AI Responses
- Uses **manually curated syllabus and notes**
- Ensures responses stay within curriculum scope
- Prevents off-topic or over-detailed answers

---

### 2. Retrieval-Augmented Generation (RAG)
- Knowledge stored in a **vector database**
- Only **relevant syllabus chunks** are retrieved per query
- Reduces hallucinations and improves factual grounding

---

### 3. Multi-Agent Architecture
The system decomposes intelligence into specialized agents:
- Intent understanding
- Knowledge retrieval
- Answer generation
- Validation & refinement

This improves reliability and explainability.

---

### 4. Exam-Oriented Output Control
- Supports 2-mark / 5-mark / 10-mark answers
- Structured output (bullet points, headings)
- Difficulty-controlled question generation

---

### 5. Guardrails & Safety
- Syllabus boundary enforcement
- Output length control
- Academic tone enforcement
- Hallucination reduction via RAG

---

## 🧱 Tech Stack

| Layer | Technology |
|------|-----------|
| API Framework | FastAPI |
| Language | Python |
| AI Orchestration | LangChain |
| Vector Store | ChromaDB (persistent) |
| Embeddings | Model set in env: `OPENAI_EMBEDDING_MODEL` or `OLLAMA_EMBEDDING_MODEL` (quick config) |
| LLM | Model set in env: `OPENAI_MODEL` or `OLLAMA_MODEL`; provider via `LLM_PROVIDER` |
| Document Parsing | PyPDF2, python-docx |
| Frontend (external) | React + Vite |

---

## 🏗️ High-Level Architecture

Client (Next.js)
↓
FastAPI Gateway
↓
Intent Agent
↓
Retrieval Agent (Vector DB)
↓
Generation Agent (LLM)
↓
Validation / Guardrail Agent
↓
Final Response


---

## 🧠 Core System Components

### 1. API Layer (FastAPI)
- Handles HTTP requests
- Performs request validation
- Routes queries to orchestration layer
- Async and scalable

---

### 2. Orchestration Layer (LangChain)
- Manages agent execution order
- Handles prompt templates
- Coordinates retrieval + generation
- Acts as the “brain” of the system

---

### 3. Vector Knowledge Layer (RAG)
- **ChromaDB** for persistent vector storage
- **Embeddings**: Model name in env (`OPENAI_EMBEDDING_MODEL` or `OLLAMA_EMBEDDING_MODEL`); provider via `EMBEDDING_PROVIDER` / `LLM_PROVIDER`
- Stores:
  - syllabus
  - unit-wise notes
  - topic content (PDF, CSV, DOCX uploads)
- Chunks topic content via LangChain `RecursiveCharacterTextSplitter`
- Retrieves top‑K relevant chunks per query with optional subject/topic filters

---

### 4. LLM Invocation Layer
- Stateless LLM API calls
- Context-grounded generation only
- No memory, no training, no fine-tuning

---

## 🤖 Multi-Agent Design

### 🔹 1. Intent Classification Agent
**Responsibility**
- Understand user intent:
  - Concept explanation
  - Notes summarization
  - Practice question generation
  - Exam revision

**Output**
- Selected workflow type

---

### 🔹 2. Retrieval Agent
**Responsibility**
- Convert query into embeddings
- Query vector database
- Fetch relevant syllabus & notes

**Guarantee**
- AI sees only approved academic content

---

### 🔹 3. Generation Agent
**Responsibility**
- Generate response using:
  - Retrieved context
  - Prompt templates
  - Exam constraints

**Tools**
- LangChain prompt templates
- LLM API

---

### 🔹 4. Validation / Guardrail Agent
**Responsibility**
- Enforce:
  - syllabus relevance
  - answer length
  - academic tone
  - exam format

**May**
- Refine or regenerate response if needed

---

## 🔁 Workflow Orchestration

### 🧩 Workflow 1: Syllabus-Based Q&A

User Query
→ Intent Agent (Q&A)
→ Retrieval Agent (syllabus chunks)
→ Generation Agent
→ Validation Agent
→ Response


---

### 🧩 Workflow 2: Notes Summarization

User Notes
→ Intent Agent (summarization)
→ Retrieval Agent (related syllabus)
→ Generation Agent (summary)
→ Validation Agent
→ Response


---

### 🧩 Workflow 3: Practice Question Generation

User Topic + Difficulty
→ Intent Agent (question generation)
→ Retrieval Agent (topic content)
→ Generation Agent (MCQ / short / long)
→ Validation Agent
→ Response


---

## 🛡️ Guardrails Strategy

The system enforces guardrails at **multiple levels**:

### 1. Retrieval Guardrails
- Only approved syllabus data is retrievable
- No open-internet generation

---

### 2. Prompt Guardrails
- Explicit syllabus boundaries
- Exam-oriented formatting instructions
- Length and difficulty constraints

---

### 3. Post‑Generation Guardrails
- Output validation
- Refusal or regeneration on violations
- Removal of irrelevant content

---

## 📂 Suggested Backend Folder Structure

```
SyllabiQ-Service/
├── app/
│   ├── main.py                     # FastAPI app initialization & routing
│   ├── api.py                      # Main API endpoints
│   ├── config.py                   # Configuration management
│   ├── agents.py                   # Agent orchestration logic
│   ├── institutions.py             # Institution management utilities
│   ├── prompts.py                  # LLM prompt templates
│   ├── rag.py                      # RAG pipeline wrapper
│   ├── schemas.py                  # Pydantic request/response schemas
│   │
│   ├── admin/                      # Admin panel API routes
│   │   └── routes.py               # Admin user/role/institution management
│   │
│   ├── auth/                       # Authentication & authorization
│   │   └── routes.py               # Login, signup, token refresh
│   │
│   ├── content/                    # Content management (syllabus, topics, etc.)
│   │   ├── __init__.py
│   │   ├── routes.py               # Main content API endpoints
│   │   ├── contexts.py             # Learning contexts database ops
│   │   ├── courses.py              # Course management
│   │   ├── departments.py          # Department management
│   │   ├── subjects.py             # Subject management
│   │   ├── syllabi.py              # Syllabus management
│   │   ├── topics.py               # Topic management
│   │   └── uploads.py              # File upload handling & parsing
│   │
│   ├── dashboard/                  # Dashboard & analytics
│   │   └── routes.py               # Dashboard stats & KPIs
│   │
│   ├── db/                         # Database utilities
│   │   ├── __init__.py
│   │   ├── utils.py                # Common database operations
│   │   └── middleware.py           # Database connection middleware
│   │
│   ├── models/                     # SQLAlchemy ORM models
│   │   ├── audit.py                # Audit log model
│   │   ├── institution.py          # Institution model
│   │   ├── role.py                 # Role & permissions model
│   │   ├── user.py                 # User model
│   │   ├── content.py              # Content models (Syllabus, Topic, etc.)
│   │   └── visits.py               # User activity tracking model
│   │
│   ├── agents/                     # Multi-agent orchestration
│   │   ├── __init__.py
│   │   └── core.py                 # Agent implementations & workflows
│   │
│   ├── rag/                        # Retrieval-Augmented Generation
│   │   ├── indexer.py              # Indexing & chunking logic
│   │   ├── retriever.py            # Vector similarity search
│   │   └── vector_store.py         # ChromaDB interface
│   │
│   ├── prompts/                    # Prompt templates & orchestration
│   │   └── __init__.py             # Prompt registry
│   │
│   ├── schemas/                    # Pydantic schemas for validation
│   │   ├── __init__.py
│   │   └── auth.py                 # Auth request/response schemas
│   │
│   └── seeds/                      # Database seeding
│       └── seed_db.py              # Initial data population
│
├── requirements.txt                # Python dependencies
├── .env.example                    # Environment template
├── README.md                       # This file
└── docs/                           # Documentation (external)
    ├── API.md
    ├── ARCHITECTURE.md
    ├── SCHEMA.md
    └── SEQUENCE_DIAGRAMS.mmd
```

---

## 🗂️ Module Descriptions

### Core Controllers
| Module | Role |
|--------|------|
| `api.py` | Main query endpoint → Intent Agent → Final response |
| `agents.py` | Multi-agent orchestration & workflow management |
| `rag.py` | RAG pipeline (retrieval + generation) |
| `config.py` | Environment & configuration management |

### API Routes
| Module | Responsibility |
|--------|-----------------|
| `auth/routes.py` | Authentication (login, signup, token refresh) |
| `admin/routes.py` | User/role/institution CRUD operations |
| `content/routes.py` | Syllabus, course, topic, subject management |
| `dashboard/routes.py` | Analytics, KPIs, usage statistics |

### Content Management
| Module | Purpose |
|--------|---------|
| `content/uploads.py` | File parsing (PDF, DOCX, CSV) & text extraction |
| `content/syllabi.py` | Syllabus CRUD & indexing |
| `content/topics.py` | Topic & topic content management |
| `content/courses.py` | Course structure management |
| `content/subjects.py` | Subject management |

### Data Layer
| Module | Purpose |
|--------|---------|
| `models/` | SQLAlchemy ORM models (User, Institution, Content, etc.) |
| `db/utils.py` | Database operations (queries, transactions) |
| `db/middleware.py` | Database session & connection management |
| `schemas/` | Pydantic validation schemas |

### Intelligence Layer
| Module | Purpose |
|--------|---------|
| `agents/core.py` | Intent, Retrieval, Generation, Validation agents |
| `rag/vector_store.py` | ChromaDB interface for semantic search |
| `rag/retriever.py` | Query embedding & context retrieval |
| `rag/indexer.py` | Text chunking & vector indexing |
| `prompts/` | Prompt templates for each agent workflow |


---

## 🎯 Design Principles

- **Control > Creativity**
- **Retrieval before generation**
- **Explainable AI workflows**
- **Academic safety over generality**

---

## 📦 Content Hierarchy & Student Binding

- **Department** → **Course** → **Subject** → **Syllabus** → **Topic** → **TopicContent**
- Students bind to a **department** during signup (required when institution is selected)
- **Topic content upload**: PDF, CSV, DOCX files are parsed, text extracted, and indexed into ChromaDB for RAG

---

## 🚀 Quick Start

### 1. Backend Setup
```bash
# Create virtual environment with Python 3.12
uv venv --python 3.12
source .venv/bin/activate

# Install dependencies
uv pip install -r requirements.txt
```

### 2. Start Backend Server
```bash
uv run uvicorn app.main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`, with docs at `http://localhost:8000/docs`.

### 3. Frontend Setup (Optional)
From the `SyllabiQ` directory:
```bash
pnpm install
VITE_API_BASE=http://localhost:8000/api pnpm dev
```

For detailed frontend setup, see [SyllabiQ Frontend README](../SyllabiQ/README.md).

---

## ⚙️ Configuration

All configuration is via environment variables. Copy `.env.example` to `.env` and set values. **All model names are in env for quick config** — switch chat or embedding models without code changes.

**RAG (LLM + embeddings):**

- `LLM_PROVIDER` — `openai` (default) or `ollama`. Chooses the chat model for generation.
- `EMBEDDING_PROVIDER` — Optional. `openai` or `ollama`; if unset, follows `LLM_PROVIDER`. Changing embedding provider may require re-indexing ChromaDB.
- **OpenAI** (when provider is `openai`): `OPENAI_API_KEY` (required); `OPENAI_MODEL` (default: `gpt-4o-mini`); `OPENAI_EMBEDDING_MODEL` (default: `text-embedding-3-small`).
- **Ollama** (when provider is `ollama`): `OLLAMA_BASE_URL` (default: `http://localhost:11434`), `OLLAMA_MODEL` (default: `llama3.2`), `OLLAMA_EMBEDDING_MODEL` (default: `nomic-embed-text`). Ensure Ollama is running locally or at the given URL.

**Other:**

- `CHROMA_PERSIST_DIR` — ChromaDB persistence directory (default: `./chroma_data`)
- `UPLOAD_MAX_SIZE_MB` — Max file size for topic uploads (default: 10)

## 📈 Future Enhancements

- Adaptive learning paths
- Analytics on student queries
- Voice-based interaction
- Multi-language support

---

## 🧠 One‑Line Summary

> *SyllabiQ is a syllabus-aware educational AI backend that uses Retrieval-Augmented Generation and a multi-agent architecture to provide accurate, exam-oriented academic assistance through controlled LLM invocation.*

---

## 📜 License
Academic / Educational Use

