#!/bin/bash

# ============================================================================
# DeepAgents Control Platform - Database Restore Script
# ============================================================================
#
# This script restores PostgreSQL and Redis data from backups.
#
# WARNING: This will overwrite existing data!
# Always create a backup before restoring.
#
# Usage:
#   ./restore.sh TIMESTAMP [--force] [--postgres-only] [--redis-only]
#
# Arguments:
#   TIMESTAMP: Backup timestamp to restore (format: YYYYMMDD_HHMMSS)
#
# Options:
#   --force: Skip confirmation prompts
#   --postgres-only: Only restore PostgreSQL
#   --redis-only: Only restore Redis
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
BACKUP_DIR="$INFRA_DIR/backups"

# Configuration
COMPOSE_FILE="$INFRA_DIR/docker-compose.prod.yml"
ENV_FILE="$INFRA_DIR/.env.prod"

# Parse command line arguments
if [ $# -lt 1 ]; then
    echo -e "${RED}Error: Missing backup timestamp${NC}"
    echo "Usage: $0 TIMESTAMP [--force] [--postgres-only] [--redis-only]"
    echo
    echo "Available backups:"
    ls -1 "$BACKUP_DIR"/*.manifest 2>/dev/null | sed 's/.*backup_/  /' | sed 's/.manifest//' || echo "  No backups found"
    exit 1
fi

TIMESTAMP="$1"
shift

FORCE=false
POSTGRES_ONLY=false
REDIS_ONLY=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --force)
            FORCE=true
            shift
            ;;
        --postgres-only)
            POSTGRES_ONLY=true
            shift
            ;;
        --redis-only)
            REDIS_ONLY=true
            shift
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
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
# Pre-restore Checks
# ============================================================================

log_info "Starting restore process..."
echo

# Check required commands
check_command docker
check_command docker-compose
check_command gunzip

# Load environment variables
if [ ! -f "$ENV_FILE" ]; then
    log_error "Environment file not found: $ENV_FILE"
    exit 1
fi
source "$ENV_FILE"

# Verify backup files exist
POSTGRES_BACKUP="$BACKUP_DIR/postgres_${TIMESTAMP}.sql.gz"
REDIS_BACKUP="$BACKUP_DIR/redis_${TIMESTAMP}.rdb.gz"
MANIFEST_FILE="$BACKUP_DIR/backup_${TIMESTAMP}.manifest"

if [ ! -f "$MANIFEST_FILE" ]; then
    log_error "Backup manifest not found: $MANIFEST_FILE"
    log_error "Available backups:"
    ls -1 "$BACKUP_DIR"/*.manifest 2>/dev/null | sed 's/.*backup_/  /' | sed 's/.manifest//' || echo "  No backups found"
    exit 1
fi

log_info "Found backup manifest: $MANIFEST_FILE"
cat "$MANIFEST_FILE"
echo

# Check PostgreSQL backup
if [ "$REDIS_ONLY" = false ]; then
    if [ ! -f "$POSTGRES_BACKUP" ]; then
        log_error "PostgreSQL backup not found: $POSTGRES_BACKUP"
        exit 1
    fi
    log_info "Found PostgreSQL backup: $POSTGRES_BACKUP"
fi

# Check Redis backup
if [ "$POSTGRES_ONLY" = false ]; then
    if [ ! -f "$REDIS_BACKUP" ]; then
        log_warning "Redis backup not found: $REDIS_BACKUP"
        if ! confirm "Continue without Redis restore?"; then
            exit 1
        fi
        REDIS_ONLY=false
        POSTGRES_ONLY=true
    else
        log_info "Found Redis backup: $REDIS_BACKUP"
    fi
fi
echo

# ============================================================================
# Warning and Confirmation
# ============================================================================

log_warning "WARNING: This will OVERWRITE existing data!"
log_warning "Current data will be LOST unless you have a backup."
echo

if ! confirm "Are you sure you want to restore from backup $TIMESTAMP?"; then
    log_info "Restore cancelled"
    exit 0
fi
echo

# Create a safety backup of current state
log_info "Creating safety backup of current state..."
SAFETY_BACKUP_TIMESTAMP=$(date +%Y%m%d_%H%M%S)
bash "$SCRIPT_DIR/backup.sh" --retention-days 1 > /dev/null 2>&1 || {
    log_warning "Failed to create safety backup"
    if ! confirm "Continue without safety backup?"; then
        exit 1
    fi
}
log_success "Safety backup created"
echo

# ============================================================================
# Restore PostgreSQL
# ============================================================================

if [ "$REDIS_ONLY" = false ]; then
    log_info "Restoring PostgreSQL database..."

    # Stop backend to prevent connections during restore
    log_info "Stopping backend service..."
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" stop backend

    # Decompress backup
    TEMP_SQL="$BACKUP_DIR/temp_restore_${TIMESTAMP}.sql"
    gunzip -c "$POSTGRES_BACKUP" > "$TEMP_SQL"

    # Drop existing connections
    log_info "Terminating existing database connections..."
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" exec -T postgres \
        psql -U "${POSTGRES_USER:-deepagents}" -d postgres -c \
        "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '${POSTGRES_DB:-deepagents_prod}' AND pid <> pg_backend_pid();" \
        > /dev/null 2>&1 || true

    # Drop and recreate database
    log_info "Recreating database..."
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" exec -T postgres \
        psql -U "${POSTGRES_USER:-deepagents}" -d postgres -c \
        "DROP DATABASE IF EXISTS ${POSTGRES_DB:-deepagents_prod};" || {
        log_error "Failed to drop database"
        rm -f "$TEMP_SQL"
        exit 1
    }

    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" exec -T postgres \
        psql -U "${POSTGRES_USER:-deepagents}" -d postgres -c \
        "CREATE DATABASE ${POSTGRES_DB:-deepagents_prod} OWNER ${POSTGRES_USER:-deepagents};" || {
        log_error "Failed to create database"
        rm -f "$TEMP_SQL"
        exit 1
    }

    # Restore backup
    log_info "Importing database backup..."
    cat "$TEMP_SQL" | docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" exec -T postgres \
        psql -U "${POSTGRES_USER:-deepagents}" -d "${POSTGRES_DB:-deepagents_prod}" > /dev/null || {
        log_error "Failed to restore PostgreSQL backup"
        rm -f "$TEMP_SQL"
        exit 1
    }

    # Cleanup temp file
    rm -f "$TEMP_SQL"

    log_success "PostgreSQL database restored successfully"
    echo
fi

# ============================================================================
# Restore Redis
# ============================================================================

if [ "$POSTGRES_ONLY" = false ] && [ -f "$REDIS_BACKUP" ]; then
    log_info "Restoring Redis data..."

    # Stop Redis
    log_info "Stopping Redis service..."
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" stop redis

    # Decompress backup
    TEMP_RDB="$BACKUP_DIR/temp_restore_${TIMESTAMP}.rdb"
    gunzip -c "$REDIS_BACKUP" > "$TEMP_RDB"

    # Copy to Redis container
    docker cp "$TEMP_RDB" deepagents-redis:/data/dump.rdb || {
        log_error "Failed to copy Redis backup to container"
        rm -f "$TEMP_RDB"
        exit 1
    }

    # Cleanup temp file
    rm -f "$TEMP_RDB"

    # Start Redis
    log_info "Starting Redis service..."
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" start redis

    # Wait for Redis to start
    sleep 5

    log_success "Redis data restored successfully"
    echo
fi

# ============================================================================
# Restart Services
# ============================================================================

log_info "Restarting all services..."
docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" restart

log_info "Waiting for services to start..."
sleep 10
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
    log_error "Backend health check failed after restore!"
    log_error "Check logs with: docker-compose logs backend"
    exit 1
fi

log_success "Backend is healthy"
echo

# ============================================================================
# Restore Summary
# ============================================================================

log_success "Restore completed successfully!"
echo
echo "Restored from backup: $TIMESTAMP"
if [ "$REDIS_ONLY" = false ]; then
    echo "  PostgreSQL: Restored"
fi
if [ "$POSTGRES_ONLY" = false ] && [ -f "$REDIS_BACKUP" ]; then
    echo "  Redis: Restored"
fi
echo
log_info "Services status:"
docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" ps
echo
log_warning "Safety backup (pre-restore state) timestamp: $SAFETY_BACKUP_TIMESTAMP"
log_info "If you need to revert, run: ./restore.sh $SAFETY_BACKUP_TIMESTAMP"
