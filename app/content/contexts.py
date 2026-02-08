from fastapi import APIRouter, HTTPException
from typing import List, Optional
import uuid
from sqlmodel import select

from app.db import async_session
from app.models.content import UserContext
from sqlmodel import SQLModel

router = APIRouter(tags=["content: contexts"])


class UserContextCreate(SQLModel):
    user_id: Optional[int] = None
    subject_id: Optional[uuid.UUID] = None
    last_topic: Optional[str] = None
    last_intent: Optional[str] = None


@router.post("/contexts", response_model=UserContext)
async def create_context(payload: UserContextCreate):
    async with async_session() as session:
        c = UserContext(
            user_id=payload.user_id,
            subject_id=payload.subject_id,
            last_topic=payload.last_topic,
            last_intent=payload.last_intent,
        )
        session.add(c)
        await session.commit()
        await session.refresh(c)
        return c


@router.get("/contexts", response_model=List[UserContext])
async def list_contexts(user_id: Optional[int] = None):
    async with async_session() as session:
        q = select(UserContext)
        if user_id is not None:
            q = q.where(UserContext.user_id == user_id)
        res = await session.execute(q)
        return res.scalars().all()


@router.get("/contexts/{context_id}", response_model=UserContext)
async def get_context(context_id: uuid.UUID):
    async with async_session() as session:
        q = select(UserContext).where(UserContext.context_id == context_id)
        res = await session.execute(q)
        c = res.scalars().first()
        if not c:
            raise HTTPException(status_code=404, detail="Context not found")
        return c


@router.put("/contexts/{context_id}", response_model=UserContext)
async def update_context(context_id: uuid.UUID, payload: UserContextCreate):
    async with async_session() as session:
        q = select(UserContext).where(UserContext.context_id == context_id)
        res = await session.execute(q)
        c = res.scalars().first()
        if not c:
            raise HTTPException(status_code=404, detail="Context not found")
        c.user_id = payload.user_id
        c.subject_id = payload.subject_id
        c.last_topic = payload.last_topic
        c.last_intent = payload.last_intent
        await session.commit()
        await session.refresh(c)
        return c


@router.delete("/contexts/{context_id}")
async def delete_context(context_id: uuid.UUID):
    async with async_session() as session:
        q = select(UserContext).where(UserContext.context_id == context_id)
        res = await session.execute(q)
        c = res.scalars().first()
        if not c:
            raise HTTPException(status_code=404, detail="Context not found")
        await session.delete(c)
        await session.commit()
        return {"deleted": True}

