from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from app.db import async_session, init_db
from app.models.user import User
from app.schemas.auth import UserCreate, UserRead, Token, LoginPayload, UserProfile
from app.models.role import Role, RoleAssignment
from app.models.role import Role, RoleAssignment
from passlib.context import CryptContext
from jose import jwt
from typing import Optional
from app.config import settings
from typing import Optional
from app.schemas.auth import UserRead
from fastapi import Header
from app.admin.routes import get_current_user

router = APIRouter()

# Prefer sha256_crypt to avoid system bcrypt binary/version issues in some environments.
# If bcrypt is available and desired, it can remain in the list as a fallback.
pwd_context = CryptContext(schemes=["sha256_crypt", "bcrypt"], deprecated="auto")
JWT_SECRET = settings.JWT_SECRET
JWT_ALGORITHM = settings.JWT_ALGORITHM
ACCESS_TOKEN_EXPIRE_SECONDS = settings.ACCESS_TOKEN_EXPIRE_SECONDS


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    q = select(User).where(User.email == email)
    result = await db.execute(q)
    return result.scalars().first()


async def create_user(db: AsyncSession, user_in: UserCreate) -> User:
    user = User(
        email=user_in.email,
        hashed_password=hash_password(user_in.password),
        full_name=user_in.full_name,
        institution_id=user_in.institution_id,
        status="pending",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


def create_access_token(*, subject: str) -> str:
    payload = {"sub": subject}
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token


@router.post("/signup", response_model=UserRead, tags=["auth"])
async def signup(user_in: UserCreate):
    """
    Create a new user (dummy flow). In production, add email verification and stronger policies.
    """
    async with async_session() as session:
        existing = await get_user_by_email(session, user_in.email)
        if existing:
            raise HTTPException(status_code=400, detail="User already exists")
        # Enforce .edu email requirement for institution-associated signups (students)
        if user_in.institution_id is not None:
            email = (user_in.email or "").lower()
            if not email.endswith(".edu"):
                raise HTTPException(status_code=400, detail="Institution signups require a .edu email address")
        user = await create_user(session, user_in)
        return UserRead.from_orm(user)


@router.post("/login", response_model=Token, tags=["auth"])
async def login(form_data: LoginPayload):
    """
    Simple login that accepts email & password and returns a JWT access token.
    """
    async with async_session() as session:
        user = await get_user_by_email(session, form_data.email)
        if not user or not verify_password(form_data.password, user.hashed_password):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        token = create_access_token(subject=str(user.id))
        # fetch role names for immediate client consumption
        q = select(Role.name).join(RoleAssignment, RoleAssignment.role_id == Role.id).where(RoleAssignment.user_id == user.id)
        res = await session.execute(q)
        role_names = [r[0] for r in res.all()]
        return Token(access_token=token, roles=role_names)


@router.get("/me", response_model=UserProfile, tags=["auth"])
async def me(authorization: Optional[str] = Header(None)):
    """
    Return authenticated user's profile.
    """
    user = await get_current_user(authorization)
    # fetch role names for this user
    async with async_session() as session:
        q = select(Role.name).join(RoleAssignment, RoleAssignment.role_id == Role.id).where(RoleAssignment.user_id == user.id)
        res = await session.execute(q)
        role_names = [r[0] for r in res.all()]
    base = UserRead.from_orm(user).model_dump()
    base["roles"] = role_names
    return base


