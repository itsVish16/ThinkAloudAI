#!/bin/sh
set -e

echo "Running prestart checks..."
python docker/prestart.py || true

echo "Applying database migrations..."
alembic upgrade head || {
    echo "Alembic upgrade encountered an issue. Ensuring tables exist via SQLAlchemy metadata..."
    python -c "import asyncio; from app.db.database import engine, Base; import app.models; asyncio.run(engine.run_sync(Base.metadata.create_all))" || true
}

WORKERS=${UVICORN_WORKERS:-1}
LOOP=${UVICORN_LOOP:-auto}

echo "Starting Uvicorn server on port 8000..."
exec ddtrace-run uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers "$WORKERS" --loop "$LOOP" --proxy-headers --forwarded-allow-ips='*'
