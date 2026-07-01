# Main Service 🧩

The learning & practice hub of the **ThinkAloud.AI** platform. Built with **FastAPI**, it handles coding practice, AI-assisted chat, and personalized roadmaps, and publishes user-activity events to the central **Scalable_User_Service** via the Redis event bus.

> **Role in the ecosystem:** This service does **not** manage users or authentication. It verifies JWTs issued by the [`Scalable_User_Service`](../Scalable_User_Service/README.md) and relies on a local copy of `user_profile_replica` for foreign-key integrity.

---

## 🏗️ Responsibilities

| Area | Description |
|------|-------------|
| **DSA Practice** | LeetCode-enriched problem bank (see `scripts/enrich_leetcode.py`), per-user submissions, tags, and AI-generated recommendations. |
| **Code Execution** | Sandboxed code execution via **E2B** / a docker runner (`app/services/docker_runner.py`). |
| **AI Chat Agent** | A LangGraph-based conversational agent (`app/agent/chat_agent.py`) with a batched DB writer (`app/services/chat_batcher.py`) for high-throughput message persistence. |
| **Roadmaps** | Topic-structured learning paths with `Roadmap / RoadmapTopic / RoadmapItem` models. |
| **System Design** | System-design question bank with an Excalidraw-backed whiteboarding frontend. |
| **Event Publishing** | Publishes user-activity events (`app/services/event_bus.py`) to the `main_events` Redis channel whenever a problem is solved. |

---

## 📂 Directory Structure

```text
main_service/
├── alembic/                  # Database migrations
├── app/
│   ├── agent/                # LangGraph chat agent
│   ├── models/               # SQLAlchemy models (chat, dsa, roadmap, system_design, user_replica)
│   ├── routes/               # API routers (auth, chat, dsa, roadmap, system_design, users)
│   ├── schemas/              # Pydantic request/response schemas
│   ├── services/             # docker_runner, event_bus, chat_batcher
│   ├── auth.py               # JWT verification against Scalable_User_Service
│   ├── config.py             # Pydantic BaseSettings (.env)
│   ├── database.py           # Async SQLAlchemy engine/session
│   ├── main.py               # FastAPI app + lifespan (creates tables, starts consumer)
│   └── worker.py             # Redis event consumer (background task)
├── scripts/                  # LeetCode seeding & enrichment utilities
├── Dockerfile                # uv-based image, serves on port 8001
└── pyproject.toml
```

---

## 🔑 Key Configuration (`app/config.py`)

| Variable | Purpose |
|----------|---------|
| `DATABASE_URL` | PostgreSQL connection string. |
| `UPSTASH_REDIS_URL` | Redis URL (used both as event bus and, by extension, a shared bus with other services). Uses logical DB `1`. |
| `USER_SERVICE_URL` | Base URL of the Scalable_User_Service, used to validate JWTs. |
| `JWT_SECRET_KEY` | Shared JWT secret (must match the User Service). |
| `FEATHERLESS_*` | LLM credentials for the chat agent. |
| `E2B_API_KEY` | Sandboxed code-execution API key. |
| `TAVILY_API_KEY` / `OPIK_*` | Agent web-search & observability integrations. |

---

## 🚀 Deployment

This service is included in the orchestrating compose at [`../docker-compose.yml`](../docker-compose.yml).

```bash
# From the Backend/ directory:
cp .env.example .env        # per-service secrets (must match User Service JWT secret)
docker compose up -d --build main-service
```

In the unified stack:
- **Host port:** `8001`
- **Container port:** `8001`
- **Database:** `main_service` (created by `../init-databases.sql` in the shared postgres container)
- **Redis logical DB:** `1`
- **Depends on:** `postgres`, `redis`, and `user-service` (started).

> **Migrations:** Tables are created via `Base.metadata.create_all` in the FastAPI lifespan (`app/main.py`). When using Alembic-managed schemas instead, run `alembic upgrade head` before serving.

---

## 🔁 Event Flow

```text
User solves a DSA problem
   └─> Main_Service persists the submission
        └─> publishes "main_events" to Redis
              └─> Scalable_User_Service consumes it
                    └─> updates streaks, skill scores, daily activity
```
