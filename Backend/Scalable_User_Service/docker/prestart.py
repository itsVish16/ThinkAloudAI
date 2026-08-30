import asyncio
import os
import sys
from urllib.parse import urlparse
import asyncpg


async def ensure_database():
    db_url = os.environ.get("DATABASE_URL", "postgresql+asyncpg://thinkaloud:thinkaloud_dev@localhost:5432/user_service")
    clean_url = db_url.replace("postgresql+asyncpg://", "postgresql://").replace("sqlite+aiosqlite://", "sqlite://")
    if clean_url.startswith("sqlite"):
        return

    parsed = urlparse(clean_url)
    db_name = parsed.path.lstrip("/")
    if "?" in db_name:
        db_name = db_name.split("?")[0]
    user = parsed.username or "thinkaloud"
    password = parsed.password or "thinkaloud_prod_secure"
    host = parsed.hostname or "localhost"
    port = parsed.port or 5432
    use_ssl = "ssl=" in db_url or "sslmode=" in db_url or "azure.com" in host

    print(f"Checking database '{db_name}' on {host}:{port} (SSL={use_ssl})...")

    for attempt in range(1, 10):
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
                if db_name.lower() == "postgres":
                    print(f"Database 'postgres' connected and verified ready.")
                    return
                exists = await conn.fetchval("SELECT 1 FROM pg_database WHERE datname = $1", db_name)
                if not exists:
                    print(f"Database '{db_name}' not found. Creating it now...")
                    await conn.execute(f'CREATE DATABASE "{db_name}"')
                    print(f"Database '{db_name}' created successfully.")
                else:
                    print(f"Database '{db_name}' already exists and is ready.")
            finally:
                await conn.close()
            return
        except Exception as e:
            print(f"Waiting for PostgreSQL on {host}:{port} (attempt {attempt}/10): {e}")
            await asyncio.sleep(1)

    print("PostgreSQL connection timeout reached. Proceeding with startup...", file=sys.stderr)


if __name__ == "__main__":
    asyncio.run(ensure_database())
