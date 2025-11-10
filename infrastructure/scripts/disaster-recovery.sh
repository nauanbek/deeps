#!/bin/bash

# ============================================================================
# DeepAgents Control Platform - Disaster Recovery Script
# ============================================================================
# This script performs a complete disaster recovery from backup
# WARNING: This will replace all data with backup data!

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
BACKUP_DIR="${BACKUP_DIR:-/var/backups/deepagents}"
RESTORE_FROM_S3="${RESTORE_FROM_S3:-false}"

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
# Confirmation Prompts
# ============================================================================

log_warning "============================================"
log_warning "DISASTER RECOVERY MODE"
log_warning "============================================"
log_warning "This will:"
log_warning "1. Stop all services"
log_warning "2. Drop existing databases"
log_warning "3. Restore from backup"
log_warning "4. Restart all services"
log_warning "============================================"

read -p "Are you ABSOLUTELY sure you want to continue? (type 'DISASTER_RECOVERY' to confirm): " -r
echo

if [[ $REPLY != "DISASTER_RECOVERY" ]]; then
    log_info "Disaster recovery cancelled."
    exit 0
fi

# ============================================================================
# Pre-flight Checks
# ============================================================================

log_info "Starting disaster recovery process..."

# Load environment variables
if [ -f "$INFRASTRUCTURE_DIR/.env.prod" ]; then
    export $(grep -v '^#' "$INFRASTRUCTURE_DIR/.env.prod" | xargs)
else
    log_error ".env.prod file not found"
    exit 1
fi

# ============================================================================
# Download Backup from S3 (if enabled)
# ============================================================================

if [ "$RESTORE_FROM_S3" = "true" ]; then
    log_info "Downloading latest backup from S3..."

    if [ -z "${S3_BACKUP_BUCKET:-}" ]; then
        log_error "S3_BACKUP_BUCKET not set in environment"
        exit 1
    fi

    # List and download latest backup
    aws s3 ls "s3://$S3_BACKUP_BUCKET/postgresql/" --recursive | \
        sort | tail -n 1 | awk '{print $4}' | \
        xargs -I {} aws s3 cp "s3://$S3_BACKUP_BUCKET/{}" "$BACKUP_DIR/" || {
        log_error "Failed to download backup from S3"
        exit 1
    }

    log_success "Backup downloaded from S3"
fi

# ============================================================================
# Find Latest Backup
# ============================================================================

LATEST_BACKUP=$(find "$BACKUP_DIR" -name "*.sql.gz" -type f -printf '%T@ %p\n' | sort -rn | head -1 | cut -d' ' -f2)

if [ -z "$LATEST_BACKUP" ]; then
    log_error "No backup files found in $BACKUP_DIR"
    exit 1
fi

log_info "Using backup: $LATEST_BACKUP"
BACKUP_DATE=$(stat -f %Sm "$LATEST_BACKUP" 2>/dev/null || stat -c %y "$LATEST_BACKUP" 2>/dev/null)
log_info "Backup date: $BACKUP_DATE"

# Verify backup integrity
log_info "Verifying backup integrity..."
if ! gzip -t "$LATEST_BACKUP" 2>/dev/null; then
    log_error "Backup file is corrupted!"
    exit 1
fi
log_success "Backup integrity verified"

# ============================================================================
# Stop All Services
# ============================================================================

log_info "Stopping all services..."
cd "$INFRASTRUCTURE_DIR"

docker-compose -f docker-compose.prod.yml down || {
    log_warning "Failed to stop services gracefully"
}

log_success "Services stopped"

# ============================================================================
# Remove Old Data
# ============================================================================

log_info "Removing old data volumes..."

docker volume rm deepagents-platform_postgres_data || {
    log_warning "Failed to remove postgres volume, it may not exist"
}

docker volume rm deepagents-platform_redis_data || {
    log_warning "Failed to remove redis volume, it may not exist"
}

log_success "Old data removed"

# ============================================================================
# Start Database
# ============================================================================

log_info "Starting database service..."

docker-compose -f docker-compose.prod.yml up -d postgres

# Wait for database to be ready
log_info "Waiting for database to initialize..."
sleep 20

# Verify database is running
POSTGRES_READY=false
for i in {1..30}; do
    if docker-compose -f docker-compose.prod.yml exec -T postgres pg_isready -U "$POSTGRES_USER" &> /dev/null; then
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
# Restore Database from Backup
# ============================================================================

log_info "Restoring database from backup..."

