# Main Service

## 📌 Overview
The Main Service manages the core business logic of ThinkAloud AI. It handles DSA question management, tracking user progress, saving code editor states, and managing interview metadata.

## ⚙️ How It Works (Excalidraw Diagram Guide)

**Draw these boxes on your whiteboard:**
1. **Frontend / Client**: The user's browser.
2. **Main Service (FastAPI)**: The central API gateway.
3. **PostgreSQL (Main DB)**: Persistent storage for questions, user code, and transcripts.
4. **Redis Cache**: In-memory storage for high-speed reads.
5. **RabbitMQ (Message Queue)**: Handles asynchronous background tasks.

**Draw the flow (arrows):**
1. **Frontend -> Main Service**: Fetch a DSA question or save code.
2. **Main Service <-> Redis**: Check cache first. If the data is actively being used (like a live session), fetch it instantly from Redis.
3. **Main Service <-> PostgreSQL**: If not in cache (or if saving permanently), query the persistent DB.
4. **Main Service -> RabbitMQ**: When a complex action happens (like an interview finishes), push an event message to RabbitMQ to generate a summary asynchronously without making the user wait.

## 🛠️ Key Details
- **Connection Pooling**: Uses `asyncpg` to maintain a pool of reusable database connections. This prevents the database from crashing if hundreds of users submit code at the exact same time.
- **Event-Driven Architecture**: Uses RabbitMQ to offload heavy post-processing tasks so API responses remain lightning fast.
