from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from typing import AsyncGenerator
from app.config import settings

DATABASE_URL = settings.DATABASE_URL
if DATABASE_URL and DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
elif DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)

engine = create_async_engine(
    DATABASE_URL, 
    pool_pre_ping=True,
    echo=False
)

SessionLocal = async_sessionmaker(
    bind=engine, 
    class_=AsyncSession,
    autocommit=False, 
    autoflush=False
)

Base = declarative_base()

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that yields a database session and ensures
    it is closed after the request is finished.
    """
    async with SessionLocal() as db:
        yield db

import redis.asyncio as redis_async

async def get_redis():
    """
    FastAPI dependency that yields a Redis client.
    """
    redis = redis_async.from_url(settings.UPSTASH_REDIS_URL, decode_responses=True)
    try:
        yield redis
    finally:
        await redis.aclose()
