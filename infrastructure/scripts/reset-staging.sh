#!/bin/bash

# ============================================================================
# DeepAgents Control Platform - Reset Staging Environment Script
# ============================================================================
# This script completely resets the staging environment:
# - Drops and recreates the database
# - Clears Redis cache
# - Runs migrations
# - Seeds test data
# WARNING: This will delete ALL staging data!

set -e  # Exit on error
set -u  # Exit on undefined variable

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INFRASTRUCTURE_DIR="$(dirname "$SCRIPT_DIR")"
PROJECT_ROOT="$(dirname "$INFRASTRUCTURE_DIR")"
COMPOSE_FILE="$INFRASTRUCTURE_DIR/docker-compose.staging.yml"
ENV_FILE="$INFRASTRUCTURE_DIR/.env.staging"

# ============================================================================
# Helper Functions
# ============================================================================

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# ============================================================================
# Confirmation Prompt
# ============================================================================

log_warning "============================================"
log_warning "WARNING: This will DELETE ALL staging data!"
log_warning "============================================"
read -p "Are you sure you want to reset staging? (yes/NO): " -r
echo

if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    log_info "Reset cancelled."
    exit 0
fi

log_warning "This is your last chance to back out!"
read -p "Type 'RESET' to confirm: " -r
echo

if [[ $REPLY != "RESET" ]]; then
    log_info "Reset cancelled."
    exit 0
fi

# ============================================================================
# Pre-flight Checks
# ============================================================================

log_info "Starting staging environment reset..."

# Check if .env.staging exists
if [ ! -f "$ENV_FILE" ]; then
    log_error ".env.staging file not found at $ENV_FILE"
    exit 1
fi

# Load environment variables
export $(grep -v '^#' "$ENV_FILE" | xargs)

# ============================================================================
# Stop All Services
# ============================================================================

log_info "Stopping all staging services..."
cd "$INFRASTRUCTURE_DIR"

docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" down || {
    log_warning "Failed to stop services, continuing..."
}

log_success "Services stopped"

# ============================================================================
# Remove Volumes (Database and Redis Data)
# ============================================================================

log_info "Removing data volumes..."

docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" down -v

log_success "Data volumes removed"

# ============================================================================
# Start Database and Redis
# ============================================================================

log_info "Starting database and Redis..."

docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d postgres redis

# Wait for services to be ready
log_info "Waiting for database to be ready..."
sleep 15

# Verify database is up
POSTGRES_READY=false
for i in {1..30}; do
    if docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" exec -T postgres pg_isready -U "$POSTGRES_USER" &> /dev/null; then
        POSTGRES_READY=true
        break
    fi
    log_info "Waiting for PostgreSQL... (attempt $i/30)"
    sleep 2
done

if [ "$POSTGRES_READY" = false ]; then
    log_error "PostgreSQL failed to start!"
    exit 1
fi

log_success "Database is ready"

# ============================================================================
# Run Database Migrations
# ============================================================================

log_info "Running database migrations..."

docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" run --rm backend alembic upgrade head || {
    log_error "Database migration failed!"
    exit 1
}

log_success "Database migrations completed"

# ============================================================================
# Seed Test Data (Optional)
# ============================================================================

if [ "${SEED_TEST_DATA:-true}" = "true" ]; then
    log_info "Seeding test data..."

    # Check if seed script exists
    if [ -f "$PROJECT_ROOT/backend/scripts/seed_test_data.py" ]; then
        docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" run --rm backend \
            python scripts/seed_test_data.py || {
            log_warning "Test data seeding failed, but continuing..."
        }
        log_success "Test data seeded"
    else
        log_warning "Test data seed script not found. Skipping."
    fi
fi

# ============================================================================
# Start All Services
# ============================================================================

log_info "Starting all services..."

docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d

# Wait for services to be healthy
log_info "Waiting for services to become healthy..."
sleep 20

# Check backend health
BACKEND_HEALTHY=false
for i in {1..30}; do
    if docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" exec -T backend curl -f http://localhost:8000/health &> /dev/null; then
        BACKEND_HEALTHY=true
        break
    fi
    log_info "Waiting for backend to be healthy... (attempt $i/30)"
    sleep 2
done

if [ "$BACKEND_HEALTHY" = false ]; then
    log_error "Backend health check failed!"
    log_error "Check logs with: docker-compose -f $COMPOSE_FILE logs backend"
    exit 1
fi

log_success "All services are running"

# ============================================================================
# Display Service Status
# ============================================================================

log_info "Service Status:"
docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" ps

# ============================================================================
# Display Access Information
# ============================================================================

NGINX_HTTP_PORT=$(grep NGINX_HTTP_PORT "$ENV_FILE" | cut -d '=' -f2 | tr -d ' ')
BACKEND_PORT=$(grep BACKEND_PORT "$ENV_FILE" | cut -d '=' -f2 | tr -d ' ')

log_success "============================================"
log_success "Staging Environment Reset Complete!"
log_success "============================================"
log_info "Access Points:"
log_info "  Frontend:     http://localhost:${NGINX_HTTP_PORT:-8081}"
log_info "  Backend API:  http://localhost:${BACKEND_PORT:-8080}"
log_info "  API Docs:     http://localhost:${BACKEND_PORT:-8080}/docs"
log_info "  Health Check: http://localhost:${BACKEND_PORT:-8080}/health"
log_success "============================================"

# ============================================================================
# Send Notification (Optional)
# ============================================================================

if [ -n "${SLACK_WEBHOOK_URL:-}" ]; then
    curl -X POST "$SLACK_WEBHOOK_URL" \
        -H 'Content-Type: application/json' \
        -d '{"text": "Staging environment has been reset and reinitialized."}' \
        &> /dev/null || true
fi

log_success "Reset script completed successfully"
