"""
RAG (Retrieval-Augmented Generation) module.
Handles embeddings, vector storage, and document retrieval.
"""

from app.rag.vector_store import (
    embed_texts,
    embed_query,
    add_documents,
    query_collection,
    get_collection,
    delete_by_content_id,
)
from app.rag.retriever import retrieve_from_vectorstore

__all__ = [
    "embed_texts",
    "embed_query",
    "add_documents",
    "query_collection",
    "get_collection",
    "delete_by_content_id",
    "retrieve_from_vectorstore",
]
