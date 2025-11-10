#!/bin/bash

# ============================================================================
# DeepAgents Control Platform - Database Backup Script
# ============================================================================
#
# This script creates backups of PostgreSQL and Redis data.
# Backups are stored locally and optionally uploaded to S3.
#
# Features:
# - Full PostgreSQL database dump
# - Redis RDB snapshot
# - Automatic retention (keeps last 7 days by default)
# - Optional S3 upload for offsite backup
# - Compression to save space
#
# Usage:
#   ./backup.sh [--upload-s3] [--retention-days N]
#
# Options:
#   --upload-s3: Upload backup to S3 (requires AWS CLI configured)
#   --retention-days N: Number of days to keep backups (default: 7)
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
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=7
UPLOAD_S3=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --upload-s3)
            UPLOAD_S3=true
            shift
            ;;
        --retention-days)
            RETENTION_DAYS="$2"
            shift 2
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Usage: $0 [--upload-s3] [--retention-days N]"
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

check_command() {
    if ! command -v $1 &> /dev/null; then
        log_error "$1 is required but not installed."
        exit 1
    fi
}

# ============================================================================
# Pre-backup Checks
# ============================================================================

log_info "Starting backup process..."
echo

# Check required commands
check_command docker
check_command docker-compose
check_command gzip

if [ "$UPLOAD_S3" = true ]; then
    check_command aws
fi

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Load environment variables
if [ ! -f "$ENV_FILE" ]; then
    log_error "Environment file not found: $ENV_FILE"
    exit 1
fi
source "$ENV_FILE"

# ============================================================================
# PostgreSQL Backup
# ============================================================================

log_info "Backing up PostgreSQL database..."

POSTGRES_BACKUP_FILE="$BACKUP_DIR/postgres_${TIMESTAMP}.sql"
POSTGRES_COMPRESSED="$POSTGRES_BACKUP_FILE.gz"

# Create PostgreSQL dump
docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" exec -T postgres \
    pg_dump -U "${POSTGRES_USER:-deepagents}" -d "${POSTGRES_DB:-deepagents_prod}" \
    > "$POSTGRES_BACKUP_FILE" || {
    log_error "PostgreSQL backup failed!"
    exit 1
}

# Compress backup
gzip "$POSTGRES_BACKUP_FILE"

POSTGRES_SIZE=$(du -h "$POSTGRES_COMPRESSED" | cut -f1)
log_success "PostgreSQL backup created: $POSTGRES_COMPRESSED ($POSTGRES_SIZE)"
echo

# ============================================================================
# Redis Backup
# ============================================================================

log_info "Backing up Redis data..."

REDIS_BACKUP_FILE="$BACKUP_DIR/redis_${TIMESTAMP}.rdb"
REDIS_COMPRESSED="$REDIS_BACKUP_FILE.gz"

# Trigger Redis save
docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" exec -T redis \
    redis-cli SAVE > /dev/null || {
    log_warning "Redis save command failed (Redis might be empty)"
}

# Copy Redis dump file from container
docker cp deepagents-redis:/data/dump.rdb "$REDIS_BACKUP_FILE" || {
    log_warning "Redis backup skipped (no dump.rdb found)"
    REDIS_BACKUP_FILE=""
}

if [ -n "$REDIS_BACKUP_FILE" ] && [ -f "$REDIS_BACKUP_FILE" ]; then
    # Compress backup
    gzip "$REDIS_BACKUP_FILE"

    REDIS_SIZE=$(du -h "$REDIS_COMPRESSED" | cut -f1)
    log_success "Redis backup created: $REDIS_COMPRESSED ($REDIS_SIZE)"
else
    REDIS_COMPRESSED=""
fi
echo

# ============================================================================
# Create Backup Manifest
# ============================================================================

MANIFEST_FILE="$BACKUP_DIR/backup_${TIMESTAMP}.manifest"

