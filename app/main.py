from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import router as api_router
# Auth router (signup/login)
from app.auth.routes import router as auth_router
from app.db import init_db
from app.config import settings
from app.db.utils import ensure_postgres_db_exists
from app.db.middleware import DBSessionMiddleware
from app.seeds.seed_db import seed as seed_db
from app.content.courses import router as courses_router
from app.content.subjects import router as subjects_router
from app.content.syllabi import router as syllabi_router
from app.content.topics import router as topics_router
from app.content.contexts import router as contexts_router

app = FastAPI(
    title="SyllabiQ Backend",
    description="Syllabus-aware educational AI backend.",
    version="0.1.0",
)

# Allow frontend to communicate (adjust origins via env in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ALLOW_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")
app.include_router(auth_router, prefix="/api/auth")
# Attach DB session middleware so handlers can access `request.state.db` if desired
app.add_middleware(DBSessionMiddleware)
app.include_router(courses_router, prefix="/api/content")
app.include_router(subjects_router, prefix="/api/content")
app.include_router(syllabi_router, prefix="/api/content")
app.include_router(topics_router, prefix="/api/content")
app.include_router(contexts_router, prefix="/api/content")


@app.on_event("startup")
async def startup_event():
    # Initialize DB and any other resources (vector stores, embeddings) here.
    # If configured, ensure Postgres DB exists before initializing SQLModel metadata.
    await ensure_postgres_db_exists()
    await init_db()
    # Seed default/demo data if not already present
    try:
        await seed_db(create_dummy_user=True, seed_content=True)
    except Exception as e:
        print(f"[startup] seeding failed: {e}")
    app.state.initialized = True


@app.get("/health", tags=["health"])
async def health_check():
    """
    Simple health check endpoint.
    """
    return {"status": "ok", "service": "syllabiq-backend"}

