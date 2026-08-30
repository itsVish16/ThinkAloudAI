from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

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

    match = re.match(r"^(postgresql\+asyncpg://)(.*)@([^@/]+(?::\d+)?(?:/.*)?)$", url)
    if match:
        proto, creds, rest = match.groups()
        if ":" in creds:
            u, p = creds.split(":", 1)
            encoded_u = quote_plus(unquote_plus(u))
            encoded_p = quote_plus(unquote_plus(p))
            return f"{proto}{encoded_u}:{encoded_p}@{rest}"

    return url

db_url = get_normalized_db_url(settings.DATABASE_URL)

engine_kwargs = {}
if db_url.startswith("postgresql"):
    engine_kwargs.update(
        {
            "pool_pre_ping": True,
            "pool_size": settings.db_pool_size,
            "max_overflow": settings.db_max_overflow,
            "pool_timeout": settings.db_pool_timeout,
            "pool_recycle": 1800,
        }
    )

engine = create_async_engine(
    db_url,
    echo=settings.debug, **engine_kwargs)

SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    async with SessionLocal() as session:
        yield session
