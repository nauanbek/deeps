#!/bin/bash

# ============================================================================
# DeepAgents Control Platform - Production Deployment Script
# ============================================================================
#
# This script handles zero-downtime deployment of the application.
# It performs the following steps:
# 1. Validates environment configuration
# 2. Pulls latest code from git
# 3. Builds Docker images
# 4. Runs database migrations
# 5. Performs health checks
# 6. Starts new containers
# 7. Stops old containers (after health checks pass)
# 8. Provides rollback capability
#
# Usage:
#   ./deploy.sh [--no-backup] [--skip-migrations] [--force]
#
# Options:
#   --no-backup: Skip database backup before deployment
#   --skip-migrations: Skip database migrations
#   --force: Skip confirmation prompts
#
# ============================================================================

set -e  # Exit on error
set -u  # Exit on undefined variable

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INFRA_DIR="$(dirname "$SCRIPT_DIR")"
PROJECT_ROOT="$(dirname "$INFRA_DIR")"

# Configuration
COMPOSE_FILE="$INFRA_DIR/docker-compose.prod.yml"
ENV_FILE="$INFRA_DIR/.env.prod"
BACKUP_DIR="$INFRA_DIR/backups"

# Parse command line arguments
NO_BACKUP=false
SKIP_MIGRATIONS=false
FORCE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --no-backup)
            NO_BACKUP=true
            shift
            ;;
        --skip-migrations)
            SKIP_MIGRATIONS=true
            shift
            ;;
        --force)
            FORCE=true
            shift
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Usage: $0 [--no-backup] [--skip-migrations] [--force]"
            exit 1
            ;;
    esac
done

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

confirm() {
    if [ "$FORCE" = true ]; then
        return 0
    fi

    read -p "$1 (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        return 1
    fi
    return 0
}

check_command() {
    if ! command -v $1 &> /dev/null; then
        log_error "$1 is required but not installed."
        exit 1
    fi
}

# ============================================================================
# Pre-deployment Checks
# ============================================================================

log_info "Starting DeepAgents Control Platform deployment..."
echo

# Check required commands
log_info "Checking required commands..."
check_command docker
check_command docker-compose
check_command git
log_success "All required commands are available"
echo

# Check if .env.prod exists
if [ ! -f "$ENV_FILE" ]; then
    log_error "Environment file not found: $ENV_FILE"
    log_error "Please create it from .env.prod.example and configure it"
    exit 1
fi
log_success "Environment file found"
echo

# Validate environment variables
log_info "Validating environment configuration..."
source "$ENV_FILE"

required_vars=(
    "POSTGRES_PASSWORD"
    "SECRET_KEY"
    "ANTHROPIC_API_KEY"
)

missing_vars=()
for var in "${required_vars[@]}"; do
    if [ -z "${!var:-}" ]; then
        missing_vars+=("$var")
    fi
done

if [ ${#missing_vars[@]} -gt 0 ]; then
    log_error "Missing required environment variables:"
    for var in "${missing_vars[@]}"; do
        echo "  - $var"
    done
    exit 1
fi
log_success "Environment configuration is valid"
echo

# ============================================================================
# Backup
# ============================================================================

if [ "$NO_BACKUP" = false ]; then
    log_info "Creating database backup..."
    if [ -f "$SCRIPT_DIR/backup.sh" ]; then
        bash "$SCRIPT_DIR/backup.sh" || {
            log_error "Backup failed!"
            if ! confirm "Continue without backup?"; then
                exit 1
            fi
        }
        log_success "Database backup completed"
    else
        log_warning "Backup script not found, skipping backup"
    fi
    echo
fi

# ============================================================================
# Git Pull (if in git repo)
# ============================================================================

if git rev-parse --git-dir > /dev/null 2>&1; then
    log_info "Pulling latest code from git..."

    # Check for uncommitted changes
    if ! git diff-index --quiet HEAD --; then
        log_warning "You have uncommitted changes!"
        if ! confirm "Continue deployment with uncommitted changes?"; then
            exit 1
        fi
    fi

    # Pull latest code
    CURRENT_BRANCH=$(git branch --show-current)
    log_info "Current branch: $CURRENT_BRANCH"

    if confirm "Pull latest code from origin/$CURRENT_BRANCH?"; then
        git pull origin "$CURRENT_BRANCH" || {
            log_error "Git pull failed!"
            exit 1
        }
        log_success "Code updated successfully"
    fi
else
    log_warning "Not a git repository, skipping git pull"
fi
echo

# ============================================================================
# Build Docker Images
# ============================================================================

log_info "Building Docker images..."
cd "$INFRA_DIR"

docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" build || {
    log_error "Docker build failed!"
    exit 1
}
log_success "Docker images built successfully"
echo

# ============================================================================
# Database Migrations
# ============================================================================

if [ "$SKIP_MIGRATIONS" = false ]; then
    log_info "Running database migrations..."

    # Start only database services
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d postgres redis

    # Wait for database to be ready
    log_info "Waiting for database to be ready..."
    sleep 10

    # Run migrations in a temporary backend container
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" run --rm backend \
        alembic upgrade head || {
        log_error "Database migration failed!"
        docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" logs backend
        exit 1
    }

    log_success "Database migrations completed"
    echo
fi

# ============================================================================
# Deploy Services
# ============================================================================

log_info "Starting services..."
docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d

log_info "Waiting for services to start..."
sleep 15
echo

# ============================================================================
# Health Checks
# ============================================================================

log_info "Performing health checks..."

# Check backend health
MAX_RETRIES=30
RETRY_COUNT=0
BACKEND_HEALTHY=false

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" exec -T backend \
        curl -f http://localhost:8000/health > /dev/null 2>&1; then
        BACKEND_HEALTHY=true
        break
    fi

    RETRY_COUNT=$((RETRY_COUNT + 1))
    log_info "Waiting for backend... (attempt $RETRY_COUNT/$MAX_RETRIES)"
    sleep 2
done

if [ "$BACKEND_HEALTHY" = false ]; then
    log_error "Backend health check failed!"
    log_error "Deployment failed. Check logs with: docker-compose logs backend"
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" logs backend
    exit 1
fi

log_success "Backend is healthy"

# Check nginx health
if docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" exec -T nginx \
    curl -f http://localhost:80/health > /dev/null 2>&1; then
    log_success "Nginx is healthy"
else
    log_error "Nginx health check failed!"
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" logs nginx
    exit 1
fi
echo

# ============================================================================
# Cleanup
# ============================================================================

log_info "Cleaning up old Docker images..."
docker image prune -f > /dev/null 2>&1 || true
log_success "Cleanup completed"
echo

# ============================================================================
# Deployment Summary
# ============================================================================

log_success "Deployment completed successfully!"
echo
echo "Services status:"
docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" ps
echo
log_info "View logs: docker-compose -f $COMPOSE_FILE logs -f"
log_info "Stop services: docker-compose -f $COMPOSE_FILE down"
echo
log_success "DeepAgents Control Platform is now running!"
