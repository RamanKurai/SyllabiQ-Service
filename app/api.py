import json
import time
import asyncio
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Header
from fastapi.responses import StreamingResponse
from jose import jwt

from app.config import settings
from app.schemas import (
    QueryRequest,
    QueryResponse,
    EmbeddingRequest,
    EmbeddingResponse,
    EmbedTextResponse,
)
from app.agents import IntentAgent, RetrievalAgent, GenerationAgent, ValidationAgent

logger = logging.getLogger(__name__)

router = APIRouter()

# initialize lightweight agents (singletons for now)
intent_agent = IntentAgent()
retrieval_agent = RetrievalAgent()
generation_agent = GenerationAgent()
validation_agent = ValidationAgent()


def _decode_user_id(authorization: Optional[str]) -> Optional[int]:
    """Extract user_id from Bearer JWT; returns None on any failure."""
    if not authorization:
        return None
    try:
        parts = authorization.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return None
        payload = jwt.decode(parts[1], settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        sub = payload.get("sub")
        return int(sub) if sub is not None else None
    except Exception:
        return None


async def _update_student_context(
    user_id: int,
    subject_id_str: Optional[str],
    topic_id_str: Optional[str],
    intent: str,
) -> None:
    """
    Upsert UserContext and record a TopicVisit for the student dashboard KPIs.
    Non-fatal — errors are swallowed so they never affect the main request.
    """
    try:
        import uuid as _uuid
        from datetime import datetime
        from sqlmodel import select as _select
        from app.db import async_session
        from app.models.content import UserContext
        from app.models.visits import TopicVisit

        subject_uuid = _uuid.UUID(subject_id_str) if subject_id_str else None
        topic_uuid = _uuid.UUID(topic_id_str) if topic_id_str else None
        now = datetime.utcnow()

        async with async_session() as session:
            # Upsert: find existing UserContext for (user_id, subject_id)
            stmt = _select(UserContext).where(
                UserContext.user_id == user_id,
                UserContext.subject_id == subject_uuid,
            )
            res = await session.execute(stmt)
            ctx = res.scalars().first()

            if ctx:
                ctx.last_intent = intent
                if topic_id_str:
                    ctx.last_topic = topic_id_str
                ctx.updated_at = now
            else:
                ctx = UserContext(
                    user_id=user_id,
                    subject_id=subject_uuid,
                    last_topic=topic_id_str,
                    last_intent=intent,
                    updated_at=now,
                )
            session.add(ctx)

            # Record a TopicVisit when a specific topic was part of the query
            if topic_uuid and subject_uuid:
                visit = TopicVisit(
                    user_id=user_id,
                    subject_id=subject_uuid,
                    topic_id=topic_uuid,
                )
                session.add(visit)

            await session.commit()
    except Exception as exc:
        logger.debug("UserContext update failed (non-fatal): %s", exc)


async def _log_query(
    user_id: Optional[int],
    payload: QueryRequest,
    intent: str,
    chunks_retrieved: int,
    response_time_ms: int,
    success: bool,
    error_type: Optional[str],
) -> None:
    """Persist a QueryLog row. Errors here must never affect the caller."""
    try:
        from app.db import async_session
        from app.models.query_log import QueryLog

        log = QueryLog(
            user_id=user_id,
            subject_id=payload.subject,
            topic_id=payload.topic,
            intent=intent,
            workflow=payload.workflow,
            llm_provider=settings.LLM_PROVIDER,
            chunks_retrieved=chunks_retrieved,
            response_time_ms=response_time_ms,
            success=success,
            error_type=error_type,
        )
        async with async_session() as session:
            session.add(log)
            await session.commit()
    except Exception as exc:
        logger.debug("QueryLog insert failed (non-fatal): %s", exc)


@router.get("/", include_in_schema=False)
async def root():
    return {"message": "SyllabiQ backend. See /docs for API"}


@router.post("/v1/query", response_model=QueryResponse, tags=["query"])
async def query_endpoint(payload: QueryRequest, authorization: Optional[str] = Header(None)):
    """
    Core query endpoint.
    Workflow:
      1. Intent detection
      2. Retrieval of relevant syllabus chunks (skipped when user notes provided for summarization)
      3. Generation of response
      4. Validation (guardrails)
    """
    start = time.monotonic()
    user_id = _decode_user_id(authorization)
    intent = "qa"
    retrieved: list = []

    try:
        intent = await intent_agent.detect_intent(payload.query, payload.workflow)

        # When user supplies their own notes for summarization, use those as context
        if payload.notes and intent == "summarize":
            retrieved = [{"id": "user-notes", "text": payload.notes, "source": "user-provided"}]
        else:
            retrieved = await retrieval_agent.retrieve(
                payload.query,
                top_k=payload.top_k or 5,
                subject_id=payload.subject,
                topic_id=payload.topic,
            )

        generated = await generation_agent.generate(
            query=payload.query,
            intent=intent,
            context=retrieved,
            marks=payload.marks,
            difficulty=payload.difficulty,
            question_type=payload.question_type,
            num_questions=payload.num_questions,
        )
        validated = await validation_agent.validate(generated, context=retrieved)

        elapsed_ms = int((time.monotonic() - start) * 1000)
        asyncio.create_task(_log_query(
            user_id=user_id,
            payload=payload,
            intent=intent,
            chunks_retrieved=len(retrieved),
            response_time_ms=elapsed_ms,
            success=True,
            error_type=None,
        ))
        if user_id and payload.subject:
            asyncio.create_task(_update_student_context(
                user_id=user_id,
                subject_id_str=payload.subject,
                topic_id_str=payload.topic,
                intent=intent,
            ))

        return QueryResponse(
            answer=validated["answer"],
            citations=validated.get("citations", []),
            metadata={"intent": intent, "chunks_returned": len(retrieved)},
        )
    except Exception as e:
        elapsed_ms = int((time.monotonic() - start) * 1000)
        asyncio.create_task(_log_query(
            user_id=user_id,
            payload=payload,
            intent=intent,
            chunks_retrieved=len(retrieved),
            response_time_ms=elapsed_ms,
            success=False,
            error_type=type(e).__name__,
        ))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/v1/query/stream", tags=["query"])
async def query_stream_endpoint(payload: QueryRequest, authorization: Optional[str] = Header(None)):
    """
    Streaming query endpoint (SSE). Yields token chunks as `data: {"delta": "..."}` events,
    followed by a final `data: {"done": true, "citations": [...]}` event.
    Works with both OpenAI and Ollama LLM providers.
    """
    user_id = _decode_user_id(authorization)

    async def event_generator():
        start = time.monotonic()
        intent = "qa"
        retrieved: list = []
        try:
            intent = await intent_agent.detect_intent(payload.query, payload.workflow)

            if payload.notes and intent == "summarize":
                retrieved = [{"id": "user-notes", "text": payload.notes, "source": "user-provided"}]
            else:
                retrieved = await retrieval_agent.retrieve(
                    payload.query,
                    top_k=payload.top_k or 5,
                    subject_id=payload.subject,
                    topic_id=payload.topic,
                )

            async for token in generation_agent.generate_stream(
                query=payload.query,
                intent=intent,
                context=retrieved,
                marks=payload.marks,
                difficulty=payload.difficulty,
                question_type=payload.question_type,
                num_questions=payload.num_questions,
            ):
                yield f"data: {json.dumps({'delta': token})}\n\n"

            elapsed_ms = int((time.monotonic() - start) * 1000)
            asyncio.create_task(_log_query(
                user_id=user_id,
                payload=payload,
                intent=intent,
                chunks_retrieved=len(retrieved),
                response_time_ms=elapsed_ms,
                success=True,
                error_type=None,
            ))
            if user_id and payload.subject:
                asyncio.create_task(_update_student_context(
                    user_id=user_id,
                    subject_id_str=payload.subject,
                    topic_id_str=payload.topic,
                    intent=intent,
                ))

            citations = [
                {"id": c.get("id", ""), "source": c.get("source"), "text": (c.get("text") or "")[:200]}
                for c in retrieved
            ]
            yield f"data: {json.dumps({'done': True, 'citations': citations})}\n\n"
        except Exception as exc:
            elapsed_ms = int((time.monotonic() - start) * 1000)
            asyncio.create_task(_log_query(
                user_id=user_id,
                payload=payload,
                intent=intent,
                chunks_retrieved=len(retrieved),
                response_time_ms=elapsed_ms,
                success=False,
                error_type=type(exc).__name__,
            ))
            yield f"data: {json.dumps({'error': str(exc)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.post("/v1/embed", response_model=EmbeddingResponse, tags=["embeddings"])
async def embed_texts_endpoint(payload: EmbeddingRequest):
    """
    Generate embeddings for one or more texts using the RAG system's embedding model.
    
    You can provide either:
    - A single `text` value, or
    - Multiple `texts` in a list
    
    Returns embeddings with metadata about the model and dimension.
    """
    try:
        from app.rag.vector_store import embed_texts, embed_query, _get_embedding_fn
        
        # Determine texts to embed
        texts_to_embed = []
        if payload.text:
            texts_to_embed = [payload.text]
        elif payload.texts:
            texts_to_embed = payload.texts
        else:
            raise HTTPException(status_code=400, detail="Provide either 'text' or 'texts'")
        
        # Check if embedding function is available
        embedding_fn = _get_embedding_fn()
        if not embedding_fn:
            detail = (
                "Embedding service not configured. Ensure Ollama is running and OLLAMA_BASE_URL is set."
                if settings.embedding_provider == "ollama"
                else "Embedding service not configured. Ensure OPENAI_API_KEY is set."
            )
            raise HTTPException(status_code=503, detail=detail)

        # Generate embeddings
        embeddings = embed_texts(texts_to_embed)
        if not embeddings:
            raise HTTPException(
                status_code=500,
                detail="Failed to generate embeddings. Check API keys and configuration."
            )
        
        return EmbeddingResponse(
            embeddings=embeddings,
            texts=texts_to_embed,
            dimension=len(embeddings[0]) if embeddings else 0,
            model=settings.embedding_model_name,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/v1/embed-query", response_model=EmbedTextResponse, tags=["embeddings"])
async def embed_query_endpoint(text: str):
    """
    Generate embedding for a single query text.
    
    This is optimized for query strings and returns a single embedding vector.
    Use this endpoint when you want to search for similar content in the vector store.
    """
    try:
        from app.rag.vector_store import embed_query, _get_embedding_fn
        
        # Check if embedding function is available
        embedding_fn = _get_embedding_fn()
        if not embedding_fn:
            detail = (
                "Embedding service not configured. Ensure Ollama is running and OLLAMA_BASE_URL is set."
                if settings.embedding_provider == "ollama"
                else "Embedding service not configured. Ensure OPENAI_API_KEY is set."
            )
            raise HTTPException(status_code=503, detail=detail)

        # Generate embedding
        embedding = embed_query(text)
        if not embedding:
            raise HTTPException(
                status_code=500,
                detail="Failed to generate embedding. Check API keys and configuration."
            )
        
        return EmbedTextResponse(
            text=text,
            embedding=embedding,
            dimension=len(embedding),
            model=settings.embedding_model_name,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