cat > "$MANIFEST_FILE" << EOF
DeepAgents Control Platform Backup Manifest
============================================
Timestamp: $(date)
Backup ID: ${TIMESTAMP}

PostgreSQL Backup:
- File: $(basename "$POSTGRES_COMPRESSED")
- Size: $POSTGRES_SIZE
- Database: ${POSTGRES_DB:-deepagents_prod}

EOF

if [ -n "$REDIS_COMPRESSED" ]; then
cat >> "$MANIFEST_FILE" << EOF
Redis Backup:
- File: $(basename "$REDIS_COMPRESSED")
- Size: $REDIS_SIZE

EOF
fi

cat >> "$MANIFEST_FILE" << EOF
Environment: ${ENVIRONMENT:-production}

Restore Instructions:
1. Extract backups: gunzip *.gz
2. Restore PostgreSQL: cat postgres_${TIMESTAMP}.sql | docker-compose exec -T postgres psql -U user -d database
3. Restore Redis: docker cp redis_${TIMESTAMP}.rdb container:/data/dump.rdb && docker restart container
EOF

log_success "Backup manifest created: $MANIFEST_FILE"
echo

# ============================================================================
# Upload to S3 (Optional)
# ============================================================================

if [ "$UPLOAD_S3" = true ]; then
    log_info "Uploading backups to S3..."

    if [ -z "${S3_BACKUP_BUCKET:-}" ]; then
        log_error "S3_BACKUP_BUCKET not set in environment"
        exit 1
    fi

    S3_PREFIX="deepagents-backups/${TIMESTAMP}"

    # Upload PostgreSQL backup
    aws s3 cp "$POSTGRES_COMPRESSED" "s3://${S3_BACKUP_BUCKET}/${S3_PREFIX}/" || {
        log_error "Failed to upload PostgreSQL backup to S3"
        exit 1
    }

    # Upload Redis backup (if exists)
    if [ -n "$REDIS_COMPRESSED" ]; then
        aws s3 cp "$REDIS_COMPRESSED" "s3://${S3_BACKUP_BUCKET}/${S3_PREFIX}/" || {
            log_warning "Failed to upload Redis backup to S3"
        }
    fi

    # Upload manifest
    aws s3 cp "$MANIFEST_FILE" "s3://${S3_BACKUP_BUCKET}/${S3_PREFIX}/" || {
        log_warning "Failed to upload manifest to S3"
    }

    log_success "Backups uploaded to S3: s3://${S3_BACKUP_BUCKET}/${S3_PREFIX}/"
    echo
fi

# ============================================================================
# Cleanup Old Backups
# ============================================================================

log_info "Cleaning up old backups (retention: $RETENTION_DAYS days)..."

# Find and delete old backups
OLD_BACKUPS=$(find "$BACKUP_DIR" -name "*.gz" -type f -mtime +$RETENTION_DAYS)
OLD_MANIFESTS=$(find "$BACKUP_DIR" -name "*.manifest" -type f -mtime +$RETENTION_DAYS)

if [ -n "$OLD_BACKUPS" ]; then
    echo "$OLD_BACKUPS" | while read file; do
        rm -f "$file"
        log_info "Deleted old backup: $(basename "$file")"
    done
fi

if [ -n "$OLD_MANIFESTS" ]; then
    echo "$OLD_MANIFESTS" | while read file; do
        rm -f "$file"
    done
fi

log_success "Old backups cleaned up"
echo

# ============================================================================
# Backup Summary
# ============================================================================

log_success "Backup completed successfully!"
echo
echo "Backup Summary:"
echo "  PostgreSQL: $POSTGRES_COMPRESSED ($POSTGRES_SIZE)"
if [ -n "$REDIS_COMPRESSED" ]; then
    echo "  Redis: $REDIS_COMPRESSED ($REDIS_SIZE)"
fi
echo "  Manifest: $MANIFEST_FILE"
echo "  Location: $BACKUP_DIR"
echo
log_info "To restore, use: ./restore.sh $TIMESTAMP"
