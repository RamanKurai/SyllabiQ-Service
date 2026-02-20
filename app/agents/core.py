from typing import List, Dict, Any, Optional
import asyncio

"""
Core agent implementations: intent, retrieval (ChromaDB), generation (OpenAI), validation.
"""


class IntentAgent:
    async def detect_intent(self, query: str, hint: Optional[str] = None) -> str:
        """
        Simple intent detection placeholder.
        Replace with a classifier or prompt-based detection.
        """
        await asyncio.sleep(0)  # keep it async
        if hint:
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
    async def generate(self, query: str, intent: str, context: List[Dict[str, Any]], marks: Optional[int] = None) -> Dict[str, Any]:
        """
        Generate answer using OpenAI LLM with retrieved context.
        Falls back to simple synthesis if not configured.
        """
        from app.config import settings
        ctx_text = "\n\n".join([c.get("text", "") for c in context if c.get("text")])
        if settings.OPENAI_API_KEY and ctx_text:
            try:
                from langchain_openai import ChatOpenAI
                from langchain.schema import HumanMessage, SystemMessage
                llm = ChatOpenAI(
                    model="gpt-4o-mini",
                    openai_api_key=settings.OPENAI_API_KEY,
                    temperature=0.3,
                )
                system = (
                    "You are a helpful tutor. Answer based only on the provided syllabus/notes context. "
                    "Be concise. For exam-style answers, match the expected length (2 marks = brief, 5 = medium, 10 = detailed)."
                )
                user = f"Context:\n{ctx_text[:8000]}\n\nQuestion: {query}\n\nProvide a clear answer."
                msgs = [SystemMessage(content=system), HumanMessage(content=user)]
                resp = await llm.ainvoke(msgs)
                answer = resp.content if hasattr(resp, "content") else str(resp)
                return {"answer": answer, "raw": {"context": context}}
            except Exception:
                pass
        # Fallback
        answer = f"Based on {len(context)} source(s): " + (ctx_text[:500] + "..." if len(ctx_text) > 500 else ctx_text) if ctx_text else "No relevant content found. Please upload topic materials."
        return {"answer": answer, "raw": {"context": context}}


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

