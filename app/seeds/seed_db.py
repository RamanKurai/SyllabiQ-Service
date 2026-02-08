"""
Run this script to create tables and optionally seed default data for the app.

Usage:
    python -m app.seeds.seed_db
"""
import asyncio
from app.db import init_db, async_session
from app.models.user import User
from app.models.content import Course, Subject, Syllabus, Topic
from app.models.role import Role, RoleAssignment
from app.models.institution import Institution
from app.auth.routes import hash_password
from sqlmodel import select


async def seed(create_dummy_user: bool = True, seed_content: bool = True):
    """
    Initialize DB tables and optionally seed demo user and sample course/subject/syllabus/topic data.
    Safe to call on startup; checks for existing rows before inserting.
    """
    await init_db()

    async with async_session() as session:
        if create_dummy_user:
            q = select(User)
            res = await session.execute(q)
            existing_user = res.scalars().first()
            if not existing_user:
                # create demo institution
                demo_inst = Institution(name="Demo University", slug="demo-university")
                session.add(demo_inst)
                await session.flush()

                user = User(
                    email="demo@syllabiq.local",
                    hashed_password=hash_password("password"),
                    full_name="Demo User",
                    institution_id=demo_inst.id,
                    status="approved",
                )
                session.add(user)
                await session.flush()

                # Seed roles
                role_names = ["SuperAdmin", "InstitutionAdmin", "Principal", "Teacher", "Student"]
                roles = []
                for rn in role_names:
                    r = Role(name=rn, description=f"Default role: {rn}", is_system=(rn == "SuperAdmin"))
                    session.add(r)
                    roles.append(r)
                await session.flush()

                # Assign SuperAdmin to demo user (global)
                super_role = next((r for r in roles if r.name == "SuperAdmin"), None)
                if super_role:
                    ra = RoleAssignment(user_id=user.id, role_id=super_role.id, institution_id=None)
                    session.add(ra)

                await session.commit()
                print("Seeded demo user: demo@syllabiq.local / password and default roles/institution")
            else:
                print("Users already exist; skipping dummy user seed")

        if seed_content:
            # Check if any courses exist
            q = select(Course)
            res = await session.execute(q)
            existing_course = res.scalars().first()
            if existing_course:
                print("Course data already present; skipping content seed")
                return

            # Create a minimal sample course -> subject -> syllabus -> topic structure
            cs_course = Course(course_name="Computer Science", description="Computer Science undergraduate program")
            session.add(cs_course)
            await session.flush()  # populate course_id

            ds_subject = Subject(course_id=cs_course.course_id, subject_name="Data Structures", semester=2)
            session.add(ds_subject)
            await session.flush()

            unit1 = Syllabus(subject_id=ds_subject.subject_id, unit_name="Arrays and Strings", unit_order=1)
            unit2 = Syllabus(subject_id=ds_subject.subject_id, unit_name="Linked Lists", unit_order=2)
            session.add_all([unit1, unit2])
            await session.flush()

            t1 = Topic(syllabus_id=unit1.syllabus_id, topic_name="Dynamic Arrays", description="Resizable array implementations and amortized analysis.")
            t2 = Topic(syllabus_id=unit1.syllabus_id, topic_name="String Algorithms", description="Basic string matching and manipulation.")
            t3 = Topic(syllabus_id=unit2.syllabus_id, topic_name="Singly/ Doubly Linked Lists", description="Implementations and operations.")
            session.add_all([t1, t2, t3])

            await session.commit()
            print("Seeded sample course/subject/syllabus/topic data")


if __name__ == "__main__":
    asyncio.run(seed())

