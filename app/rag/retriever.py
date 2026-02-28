import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

"""
RAG (Retrieval-Augmented Generation) helpers.
Uses ChromaDB + OpenAI/Ollama embeddings when configured.
"""


async def retrieve_from_vectorstore(
    query: str,
    top_k: int = 5,
    subject_id: Optional[str] = None,
    topic_id: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Retrieve relevant chunks from vector store.
    Return format: [{"id": "...", "text": "...", "source": "topic_name", "metadata": {...}}]
    Returns an empty list when the vector store or embeddings are unavailable.
    """
    try:
        from app.rag.vector_store import embed_query, query_collection
    except ImportError:
        logger.warning("Vector store module not available — returning empty context")
        return []

    embedding = embed_query(query)
    if not embedding:
        logger.warning("Embedding generation failed — returning empty context")
        return []

    where = None
    if subject_id or topic_id:
        conditions = []
        if subject_id:
            conditions.append({"subject_id": subject_id})
        if topic_id:
            conditions.append({"topic_id": topic_id})
        where = {"$and": conditions} if len(conditions) > 1 else conditions[0]

    return query_collection(embedding, top_k=top_k, where=where)

