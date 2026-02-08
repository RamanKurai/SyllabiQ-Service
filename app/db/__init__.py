from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.config import settings

# Use configured DATABASE_URL (reads from environment or .env). Defaults to SQLite for dev.
DATABASE_URL = settings.DATABASE_URL

engine = create_async_engine(DATABASE_URL, echo=False, future=True)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def init_db():
    """
    Create database tables (based on SQLModel metadata).
    Call this on startup or from a seed script.
    """
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

