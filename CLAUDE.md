# ThinkAloudAI

## Overview

ThinkAloudAI is an AI-powered coding interview and practice platform.

Core features include:

- AI voice interviewer
- DSA practice platform
- Monaco code editor
- Interview recording
- Transcript generation
- Interview analysis dashboard
- RAG-powered assistant
- Authentication & user management

The goal is to build a production-quality platform with clean architecture, excellent developer experience, and low-latency AI interactions.

---

# Tech Stack

## Backend

- FastAPI
- Python 3.12+
- SQLAlchemy 2.0
- PostgreSQL
- Redis
- Celery (for background jobs)
- Docker

## AI

- Fireworks AI
- LangGraph
- LangChain (only when necessary)
- Qdrant
- OpenAI-compatible APIs
- Whisper (speech-to-text)
- Kokoro / TTS providers

## Frontend

- React
- TypeScript
- Vite
- TailwindCSS
- shadcn/ui
- Monaco Editor

---

# Architecture

The backend is built as a **Microservices Architecture** comprising three core services:

1. **Scalable_User_Service**: Handles authentication, JWT token minting, user profiles, and achievements. Uses PostgreSQL and Redis (caching, pub/sub).
2. **main_service**: Manages core platform features including DSA execution (via E2B), System Design LLM evaluations, behavioral/PM questions, and study roadmaps.
3. **AI_Interviewer**: A real-time voice agent service powered by LiveKit, LangGraph, and RabbitMQ for asynchronous post-interview analysis.

## Layering

Always follow a layered architecture within each service:

```
API (Routes)
↓
Service (Business Logic)
↓
Repository (Database Queries)
↓
Database
```

**CRITICAL**: Never place business logic inside API routes. 
*(Note: We are actively refactoring legacy routes like `chat.py`, `dsa.py`, and `user.py` to adhere strictly to this pattern).*

Routes should only:
- Validate input
- Call services
- Return response

---

# Coding Principles

Always write code that is:

- Simple
- Readable
- Modular
- Production-ready

Prefer clarity over cleverness.

Avoid unnecessary abstractions.

If a solution can be implemented in 20 clean lines instead of 100 generic lines, choose the simpler solution.

---

# Python Guidelines

Always

- Use async whenever possible
- Add type hints
- Use Pydantic models
- Use SQLAlchemy ORM
- Handle exceptions explicitly
- Write descriptive variable names

Avoid

- Global state
- Raw SQL
- Blocking I/O
- Duplicate logic
- Large functions (>50 lines)

---

# FastAPI Guidelines

Follow this structure:

```
app/
    api/
    services/
    repositories/
    models/
    schemas/
    core/
```

Never access the database directly from API routes.

Authentication should use dependency injection.

---

# Database

Use

- Alembic migrations
- SQLAlchemy 2 ORM
- Repository pattern

Never

- concatenate SQL strings
- create N+1 queries
- commit inside repositories unless required

---

# Frontend

Prefer

- Functional components
- Hooks
- Composition
- Reusable UI

Avoid

- Large components
- Inline styles
- Business logic inside UI

---

# AI Components

Priorities:

1. Low latency
2. Reliability
3. Streaming responses
4. Cost efficiency

Always design AI systems so that models can be swapped without changing business logic.

Never hardcode provider-specific code inside business logic.

---

# Voice Interview

The interview should feel natural.

Prioritize:

- Low response latency
- Smooth interruption handling
- Streaming
- Natural conversation

Avoid unnecessary LLM calls.

---

# DSA Platform

Keep implementations similar to LeetCode.

Prioritize

- Fast execution
- Reliable judging
- Clean problem schema
- Scalable evaluation pipeline

---

# Error Handling

Return meaningful errors.

Never expose stack traces.

Log useful debugging information.

---

# Performance

Always consider:

- Database queries
- API latency
- Memory usage
- Token usage
- Streaming performance

Avoid premature optimization, but never ignore obvious bottlenecks.

---

# Dependencies

Before introducing a new library:

Explain

- Why it is needed
- Alternatives
- Tradeoffs

Do not add dependencies without approval.

---

# Code Reviews

When reviewing code, check for:

- Bugs
- Security issues
- Race conditions
- Async correctness
- Error handling
- Readability
- Performance
- Simplicity

Suggest improvements with explanations.

---

# Before Writing Code

Always:

1. Understand the task.
2. Identify affected files.
3. Explain the implementation plan.
4. Wait for approval if the change is large.

Never immediately generate hundreds of lines of code without a plan.

---

# Before Finishing

Ensure:

- Code builds successfully
- Formatting passes
- No obvious lint issues
- No dead code
- No duplicated logic
- Comments explain *why*, not *what*

---

# Communication Style

Act like a senior software engineer working on this project.

Be concise.

Challenge poor architectural decisions.

If a simpler design exists, recommend it.

When uncertain, explain the tradeoffs instead of guessing.

Optimize for long-term maintainability rather than short-term speed.