# ThinkAloud.AI Backend Deployment

This directory contains the single-VM backend deployment stack.

## Containers

`docker-compose.yml` starts:

- `postgres` - one shared PostgreSQL server
- `redis` - one shared Redis server
- `datadog-agent` - Datadog metrics/logs/APM agent
- `user-service` - auth, users, profile, events
- `main-service` - chat, DSA, roadmaps, code execution
- `ai-interviewer-api` - interview API and LiveKit token generation
- `ai-interviewer-worker` - LiveKit realtime interview worker

## Data Isolation

PostgreSQL uses one database per service:

- `user_service`
- `main_service`
- `interviewer_service`

Redis uses one logical DB per service:

- DB `0` - user service
- DB `1` - main service
- DB `2` - AI interviewer

## First Deploy

```bash
cd Backend
cp .env.example .env
```

Edit `.env` and set real production values for passwords, JWT secret, AI keys,
LiveKit keys, frontend URL, CORS origins, and Datadog.

Then start the stack:

```bash
docker compose up -d --build
```

Check status:

```bash
docker compose ps
docker compose logs -f user-service main-service ai-interviewer-api
```

## Ports

Default host ports:

- `8000` - user service
- `8001` - main service
- `8002` - AI interviewer API
- `5432` - Postgres, bound to `127.0.0.1` by default
- `6379` - Redis, bound to `127.0.0.1` by default

Keep `INFRA_BIND_ADDRESS=127.0.0.1` unless Postgres/Redis are explicitly
secured another way.

## Health Checks

Compose checks:

- user service: `GET /health/ready`
- main service: `GET /`
- AI interviewer API: `GET /api/interview-types`
- Postgres: `pg_isready`
- Redis: `redis-cli ping`

## Updating

```bash
git pull
docker compose up -d --build
docker compose ps
```

## Local Infrastructure Only

For local development infra without application containers:

```bash
docker compose -f docker-compose.infra.yml up -d
```

Production should use the root `docker-compose.yml`.
