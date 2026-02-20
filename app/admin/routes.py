from typing import Optional, List
from datetime import datetime, timedelta, date
import uuid

from fastapi import APIRouter, HTTPException, Header
from sqlmodel import select
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from jose import jwt

from app.db import async_session
from app.config import settings
from app.models.institution import Institution
from app.models.role import Role, RoleAssignment
from app.models.user import User, UserStatus
from app.models.content import Department, Course, Subject, Syllabus, Topic
from app.models.audit import AuditLog
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


async def _log_audit(session: AsyncSession, user_id: Optional[int], action: str, entity: Optional[str] = None, entity_id: Optional[str] = None, details: Optional[dict] = None):
    try:
        al = AuditLog(user_id=user_id, action=action, entity=entity, entity_id=str(entity_id) if entity_id is not None else None, details=details)
        session.add(al)
        # don't commit here; caller will commit as part of their transaction
    except Exception:
        # best-effort: don't fail admin operation if logging fails
        pass


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
        await _log_audit(session, current.id, "create_institution", "Institution", None, {"name": payload.name})
        await session.commit()
        await session.refresh(inst)
        return inst


@router.get("/institutions", response_model=list[Institution])
async def list_institutions(limit: int = 50, offset: int = 0):
    async with async_session() as session:
        q = select(Institution).limit(limit).offset(offset)
        res = await session.execute(q)
        return res.scalars().all()


