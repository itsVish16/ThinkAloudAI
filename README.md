<div align="center">
  <img src="./logo.png" alt="ThinkAloud AI Logo" width="300" />
  <h1>ThinkAloud AI</h1>
  <p>An interactive, AI-powered system design and DSA interview platform.</p>
</div>

---

## 📌 Architecture Overview

ThinkAloud AI is composed of a microservices backend and a React/Vite frontend. It leverages **FastAPI** for robust, asynchronous backend services and **LiveKit** to handle real-time WebRTC audio for the AI interviewer.

### High-Level System Architecture

![System Architecture](./System_design.png)

## 🏗️ Backend Services Explained

We split the backend into three distinct microservices to ensure scalability, fault isolation, and independent deployments.

1. **User Service (`user-service`)**
   - **Role:** Manages user authentication, profile creation, and session JWT issuing.
   - **Why separate?** Keeping authentication decoupled ensures that if the main or interview services experience high load, users can still log in, sign up, and view their dashboards without latency.

2. **Main Service (`main-service`)**
   - **Role:** Handles the core business logic, including fetching DSA questions, storing interview transcripts, maintaining user progress, and saving live code-editor states.
   - **Data Flow:** Uses PostgreSQL for persistent storage and Redis for caching fast-access data like active sessions.

3. **AI Interviewer Worker (`ai-interviewer-worker` / `api`)**
   - **Role:** The "brain" of the platform. It maintains a persistent WebSocket connection with LiveKit to process live audio (STT), stream context to the LLM (Fireworks), and synthesize speech back to the user (TTS via Cartesia/OpenAI).
   - **Why LiveKit?** Traditional HTTP polling is too slow for voice AI. WebRTC guarantees ultra-low latency (<500ms) necessary for a natural, conversational interview flow.

---

## 🛠️ Design Decisions & Trade-offs

### 1. Why FastAPI?
- **Speed & Async Native:** FastAPI is built on Starlette and allows native `async`/`await`. Since our system heavily relies on I/O-bound tasks (database queries, external LLM API calls, LiveKit webhooks), asynchronous endpoints prevent thread blocking and allow massive concurrency.
- **Validation:** Pydantic ensures strict type validation for incoming JSON data, dramatically reducing runtime errors and manual validation code.

### 2. Why Async Endpoints?
Synchronous endpoints block the worker thread while waiting for a network request (e.g., waiting 2 seconds for an LLM to generate a response). By using asynchronous endpoints (`async def`), a single Uvicorn worker can handle thousands of concurrent API requests, releasing the thread while waiting for I/O operations to complete.

### 3. JWT in Background Tasks
- **Why JWT?** We use JSON Web Tokens (JWT) for stateless authentication. Instead of querying the database for every single request to verify a session, the microservices simply verify the cryptographic signature of the token.
- **Background Tasks:** When a background task (like generating an interview summary) needs to run asynchronously via RabbitMQ, we pass the JWT payload rather than maintaining a persistent DB connection. This keeps background workers decoupled from the HTTP request lifecycle and highly scalable.

### 4. Connection Pooling (Database)
- **What is it?** Instead of opening a new TCP connection to PostgreSQL for every user request (which is incredibly slow and resource-heavy), we use a Connection Pool (via `asyncpg` and SQLAlchemy). The pool maintains a set of ready-to-use connections.
- **Why?** It drastically reduces latency and prevents the database from crashing under high load (e.g., if 1,000 users submit their code at the exact same time).

### 5. Dependency Injection (`Depends`)
- FastAPI's Dependency Injection system is used extensively throughout the routes (e.g., `Depends(get_db)`, `Depends(get_current_user)`).
- **Benefit:** It makes the code modular, extremely easy to mock during unit testing, and ensures database connections are automatically opened and safely closed per request without boilerplate code.

---

## ⚠️ Known Limitations & Failure Points ("Where does it break?")

Every architecture has trade-offs. Here is where our current design might fail at scale:

- **WebRTC Network Restrictions:** Corporate firewalls or strict NATs can block UDP traffic, causing the LiveKit audio connection to fallback to slower TCP TURN servers, resulting in noticeable audio latency.
- **Database Bottleneck:** While connection pooling helps, the primary PostgreSQL database is currently a single point of failure. If the DB goes down, the Main and User services halt. A future improvement would be implementing read replicas.
- **External API Rate Limits:** The AI Interviewer heavily depends on third-party APIs (Fireworks for LLM, Speechmatics/Cartesia for Voice). If an external API goes down or we hit a rate limit, the AI worker will timeout. We mitigate this using fallbacks (e.g., failing over to OpenAI), but it remains a critical external dependency risk.
