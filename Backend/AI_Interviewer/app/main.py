from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.config import settings
from app.services.db import init_db
from app.services.http_client import http_client
from app.routers.admin import router as admin_router
from app.routers.interview_types import router as interview_types_router
from app.routers.interviews import router as interviews_router
from app.routers.analytics import router as analytics_router


class NormalizePathMiddleware(BaseHTTPMiddleware):
    """Middleware to normalize multiple consecutive slashes in request paths."""
    async def dispatch(self, request: Request, call_next):
        path = request.scope.get("path", "")
        while "//" in path:
            path = path.replace("//", "/")
        request.scope["path"] = path
        return await call_next(request)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield
    # Gracefully close shared HTTP client
    if not http_client.is_closed:
        await http_client.aclose()


app = FastAPI(
    title="AI Interviewer API",
    description="Real-time WebRTC AI Interviewer backend powered by LiveKit and LLM.",
    version="1.1.0",
    lifespan=lifespan,
)

# Middleware
app.add_middleware(NormalizePathMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Modular Routers
app.include_router(interview_types_router)
app.include_router(interviews_router)
app.include_router(analytics_router)
app.include_router(admin_router)


@app.get("/health", tags=["system"])
async def health_check():
    return {"status": "ok", "service": "ai-interviewer"}
