from typing import Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Header
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from jose import jwt

from app.db import async_session
from app.config import settings
from app.models.institution import Institution
from app.models.role import Role, RoleAssignment
from app.models.user import User
from pydantic import BaseModel

router = APIRouter(tags=["admin"])


JWT_SECRET = settings.JWT_SECRET
JWT_ALGORITHM = settings.JWT_ALGORITHM


def _get_token_from_header(authorization: Optional[str]) -> str:
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid Authorization header")
    return parts[1]


async def get_current_user(authorization: Optional[str] = Header(None)) -> User:
    token = _get_token_from_header(authorization)
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        uid = int(payload.get("sub"))
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")
    async with async_session() as session:
        q = select(User).where(User.id == uid)
        res = await session.execute(q)
        user = res.scalars().first()
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user


async def user_has_role(session: AsyncSession, user_id: int, role_name: str, institution_id: Optional[int] = None) -> bool:
    q = select(RoleAssignment, Role).join(Role, RoleAssignment.role_id == Role.id).where(
        Role.name == role_name, RoleAssignment.user_id == user_id
    )
    res = await session.execute(q)
    rows = res.all()
    if not rows:
        return False
    # If institution_id provided, require a matching scoped assignment or global (institution_id is NULL)
    for ra, role in rows:
        if institution_id is None:
            # any matching assignment works
            return True
        if ra.institution_id is None or ra.institution_id == institution_id:
            return True
    return False


class InstitutionCreate(BaseModel):
    name: str
    slug: Optional[str] = None
    type: Optional[str] = "college"


@router.post("/institutions", response_model=Institution)
async def create_institution(payload: InstitutionCreate, authorization: Optional[str] = Header(None)):
    current = await get_current_user(authorization)
    # only SuperAdmin can create institutions
    async with async_session() as session:
        allowed = await user_has_role(session, current.id, "SuperAdmin")
        if not allowed:
            raise HTTPException(status_code=403, detail="Requires SuperAdmin")
        inst = Institution(name=payload.name, slug=payload.slug or payload.name.lower().replace(" ", "-"), type=payload.type)
        session.add(inst)
        await session.commit()
        await session.refresh(inst)
        return inst


@router.get("/institutions", response_model=list[Institution])
async def list_institutions():
    async with async_session() as session:
        q = select(Institution)
        res = await session.execute(q)
        return res.scalars().all()


class RoleCreate(BaseModel):
    name: str
    description: Optional[str] = None
    is_system: Optional[bool] = False


@router.post("/roles", response_model=Role)
async def create_role(payload: RoleCreate, authorization: Optional[str] = Header(None)):
    current = await get_current_user(authorization)
    async with async_session() as session:
        allowed = await user_has_role(session, current.id, "SuperAdmin")
        if not allowed:
            raise HTTPException(status_code=403, detail="Requires SuperAdmin")
        role = Role(name=payload.name, description=payload.description, is_system=payload.is_system)
        session.add(role)
        await session.commit()
        await session.refresh(role)
        return role


@router.get("/roles", response_model=list[Role])
async def list_roles():
    async with async_session() as session:
        q = select(Role)
        res = await session.execute(q)
        return res.scalars().all()


class RoleAssignPayload(BaseModel):
    user_id: int
    role_id: int
    institution_id: Optional[int] = None


@router.post("/role-assignments")
async def assign_role(payload: RoleAssignPayload, authorization: Optional[str] = Header(None)):
    current = await get_current_user(authorization)
    async with async_session() as session:
        # If assigning global role (institution_id is None) require SuperAdmin
        if payload.institution_id is None:
            allowed = await user_has_role(session, current.id, "SuperAdmin")
            if not allowed:
                raise HTTPException(status_code=403, detail="Requires SuperAdmin to assign global roles")
        else:
            # allow if current is SuperAdmin or InstitutionAdmin for that institution
            allowed = await user_has_role(session, current.id, "SuperAdmin") or await user_has_role(session, current.id, "InstitutionAdmin", payload.institution_id)
            if not allowed:
                raise HTTPException(status_code=403, detail="Requires InstitutionAdmin or SuperAdmin")

        # create assignment
        ra = RoleAssignment(user_id=payload.user_id, role_id=payload.role_id, institution_id=payload.institution_id)
        session.add(ra)
        await session.commit()
        return {"assigned": True}


@router.get("/users/pending", response_model=list[User])
async def list_pending_users(institution_id: Optional[int] = None, authorization: Optional[str] = Header(None)):
    current = await get_current_user(authorization)
    async with async_session() as session:
        # Only allowed for SuperAdmin or InstitutionAdmin of the institution
        if institution_id is not None:
            allowed = await user_has_role(session, current.id, "SuperAdmin") or await user_has_role(session, current.id, "InstitutionAdmin", institution_id)
            if not allowed:
                raise HTTPException(status_code=403, detail="Requires InstitutionAdmin or SuperAdmin")
        q = select(User).where(User.status == "pending")
        if institution_id is not None:
            q = q.where(User.institution_id == institution_id)
        res = await session.execute(q)
        return res.scalars().all()


class ApprovePayload(BaseModel):
    assign_role_id: Optional[int] = None


@router.post("/users/{user_id}/approve")
async def approve_user(user_id: int, payload: ApprovePayload, authorization: Optional[str] = Header(None)):
    current = await get_current_user(authorization)
    async with async_session() as session:
        q = select(User).where(User.id == user_id)
        res = await session.execute(q)
        user = res.scalars().first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        # Only institution admin for the user's institution or superadmin can approve
        allowed = await user_has_role(session, current.id, "SuperAdmin") or (user.institution_id and await user_has_role(session, current.id, "InstitutionAdmin", user.institution_id))
        if not allowed:
            raise HTTPException(status_code=403, detail="Requires InstitutionAdmin or SuperAdmin")
        user.status = "approved"
        session.add(user)
        # optionally assign role (e.g., Student)
        if payload.assign_role_id:
            ra = RoleAssignment(user_id=user.id, role_id=payload.assign_role_id, institution_id=user.institution_id)
            session.add(ra)
        await session.commit()
        return {"approved": True}


@router.post("/users/{user_id}/deny")
async def deny_user(user_id: int, authorization: Optional[str] = Header(None)):
    current = await get_current_user(authorization)
    async with async_session() as session:
        q = select(User).where(User.id == user_id)
        res = await session.execute(q)
        user = res.scalars().first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        allowed = await user_has_role(session, current.id, "SuperAdmin") or (user.institution_id and await user_has_role(session, current.id, "InstitutionAdmin", user.institution_id))
        if not allowed:
            raise HTTPException(status_code=403, detail="Requires InstitutionAdmin or SuperAdmin")
        user.status = "denied"
        session.add(user)
        await session.commit()
        return {"denied": True}

