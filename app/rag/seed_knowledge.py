"""
Seed static SyllabiQ knowledge into ChromaDB so the RAG system can answer
questions about the platform itself (what it is, how it works, its features).

This is idempotent: it checks for the presence of seeded docs before indexing.
Embedding is synchronous (run in a thread pool from async startup code).
"""

SYLLABIQ_KNOWLEDGE = """
SyllabiQ: AI-Powered Syllabus-Aware Educational Assistant

What is SyllabiQ?
SyllabiQ is an intelligent educational assistant designed for students and educators in higher education institutions. It combines a Retrieval-Augmented Generation (RAG) architecture with a multi-agent AI system to deliver accurate, syllabus-specific answers, summaries, and practice questions. Unlike generic AI chatbots, SyllabiQ grounds every response in the actual uploaded course material for each subject and topic.

Role and Purpose
SyllabiQ bridges the gap between raw syllabus content and student comprehension. Administrators upload PDF, CSV, or DOCX files for each topic, which are automatically parsed, chunked into semantic pieces, embedded into vectors, and stored in ChromaDB. When a student asks a question, the system retrieves the most relevant syllabus chunks and generates an answer grounded in those chunks — not hallucinated from general internet training data. This makes SyllabiQ ideal for exam preparation, note revision, and self-assessment.

How SyllabiQ Works: The RAG Pipeline
RAG stands for Retrieval-Augmented Generation. The process for every query is:
1. The student types a question or pastes notes in the frontend.
2. The frontend sends a POST request to /api/v1/query with the selected subject_id, topic_id, and query text.
3. The query is embedded into a high-dimensional vector using the configured embedding model.
4. ChromaDB is searched for the top-k most semantically similar syllabus text chunks, filtered by subject and topic.
5. Those chunks are passed as context to the LLM (OpenAI or Ollama).
6. The LLM generates an answer grounded in the retrieved context.
7. A validation step applies guardrails: length limits, citation formatting, and scope enforcement.
8. The response is returned to the frontend with the answer and source citations.

The Multi-Agent System
SyllabiQ uses four specialized agents that run in sequence for every query:

IntentAgent: Detects what the user wants to do. If the user sends workflow="qa", it returns a question-answer response. If workflow="summarize", it generates a bullet-point summary. If workflow="generate", it creates structured practice questions. The agent also performs keyword-based detection as a fallback.

RetrievalAgent: Queries ChromaDB using the embedded query vector. It filters results by subject_id and topic_id to ensure only relevant course material is retrieved. If the embedding provider is unavailable (Ollama offline, no OpenAI key), it returns an empty result and the system informs the user that no content was found.

GenerationAgent: Calls the configured LLM using LangChain. It supports both OpenAI (GPT models via langchain-openai) and Ollama (local open-source models via langchain-ollama). The agent builds a system prompt and user message based on the detected intent, retrieved context, and any additional parameters (marks, difficulty, question type). It supports both standard invocation (ainvoke) and streaming (astream).

ValidationAgent: Applies guardrails to the generated response. It trims overly long answers, formats citations from the retrieved chunks, and returns the final validated response with source references.

Features and Capabilities
Chat Q&A: Ask any question about your subject or topic. SyllabiQ retrieves the relevant portions of the uploaded syllabus and provides a precise, cited answer. Answer length is controlled by the marks parameter (2, 5, or 10 marks).

Notes Summarizer: Paste your own handwritten or typed notes. SyllabiQ summarizes them into concise, numbered bullet points optimized for exam revision, focusing on key concepts, definitions, formulas, and important facts.

Practice Generator: Generate custom practice questions from your syllabus content. Choose the difficulty (easy, medium, hard), question type (MCQ, short answer, long answer, mixed), and number of questions. Questions are returned as structured JSON with the question, type, options (for MCQ), and answer.

Streaming Responses: The Chat Q&A interface uses Server-Sent Events (SSE) for real-time token-by-token streaming, providing a responsive chat experience even for longer answers.

Subject and Topic Filtering: Students select their subject and topic from the sidebar. All queries are automatically scoped to that subject and topic, ensuring the RAG retrieval only returns chunks from relevant course material.

AI Providers: OpenAI and Ollama
SyllabiQ supports two LLM providers configurable via the LLM_PROVIDER environment variable:

OpenAI Provider: Uses GPT models (default: gpt-4o-mini) for generation and text-embedding-3-small for embeddings. Requires an OPENAI_API_KEY. Best for production deployments with consistent quality.

Ollama Provider: Uses locally hosted open-source models (default: llama3.2) and nomic-embed-text for embeddings. Requires Ollama to be running at OLLAMA_BASE_URL (default: http://localhost:11434). Enables fully offline, private AI operation — no data leaves the institution's infrastructure. Switching providers requires re-indexing the ChromaDB vector store since embeddings change.

Multi-tenant Architecture
SyllabiQ is built for multiple institutions on a single deployment. Each institution has its own hierarchy: Institution → Departments → Courses → Subjects → Syllabi (units) → Topics → TopicContent (uploaded files). Role-based access control (RBAC) ensures users only see content relevant to their institution.

User Roles and Permissions
Student: Can access Chat Q&A, Notes Summarizer, and Practice Generator for their enrolled subjects. Must sign up with an institutional .edu email and wait for admin approval.

Teacher: Can manage student access and view content for their institution. Can approve or deny student sign-up requests.

Principal: Can manage institution-wide content and all users within their institution.

InstitutionAdmin: Full administrative access for their institution including user management, content management, and role assignments.

SuperAdmin: Global access to all institutions, content, users, and system settings. Can create new institutions and assign InstitutionAdmin roles.

Admin Dashboard and AI Insights
The admin panel provides KPIs for both platform usage (user counts, content distribution, signup trends) and AI usage (query volume, intent distribution, LLM provider breakdown, average response time, top subjects by query count). AI Insights are tracked via a QueryLog that records every query with its intent, LLM provider, retrieval count, response time, and success status.

Getting Started with SyllabiQ
Students: Sign up at /signup with your institution email (.edu required). Wait for admin approval. Once approved, log in, select your subject and topic from the sidebar, and start asking questions in the Chat tab.

Admins: Log in at /admin/login. Use the Admin panel to create institutions, upload topic content, manage users, and view AI Insights.

Technical Stack
Backend: FastAPI with SQLModel ORM, PostgreSQL or SQLite database, ChromaDB vector store, LangChain for LLM orchestration, JWT authentication.
Frontend: React 18 with TypeScript, Vite, Tailwind CSS, Radix UI components, recharts for visualizations.
"""

