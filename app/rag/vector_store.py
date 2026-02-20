"""
ChromaDB vector store with OpenAI embeddings.
"""
from typing import List, Dict, Any, Optional

from app.config import settings

_COLLECTION_NAME = "syllabiq_chunks"
_chroma_client = None
_embedding_fn = None


def _get_embedding_fn():
    global _embedding_fn
    if _embedding_fn is not None:
        return _embedding_fn
    if not settings.OPENAI_API_KEY:
        return None
    try:
        from langchain_openai import OpenAIEmbeddings
        _embedding_fn = OpenAIEmbeddings(
            model="text-embedding-3-small",
            openai_api_key=settings.OPENAI_API_KEY,
        )
    except ImportError:
        try:
            from langchain.embeddings import OpenAIEmbeddings
            _embedding_fn = OpenAIEmbeddings(
                model="text-embedding-3-small",
                openai_api_key=settings.OPENAI_API_KEY,
            )
        except ImportError:
            _embedding_fn = None
    return _embedding_fn


def _get_client():
    global _chroma_client
    if _chroma_client is not None:
        return _chroma_client
    try:
        import chromadb
        from chromadb.config import Settings as ChromaSettings
        persist_dir = getattr(settings, "CHROMA_PERSIST_DIR", "./chroma_data") or "./chroma_data"
        _chroma_client = chromadb.PersistentClient(
            path=persist_dir,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        return _chroma_client
    except ImportError:
        return None


def get_collection():
    """Get or create the ChromaDB collection."""
    client = _get_client()
    if not client:
        return None
    return client.get_or_create_collection(
        _COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


def embed_texts(texts: List[str]) -> List[List[float]]:
    """Embed texts using OpenAI. Returns empty if not configured."""
    fn = _get_embedding_fn()
    if not fn:
        return []
    try:
        return fn.embed_documents(texts)
    except Exception:
        return []


def embed_query(query: str) -> List[float]:
    """Embed a single query string."""
    fn = _get_embedding_fn()
    if not fn:
        return []
    try:
        return fn.embed_query(query)
    except Exception:
        return []


def add_documents(ids: List[str], texts: List[str], metadatas: Optional[List[Dict[str, Any]]] = None):
    """Add documents to the collection. Embeds and upserts."""
    coll = get_collection()
    if not coll:
        return
    embeddings = embed_texts(texts)
    if not embeddings:
        return
    # Chroma expects metadata values to be str, int, float, or bool
    safe_metadatas = []
    for m in (metadatas or [{}] * len(texts)):
        safe = {}
        for k, v in m.items():
            if v is not None:
                safe[k] = str(v) if not isinstance(v, (int, float, bool)) else v
        safe_metadatas.append(safe)
    coll.upsert(ids=ids, embeddings=embeddings, documents=texts, metadatas=safe_metadatas)


def query_collection(
    query_embedding: List[float],
    top_k: int = 5,
    where: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """Query the collection. Returns list of {id, text, metadata}."""
    coll = get_collection()
    if not coll:
        return []
    kwargs = {"query_embeddings": [query_embedding], "n_results": top_k}
    if where:
        kwargs["where"] = where
    res = coll.query(**kwargs)
    if not res or not res["ids"] or not res["ids"][0]:
        return []
    results = []
    for i, doc_id in enumerate(res["ids"][0]):
        text = (res["documents"][0][i] if res.get("documents") else "") or ""
        meta = (res["metadatas"][0][i] if res.get("metadatas") else {}) or {}
        results.append({"id": doc_id, "text": text, "source": meta.get("topic_name", "syllabus"), "metadata": meta})
    return results


def delete_by_content_id(content_id: str):
    """Delete all chunks belonging to a TopicContent."""
    coll = get_collection()
    if not coll:
        return
    try:
        coll.delete(where={"content_id": content_id})
    except Exception:
        pass
