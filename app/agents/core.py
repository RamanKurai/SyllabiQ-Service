import logging
from typing import List, Dict, Any, Optional
import asyncio

logger = logging.getLogger(__name__)

"""
Core agent implementations: intent, retrieval (ChromaDB), generation (OpenAI or Ollama), validation.
"""

_VALID_INTENTS = {"qa", "summarize", "generate"}


class IntentAgent:
    async def detect_intent(self, query: str, hint: Optional[str] = None) -> str:
        """
        Simple intent detection.
        Accepts an optional workflow hint; falls back to keyword matching.
        """
        await asyncio.sleep(0)  # keep it async
        if hint and hint in _VALID_INTENTS:
            return hint
        q = query.lower()
        if any(w in q for w in ["summarize", "summary", "short notes"]):
            return "summarize"
        if any(w in q for w in ["generate", "mcq", "questions", "practice"]):
            return "generate"
        return "qa"


class RetrievalAgent:
    async def retrieve(
        self,
        query: str,
        top_k: int = 5,
        subject_id: Optional[str] = None,
        topic_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve from ChromaDB vector store. Falls back to stub if not configured.
        """
        from app.rag.retriever import retrieve_from_vectorstore
        return await retrieve_from_vectorstore(
            query, top_k=top_k, subject_id=subject_id, topic_id=topic_id
        )


class GenerationAgent:
    def _get_llm(self):
        from app.config import settings
        if settings.LLM_PROVIDER == "ollama":
            from langchain_ollama import ChatOllama
            return ChatOllama(
                base_url=settings.OLLAMA_BASE_URL,
                model=settings.OLLAMA_MODEL,
                temperature=0.3,
            )
        elif settings.OPENAI_API_KEY:
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(
                model=settings.OPENAI_MODEL,
                openai_api_key=settings.OPENAI_API_KEY,
                temperature=0.3,
            )
        return None

    def _build_messages(
        self,
        query: str,
        intent: str,
        ctx_text: str,
        marks: Optional[int] = None,
        difficulty: Optional[str] = None,
        question_type: Optional[str] = None,
        num_questions: Optional[int] = None,
    ):
        from langchain_core.messages import HumanMessage, SystemMessage

        if intent == "summarize":
            system = (
                "You are a helpful tutor. Summarize the provided text into concise, numbered bullet points "
                "suitable for exam revision. Focus on key concepts, definitions, formulas, and important facts."
            )
            user = f"Content to summarize:\n{ctx_text[:8000]}\n\nProvide a structured bullet-point summary."
        elif intent == "generate":
            n = num_questions or 5
            qt = question_type or "mixed"
            diff = difficulty or "medium"
            system = (
                "You are an exam paper setter. Generate practice questions from the provided context. "
                "Return ONLY a valid JSON array. Each element must have: "
                '"question" (string), "type" ("mcq"|"short"|"long"), '
                '"options" (array of 4 strings for mcq, null otherwise), "answer" (string). '
                "Do not include any text outside the JSON array."
            )
            user = (
                f"Context:\n{ctx_text[:8000]}\n\n"
                f"Generate {n} {qt} questions at {diff} difficulty level. "
                f"Return only the JSON array."
            )
        else:
            marks_hint = ""
            if marks:
                length_map = {2: "brief (2-3 sentences)", 5: "medium (1-2 paragraphs)", 10: "detailed (3-5 paragraphs)"}
                marks_hint = f" Answer length: {length_map.get(marks, 'medium')}."
            system = (
                "You are a helpful tutor. Answer based only on the provided syllabus/notes context. "
                f"Be concise.{marks_hint}"
            )
            user = f"Context:\n{ctx_text[:8000]}\n\nQuestion: {query}\n\nProvide a clear answer."

        return [SystemMessage(content=system), HumanMessage(content=user)]

    async def generate(
        self,
        query: str,
        intent: str,
        context: List[Dict[str, Any]],
        marks: Optional[int] = None,
        difficulty: Optional[str] = None,
        question_type: Optional[str] = None,
        num_questions: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Generate answer using configured LLM (OpenAI or Ollama) with retrieved context.
        Falls back to simple synthesis if not configured.
        """
        ctx_text = "\n\n".join([c.get("text", "") for c in context if c.get("text")])
        if not ctx_text:
            if intent in ("generate", "summarize"):
                # No uploaded material yet — let the LLM work from the query/topic alone
                ctx_text = f"Topic: {query}"
            else:
                answer = "No relevant content found in the knowledge base. Please upload topic materials or ask a more specific question."
                return {"answer": answer, "raw": {"context": context}}

        msgs = self._build_messages(query, intent, ctx_text, marks, difficulty, question_type, num_questions)
        llm = self._get_llm()

        if llm:
            try:
                resp = await llm.ainvoke(msgs)
                answer = resp.content if hasattr(resp, "content") else str(resp)
                return {"answer": answer, "raw": {"context": context}}
            except Exception as exc:
                logger.error("LLM invocation failed (%s): %s", type(exc).__name__, exc)
                return {
                    "answer": "Sorry, the language model is currently unavailable. Please try again shortly.",
                    "raw": {"context": context, "error": str(exc)},
                }

        logger.warning("No LLM provider configured — returning raw context fallback")
        answer = f"Based on {len(context)} source(s): " + (ctx_text[:500] + "..." if len(ctx_text) > 500 else ctx_text)
        return {"answer": answer, "raw": {"context": context}}

    async def generate_stream(
        self,
        query: str,
        intent: str,
        context: List[Dict[str, Any]],
        marks: Optional[int] = None,
        difficulty: Optional[str] = None,
        question_type: Optional[str] = None,
        num_questions: Optional[int] = None,
    ):
        """Yield token chunks via LLM streaming. Works with both ChatOpenAI and ChatOllama."""
        ctx_text = "\n\n".join([c.get("text", "") for c in context if c.get("text")])
        if not ctx_text:
            if intent in ("generate", "summarize"):
                ctx_text = f"Topic: {query}"
            else:
                yield "No relevant content found in the knowledge base. Please upload topic materials or ask a more specific question."
                return

        msgs = self._build_messages(query, intent, ctx_text, marks, difficulty, question_type, num_questions)
        llm = self._get_llm()

        if llm:
            try:
                async for chunk in llm.astream(msgs):
                    token = chunk.content if hasattr(chunk, "content") else str(chunk)
                    if token:
                        yield token
            except Exception as exc:
                logger.error("LLM streaming failed (%s): %s", type(exc).__name__, exc)
                yield "Sorry, the language model is currently unavailable. Please try again shortly."
        else:
            logger.warning("No LLM provider configured — returning raw context fallback")
            yield f"Based on {len(context)} source(s): " + (ctx_text[:500] + "..." if len(ctx_text) > 500 else ctx_text)


class ValidationAgent:
    async def validate(self, generated: Dict[str, Any], context: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Enforce guardrails: ensure answer is within syllabus scope, length limits, and format.
        This is a placeholder: implement detailed checks and possible regeneration.
        """
        await asyncio.sleep(0)
        answer = generated.get("answer", "")
        # Very simple guardrail: trim overly long answers
        if len(answer) > 2000:
            answer = answer[:2000] + "..."
        citations = [
            {"id": c.get("id", ""), "source": c.get("source"), "text": (c.get("text") or "")[:200]}
            for c in context
        ]
        return {"answer": answer, "citations": citations}

