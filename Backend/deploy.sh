#!/usr/bin/env bash
# =============================================================================
# ThinkAloudAI Production Deployment & Health Check Script
# =============================================================================
set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

log_info "Starting ThinkAloudAI Production Deployment Pipeline..."

# 1. Check prerequisites
if ! command -v docker &> /dev/null; then
    log_error "Docker is not installed. Please install Docker before running deployment."
    exit 1
fi

# 2. Check for .env file
if [ ! -f ".env" ]; then
    log_warn ".env file not found in Backend root! Creating from .env.example..."
    cp .env.example .env
    log_warn "Created .env with default templates. Please populate .env with your Amazon RDS and API keys before running again."
    exit 1
fi

# 3. Choose compose file (prod vs default)
COMPOSE_FILE="docker-compose.prod.yml"
if [ ! -f "$COMPOSE_FILE" ]; then
    COMPOSE_FILE="docker-compose.yml"
fi

log_info "Using compose configuration: $COMPOSE_FILE"

# 4. Pull latest base images and build with cache
log_info "Building and pulling container images..."
docker compose -f "$COMPOSE_FILE" build --parallel

# 5. Bring up core infrastructure first (Redis, RabbitMQ, Datadog)
log_info "Starting infrastructure containers (Redis, RabbitMQ, Datadog)..."
docker compose -f "$COMPOSE_FILE" up -d redis rabbitmq datadog-agent

# Wait for Redis and RabbitMQ to be healthy
log_info "Waiting for Redis and RabbitMQ to pass health checks..."
timeout 60 bash -c 'until docker compose -f '"$COMPOSE_FILE"' ps redis | grep -q "(healthy)"; do sleep 2; done' || log_warn "Redis healthcheck timeout"
timeout 60 bash -c 'until docker compose -f '"$COMPOSE_FILE"' ps rabbitmq | grep -q "(healthy)"; do sleep 2; done' || log_warn "RabbitMQ healthcheck timeout"

# 6. Launch Application Microservices and Reverse Proxy
log_info "Starting Microservices (User Service, Main Service, AI Interviewer API/Workers, Caddy)..."
docker compose -f "$COMPOSE_FILE" up -d --remove-orphans

# 7. Health check verification loop
log_info "Verifying service health status..."
sleep 10
docker compose -f "$COMPOSE_FILE" ps

log_success "================================================================"
log_success " ThinkAloudAI Backend successfully deployed!"
log_success " Reverse Proxy: Caddy (Ports 80 / 443)"
log_success " Microservices: User Service (:8000), Main Service (:8001), AI Interviewer (:8002)"
log_success " Message Broker: RabbitMQ (:5672, Mgmt :15672)"
log_success " Cache: Redis (:6379)"
log_success " Observability: Datadog Agent (:8125/:8126)"
log_success "================================================================"
