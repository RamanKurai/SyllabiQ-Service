from fastapi import APIRouter, HTTPException
from typing import List, Optional
import uuid
from sqlmodel import select

from app.db import async_session
from app.models.content import Topic
from sqlmodel import SQLModel

router = APIRouter(tags=["content: topics"])


class TopicCreate(SQLModel):
    syllabus_id: uuid.UUID
    topic_name: str
    description: Optional[str] = None


@router.post("/topics", response_model=Topic)
async def create_topic(payload: TopicCreate):
    async with async_session() as session:
        t = Topic(syllabus_id=payload.syllabus_id, topic_name=payload.topic_name, description=payload.description)
        session.add(t)
        await session.commit()
        await session.refresh(t)
        return t


@router.get("/topics", response_model=List[Topic])
async def list_topics(syllabus_id: Optional[uuid.UUID] = None):
    async with async_session() as session:
        q = select(Topic)
        if syllabus_id:
            q = q.where(Topic.syllabus_id == syllabus_id)
        res = await session.execute(q)
        return res.scalars().all()


@router.get("/topics/{topic_id}", response_model=Topic)
async def get_topic(topic_id: uuid.UUID):
    async with async_session() as session:
        q = select(Topic).where(Topic.topic_id == topic_id)
        res = await session.execute(q)
        t = res.scalars().first()
        if not t:
            raise HTTPException(status_code=404, detail="Topic not found")
        return t


@router.put("/topics/{topic_id}", response_model=Topic)
async def update_topic(topic_id: uuid.UUID, payload: TopicCreate):
    async with async_session() as session:
        q = select(Topic).where(Topic.topic_id == topic_id)
        res = await session.execute(q)
        t = res.scalars().first()
        if not t:
            raise HTTPException(status_code=404, detail="Topic not found")
        t.topic_name = payload.topic_name
        t.description = payload.description
        t.syllabus_id = payload.syllabus_id
        session.add(t)
        await session.commit()
        await session.refresh(t)
        return t


@router.delete("/topics/{topic_id}")
async def delete_topic(topic_id: uuid.UUID):
    async with async_session() as session:
        q = select(Topic).where(Topic.topic_id == topic_id)
        res = await session.execute(q)
        t = res.scalars().first()
        if not t:
            raise HTTPException(status_code=404, detail="Topic not found")
        await session.delete(t)
        await session.commit()
        return {"deleted": True}