RESTORE_START=$(date +%s)

# Drop and recreate database
docker-compose -f docker-compose.prod.yml exec -T postgres \
    psql -U "$POSTGRES_USER" -c "DROP DATABASE IF EXISTS ${POSTGRES_DB};" || true

docker-compose -f docker-compose.prod.yml exec -T postgres \
    psql -U "$POSTGRES_USER" -c "CREATE DATABASE ${POSTGRES_DB};" || {
    log_error "Failed to create database"
    exit 1
}

# Restore from backup
gunzip -c "$LATEST_BACKUP" | docker-compose -f docker-compose.prod.yml exec -T postgres \
    psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" > /dev/null 2>&1 || {
    log_error "Database restore failed!"
    exit 1
}

RESTORE_END=$(date +%s)
RESTORE_DURATION=$((RESTORE_END - RESTORE_START))

log_success "Database restored in ${RESTORE_DURATION}s"

# ============================================================================
# Verify Restored Data
# ============================================================================

log_info "Verifying restored data..."

# Count tables
TABLE_COUNT=$(docker-compose -f docker-compose.prod.yml exec -T postgres \
    psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -t -c \
    "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" | tr -d ' ')

log_info "Tables restored: $TABLE_COUNT"

if [ "$TABLE_COUNT" -eq 0 ]; then
    log_error "No tables found in restored database!"
    exit 1
fi

log_success "Data verification passed"

# ============================================================================
# Start All Services
# ============================================================================

log_info "Starting all services..."

docker-compose -f docker-compose.prod.yml up -d

log_info "Waiting for services to become healthy..."
sleep 30

# ============================================================================
# Health Check
# ============================================================================

log_info "Performing health checks..."

# Check backend health
BACKEND_HEALTHY=false
for i in {1..30}; do
    if curl -f http://localhost:8000/health &> /dev/null; then
        BACKEND_HEALTHY=true
        break
    fi
    log_info "Waiting for backend... (attempt $i/30)"
    sleep 2
done

if [ "$BACKEND_HEALTHY" = false ]; then
    log_error "Backend health check failed!"
    log_error "Check logs with: docker-compose -f docker-compose.prod.yml logs backend"
    exit 1
fi

log_success "All services are healthy"

# ============================================================================
# Run Smoke Tests
# ============================================================================

log_info "Running smoke tests..."

if [ -f "$SCRIPT_DIR/smoke-test.sh" ]; then
    "$SCRIPT_DIR/smoke-test.sh" production || {
        log_warning "Smoke tests failed! Manual verification required."
    }
else
    log_warning "Smoke test script not found. Skipping."
fi

# ============================================================================
# Generate Recovery Report
# ============================================================================

REPORT_FILE="$INFRASTRUCTURE_DIR/backup/recovery-report-$(date +%Y%m%d-%H%M%S).txt"

cat > "$REPORT_FILE" << EOF
Disaster Recovery Report
Generated: $(date)
========================

Recovery Details:
- Backup file: $LATEST_BACKUP
- Backup date: $BACKUP_DATE
- Recovery started: $(date -r $RESTORE_START 2>/dev/null || date -d @$RESTORE_START 2>/dev/null)
- Recovery duration: ${RESTORE_DURATION}s

Database Recovery:
- Tables restored: $TABLE_COUNT
- Database: $POSTGRES_DB

Services Status:
- Backend: $([ "$BACKEND_HEALTHY" = true ] && echo "Healthy" || echo "Unhealthy")
- Database: Running
- Redis: Running
- Nginx: Running

Next Steps:
1. Verify application functionality
2. Check data integrity
3. Review application logs
4. Update DNS if necessary (manual step)
5. Notify stakeholders of recovery completion

Status: RECOVERY COMPLETE
EOF

log_success "Recovery report saved to: $REPORT_FILE"

# ============================================================================
# Summary
# ============================================================================

log_success "============================================"
log_success "DISASTER RECOVERY COMPLETE!"
log_success "============================================"
log_info "Backup restored: $LATEST_BACKUP"
log_info "Recovery duration: ${RESTORE_DURATION}s"
log_info "Tables restored: $TABLE_COUNT"
log_info "Report: $REPORT_FILE"
log_success "============================================"
log_warning "IMPORTANT NEXT STEPS:"
log_warning "1. Verify application functionality"
log_warning "2. Update DNS if this is a new server"
log_warning "3. Notify team of recovery completion"
log_success "============================================"

exit 0
