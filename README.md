# SyllabiQ – Backend Service
**Syllabus-Aware Educational AI using RAG & Multi-Agent Architecture**

---

## 📌 Overview

SyllabiQ is a backend service for a syllabus-aware educational AI platform designed to help college students with:
- syllabus-aligned Q&A
- exam-oriented explanations
- notes summarization
- practice question generation

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
| Embeddings | OpenAI text-embedding-3-small |
| LLM | OpenAI GPT-4o-mini |
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
- **OpenAI embeddings** (text-embedding-3-small) for semantic search
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

backend/
│
├── app/
│ ├── main.py
│ ├── api/
│ ├── agents/
│ │ ├── intent_agent.py
│ │ ├── retrieval_agent.py
│ │ ├── generation_agent.py
│ │ └── validation_agent.py
│ ├── rag/
│ │ ├── embeddings.py
│ │ ├── vector_store.py
│ │ └── retriever.py
│ ├── prompts/
│ ├── schemas/
│ └── utils/
│
├── data/
├── requirements.txt
└── README.md


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

## ⚙️ Configuration

Set in `.env` (see `.env.example`):

- `OPENAI_API_KEY` — Required for RAG (embeddings + generation)
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

