from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes.chat import router as chat_router
from app.routes.dsa import router as dsa_router
from app.routes.users import router as users_router
from app.routes.auth import router as auth_router
from app.routes.system_design import router as sd_router
from app.routes.roadmap import router as roadmap_router
from app.database import Base, engine
from app.config import settings

# Import ALL models so SQLAlchemy registers them for create_all()
from app.models.chat import ChatSession, ChatMessageModel
from app.models.dsa import DSAQuestion, CodeSubmission, ProblemTag, Recommendation
from app.models.system_design import SystemDesignQuestion
from app.models.user_replica import UserProfileReplica
from app.models.roadmap import Roadmap, RoadmapTopic, RoadmapItem

import asyncio
from app.worker import start_event_consumer
from app.services.chat_batcher import start_chat_batch_writer


from sqlalchemy import text

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Modern lifespan context manager (replaces deprecated on_event)."""
    # Startup: create tables and start event consumer
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
        # Add domain and role columns if they don't exist (Postgres 9.6+)
        await conn.execute(text("ALTER TABLE system_design_questions ADD COLUMN IF NOT EXISTS domain VARCHAR;"))
        await conn.execute(text("ALTER TABLE system_design_questions ADD COLUMN IF NOT EXISTS role VARCHAR;"))
        
        # Seed initial system design questions
        res = await conn.execute(text("SELECT COUNT(*) FROM system_design_questions"))
        if res.scalar() == 0:
            await conn.execute(text("""
                INSERT INTO system_design_questions (title, description, domain, role, created_at) VALUES 
                ('Design a Distributed Message Queue', 'Design a distributed message queue system like Apache Kafka or RabbitMQ. Focus on partitioning, replication, message durability, and consumer groups.', 'Backend', 'Senior Software Engineer', NOW()),
                ('Design a URL Shortener', 'Design a scalable URL shortener like bit.ly. Focus on collision prevention, capacity estimation, caching strategies, and highly available reads.', 'Backend', 'Software Engineer', NOW()),
                ('Design a Recommendation System for Netflix', 'Design a video recommendation system. Focus on the ML pipeline, feature store, real-time vs batch inference, and model serving infrastructure.', 'AI/ML', 'Senior Software Engineer', NOW()),
                ('Design a RAG-based Customer Support Chatbot', 'Design a Retrieval-Augmented Generation (RAG) customer support agent. Discuss vector database scaling, embedding generation, context window management, and handling hallucinations.', 'AI/ML', 'Software Engineer', NOW());
            """))
    consumer_task = asyncio.create_task(start_event_consumer())
    chat_batcher_task = asyncio.create_task(start_chat_batch_writer())
    yield
    # Shutdown: cancel background tasks
    consumer_task.cancel()
    chat_batcher_task.cancel()
    try:
        await asyncio.gather(consumer_task, chat_batcher_task, return_exceptions=True)
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
app.include_router(auth_router)
app.include_router(sd_router)
app.include_router(roadmap_router)


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
