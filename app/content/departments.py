from fastapi import APIRouter, HTTPException
from typing import List, Optional
import uuid
from sqlmodel import select

from app.db import async_session
from app.models.content import Department
from sqlmodel import SQLModel

router = APIRouter(tags=["content: departments"])


class DepartmentCreate(SQLModel):
    institution_id: Optional[int] = None
    name: str
    slug: Optional[str] = None


class DepartmentUpdate(SQLModel):
    institution_id: Optional[int] = None
    name: Optional[str] = None
    slug: Optional[str] = None


@router.post("/departments", response_model=Department)
async def create_department(payload: DepartmentCreate):
    async with async_session() as session:
        dept = Department(
            institution_id=payload.institution_id,
            name=payload.name,
            slug=payload.slug,
        )
        session.add(dept)
        await session.commit()
        await session.refresh(dept)
        return dept


@router.get("/departments", response_model=List[Department])
async def list_departments(institution_id: Optional[int] = None):
    async with async_session() as session:
        q = select(Department)
        if institution_id is not None:
            q = q.where(Department.institution_id == institution_id)
        res = await session.execute(q)
        return res.scalars().all()


@router.get("/departments/{department_id}", response_model=Department)
async def get_department(department_id: uuid.UUID):
    async with async_session() as session:
        q = select(Department).where(Department.department_id == department_id)
        res = await session.execute(q)
        dept = res.scalars().first()
        if not dept:
            raise HTTPException(status_code=404, detail="Department not found")
        return dept


@router.put("/departments/{department_id}", response_model=Department)
async def update_department(department_id: uuid.UUID, payload: DepartmentUpdate):
    async with async_session() as session:
        q = select(Department).where(Department.department_id == department_id)
        res = await session.execute(q)
        dept = res.scalars().first()
        if not dept:
            raise HTTPException(status_code=404, detail="Department not found")
        if payload.institution_id is not None:
            dept.institution_id = payload.institution_id
        if payload.name is not None:
            dept.name = payload.name
        if payload.slug is not None:
            dept.slug = payload.slug
        session.add(dept)
        await session.commit()
        await session.refresh(dept)
        return dept


@router.delete("/departments/{department_id}")
async def delete_department(department_id: uuid.UUID):
    async with async_session() as session:
        q = select(Department).where(Department.department_id == department_id)
        res = await session.execute(q)
        dept = res.scalars().first()
        if not dept:
            raise HTTPException(status_code=404, detail="Department not found")
        await session.delete(dept)
        await session.commit()
        return {"deleted": True}
