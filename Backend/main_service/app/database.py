from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from typing import AsyncGenerator
from app.config import settings

import asyncio
import asyncpg
from urllib.parse import urlparse

DATABASE_URL = settings.DATABASE_URL
if DATABASE_URL and DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
elif DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)


async def ensure_db_exists(db_url: str):
    if not db_url or "sqlite" in db_url:
        return
    clean_url = db_url.replace("postgresql+asyncpg://", "postgresql://").replace("postgres://", "postgresql://")
    parsed = urlparse(clean_url)
    db_name = parsed.path.lstrip("/")
    user = parsed.username or "thinkaloud"
    password = parsed.password or "thinkaloud_prod_secure"
    host = parsed.hostname or "localhost"
    port = parsed.port or 5432

    for _ in range(15):
        try:
            conn = await asyncpg.connect(
                user=user,
                password=password,
                host=host,
                port=port,
                database="postgres",
                timeout=5
            )
            try:
                exists = await conn.fetchval("SELECT 1 FROM pg_database WHERE datname = $1", db_name)
                if not exists:
                    await conn.execute(f'CREATE DATABASE "{db_name}"')
            finally:
                await conn.close()
            return
        except Exception:
            await asyncio.sleep(1)


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

# Create a shared Redis client with a connection pool
redis_client = redis_async.from_url(settings.REDIS_URL, decode_responses=True)

async def get_redis():
    """
    FastAPI dependency that yields a shared Redis client.
    """
    yield redis_client
