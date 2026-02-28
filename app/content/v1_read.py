"""Lightweight read-only endpoints consumed by the frontend.

Mounted at /api/v1 so the FE can call GET /api/v1/subjects and
GET /api/v1/subjects/{subject_id}/topics without path translation.
"""

from fastapi import APIRouter, HTTPException
from typing import List
import uuid
from sqlmodel import select

from app.db import async_session
from app.models.content import Subject, Syllabus, Topic
from app.schemas import SubjectListItem, TopicListItem

router = APIRouter(tags=["v1: content"])


@router.get("/subjects", response_model=List[SubjectListItem])
async def v1_list_subjects():
    async with async_session() as session:
        res = await session.execute(select(Subject))
        subjects = res.scalars().all()
        return [SubjectListItem(id=str(s.subject_id), name=s.subject_name) for s in subjects]


@router.get("/subjects/{subject_id}/topics", response_model=List[TopicListItem])
async def v1_list_topics_for_subject(subject_id: uuid.UUID):
    """Return all topics across every syllabus unit belonging to this subject."""
    async with async_session() as session:
        subj = await session.execute(select(Subject).where(Subject.subject_id == subject_id))
        if not subj.scalars().first():
            raise HTTPException(status_code=404, detail="Subject not found")

        q = (
            select(Topic)
            .join(Syllabus, Topic.syllabus_id == Syllabus.syllabus_id)
            .where(Syllabus.subject_id == subject_id)
        )
        res = await session.execute(q)
        topics = res.scalars().all()
        return [TopicListItem(id=str(t.topic_id), name=t.topic_name) for t in topics]
