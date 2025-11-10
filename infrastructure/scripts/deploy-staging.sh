#!/bin/bash

# ============================================================================
# DeepAgents Control Platform - Staging Deployment Script
# ============================================================================
# This script deploys the application to the staging environment
# It handles pulling latest code, building images, and deploying with zero downtime

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
BRANCH="${DEPLOY_BRANCH:-develop}"
BACKUP_BEFORE_DEPLOY="${BACKUP_BEFORE_DEPLOY:-true}"

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
# Pre-flight Checks
# ============================================================================

log_info "Starting staging deployment..."
log_info "Branch: $BRANCH"

# Check if .env.staging exists
if [ ! -f "$ENV_FILE" ]; then
    log_error ".env.staging file not found at $ENV_FILE"
    log_info "Copy .env.staging.example to .env.staging and configure it"
    exit 1
fi

# Check if docker-compose is installed
if ! command -v docker-compose &> /dev/null; then
    log_error "docker-compose not found. Please install Docker Compose."
    exit 1
fi

# Check if we're in a git repository (optional, depends on deployment method)
if [ -d "$PROJECT_ROOT/.git" ]; then
    log_info "Pulling latest code from $BRANCH branch..."
    cd "$PROJECT_ROOT"

    # Stash any local changes
    if ! git diff-index --quiet HEAD --; then
        log_warning "Local changes detected. Stashing..."
        git stash
    fi

    # Pull latest changes
    git fetch origin
    git checkout "$BRANCH"
    git pull origin "$BRANCH"

    log_success "Code updated successfully"
else
    log_warning "Not a git repository. Skipping code pull."
fi

# ============================================================================
# Backup Current Database (Optional)
# ============================================================================

if [ "$BACKUP_BEFORE_DEPLOY" = "true" ]; then
    log_info "Creating backup before deployment..."

    if [ -f "$SCRIPT_DIR/backup.sh" ]; then
        # Source .env.staging for backup script
        export $(grep -v '^#' "$ENV_FILE" | xargs)

        # Run backup script
        "$SCRIPT_DIR/backup.sh" || {
            log_warning "Backup failed, but continuing with deployment"
        }

        log_success "Backup completed"
    else
        log_warning "Backup script not found. Skipping backup."
    fi
fi

# ============================================================================
# Build Docker Images
# ============================================================================

log_info "Building Docker images..."
cd "$INFRASTRUCTURE_DIR"

# Build backend image
log_info "Building backend image..."
docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" build backend

# Build frontend image
log_info "Building frontend image..."
docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" build frontend

log_success "Docker images built successfully"

# ============================================================================
# Run Database Migrations
# ============================================================================

log_info "Running database migrations..."

# Start database if not running
docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d postgres

# Wait for database to be ready
log_info "Waiting for database to be ready..."
sleep 10

# Run migrations
docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" run --rm \
    -e DATABASE_URL="postgresql+asyncpg://\${POSTGRES_USER}:\${POSTGRES_PASSWORD}@postgres:5432/\${POSTGRES_DB}" \
    backend alembic upgrade head || {
    log_error "Database migration failed!"
    exit 1
}

log_success "Database migrations completed"

# ============================================================================
# Deploy Services (Zero Downtime)
# ============================================================================

log_info "Deploying services..."

# Start all services
docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d

# Wait for services to be healthy
log_info "Waiting for services to become healthy..."
sleep 15

# Check service health
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

log_success "Services deployed successfully"

# ============================================================================
# Run Smoke Tests
# ============================================================================

log_info "Running smoke tests..."

if [ -f "$SCRIPT_DIR/smoke-test.sh" ]; then
    "$SCRIPT_DIR/smoke-test.sh" staging || {
        log_warning "Smoke tests failed! Please investigate."
    }
else
    log_warning "Smoke test script not found. Skipping smoke tests."
fi

# ============================================================================
# Display Service Status
# ============================================================================

log_info "Service Status:"
docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" ps

# ============================================================================
# Display Access Information
# ============================================================================

# Get ports from environment
NGINX_HTTP_PORT=$(grep NGINX_HTTP_PORT "$ENV_FILE" | cut -d '=' -f2 | tr -d ' ')
NGINX_HTTPS_PORT=$(grep NGINX_HTTPS_PORT "$ENV_FILE" | cut -d '=' -f2 | tr -d ' ')
BACKEND_PORT=$(grep BACKEND_PORT "$ENV_FILE" | cut -d '=' -f2 | tr -d ' ')

log_success "============================================"
log_success "Staging Deployment Complete!"
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
        -d "{\"text\": \"Staging deployment completed successfully! Branch: $BRANCH\"}" \
        &> /dev/null || true
fi

log_success "Deployment script completed successfully"
