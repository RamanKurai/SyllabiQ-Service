from fastapi import APIRouter, HTTPException
from typing import List, Optional
import uuid
from sqlmodel import select

from app.db import async_session
from app.models.content import Course
from sqlmodel import SQLModel

router = APIRouter(tags=["content: courses"])


class CourseCreate(SQLModel):
    department_id: Optional[uuid.UUID] = None
    course_name: str
    description: Optional[str] = None


@router.post("/courses", response_model=Course)
async def create_course(payload: CourseCreate):
    async with async_session() as session:
        course = Course(
            department_id=payload.department_id,
            course_name=payload.course_name,
            description=payload.description,
        )
        session.add(course)
        await session.commit()
        await session.refresh(course)
        return course


@router.get("/courses", response_model=List[Course])
async def list_courses():
    async with async_session() as session:
        q = select(Course)
        res = await session.execute(q)
        return res.scalars().all()


@router.get("/courses/{course_id}", response_model=Course)
async def get_course(course_id: uuid.UUID):
    async with async_session() as session:
        q = select(Course).where(Course.course_id == course_id)
        res = await session.execute(q)
        course = res.scalars().first()
        if not course:
            raise HTTPException(status_code=404, detail="Course not found")
        return course


@router.put("/courses/{course_id}", response_model=Course)
async def update_course(course_id: uuid.UUID, payload: CourseCreate):
    async with async_session() as session:
        q = select(Course).where(Course.course_id == course_id)
        res = await session.execute(q)
        course = res.scalars().first()
        if not course:
            raise HTTPException(status_code=404, detail="Course not found")
        course.department_id = payload.department_id
        course.course_name = payload.course_name
        course.description = payload.description
        session.add(course)
        await session.commit()
        await session.refresh(course)
        return course


@router.delete("/courses/{course_id}")
async def delete_course(course_id: uuid.UUID):
    async with async_session() as session:
        q = select(Course).where(Course.course_id == course_id)
        res = await session.execute(q)
        course = res.scalars().first()
        if not course:
            raise HTTPException(status_code=404, detail="Course not found")
        await session.delete(course)
        await session.commit()
        return {"deleted": True}

