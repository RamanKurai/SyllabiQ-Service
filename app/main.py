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
from app.rag.seed_knowledge import seed_syllabiq_knowledge
from app.content.courses import router as courses_router
from app.content.subjects import router as subjects_router
from app.content.syllabi import router as syllabi_router
from app.content.topics import router as topics_router
from app.content.contexts import router as contexts_router
from app.content.departments import router as departments_router
from app.content.uploads import router as uploads_router
from app.content.v1_read import router as v1_content_router
from app.admin.routes import router as admin_router
from app.institutions import router as institutions_router
from app.dashboard.routes import router as dashboard_router
# Ensure new models are imported so SQLModel metadata is registered before init_db()
import app.models.role  # noqa: F401
import app.models.institution  # noqa: F401
import app.models.visits  # noqa: F401
import app.models.content  # noqa: F401
import app.models.query_log  # noqa: F401

# Paths that do NOT require Bearer token (so Swagger can call them without Authorize)
PUBLIC_PATH_PREFIXES = ("/api/auth/signup", "/api/auth/login")

app = FastAPI(
    title="SyllabiQ Backend",
    description="Syllabus-aware educational AI backend.",
    version="0.1.0",
    openapi_tags=[
        {"name": "admin", "description": "All admin APIs: institutions, roles, content CRUD (departments, courses, subjects, syllabi, topics), role assignments, user management (pending, approve/deny, CRUD, suspend, delete). Requires Bearer JWT."},
        {"name": "auth", "description": "Signup, login, and current user profile."},
        {"name": "query", "description": "RAG query endpoint."},
        {"name": "embeddings", "description": "Embedding endpoints."},
        {"name": "dashboard", "description": "User dashboard and KPIs."},
    ],
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
app.include_router(departments_router, prefix="/api/content")
app.include_router(uploads_router, prefix="/api/content")
app.include_router(v1_content_router, prefix="/api/v1")
app.include_router(admin_router, prefix="/api/admin")
app.include_router(institutions_router, prefix="/api/institutions")
app.include_router(dashboard_router, prefix="/api/dashboard")


def custom_openapi():
    """Add Bearer JWT security scheme to OpenAPI so Swagger UI shows Authorize and sends token."""
    if app.openapi_schema:
        return app.openapi_schema
    from fastapi.openapi.utils import get_openapi
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "JWT from POST /api/auth/login. Enter the token only (no 'Bearer ' prefix).",
        }
    }
    # Require Bearer for all paths except public auth (signup/login)
    http_methods = {"get", "put", "post", "delete", "patch", "head", "options"}
    for path, path_item in openapi_schema.get("paths", {}).items():
        if any(path.rstrip("/").startswith(p.rstrip("/")) for p in PUBLIC_PATH_PREFIXES):
            continue
        for method in path_item:
            if method.lower() in http_methods:
                path_item[method]["security"] = [{"BearerAuth": []}]
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


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
    # Seed SyllabiQ platform knowledge into ChromaDB (idempotent; skipped if embedding unavailable)
    try:
        import asyncio
        loop = asyncio.get_event_loop()
        count = await loop.run_in_executor(None, seed_syllabiq_knowledge)
        if count:
            print(f"[startup] SyllabiQ knowledge indexed: {count} chunks")
    except Exception as e:
        print(f"[startup] knowledge seeding skipped: {e}")
    app.state.initialized = True


@app.get("/health", tags=["health"])
async def health_check():
    """
    Simple health check endpoint.
    """
    return {"status": "ok", "service": "syllabiq-backend"}

