from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Header, HTTPException
from sqlmodel import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import async_session
from app.models.user import User
from app.models.content import UserContext, Subject, Syllabus, Topic
from app.models.visits import TopicVisit
from app.models.institution import Institution
from app.admin.routes import get_current_user
from app.models.role import RoleAssignment, Role
from datetime import datetime, timezone

router = APIRouter(tags=["dashboard"])


@router.get("/me")
async def my_dashboard(authorization: Optional[str] = Header(None)):
    """
    Aggregated dashboard for the current authenticated student.
    """
    current = await get_current_user(authorization)

    async with async_session() as session:
        # Account info
        account = {
            "id": current.id,
            "email": current.email,
            "full_name": current.full_name,
            "is_active": current.is_active,
            "status": current.status,
            "institution_id": current.institution_id,
            "created_at": current.created_at.isoformat() if getattr(current, "created_at", None) else None,
        }

        # KPIs / activity
        q_total_contexts = select(func.count()).select_from(UserContext).where(UserContext.user_id == current.id)
        res = await session.execute(q_total_contexts)
        total_contexts = res.scalar_one() or 0

        q_last_active = select(func.max(UserContext.updated_at)).where(UserContext.user_id == current.id)
        res = await session.execute(q_last_active)
        last_active = res.scalar_one()

        # current subject / last topic
        q_recent = select(UserContext).where(UserContext.user_id == current.id).order_by(UserContext.updated_at.desc()).limit(1)
        res = await session.execute(q_recent)
        recent_ctx = res.scalars().first()

        # resolve current subject name if available
        current_subject_name = None
        if recent_ctx and recent_ctx.subject_id:
            q_sub = select(Subject).where(Subject.subject_id == recent_ctx.subject_id)
            r = await session.execute(q_sub)
            sub_obj = r.scalars().first()
            if sub_obj:
                current_subject_name = sub_obj.subject_name

        activity = {
            "total_contexts": int(total_contexts),
            "last_active": (last_active.isoformat() if last_active else None),
            "current_subject_id": str(recent_ctx.subject_id) if recent_ctx and recent_ctx.subject_id else None,
            "current_subject_name": current_subject_name,
            "last_topic": recent_ctx.last_topic if recent_ctx else None,
            "last_intent": recent_ctx.last_intent if recent_ctx else None,
        }

        # Subject-wise summary
        q_subjects = select(Subject.subject_id, Subject.subject_name, Subject.semester, func.max(UserContext.updated_at).label("last_studied"), func.count(func.distinct(UserContext.last_topic)).label("topics_explored")).join(UserContext, Subject.subject_id == UserContext.subject_id).where(UserContext.user_id == current.id).group_by(Subject.subject_id)
        res = await session.execute(q_subjects)
        subjects = []
        for row in res.all():
            sid, name, semester, last_studied, topics_explored = row
            subjects.append({
                "id": str(sid),
                "name": name,
                "semester": semester,
                "last_studied": last_studied.isoformat() if last_studied else None,
                "topics_explored": int(topics_explored or 0),
            })

        # Syllabus progress per subject (topics touched vs total) using TopicVisit
        syllabus_progress: List[Dict[str, Any]] = []
        for s in subjects:
            subj_id = s["id"]
            # total topics in subject
            q_total_topics = select(func.count()).select_from(Topic).join(Syllabus, Topic.syllabus_id == Syllabus.syllabus_id).where(Syllabus.subject_id == subj_id)
            res_total = await session.execute(q_total_topics)
            total_topics = int(res_total.scalar_one() or 0)

            # topics touched by user via TopicVisit
            q_touched = select(func.count(func.distinct(TopicVisit.topic_id))).where(TopicVisit.user_id == current.id, TopicVisit.subject_id == subj_id)
            res_touched = await session.execute(q_touched)
            touched = int(res_touched.scalar_one() or 0)

            # units total / units covered (approx via syllabus count)
            q_units_total = select(func.count()).select_from(Syllabus).where(Syllabus.subject_id == subj_id)
            res_units = await session.execute(q_units_total)
            units_total = int(res_units.scalar_one() or 0)

            # units covered inferred from TopicVisit -> Topic -> Syllabus
            q_units_covered = select(func.count(func.distinct(Syllabus.syllabus_id))).select_from(TopicVisit).join(Topic, Topic.topic_id == TopicVisit.topic_id).join(Syllabus, Syllabus.syllabus_id == Topic.syllabus_id).where(TopicVisit.user_id == current.id, Syllabus.subject_id == subj_id)
            res_units_covered = await session.execute(q_units_covered)
            units_covered = int(res_units_covered.scalar_one() or 0)

            syllabus_progress.append({
                "subject_id": subj_id,
                "subject_name": s["name"],
                "units_covered": units_covered,
                "units_total": units_total,
                "topics_touched": touched,
                "topics_total": total_topics,
            })

        # Intent analytics (counts by last_intent)
        q_intents = select(UserContext.last_intent, func.count()).where(UserContext.user_id == current.id).group_by(UserContext.last_intent)
        res = await session.execute(q_intents)
        intents = {row[0] or "unknown": int(row[1]) for row in res.all()}

        # Roles and expiry
        q_roles = select(Role.name, RoleAssignment.expires_at).join(Role, Role.id == RoleAssignment.role_id).where(RoleAssignment.user_id == current.id)
        res = await session.execute(q_roles)
        roles = []
        soon_expiring = []
        now = datetime.now(timezone.utc)
        for name, expires_at in res.all():
            expires_iso = expires_at.isoformat() if expires_at else None
            roles.append({"name": name, "expires_at": expires_iso})
            if expires_at:
                # warn if expires within 7 days
                delta = expires_at - now
                if delta.total_seconds() > 0 and delta.total_seconds() < 7 * 24 * 3600:
                    soon_expiring.append({"name": name, "expires_at": expires_iso, "days_left": int(delta.total_seconds() // 86400)})


        # institution name
        institution_name = None
        if current.institution_id:
            q_inst = select(Institution).where(Institution.id == current.institution_id)
            r = await session.execute(q_inst)
            inst = r.scalars().first()
            if inst:
                institution_name = inst.name

        # recent activity list (last 5)
        q_recent_list = select(UserContext, Subject.subject_name).join(Subject, UserContext.subject_id == Subject.subject_id, isouter=True).where(UserContext.user_id == current.id).order_by(UserContext.updated_at.desc()).limit(5)
        res = await session.execute(q_recent_list)
        recent_activity = []
        for row in res.all():
            uc, subj_name = row
            recent_activity.append({
                "last_topic": uc.last_topic,
                "last_intent": uc.last_intent,
                "subject_name": subj_name,
                "updated_at": uc.updated_at.isoformat() if uc.updated_at else None,
            })

        return {
            "account": account,
            "kpis": {
                "subjects_studied": len(subjects),
                "topics_explored": sum([s["topics_explored"] for s in subjects]),
                "last_active": (last_active.isoformat() if last_active else None),
            },
            "activity": activity,
            "subjects": subjects,
            "syllabus_progress": syllabus_progress,
            "intent_analytics": intents,
            "roles": roles,
            "soon_expiring_roles": soon_expiring,
            "institution_name": institution_name,
            "recent_activity": recent_activity,
        }

