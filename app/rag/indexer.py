"""
Chunk TopicContent, embed, and index into ChromaDB.
"""
from typing import List
import uuid

from app.db import async_session
from app.models.content import TopicContent, Topic, Syllabus, Subject, Course
from sqlmodel import select

from app.rag.vector_store import add_documents, embed_texts, delete_by_content_id, get_collection


def _chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """Simple chunking by character count with overlap."""
    if not text or not text.strip():
        return []
    try:
        from langchain.text_splitter import RecursiveCharacterTextSplitter
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=overlap,
            length_function=len,
        )
        return splitter.split_text(text)
    except ImportError:
        # Fallback: split by paragraphs/sentences
        chunks = []
        current = []
        current_len = 0
        for para in text.split("\n\n"):
            if current_len + len(para) > chunk_size and current:
                chunks.append("\n\n".join(current))
                current = [para]
                current_len = len(para)
            else:
                current.append(para)
                current_len += len(para)
        if current:
            chunks.append("\n\n".join(current))
        return chunks


async def index_topic_content(content_id: uuid.UUID) -> bool:
    """
    Index a TopicContent: chunk extracted_text, embed, add to ChromaDB.
    Returns True if successful.
    """
    async with async_session() as session:
        q = (
            select(TopicContent, Topic, Syllabus, Subject, Course)
            .join(Topic, TopicContent.topic_id == Topic.topic_id)
            .join(Syllabus, Topic.syllabus_id == Syllabus.syllabus_id)
            .join(Subject, Syllabus.subject_id == Subject.subject_id)
            .join(Course, Subject.course_id == Course.course_id)
            .where(TopicContent.content_id == content_id)
        )
        res = await session.execute(q)
        row = res.first()
        if not row:
            return False
        tc, topic, syllabus, subject, course = row
        if not tc.extracted_text or not tc.extracted_text.strip():
            return False

    # Remove old chunks for this content
    delete_by_content_id(str(content_id))

    chunks = _chunk_text(tc.extracted_text)
    if not chunks:
        return False

    embeddings = embed_texts(chunks)
    if not embeddings:
        return False

    metadata_base = {
        "content_id": str(content_id),
        "topic_id": str(tc.topic_id),
        "topic_name": topic.topic_name,
        "subject_id": str(subject.subject_id),
        "course_id": str(course.course_id),
    }
    if course.department_id:
        metadata_base["department_id"] = str(course.department_id)

    ids = [f"{content_id}_{i}" for i in range(len(chunks))]
    metadatas = [dict(metadata_base) for _ in chunks]
    add_documents(ids, chunks, metadatas)
    return True


async def reindex_all() -> int:
    """Reindex all TopicContent. Returns count of indexed items."""
    async with async_session() as session:
        q = select(TopicContent)
        res = await session.execute(q)
        items = res.scalars().all()
    count = 0
    for tc in items:
        if await index_topic_content(tc.content_id):
            count += 1
    return count