# Institutions update/delete (SuperAdmin)
class InstitutionUpdate(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None
    type: Optional[str] = None
    is_active: Optional[bool] = None


@router.put("/institutions/{institution_id}", response_model=Institution)
async def update_institution(institution_id: int, payload: InstitutionUpdate, authorization: Optional[str] = Header(None)):
    current = await get_current_user(authorization)
    async with async_session() as session:
        allowed = await user_has_role(session, current.id, "SuperAdmin")
        if not allowed:
            raise HTTPException(status_code=403, detail="Requires SuperAdmin")
        q = select(Institution).where(Institution.id == institution_id)
        res = await session.execute(q)
        inst = res.scalars().first()
        if not inst:
            raise HTTPException(status_code=404, detail="Institution not found")
        if payload.name is not None:
            inst.name = payload.name
        if payload.slug is not None:
            inst.slug = payload.slug
        if payload.type is not None:
            inst.type = payload.type
        if payload.is_active is not None:
            inst.is_active = payload.is_active
        session.add(inst)
        await _log_audit(session, current.id, "update_institution", "Institution", inst.id, {"name": inst.name})
        await session.commit()
        await session.refresh(inst)
        return inst


@router.delete("/institutions/{institution_id}")
async def delete_institution(institution_id: int, authorization: Optional[str] = Header(None)):
    current = await get_current_user(authorization)
    async with async_session() as session:
        allowed = await user_has_role(session, current.id, "SuperAdmin")
        if not allowed:
            raise HTTPException(status_code=403, detail="Requires SuperAdmin")
        q = select(Institution).where(Institution.id == institution_id)
        res = await session.execute(q)
        inst = res.scalars().first()
        if not inst:
            raise HTTPException(status_code=404, detail="Institution not found")
        await session.delete(inst)
        await _log_audit(session, current.id, "delete_institution", "Institution", inst.id)
        await session.commit()
        return {"deleted": True}


@router.get("/kpis")
async def get_kpis(days: int = 7, authorization: Optional[str] = Header(None)):
    """
    Return aggregated counts and a simple time-series of signups and approvals for the last `days`.
    """
    current = await get_current_user(authorization)
    async with async_session() as session:
        # require SuperAdmin
        allowed = await user_has_role(session, current.id, "SuperAdmin")
        if not allowed:
            raise HTTPException(status_code=403, detail="Requires SuperAdmin")

        # counts
        res = await session.execute(select(func.count(User.id)))
        total_users = int(res.scalar_one() or 0)
        res = await session.execute(select(func.count()).select_from(User).where(User.status == "pending"))
        pending_users = int(res.scalar_one() or 0)
        res = await session.execute(select(func.count()).select_from(User).where(User.is_active == True))
        active_users = int(res.scalar_one() or 0)

        res = await session.execute(select(func.count()).select_from(Institution))
        institutions_count = int(res.scalar_one() or 0)
        res = await session.execute(select(func.count()).select_from(Role))
        roles_count = int(res.scalar_one() or 0)
        res = await session.execute(select(func.count()).select_from(Course))
        courses_count = int(res.scalar_one() or 0)
        res = await session.execute(select(func.count()).select_from(Subject))
        subjects_count = int(res.scalar_one() or 0)
        res = await session.execute(select(func.count()).select_from(Topic))
        topics_count = int(res.scalar_one() or 0)
        res = await session.execute(select(func.count()).select_from(Syllabus))
        syllabi_count = int(res.scalar_one() or 0)

        counts = {
            "total_users": total_users,
            "pending_users": pending_users,
            "active_users": active_users,
            "institutions_count": institutions_count,
            "roles_count": roles_count,
            "courses_count": courses_count,
            "subjects_count": subjects_count,
            "topics_count": topics_count,
            "syllabi_count": syllabi_count,
        }

        # time-series (signups by created_at date, approvals from audit logs)
        cutoff = datetime.utcnow() - timedelta(days=days - 1)
        # initialize series with zero values for each day
        series_map: dict[str, dict] = {}
        for i in range(days):
            d = (date.today() - timedelta(days=(days - 1 - i))).isoformat()
            series_map[d] = {"date": d, "signups": 0, "approvals": 0}

        q = select(func.date(User.created_at), func.count()).where(User.created_at >= cutoff).group_by(func.date(User.created_at)).order_by(func.date(User.created_at))
        res = await session.execute(q)
        for row in res.all():
            day = (row[0] if isinstance(row[0], str) else row[0].isoformat())
            series_map.setdefault(day, {"date": day, "signups": 0, "approvals": 0})
            series_map[day]["signups"] = int(row[1] or 0)

        q2 = select(func.date(AuditLog.created_at), func.count()).where(AuditLog.action == "approve_user", AuditLog.created_at >= cutoff).group_by(func.date(AuditLog.created_at)).order_by(func.date(AuditLog.created_at))
        res2 = await session.execute(q2)
        for row in res2.all():
            day = (row[0] if isinstance(row[0], str) else row[0].isoformat())
            series_map.setdefault(day, {"date": day, "signups": 0, "approvals": 0})
            series_map[day]["approvals"] = int(row[1] or 0)

        # produce ordered list
        series = [series_map[d.isoformat()] if isinstance(d, date) else series_map[d] for d in [ (date.today() - timedelta(days=(days - 1 - i))).isoformat() for i in range(days) ]]

        return {"counts": counts, "series": series}

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
        await _log_audit(session, current.id, "create_role", "Role", None, {"name": payload.name})
        await session.commit()
        await session.refresh(role)
        return role


@router.get("/roles", response_model=list[Role])
async def list_roles(limit: int = 50, offset: int = 0):
    async with async_session() as session:
        q = select(Role).limit(limit).offset(offset)
        res = await session.execute(q)
        return res.scalars().all()


# Role update/delete (SuperAdmin)
class RoleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


@router.put("/roles/{role_id}", response_model=Role)
async def update_role(role_id: int, payload: RoleUpdate, authorization: Optional[str] = Header(None)):
    current = await get_current_user(authorization)
    async with async_session() as session:
        allowed = await user_has_role(session, current.id, "SuperAdmin")
        if not allowed:
            raise HTTPException(status_code=403, detail="Requires SuperAdmin")
        q = select(Role).where(Role.id == role_id)
        res = await session.execute(q)
        role = res.scalars().first()
        if not role:
            raise HTTPException(status_code=404, detail="Role not found")
        if payload.name is not None:
            role.name = payload.name
        if payload.description is not None:
            role.description = payload.description
        if payload.is_active is not None:
            role.is_active = payload.is_active
        session.add(role)
        await _log_audit(session, current.id, "update_role", "Role", role.id, {"name": role.name})
        await session.commit()
        await session.refresh(role)
        return role


@router.delete("/roles/{role_id}")
async def delete_role(role_id: int, authorization: Optional[str] = Header(None)):
    current = await get_current_user(authorization)
    async with async_session() as session:
        allowed = await user_has_role(session, current.id, "SuperAdmin")
        if not allowed:
            raise HTTPException(status_code=403, detail="Requires SuperAdmin")
        q = select(Role).where(Role.id == role_id)
        res = await session.execute(q)
        role = res.scalars().first()
        if not role:
            raise HTTPException(status_code=404, detail="Role not found")
        await session.delete(role)
        await _log_audit(session, current.id, "delete_role", "Role", role.id)
        await session.commit()
        return {"deleted": True}
# -----------------------
# Admin-protected content CRUD (require SuperAdmin)
# -----------------------

class DepartmentCreate(BaseModel):
    institution_id: Optional[int] = None
    name: str
    slug: Optional[str] = None


class DepartmentUpdate(BaseModel):
    institution_id: Optional[int] = None
    name: Optional[str] = None
    slug: Optional[str] = None


@router.post("/content/departments", response_model=Department)
async def admin_create_department(payload: DepartmentCreate, authorization: Optional[str] = Header(None)):
    current = await get_current_user(authorization)
    async with async_session() as session:
        allowed = await user_has_role(session, current.id, "SuperAdmin")
        if not allowed:
            raise HTTPException(status_code=403, detail="Requires SuperAdmin")
        dept = Department(institution_id=payload.institution_id, name=payload.name, slug=payload.slug)
        session.add(dept)
        await _log_audit(session, current.id, "create", "Department", None, {"name": payload.name})
        await session.commit()
        await session.refresh(dept)
        return dept


@router.put("/content/departments/{department_id}", response_model=Department)
async def admin_update_department(department_id: uuid.UUID, payload: DepartmentUpdate, authorization: Optional[str] = Header(None)):
    current = await get_current_user(authorization)
    async with async_session() as session:
        allowed = await user_has_role(session, current.id, "SuperAdmin")
        if not allowed:
            raise HTTPException(status_code=403, detail="Requires SuperAdmin")
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
        await _log_audit(session, current.id, "update", "Department", department_id, {"name": dept.name})
        await session.commit()
        await session.refresh(dept)
        return dept


@router.delete("/content/departments/{department_id}")
async def admin_delete_department(department_id: uuid.UUID, authorization: Optional[str] = Header(None)):
    current = await get_current_user(authorization)
    async with async_session() as session:
        allowed = await user_has_role(session, current.id, "SuperAdmin")
        if not allowed:
            raise HTTPException(status_code=403, detail="Requires SuperAdmin")
        q = select(Department).where(Department.department_id == department_id)
        res = await session.execute(q)
        dept = res.scalars().first()
        if not dept:
            raise HTTPException(status_code=404, detail="Department not found")
        await session.delete(dept)
        await _log_audit(session, current.id, "delete", "Department", department_id)
        await session.commit()
        return {"deleted": True}


class CourseCreate(BaseModel):
    department_id: Optional[uuid.UUID] = None
    course_name: str
    description: Optional[str] = None


@router.post("/content/courses", response_model=Course)
async def admin_create_course(payload: CourseCreate, authorization: Optional[str] = Header(None)):
    current = await get_current_user(authorization)
    async with async_session() as session:
        allowed = await user_has_role(session, current.id, "SuperAdmin")
        if not allowed:
            raise HTTPException(status_code=403, detail="Requires SuperAdmin")
        course = Course(department_id=payload.department_id, course_name=payload.course_name, description=payload.description)
        session.add(course)
        await _log_audit(session, current.id, "create", "Course", None, {"course_name": payload.course_name})
        await session.commit()
        await session.refresh(course)
        return course


@router.put("/content/courses/{course_id}", response_model=Course)
async def admin_update_course(course_id: uuid.UUID, payload: CourseCreate, authorization: Optional[str] = Header(None)):
    current = await get_current_user(authorization)
    async with async_session() as session:
        allowed = await user_has_role(session, current.id, "SuperAdmin")
        if not allowed:
            raise HTTPException(status_code=403, detail="Requires SuperAdmin")
        q = select(Course).where(Course.course_id == course_id)
        res = await session.execute(q)
        course = res.scalars().first()
        if not course:
            raise HTTPException(status_code=404, detail="Course not found")
        course.department_id = payload.department_id
        course.course_name = payload.course_name
        course.description = payload.description
        session.add(course)
        await _log_audit(session, current.id, "update", "Course", course.course_id, {"course_name": payload.course_name})
        await session.commit()
        await session.refresh(course)
        return course


@router.delete("/content/courses/{course_id}")
async def admin_delete_course(course_id: uuid.UUID, authorization: Optional[str] = Header(None)):
    current = await get_current_user(authorization)
    async with async_session() as session:
        allowed = await user_has_role(session, current.id, "SuperAdmin")
        if not allowed:
            raise HTTPException(status_code=403, detail="Requires SuperAdmin")
        q = select(Course).where(Course.course_id == course_id)
        res = await session.execute(q)
        course = res.scalars().first()
        if not course:
            raise HTTPException(status_code=404, detail="Course not found")
        await session.delete(course)
        await _log_audit(session, current.id, "delete", "Course", course.course_id)
        await session.commit()
        return {"deleted": True}


class SubjectCreate(BaseModel):
    course_id: uuid.UUID
    subject_name: str
    semester: Optional[int] = 1


@router.post("/content/subjects", response_model=Subject)
async def admin_create_subject(payload: SubjectCreate, authorization: Optional[str] = Header(None)):
    current = await get_current_user(authorization)
    async with async_session() as session:
        allowed = await user_has_role(session, current.id, "SuperAdmin")
        if not allowed:
            raise HTTPException(status_code=403, detail="Requires SuperAdmin")
        subject = Subject(course_id=payload.course_id, subject_name=payload.subject_name, semester=payload.semester)
        session.add(subject)
        await _log_audit(session, current.id, "create", "Subject", None, {"subject_name": payload.subject_name})
        await session.commit()
        await session.refresh(subject)
        return subject


@router.put("/content/subjects/{subject_id}", response_model=Subject)
async def admin_update_subject(subject_id: uuid.UUID, payload: SubjectCreate, authorization: Optional[str] = Header(None)):
    current = await get_current_user(authorization)
    async with async_session() as session:
        allowed = await user_has_role(session, current.id, "SuperAdmin")
        if not allowed:
            raise HTTPException(status_code=403, detail="Requires SuperAdmin")
        q = select(Subject).where(Subject.subject_id == subject_id)
        res = await session.execute(q)
        subject = res.scalars().first()
        if not subject:
            raise HTTPException(status_code=404, detail="Subject not found")
        subject.course_id = payload.course_id
        subject.subject_name = payload.subject_name
        subject.semester = payload.semester
        session.add(subject)
        await _log_audit(session, current.id, "update", "Subject", subject.subject_id, {"subject_name": payload.subject_name})
        await session.commit()
        await session.refresh(subject)
        return subject


@router.delete("/content/subjects/{subject_id}")
async def admin_delete_subject(subject_id: uuid.UUID, authorization: Optional[str] = Header(None)):
    current = await get_current_user(authorization)
    async with async_session() as session:
        allowed = await user_has_role(session, current.id, "SuperAdmin")
        if not allowed:
            raise HTTPException(status_code=403, detail="Requires SuperAdmin")
        q = select(Subject).where(Subject.subject_id == subject_id)
        res = await session.execute(q)
        subject = res.scalars().first()
        if not subject:
            raise HTTPException(status_code=404, detail="Subject not found")
        await session.delete(subject)
        await _log_audit(session, current.id, "delete", "Subject", subject.subject_id)
        await session.commit()
        return {"deleted": True}


class SyllabusCreate(BaseModel):
    subject_id: uuid.UUID
    unit_name: str
    unit_order: Optional[int] = 1


@router.post("/content/syllabi", response_model=Syllabus)
async def admin_create_syllabus(payload: SyllabusCreate, authorization: Optional[str] = Header(None)):
    current = await get_current_user(authorization)
    async with async_session() as session:
        allowed = await user_has_role(session, current.id, "SuperAdmin")
        if not allowed:
            raise HTTPException(status_code=403, detail="Requires SuperAdmin")
        syl = Syllabus(subject_id=payload.subject_id, unit_name=payload.unit_name, unit_order=payload.unit_order)
        session.add(syl)
        await _log_audit(session, current.id, "create", "Syllabus", None, {"unit_name": payload.unit_name})
        await session.commit()
        await session.refresh(syl)
        return syl


@router.put("/content/syllabi/{syllabus_id}", response_model=Syllabus)
async def admin_update_syllabus(syllabus_id: uuid.UUID, payload: SyllabusCreate, authorization: Optional[str] = Header(None)):
    current = await get_current_user(authorization)
    async with async_session() as session:
        allowed = await user_has_role(session, current.id, "SuperAdmin")
        if not allowed:
            raise HTTPException(status_code=403, detail="Requires SuperAdmin")
        q = select(Syllabus).where(Syllabus.syllabus_id == syllabus_id)
        res = await session.execute(q)
        syl = res.scalars().first()
        if not syl:
            raise HTTPException(status_code=404, detail="Syllabus not found")
        syl.subject_id = payload.subject_id
        syl.unit_name = payload.unit_name
        syl.unit_order = payload.unit_order
        session.add(syl)
        await _log_audit(session, current.id, "update", "Syllabus", syl.syllabus_id, {"unit_name": payload.unit_name})
        await session.commit()
        await session.refresh(syl)
        return syl


@router.delete("/content/syllabi/{syllabus_id}")
async def admin_delete_syllabus(syllabus_id: uuid.UUID, authorization: Optional[str] = Header(None)):
    current = await get_current_user(authorization)
    async with async_session() as session:
        allowed = await user_has_role(session, current.id, "SuperAdmin")
        if not allowed:
            raise HTTPException(status_code=403, detail="Requires SuperAdmin")
        q = select(Syllabus).where(Syllabus.syllabus_id == syllabus_id)
        res = await session.execute(q)
        syl = res.scalars().first()
        if not syl:
            raise HTTPException(status_code=404, detail="Syllabus not found")
        await session.delete(syl)
        await _log_audit(session, current.id, "delete", "Syllabus", syl.syllabus_id)
        await session.commit()
        return {"deleted": True}


class TopicCreate(BaseModel):
    syllabus_id: uuid.UUID
    topic_name: str
    description: Optional[str] = None


@router.post("/content/topics", response_model=Topic)
async def admin_create_topic(payload: TopicCreate, authorization: Optional[str] = Header(None)):
    current = await get_current_user(authorization)
    async with async_session() as session:
        allowed = await user_has_role(session, current.id, "SuperAdmin")
        if not allowed:
            raise HTTPException(status_code=403, detail="Requires SuperAdmin")
        t = Topic(syllabus_id=payload.syllabus_id, topic_name=payload.topic_name, description=payload.description)
        session.add(t)
        await _log_audit(session, current.id, "create", "Topic", None, {"topic_name": payload.topic_name})
        await session.commit()
        await session.refresh(t)
        return t


@router.put("/content/topics/{topic_id}", response_model=Topic)
async def admin_update_topic(topic_id: uuid.UUID, payload: TopicCreate, authorization: Optional[str] = Header(None)):
    current = await get_current_user(authorization)
    async with async_session() as session:
        allowed = await user_has_role(session, current.id, "SuperAdmin")
        if not allowed:
            raise HTTPException(status_code=403, detail="Requires SuperAdmin")
        q = select(Topic).where(Topic.topic_id == topic_id)
        res = await session.execute(q)
        t = res.scalars().first()
        if not t:
            raise HTTPException(status_code=404, detail="Topic not found")
        t.syllabus_id = payload.syllabus_id
        t.topic_name = payload.topic_name
        t.description = payload.description
        session.add(t)
        await _log_audit(session, current.id, "update", "Topic", t.topic_id, {"topic_name": payload.topic_name})
        await session.commit()
        await session.refresh(t)
        return t


@router.delete("/content/topics/{topic_id}")
async def admin_delete_topic(topic_id: uuid.UUID, authorization: Optional[str] = Header(None)):
    current = await get_current_user(authorization)
    async with async_session() as session:
        allowed = await user_has_role(session, current.id, "SuperAdmin")
        if not allowed:
            raise HTTPException(status_code=403, detail="Requires SuperAdmin")
        q = select(Topic).where(Topic.topic_id == topic_id)
        res = await session.execute(q)
        t = res.scalars().first()
        if not t:
            raise HTTPException(status_code=404, detail="Topic not found")
        await session.delete(t)
        await _log_audit(session, current.id, "delete", "Topic", t.topic_id)
        await session.commit()
        return {"deleted": True}


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
        await _log_audit(session, current.id, "assign_role", "RoleAssignment", None, {"user_id": payload.user_id, "role_id": payload.role_id, "institution_id": payload.institution_id})
        await session.commit()
        return {"assigned": True}


@router.get("/users/pending", response_model=list[User])
async def list_pending_users(institution_id: Optional[int] = None, limit: int = 50, offset: int = 0, authorization: Optional[str] = Header(None)):
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
        q = q.limit(limit).offset(offset)
        res = await session.execute(q)
        return res.scalars().all()


@router.get("/users", response_model=list[User])
async def list_users(status: Optional[str] = None, institution_id: Optional[int] = None, limit: int = 50, offset: int = 0, authorization: Optional[str] = Header(None)):
    """
    List users with optional status filter, pagination, and optional institution scoping.
    """
    current = await get_current_user(authorization)
    async with async_session() as session:
        # If institution_id provided, allow SuperAdmin or InstitutionAdmin for that institution
        if institution_id is not None:
            allowed = await user_has_role(session, current.id, "SuperAdmin") or await user_has_role(session, current.id, "InstitutionAdmin", institution_id)
            if not allowed:
                raise HTTPException(status_code=403, detail="Requires InstitutionAdmin or SuperAdmin")
        else:
            # When no institution_id is provided, require SuperAdmin to list across all institutions
            allowed = await user_has_role(session, current.id, "SuperAdmin")
            if not allowed:
                raise HTTPException(status_code=403, detail="Requires SuperAdmin")

        q = select(User)
        if status is not None and status != "":
            q = q.where(User.status == status)
        if institution_id is not None:
            q = q.where(User.institution_id == institution_id)
        q = q.limit(limit).offset(offset)
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
        await _log_audit(session, current.id, "approve_user", "User", user.id, {"assign_role_id": payload.assign_role_id})
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
        await _log_audit(session, current.id, "deny_user", "User", user.id)
        await session.commit()
        return {"denied": True}


# -------------
# User management (CRUD)
# -------------


class UserUpdatePayload(BaseModel):
    full_name: Optional[str] = None
    institution_id: Optional[int] = None
    is_active: Optional[bool] = None
    status: Optional[UserStatus] = None


@router.get("/users/{user_id}", response_model=User)
async def get_user(user_id: int, authorization: Optional[str] = Header(None)):
    current = await get_current_user(authorization)
    # allow admins or the user themself
    async with async_session() as session:
        q = select(User).where(User.id == user_id)
        res = await session.execute(q)
        user = res.scalars().first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        allowed = await user_has_role(session, current.id, "SuperAdmin") or current.id == user_id or (user.institution_id and await user_has_role(session, current.id, "InstitutionAdmin", user.institution_id))
        if not allowed:
            raise HTTPException(status_code=403, detail="Requires permission")
        return user


@router.put("/users/{user_id}", response_model=User)
async def update_user(user_id: int, payload: UserUpdatePayload, authorization: Optional[str] = Header(None)):
    current = await get_current_user(authorization)
    async with async_session() as session:
        q = select(User).where(User.id == user_id)
        res = await session.execute(q)
        user = res.scalars().first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        # allow SuperAdmin or InstitutionAdmin for the user's institution
        allowed = await user_has_role(session, current.id, "SuperAdmin") or (user.institution_id and await user_has_role(session, current.id, "InstitutionAdmin", user.institution_id))
        if not allowed:
            raise HTTPException(status_code=403, detail="Requires InstitutionAdmin or SuperAdmin")
        if payload.full_name is not None:
            user.full_name = payload.full_name
        if payload.institution_id is not None:
            user.institution_id = payload.institution_id
        if payload.is_active is not None:
            user.is_active = payload.is_active
        if payload.status is not None:
            user.status = payload.status
        session.add(user)
        await _log_audit(session, current.id, "update_user", "User", user.id, {"status": user.status})
        await session.commit()
        await session.refresh(user)
        return user


@router.post("/users/{user_id}/suspend")
async def suspend_user(user_id: int, authorization: Optional[str] = Header(None)):
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
        user.status = "suspended"
        user.is_active = False
        session.add(user)
        await _log_audit(session, current.id, "suspend_user", "User", user.id)
        await session.commit()
        return {"suspended": True}


@router.delete("/users/{user_id}")
async def delete_user(user_id: int, authorization: Optional[str] = Header(None)):
    current = await get_current_user(authorization)
    async with async_session() as session:
        # only SuperAdmin may delete users
        allowed = await user_has_role(session, current.id, "SuperAdmin")
        if not allowed:
            raise HTTPException(status_code=403, detail="Requires SuperAdmin")
        q = select(User).where(User.id == user_id)
        res = await session.execute(q)
        user = res.scalars().first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        await session.delete(user)
        await _log_audit(session, current.id, "delete_user", "User", user.id)
        await session.commit()
        return {"deleted": True}

