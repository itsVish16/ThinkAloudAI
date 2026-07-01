# Use the official Python slim image for a small footprint
FROM python:3.12-slim

# Install system dependencies (e.g. for psycopg2)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast dependency resolution
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Set the working directory
WORKDIR /app

# Copy the pyproject.toml and uv.lock (if exists) into the container
COPY pyproject.toml uv.lock* ./

# Sync dependencies using uv. We use --no-dev to exclude dev dependencies if desired, 
# but for simplicity, we'll install all dependencies.
RUN uv sync --frozen || uv sync

# Copy the rest of the application code
COPY . .

# Expose the application port
EXPOSE 8001

# Run via ddtrace-run so every FastAPI endpoint / httpx / redis call is auto-traced
# by Datadog APM. DD_AGENT_HOST / DD_SERVICE / DD_ENV are set in docker-compose.yml.
CMD ["uv", "run", "ddtrace-run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
