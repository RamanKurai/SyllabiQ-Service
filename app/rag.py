"""
RAG helpers: embeddings, vector store shim, and retriever.
These are intended as integration points for concrete implementations
(e.g., OpenAI embeddings + Chroma/FAISS).
"""
from typing import List, Dict, Any, Optional


def embed_texts(texts: List[str]) -> List[List[float]]:
    """
    Return embeddings for a list of texts.
    Replace with real embedding call (OpenAI, Cohere, etc).
    """
    # Dummy embeddings: vector of zeros sized to 8
    return [[0.0] * 8 for _ in texts]


class VectorStore:
    def __init__(self):
        # placeholder in-memory index
        self.store = []

    def add(self, id: str, text: str, metadata: Optional[Dict[str, Any]] = None):
        self.store.append({"id": id, "text": text, "metadata": metadata or {}})

    def query(self, embedding, top_k: int = 5):
        # naive: return first top_k items
        return self.store[:top_k]


def build_retriever_from_store(store: VectorStore):
    """
    Return a callable retriever that accepts a query string and returns top-k chunks.
    """
    def retriever(query: str, top_k: int = 5):
        return store.query(None, top_k=top_k)
    return retriever

