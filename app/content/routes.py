from fastapi import APIRouter, HTTPException
from typing import List, Optional
import uuid
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import async_session
from app.models.content import Course, Subject, Syllabus, Topic, UserContext
from sqlmodel import SQLModel, Field


router = APIRouter(tags=["content"])


class CourseCreate(SQLModel):
    course_name: str
    description: Optional[str] = None


class SubjectCreate(SQLModel):
    course_id: uuid.UUID
    subject_name: str
    semester: Optional[int] = 1


class SyllabusCreate(SQLModel):
    subject_id: uuid.UUID
    unit_name: str
    unit_order: Optional[int] = 1


class TopicCreate(SQLModel):
    syllabus_id: uuid.UUID
    topic_name: str
    description: Optional[str] = None


class UserContextCreate(SQLModel):
    user_id: Optional[int] = None
    subject_id: Optional[uuid.UUID] = None
    last_topic: Optional[str] = None
    last_intent: Optional[str] = None


# Courses
@router.post("/courses", response_model=Course)
async def create_course(payload: CourseCreate):
    async with async_session() as session:
        course = Course(course_name=payload.course_name, description=payload.description)
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


# Subjects
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


# Syllabi
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


# Topics
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


# UserContext
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

