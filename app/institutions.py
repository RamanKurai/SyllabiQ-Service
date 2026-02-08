from fastapi import APIRouter
from sqlmodel import select
from app.db import async_session
from app.models.institution import Institution

router = APIRouter(tags=["institutions"])


@router.get("/", response_model=list[Institution])
async def list_institutions():
    """
    Public endpoint to list institutions for registration flows.
    """
    async with async_session() as session:
        q = select(Institution).where(Institution.is_active == True)
        res = await session.execute(q)
        return res.scalars().all()

