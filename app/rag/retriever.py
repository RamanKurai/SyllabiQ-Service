from typing import List, Dict, Any, Optional

"""
RAG (Retrieval-Augmented Generation) helpers.
Uses ChromaDB + OpenAI embeddings when configured.
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
    """
    try:
        from app.rag.vector_store import embed_query, query_collection
    except ImportError:
        return _stub_retrieve(query, top_k)

    embedding = embed_query(query)
    if not embedding:
        return _stub_retrieve(query, top_k)

    where = None
    if subject_id or topic_id:
        conditions = []
        if subject_id:
            conditions.append({"subject_id": subject_id})
        if topic_id:
            conditions.append({"topic_id": topic_id})
        where = {"$and": conditions} if len(conditions) > 1 else conditions[0]

    results = query_collection(embedding, top_k=top_k, where=where)
    if not results:
        return _stub_retrieve(query, top_k)
    return results


def _stub_retrieve(query: str, top_k: int) -> List[Dict[str, Any]]:
    """Fallback when vector store is not configured."""
    return [
        {"id": f"chunk_{i+1}", "text": f"Stub snippet {i+1} for '{query}'", "source": "syllabus"}
        for i in range(top_k)
    ]

