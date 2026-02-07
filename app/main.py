from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import router as api_router

app = FastAPI(
    title="SyllabiQ Backend",
    description="Syllabus-aware educational AI backend (skeleton).",
    version="0.1.0",
)

# Allow frontend to communicate (adjust origins in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")


@app.on_event("startup")
async def startup_event():
    # Placeholder: initialize vector stores, embeddings, and any other resources here.
    app.state.initialized = True


@app.get("/health", tags=["health"])
async def health_check():
    """
    Simple health check endpoint.
    """
    return {"status": "ok", "service": "syllabiq-backend"}

