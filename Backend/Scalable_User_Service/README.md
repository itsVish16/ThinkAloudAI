# Scalable User Service 🧠

A production-grade, highly-scalable user authentication and identity microservice built with **FastAPI**. It is the central nervous system for user identity within the **ThinkAloud.AI** ecosystem.

It features stateless JWT authentication, Redis-backed caching & rate limiting, PostgreSQL persistence, and asynchronous background email dispatching via AWS SQS & Lambda.

---

## 🏗️ Role in the ThinkAloudAI Architecture

In the ThinkAloudAI microservice ecosystem, the **Scalable User Service** holds three primary responsibilities:

### 1. Identity Provider & Authentication
It acts as the strict gatekeeper for the entire platform. 
- Handles user registration, email verification (via OTP), and password resets.
- Issues stateless JWT `access_tokens` and `refresh_tokens`. 
- Maintains a Redis-backed token blacklist to immediately revoke compromised sessions.
- Other microservices (like `Main_Service` and `AI_Interviewer`) do not store user passwords or handle logins. They simply verify the JWT signatures issued by this service.

### 2. Global Event Subscriber & Gamification Engine
To keep the microservices decoupled, the User Service acts as a central listener for user activity across the platform:
- It runs an asynchronous `event_consumer_loop` listening to event channels (e.g., `main_events`, `interview_events`).
- When a user solves a DSA problem in the `Main_Service`, or finishes a mock interview in the `AI_Interviewer`, an event is published.
- The User Service consumes these events, creates a permanent `LearningEvent` log, and automatically recalculates the user's **Current Streak**, **Longest Streak**, and **Domain Skills** (e.g., Python proficiency, System Design Elo).

### 3. Profile Data Aggregator
It provides the core `/api/v1/users/me/profile` endpoint which concurrently aggregates:
- Basic Profile Details (Bio, Github, LinkedIn)
- Domain Skill Scores
- Achievement Badges
- Learning Event Logs
*(Note: To render the full LeetCode-style profile, the frontend stitches this data together with the Submission Heatmap provided by the `Main_Service`).*

---

## 🚀 Architectural Components

1. **FastAPI Application Server**: High-performance ASGI web server utilizing `uvloop`. It handles routing, request validation, authentication checks, and rate limiting.
2. **PostgreSQL (Neon DB)**: Used as the primary persistent database for core user data (passwords, emails, streaks, skills) using SQLAlchemy (via `asyncpg` for non-blocking I/O).
3. **Redis Cache (Upstash)**:
   - **Caching**: Stores active user profiles (`user_id` -> JSON profile) to avoid hitting PostgreSQL on every authenticated request.
   - **Rate Limiting**: Uses a sliding window log/counter algorithm via `slowapi` to mitigate brute-force and DDoS attacks.
4. **AWS SQS & Lambda**: Background operations (like sending verification and password reset emails via Resend) are pushed to an SQS queue so the main request-response thread is completely unblocked. An AWS Lambda function consumes the queue and delivers the emails.
5. **Datadog**: Fully integrated telemetry, tracking request times, traces, and application health.

---

## 🛠️ Deployment (Docker Compose)

This service is fully dockerized and ready to deploy on any virtual machine (VM). It utilizes a multi-stage Dockerfile powered by `uv` for lightning-fast, reproducible builds.

### Prerequisites
Ensure the VM has **Docker** and **Docker Compose** installed.

### Step-by-Step Deployment

1. **Configure Environment Variables**:
   Copy the example environment file and fill in your production credentials:
   ```bash
   cp .env.example .env
   ```

2. **Spin up the stack**:
   ```bash
   docker compose up -d --build
   ```
   *This command will build the lightweight image, auto-apply database migrations (`alembic upgrade head`), start the Datadog agent, and boot the API server on port 8000.*

3. **Verify Deployment**:
   Verify that the API is responding to health checks:
   ```bash
   curl http://localhost:8000/health/live
   # Response: {"status":"alive"}
   ```
   Check system-wide health (database and redis connectivity):
   ```bash
   curl http://localhost:8000/health/ready
   ```

---

## 🛡️ Production & Performance Optimizations

- **Bcrypt Concurrency Control**: Computations for password hashing are capped inside a worker-level capacity limiter to prevent CPU starvation when many logins hit simultaneously.
- **Concurrent DB Queries**: Endpoints that aggregate data across multiple tables (like the Profile endpoint) use `asyncio.gather` to fire SQL queries concurrently, dropping latency to milliseconds.
- **Fast Database Release**: DB connections are returned to the pool *before* performing heavy CPU-bound tasks, protecting pool throughput under heavy traffic spikes.
- **Zero-Latency Email Dispatch**: Completely removed Celery. Email tasks are instantly pushed over HTTP to AWS SQS using a globally reused `aioboto3` session.

---

## 📚 API Documentation

A full, machine-generated API documentation file mapping all routes, input schemas, and output schemas is available in this repository at `API_DOCS.md`. 

A specialized documentation specifically for the frontend profile dashboard is available at `PROFILE_API_DOCS.md`.
