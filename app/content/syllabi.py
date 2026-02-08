from fastapi import APIRouter, HTTPException
from typing import List, Optional
import uuid
from sqlmodel import select

from app.db import async_session
from app.models.content import Syllabus
from sqlmodel import SQLModel

router = APIRouter(tags=["content: syllabi"])


class SyllabusCreate(SQLModel):
    subject_id: uuid.UUID
    unit_name: str
    unit_order: Optional[int] = 1


@router.post("/syllabi", response_model=Syllabus)
async def create_syllabus(payload: SyllabusCreate):
    async with async_session() as session:
        s = Syllabus(subject_id=payload.subject_id, unit_name=payload.unit_name, unit_order=payload.unit_order)
        session.add(s)
        await session.commit()
        await session.refresh(s)
        return s


@router.get("/syllabi", response_model=List[Syllabus])
async def list_syllabi(subject_id: Optional[uuid.UUID] = None):
    async with async_session() as session:
        q = select(Syllabus)
        if subject_id:
            q = q.where(Syllabus.subject_id == subject_id)
        res = await session.execute(q)
        return res.scalars().all()


@router.get("/syllabi/{syllabus_id}", response_model=Syllabus)
async def get_syllabus(syllabus_id: uuid.UUID):
    async with async_session() as session:
        q = select(Syllabus).where(Syllabus.syllabus_id == syllabus_id)
        res = await session.execute(q)
        s = res.scalars().first()
        if not s:
            raise HTTPException(status_code=404, detail="Syllabus not found")
        return s


@router.put("/syllabi/{syllabus_id}", response_model=Syllabus)
async def update_syllabus(syllabus_id: uuid.UUID, payload: SyllabusCreate):
    async with async_session() as session:
        q = select(Syllabus).where(Syllabus.syllabus_id == syllabus_id)
        res = await session.execute(q)
        s = res.scalars().first()
        if not s:
            raise HTTPException(status_code=404, detail="Syllabus not found")
        s.unit_name = payload.unit_name
        s.unit_order = payload.unit_order
        s.subject_id = payload.subject_id
        session.add(s)
        await session.commit()
        await session.refresh(s)
        return s


@router.delete("/syllabi/{syllabus_id}")
async def delete_syllabus(syllabus_id: uuid.UUID):
    async with async_session() as session:
        q = select(Syllabus).where(Syllabus.syllabus_id == syllabus_id)
        res = await session.execute(q)
        s = res.scalars().first()
        if not s:
            raise HTTPException(status_code=404, detail="Syllabus not found")
        await session.delete(s)
        await session.commit()
        return {"deleted": True}

