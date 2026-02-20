"""
Topic content upload: PDF, CSV, DOCX parsing and storage.
"""
import csv
import io
from typing import Optional

from fastapi import APIRouter, HTTPException, UploadFile, File, Header
from sqlmodel import select
from typing import Optional
import uuid

from app.db import async_session
from app.models.content import Topic, TopicContent
from app.config import settings
from app.admin.routes import get_current_user

router = APIRouter(tags=["content: uploads"])

ALLOWED_EXTENSIONS = {".pdf", ".csv", ".docx"}
ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "text/csv",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


def _parse_pdf(content: bytes) -> str:
    try:
        from PyPDF2 import PdfReader
    except ImportError:
        raise HTTPException(status_code=500, detail="PDF parsing not available (install pypdf2)")
    reader = PdfReader(io.BytesIO(content))
    parts = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            parts.append(text)
    return "\n\n".join(parts)


def _parse_csv(content: bytes) -> str:
    try:
        text = content.decode("utf-8", errors="replace")
    except Exception:
        text = content.decode("latin-1", errors="replace")
    reader = csv.reader(io.StringIO(text))
    rows = []
    for row in reader:
        rows.append(" | ".join(row))
    return "\n".join(rows)


def _parse_docx(content: bytes) -> str:
    try:
        from docx import Document
    except ImportError:
        raise HTTPException(status_code=500, detail="DOCX parsing not available (install python-docx)")
    doc = Document(io.BytesIO(content))
    return "\n\n".join(p.text for p in doc.paragraphs if p.text)


def extract_text(content: bytes, file_type: str) -> str:
    if file_type == "pdf":
        return _parse_pdf(content)
    if file_type == "csv":
        return _parse_csv(content)
    if file_type == "docx":
        return _parse_docx(content)
    raise HTTPException(status_code=400, detail=f"Unsupported file type: {file_type}")


def get_file_type(filename: str) -> Optional[str]:
    ext = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""
    if ext in ("pdf", "csv", "docx"):
        return ext
    return None


@router.post("/topics/{topic_id}/upload", response_model=TopicContent)
async def upload_topic_content(
    topic_id: uuid.UUID,
    file: UploadFile = File(...),
    authorization: Optional[str] = Header(None),
):
    """
    Upload PDF, CSV, or DOCX file for a topic. Extracts text and stores in DB.
    Requires authentication.
    """
    await get_current_user(authorization)
    max_bytes = (getattr(settings, "UPLOAD_MAX_SIZE_MB", 10) or 10) * 1024 * 1024
    content = await file.read()
    if len(content) > max_bytes:
        raise HTTPException(status_code=413, detail=f"File too large (max {max_bytes // (1024*1024)}MB)")

    file_type = get_file_type(file.filename or "")
    if not file_type:
        raise HTTPException(
            status_code=400,
            detail="Unsupported format. Use PDF, CSV, or DOCX.",
        )

    async with async_session() as session:
        q = select(Topic).where(Topic.topic_id == topic_id)
        res = await session.execute(q)
        topic = res.scalars().first()
        if not topic:
            raise HTTPException(status_code=404, detail="Topic not found")

        try:
            extracted_text = extract_text(content, file_type)
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to parse file: {e}")

        tc = TopicContent(
            topic_id=topic_id,
            file_name=file.filename or "unknown",
            file_type=file_type,
            extracted_text=extracted_text or "",
            file_size_bytes=len(content),
        )
        session.add(tc)
        await session.commit()
        await session.refresh(tc)

        # Trigger indexing (Phase 4) - will be implemented in indexer
        try:
            from app.rag.indexer import index_topic_content
            await index_topic_content(tc.content_id)
        except ImportError:
            pass
        except Exception:
            pass  # Indexing is best-effort; content is stored

        return tc


@router.get("/topics/{topic_id}/content", response_model=list)
async def list_topic_content(
    topic_id: uuid.UUID,
    authorization: Optional[str] = Header(None),
):
    """List all content items for a topic. Requires authentication."""
    await get_current_user(authorization)
    async with async_session() as session:
        q = select(TopicContent).where(TopicContent.topic_id == topic_id)
        res = await session.execute(q)
        items = res.scalars().all()
        return [
            {
                "content_id": str(c.content_id),
                "file_name": c.file_name,
                "file_type": c.file_type,
                "file_size_bytes": c.file_size_bytes,
                "created_at": c.created_at.isoformat() if c.created_at else None,
            }
            for c in items
        ]
