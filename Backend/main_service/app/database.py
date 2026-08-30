from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from typing import AsyncGenerator
from app.config import settings

import asyncio
import asyncpg
from urllib.parse import urlparse

import re
from urllib.parse import quote_plus, unquote_plus

def get_normalized_db_url(raw_url: str) -> str:
    if not raw_url:
        return "postgresql+asyncpg://thinkaloud:thinkaloud_dev@localhost:5432/postgres"
    url = raw_url.strip()
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)

    if "sslmode=require" in url and "ssl=" not in url:
        url = url.replace("sslmode=require", "ssl=require")

    # Safely percent-encode credentials if they contain special characters like '@'
    match = re.match(r"^(postgresql\+asyncpg://)(.*)@([^@/]+(?::\d+)?(?:/.*)?)$", url)
    if match:
        proto, creds, rest = match.groups()
        if ":" in creds:
            u, p = creds.split(":", 1)
            encoded_u = quote_plus(unquote_plus(u))
            encoded_p = quote_plus(unquote_plus(p))
            return f"{proto}{encoded_u}:{encoded_p}@{rest}"

    return url

DATABASE_URL = get_normalized_db_url(settings.DATABASE_URL)


async def ensure_db_exists(db_url: str):
    if not db_url or "sqlite" in db_url:
        return
    clean_url = db_url.replace("postgresql+asyncpg://", "postgresql://").replace("postgres://", "postgresql://")
    parsed = urlparse(clean_url)
    db_name = parsed.path.lstrip("/")
    if "?" in db_name:
        db_name = db_name.split("?")[0]
    user = unquote_plus(parsed.username or "thinkaloud")
    password = unquote_plus(parsed.password or "thinkaloud_prod_secure")
    host = parsed.hostname or "localhost"
    port = parsed.port or 5432
    use_ssl = "ssl=" in db_url or "sslmode=" in db_url or "azure.com" in host

    if db_name.lower() == "postgres":
        return

    for attempt in range(1, 4):
        try:
            connect_kwargs = {
                "user": user,
                "password": password,
                "host": host,
                "port": port,
                "database": "postgres",
                "timeout": 5,
            }
            if use_ssl:
                connect_kwargs["ssl"] = "require"

            conn = await asyncpg.connect(**connect_kwargs)
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
    pool_recycle=1800,
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
