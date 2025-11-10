#!/bin/bash

# ============================================================================
# DeepAgents Control Platform - Backup Testing Script
# ============================================================================
# This script tests the backup and restore process
# It creates a test database, restores the latest backup, and verifies integrity

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
TEST_DB_NAME="deepagents_backup_test_$(date +%s)"

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

cleanup() {
    log_info "Cleaning up test database..."
    docker-compose -f "$INFRASTRUCTURE_DIR/docker-compose.prod.yml" exec -T postgres \
        psql -U "$POSTGRES_USER" -c "DROP DATABASE IF EXISTS $TEST_DB_NAME;" || true
    log_success "Cleanup completed"
}

# ============================================================================
# Pre-flight Checks
# ============================================================================

log_info "Starting backup test..."

# Load environment variables
if [ -f "$INFRASTRUCTURE_DIR/.env.prod" ]; then
    export $(grep -v '^#' "$INFRASTRUCTURE_DIR/.env.prod" | xargs)
else
    log_error ".env.prod file not found"
    exit 1
fi

# Check if backup directory exists
if [ ! -d "$BACKUP_DIR" ]; then
    log_error "Backup directory not found: $BACKUP_DIR"
    exit 1
fi

# Find latest backup
LATEST_BACKUP=$(find "$BACKUP_DIR" -name "*.sql.gz" -type f -printf '%T@ %p\n' | sort -rn | head -1 | cut -d' ' -f2)

if [ -z "$LATEST_BACKUP" ]; then
    log_error "No backup files found in $BACKUP_DIR"
    exit 1
fi

log_info "Latest backup: $LATEST_BACKUP"
BACKUP_SIZE=$(du -h "$LATEST_BACKUP" | cut -f1)
log_info "Backup size: $BACKUP_SIZE"

# Register cleanup on exit
trap cleanup EXIT

# ============================================================================
# Verify Backup Integrity
# ============================================================================

log_info "Verifying backup file integrity..."

# Check if file is valid gzip
if ! gzip -t "$LATEST_BACKUP" 2>/dev/null; then
    log_error "Backup file is corrupted (gzip test failed)"
    exit 1
fi

log_success "Backup file integrity verified"

# ============================================================================
# Create Test Database
# ============================================================================

log_info "Creating test database: $TEST_DB_NAME"

docker-compose -f "$INFRASTRUCTURE_DIR/docker-compose.prod.yml" exec -T postgres \
    psql -U "$POSTGRES_USER" -c "CREATE DATABASE $TEST_DB_NAME;" || {
    log_error "Failed to create test database"
    exit 1
}

log_success "Test database created"

# ============================================================================
# Restore Backup to Test Database
# ============================================================================

log_info "Restoring backup to test database..."

RESTORE_START=$(date +%s)

# Decompress and restore
gunzip -c "$LATEST_BACKUP" | docker-compose -f "$INFRASTRUCTURE_DIR/docker-compose.prod.yml" exec -T postgres \
    psql -U "$POSTGRES_USER" -d "$TEST_DB_NAME" > /dev/null 2>&1 || {
    log_error "Backup restore failed"
    exit 1
}

RESTORE_END=$(date +%s)
RESTORE_DURATION=$((RESTORE_END - RESTORE_START))

log_success "Backup restored successfully in ${RESTORE_DURATION}s"

# ============================================================================
# Verify Restored Data
# ============================================================================

log_info "Verifying restored data..."

# Count tables
TABLE_COUNT=$(docker-compose -f "$INFRASTRUCTURE_DIR/docker-compose.prod.yml" exec -T postgres \
    psql -U "$POSTGRES_USER" -d "$TEST_DB_NAME" -t -c \
    "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" | tr -d ' ')

log_info "Tables found: $TABLE_COUNT"

if [ "$TABLE_COUNT" -eq 0 ]; then
    log_error "No tables found in restored database"
    exit 1
fi

# Check for expected tables
EXPECTED_TABLES=("users" "agents" "tools" "executions" "traces" "plans" "agent_tools" "subagents")
MISSING_TABLES=()

for table in "${EXPECTED_TABLES[@]}"; do
    EXISTS=$(docker-compose -f "$INFRASTRUCTURE_DIR/docker-compose.prod.yml" exec -T postgres \
        psql -U "$POSTGRES_USER" -d "$TEST_DB_NAME" -t -c \
        "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = '$table');" | tr -d ' ')

    if [ "$EXISTS" != "t" ]; then
        MISSING_TABLES+=("$table")
    fi
done

if [ ${#MISSING_TABLES[@]} -gt 0 ]; then
    log_warning "Missing tables: ${MISSING_TABLES[*]}"
else
    log_success "All expected tables present"
fi

# Count records in key tables
for table in "users" "agents" "executions"; do
    if docker-compose -f "$INFRASTRUCTURE_DIR/docker-compose.prod.yml" exec -T postgres \
        psql -U "$POSTGRES_USER" -d "$TEST_DB_NAME" -t -c \
        "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = '$table');" | grep -q 't'; then

        COUNT=$(docker-compose -f "$INFRASTRUCTURE_DIR/docker-compose.prod.yml" exec -T postgres \
            psql -U "$POSTGRES_USER" -d "$TEST_DB_NAME" -t -c \
            "SELECT COUNT(*) FROM $table;" | tr -d ' ')

        log_info "$table records: $COUNT"
    fi
done

# ============================================================================
# Generate Test Report
# ============================================================================

REPORT_FILE="$INFRASTRUCTURE_DIR/backup/test-report-$(date +%Y%m%d-%H%M%S).txt"

cat > "$REPORT_FILE" << EOF
Backup Test Report
Generated: $(date)
==================

Backup Details:
- File: $LATEST_BACKUP
- Size: $BACKUP_SIZE
- Created: $(stat -f %Sm "$LATEST_BACKUP" 2>/dev/null || stat -c %y "$LATEST_BACKUP" 2>/dev/null)

Restore Performance:
- Duration: ${RESTORE_DURATION}s
- Database: $TEST_DB_NAME

Data Verification:
- Tables found: $TABLE_COUNT
- Missing tables: ${MISSING_TABLES[*]:-None}

Status: SUCCESS
EOF

log_success "Test report saved to: $REPORT_FILE"

# ============================================================================
# Summary
# ============================================================================

log_success "============================================"
log_success "Backup Test Completed Successfully!"
log_success "============================================"
log_info "Backup file: $LATEST_BACKUP"
log_info "Restore duration: ${RESTORE_DURATION}s"
log_info "Tables restored: $TABLE_COUNT"
log_info "Report: $REPORT_FILE"
log_success "============================================"

exit 0