_DOC_SOURCE_TAG = "syllabiq_docs"
_DOC_ID_PREFIX = "syllabiq_knowledge"


def _is_already_seeded() -> bool:
    """Return True if SyllabiQ knowledge chunks are already present in ChromaDB."""
    try:
        from app.rag.vector_store import get_collection
        coll = get_collection()
        if not coll:
            return False
        result = coll.get(where={"source": _DOC_SOURCE_TAG}, limit=1)
        return bool(result and result.get("ids"))
    except Exception:
        return False


def seed_syllabiq_knowledge() -> int:
    """
    Chunk, embed, and index SyllabiQ knowledge into ChromaDB.
    Idempotent: skips if already seeded.
    Returns the number of chunks indexed (0 if skipped or embedding unavailable).
    """
    if _is_already_seeded():
        return 0

    try:
        from app.rag.vector_store import embed_texts, add_documents
        from app.rag.indexer import _chunk_text

        chunks = _chunk_text(SYLLABIQ_KNOWLEDGE.strip(), chunk_size=600, overlap=60)
        if not chunks:
            return 0

        embeddings = embed_texts(chunks)
        if not embeddings:
            # Embedding provider not yet available (Ollama not running, no API key); skip silently.
            return 0

        ids = [f"{_DOC_ID_PREFIX}_{i}" for i in range(len(chunks))]
        metadatas = [
            {
                "source": _DOC_SOURCE_TAG,
                "doc_type": "knowledge_base",
                "doc_name": "SyllabiQ Platform Overview",
                "chunk_index": str(i),
            }
            for i in range(len(chunks))
        ]
        add_documents(ids, chunks, metadatas)
        return len(chunks)
    except Exception:
        return 0
