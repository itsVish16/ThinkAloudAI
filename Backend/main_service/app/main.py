from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes.chat import router as chat_router
from app.routes.dsa import router as dsa_router
from app.routes.users import router as users_router
from app.routes.system_design import router as sd_router
from app.routes.roadmap import router as roadmap_router
from app.routes.behavioral import router as behavioral_router
from app.routes.pm import router as pm_router
from app.routes.aiml import router as aiml_router
from app.routes.admin import router as admin_router
from app.routes.dashboard import router as dashboard_router
from app.database import Base, engine
from app.config import settings
# Import ALL models so SQLAlchemy registers them for create_all()
from app.models.chat import ChatSession, ChatMessageModel
from app.models.dsa import DSAQuestion, CodeSubmission, ProblemTag, Recommendation
from app.models.system_design import SystemDesignQuestion
from app.models.roadmap import Roadmap, RoadmapTopic, RoadmapItem
from app.models.behavioral import BehavioralQuestion
from app.models.product_management import PMQuestion
from app.models.aiml import AIMLQuestion
from app.models.analytics import UserStats, DailyActivity, UserSkillScore, LearningEvent

import asyncio
from app.services.chat_batcher import start_chat_batch_writer
from app.services.event_consumer import start_event_consumer
from app.services.code_worker import start_code_worker


from sqlalchemy import text

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Modern lifespan context manager (replaces deprecated on_event)."""
    # Startup: create tables and start event consumer
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    consumer_task = asyncio.create_task(start_event_consumer())
    code_worker_task = asyncio.create_task(start_code_worker())
    chat_batcher_task = asyncio.create_task(start_chat_batch_writer())
    yield
    # Shutdown: cancel background tasks
    consumer_task.cancel()
    code_worker_task.cancel()
    chat_batcher_task.cancel()
    try:
        await asyncio.gather(consumer_task, code_worker_task, chat_batcher_task, return_exceptions=True)
    except asyncio.CancelledError:
        pass


app = FastAPI(
    title="ThinkAloud.ai — Main Service",
    description="Handles DSA problems, code execution (E2B), AI chat (LangGraph), and event publishing to the User Service.",
    version="2.0.0",
    lifespan=lifespan,
)

# Configure CORS for the frontend (port 5173)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routers
app.include_router(chat_router)
app.include_router(dsa_router)
app.include_router(users_router)
app.include_router(sd_router)
app.include_router(roadmap_router)
app.include_router(behavioral_router)
app.include_router(pm_router)
app.include_router(aiml_router)
app.include_router(admin_router)
app.include_router(dashboard_router)

@app.get("/")
async def root():
    return {
        "status": "online",
        "service": "ThinkAloud.ai — Main Service",
        "endpoints": {
            "chat_stream": "POST /chat/stream",
            "dsa_questions": "GET /dsa/questions",
            "submit_code": "POST /dsa/questions/{id}/submit",
        }
    }
