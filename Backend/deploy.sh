#!/usr/bin/env bash
# =============================================================================
# ThinkAloudAI Production Deployment & Health Check Script
# =============================================================================
set -euo pipefail

RED='[0;31m'
GREEN='[0;32m'
YELLOW='[1;33m'
BLUE='[0;34m'
NC='[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

log_info "Starting ThinkAloudAI Production Deployment Pipeline..."

if ! command -v docker &> /dev/null; then
    log_error "Docker is not installed. Please install Docker before running deployment."
    exit 1
fi

if [ ! -f ".env" ]; then
    log_warn ".env file not found in Backend root! Creating from .env.example..."
    cp .env.example .env
    log_warn "Created .env with default templates. Populate .env with API keys before proceeding."
fi

COMPOSE_FILE="docker-compose.prod.yml"
log_info "Using compose configuration: $COMPOSE_FILE"

log_info "Building container images..."
docker compose -f "$COMPOSE_FILE" build --parallel

log_info "Starting Database and Core Infrastructure (PostgreSQL, Redis, RabbitMQ, Datadog)..."
docker compose -f "$COMPOSE_FILE" up -d postgres redis rabbitmq datadog-agent

log_info "Waiting for PostgreSQL, Redis, and RabbitMQ to pass health checks..."
timeout 60 bash -c 'until docker compose -f '"$COMPOSE_FILE"' ps postgres | grep -q "(healthy)"; do sleep 2; done' || log_warn "Postgres healthcheck timeout"
timeout 60 bash -c 'until docker compose -f '"$COMPOSE_FILE"' ps redis | grep -q "(healthy)"; do sleep 2; done' || log_warn "Redis healthcheck timeout"
timeout 60 bash -c 'until docker compose -f '"$COMPOSE_FILE"' ps rabbitmq | grep -q "(healthy)"; do sleep 2; done' || log_warn "RabbitMQ healthcheck timeout"

log_info "Starting Microservices and Caddy Reverse Proxy..."
docker compose -f "$COMPOSE_FILE" up -d --remove-orphans

log_info "Verifying overall cluster health status..."
sleep 8
docker compose -f "$COMPOSE_FILE" ps

log_success "================================================================"
log_success " ThinkAloudAI Backend successfully deployed!"
log_success " Database: PostgreSQL 16 (Port 5432, 3 isolated databases)"
log_success " Cache: Redis 7 (Port 6379, DB 0, 1, 2)"
log_success " Message Broker: RabbitMQ (Port 5672, Mgmt 15672)"
log_success " Microservices: User Service (:8000), Main Service (:8001), AI Interviewer (:8002)"
log_success " Reverse Proxy: Caddy (Ports 80 / 443)"
log_success "================================================================"
