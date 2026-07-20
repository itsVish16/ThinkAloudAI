FROM python:3.12-slim AS base

WORKDIR /workspace

# Install system dependencies, WebRTC/FFI runtime libs, and build libraries.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    pkg-config \
    libopus-dev \
    libvpx-dev \
    libssl-dev \
    libglib2.0-0 \
    libgl1 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

COPY pyproject.toml uv.lock* ./

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --no-dev --no-install-project

COPY app/ ./app/

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --no-dev
RUN uv run python -c "from livekit.plugins import silero; silero.VAD.load()"

# Target for FastAPI Server
# ddtrace-run enables Datadog APM auto-instrumentation of every endpoint.
FROM base AS api
EXPOSE 8000
CMD ["sh", "-c", "uv run ddtrace-run uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers ${UVICORN_WORKERS:-4} --proxy-headers --forwarded-allow-ips='*'"]

# Target for Voice Worker
# The LiveKit worker is also traced via ddtrace-run (background tasks + LLM calls).
FROM base AS worker
CMD ["uv", "run", "ddtrace-run", "python", "-m", "app.worker", "start"]

# Target for Background Analysis Worker
FROM base AS analysis_worker
CMD ["uv", "run", "ddtrace-run", "python", "-m", "app.analysis_worker"]
