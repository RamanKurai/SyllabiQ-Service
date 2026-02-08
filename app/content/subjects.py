from fastapi import APIRouter, HTTPException
from typing import List, Optional
import uuid
from sqlmodel import select

from app.db import async_session
from app.models.content import Subject
from sqlmodel import SQLModel

router = APIRouter(tags=["content: subjects"])


class SubjectCreate(SQLModel):
    course_id: uuid.UUID
    subject_name: str
    semester: Optional[int] = 1


@router.post("/subjects", response_model=Subject)
async def create_subject(payload: SubjectCreate):
    async with async_session() as session:
        subject = Subject(course_id=payload.course_id, subject_name=payload.subject_name, semester=payload.semester)
        session.add(subject)
        await session.commit()
        await session.refresh(subject)
        return subject


@router.get("/subjects", response_model=List[Subject])
async def list_subjects(course_id: Optional[uuid.UUID] = None):
    async with async_session() as session:
        q = select(Subject)
        if course_id:
            q = q.where(Subject.course_id == course_id)
        res = await session.execute(q)
        return res.scalars().all()


@router.get("/subjects/{subject_id}", response_model=Subject)
async def get_subject(subject_id: uuid.UUID):
    async with async_session() as session:
        q = select(Subject).where(Subject.subject_id == subject_id)
        res = await session.execute(q)
        subject = res.scalars().first()
        if not subject:
            raise HTTPException(status_code=404, detail="Subject not found")
        return subject


@router.put("/subjects/{subject_id}", response_model=Subject)
async def update_subject(subject_id: uuid.UUID, payload: SubjectCreate):
    async with async_session() as session:
        q = select(Subject).where(Subject.subject_id == subject_id)
        res = await session.execute(q)
        subject = res.scalars().first()
        if not subject:
            raise HTTPException(status_code=404, detail="Subject not found")
        subject.subject_name = payload.subject_name
        subject.semester = payload.semester
        subject.course_id = payload.course_id
        session.add(subject)
        await session.commit()
        await session.refresh(subject)
        return subject


@router.delete("/subjects/{subject_id}")
async def delete_subject(subject_id: uuid.UUID):
    async with async_session() as session:
        q = select(Subject).where(Subject.subject_id == subject_id)
        res = await session.execute(q)
        subject = res.scalars().first()
        if not subject:
            raise HTTPException(status_code=404, detail="Subject not found")
        await session.delete(subject)
        await session.commit()
        return {"deleted": True}

