# ThinkAloud.AI Backend Deployment

This directory contains the single-VM backend deployment stack.

## Containers

`docker-compose.yml` starts:

- `caddy` - public HTTPS reverse proxy with automatic TLS
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

For production HTTPS, create a DNS `A` record such as
`api.thinkaloudai.tech -> <EC2_PUBLIC_IP>`, then set:

```env
API_DOMAIN=api.thinkaloudai.tech
ACME_EMAIL=admin@thinkaloudai.tech
CORS_ALLOWED_ORIGINS=https://thinkaloudai.tech,https://www.thinkaloudai.tech
FRONTEND_BASE_URL=https://thinkaloudai.tech
APP_BIND_ADDRESS=127.0.0.1
```

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

- `80` - Caddy HTTP challenge/redirect
- `443` - public HTTPS API
- `8000` - user service, bound to `127.0.0.1` by default
- `8001` - main service, bound to `127.0.0.1` by default
- `8002` - AI interviewer API, bound to `127.0.0.1` by default
- `5432` - Postgres, bound to `127.0.0.1` by default
- `6379` - Redis, bound to `127.0.0.1` by default

Open only `80` and `443` publicly for the API. Keep `APP_BIND_ADDRESS` and
`INFRA_BIND_ADDRESS` set to `127.0.0.1` unless those services are explicitly
secured another way.

## Frontend Environment

In Vercel, set the frontend environment variables to the HTTPS API domain and
redeploy the frontend:

```env
VITE_USER_SERVICE_URL=https://api.thinkaloudai.tech
VITE_MAIN_SERVICE_URL=https://api.thinkaloudai.tech
VITE_AI_SERVICE_URL=https://api.thinkaloudai.tech
```

Do not use `http://<EC2_PUBLIC_IP>:8000` from the HTTPS frontend. Browsers block
that as mixed content.

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
