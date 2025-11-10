# Restore Procedures - DeepAgents Control Platform

Detailed step-by-step procedures for restoring backups in various scenarios.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Full Database Restore](#full-database-restore)
- [Selective Restore](#selective-restore)
- [Point-in-Time Recovery](#point-in-time-recovery)
- [Configuration Restore](#configuration-restore)
- [Verification Steps](#verification-steps)
- [Rollback Procedures](#rollback-procedures)

## Prerequisites

Before performing any restore:

1. **Verify backup integrity**:
   ```bash
   gzip -t /var/backups/deepagents/backup-20250108.tar.gz
   ```

2. **Notify team**:
   - Post in #ops channel
   - Update status page if production restore

3. **Create safety backup** (if production database still accessible):
   ```bash
   cd infrastructure/scripts
   ./backup.sh
   ```

4. **Estimate downtime**:
   - Small database (<1GB): 5-10 minutes
   - Medium database (1-10GB): 10-30 minutes
   - Large database (>10GB): 30-60 minutes

## Full Database Restore

### Scenario: Complete database corruption or data loss

**RTO**: 4 hours
**RPO**: Last backup (up to 24 hours)

### Using Automated Script (Recommended)

```bash
cd infrastructure/scripts

# Run restore script
./restore.sh /var/backups/deepagents/backup-20250108-020000.tar.gz

# Monitor progress
# Script will show progress and confirm completion
```

### Manual Restore Procedure

If automated script fails, follow these steps:

**Step 1: Stop Backend (2 minutes)**
```bash
cd infrastructure
docker-compose -f docker-compose.prod.yml stop backend
docker-compose -f docker-compose.prod.yml stop nginx
```

**Step 2: Backup Current Database** (if accessible)
```bash
docker-compose -f docker-compose.prod.yml exec -T postgres \
    pg_dump -U deepagents -d deepagents_prod -Fc \
    > /tmp/before-restore-$(date +%Y%m%d-%H%M%S).dump
```

**Step 3: Drop Existing Database**
```bash
docker-compose -f docker-compose.prod.yml exec -T postgres \
    psql -U deepagents -c "DROP DATABASE deepagents_prod;"
```

**Step 4: Create Fresh Database**
```bash
docker-compose -f docker-compose.prod.yml exec -T postgres \
    psql -U deepagents -c "CREATE DATABASE deepagents_prod;"
```

**Step 5: Extract and Restore Backup**
```bash
# Extract backup archive
cd /var/backups/deepagents
tar -xzf backup-20250108-020000.tar.gz

# Restore PostgreSQL
gunzip -c postgresql/deepagents_prod.sql.gz | \
    docker-compose -f /path/to/docker-compose.prod.yml exec -T postgres \
    psql -U deepagents -d deepagents_prod
```

**Step 6: Verify Restoration**
```bash
# Check table count
docker-compose -f docker-compose.prod.yml exec -T postgres \
    psql -U deepagents -d deepagents_prod -c \
    "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';"

# Check for expected tables
docker-compose -f docker-compose.prod.yml exec -T postgres \
    psql -U deepagents -d deepagents_prod -c "\dt"

# Verify record counts
docker-compose -f docker-compose.prod.yml exec -T postgres \
    psql -U deepagents -d deepagents_prod -c \
    "SELECT 'users' as table_name, COUNT(*) FROM users
     UNION ALL
     SELECT 'agents', COUNT(*) FROM agents
     UNION ALL
     SELECT 'executions', COUNT(*) FROM executions;"
```

**Step 7: Restore Redis** (if needed)
```bash
# Copy Redis RDB file
docker cp /var/backups/deepagents/redis/dump.rdb \
    deepagents-redis:/data/dump.rdb

# Restart Redis to load data
docker-compose -f docker-compose.prod.yml restart redis
```

**Step 8: Restart Services**
```bash
docker-compose -f docker-compose.prod.yml up -d
```

**Step 9: Verify Application**
```bash
# Wait for services to be ready
sleep 30

# Run smoke tests
cd infrastructure/scripts
./smoke-test.sh production
```

**Step 10: Monitor**
```bash
# Check Grafana dashboards
open http://localhost:3000

# Watch logs for errors
docker-compose -f docker-compose.prod.yml logs -f backend
```

## Selective Restore

### Scenario: Need to restore specific tables without full restore

**Example: Restore only 'agents' table from backup**

**Step 1: Create Temporary Database**
```bash
docker-compose -f docker-compose.prod.yml exec -T postgres \
    psql -U deepagents -c "CREATE DATABASE temp_restore;"
```

**Step 2: Restore Full Backup to Temp Database**
```bash
gunzip -c /var/backups/deepagents/backup.sql.gz | \
    docker-compose -f docker-compose.prod.yml exec -T postgres \
    psql -U deepagents -d temp_restore
```

**Step 3: Export Specific Table(s)**
```bash
docker-compose -f docker-compose.prod.yml exec -T postgres \
    pg_dump -U deepagents -d temp_restore -t agents --data-only \
    > /tmp/agents_data.sql
```

**Step 4: Truncate Production Table** (DANGEROUS!)
```bash
# Make backup first!
docker-compose -f docker-compose.prod.yml exec -T postgres \
    pg_dump -U deepagents -d deepagents_prod -t agents \
    > /tmp/agents_backup_before_restore.sql

# Truncate table
docker-compose -f docker-compose.prod.yml exec -T postgres \
    psql -U deepagents -d deepagents_prod -c "TRUNCATE TABLE agents CASCADE;"
```

**Step 5: Import Data**
```bash
cat /tmp/agents_data.sql | \
    docker-compose -f docker-compose.prod.yml exec -T postgres \
    psql -U deepagents -d deepagents_prod
```

**Step 6: Verify**
```bash
docker-compose -f docker-compose.prod.yml exec -T postgres \
    psql -U deepagents -d deepagents_prod -c \
    "SELECT COUNT(*) FROM agents;"
```

**Step 7: Cleanup**
```bash
docker-compose -f docker-compose.prod.yml exec -T postgres \
    psql -U deepagents -c "DROP DATABASE temp_restore;"

rm /tmp/agents_data.sql
```

## Point-in-Time Recovery

### Scenario: Restore to specific time before data corruption

**Prerequisites**: WAL archiving must be enabled

**Step 1: Restore Base Backup**
```bash
# Use backup from before the incident
./restore.sh /var/backups/deepagents/backup-20250107-020000.tar.gz
```

**Step 2: Configure Recovery Target**
```bash
# Stop database
docker-compose -f docker-compose.prod.yml stop postgres

# Create recovery.conf
cat > /var/lib/postgresql/data/recovery.conf << EOF
restore_command = 'cp /var/lib/postgresql/wal_archive/%f %p'
recovery_target_time = '2025-01-08 14:30:00'
recovery_target_action = 'promote'
EOF

# Set ownership
chown postgres:postgres /var/lib/postgresql/data/recovery.conf
```

**Step 3: Start Recovery**
```bash
# Start PostgreSQL
docker-compose -f docker-compose.prod.yml start postgres

# Monitor recovery
docker-compose -f docker-compose.prod.yml logs -f postgres
# Look for: "database system is ready to accept connections"
```

**Step 4: Verify Recovery Point**
```bash
docker-compose -f docker-compose.prod.yml exec postgres \
    psql -U deepagents -d deepagents_prod -c \
    "SELECT pg_last_xact_replay_timestamp();"
```

**Step 5: Resume Normal Operations**
```bash
# Start all services
docker-compose -f docker-compose.prod.yml up -d
```

## Configuration Restore

### Scenario: Restore nginx or SSL configuration after loss

**Step 1: Extract Configuration from Backup**
```bash
cd /var/backups/deepagents
tar -xzf backup-latest.tar.gz

# List configuration files
ls -la config/
```

**Step 2: Restore Nginx Configuration**
```bash
# Backup current config
cp -r infrastructure/nginx infrastructure/nginx.backup

# Restore from backup
cp -r config/nginx/* infrastructure/nginx/

# Verify syntax
docker-compose -f docker-compose.prod.yml exec nginx nginx -t

# Reload nginx
docker-compose -f docker-compose.prod.yml exec nginx nginx -s reload
```

**Step 3: Restore SSL Certificates**
```bash
# Restore certificates
cp -r config/ssl/* infrastructure/ssl/

# Verify certificate
openssl x509 -in infrastructure/ssl/cert.pem -text -noout

# Restart nginx
docker-compose -f docker-compose.prod.yml restart nginx
```

**Step 4: Restore Environment Variables**
```bash
# Compare current vs backup
diff infrastructure/.env.prod config/.env.prod

# Restore if needed (CAREFUL!)
cp config/.env.prod infrastructure/.env.prod

# Restart services to pick up changes
docker-compose -f docker-compose.prod.yml restart
```

## Verification Steps

### Post-Restore Verification Checklist

After any restore, verify:

**1. Service Health**
```bash
curl http://localhost:8000/api/v1/health/deep
# Should return: {"status": "healthy", ...}
```

**2. Database Integrity**
```bash
# Check table count
docker-compose exec postgres \
    psql -U deepagents -d deepagents_prod -c \
    "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';"

# Run vacuum analyze
docker-compose exec postgres \
    psql -U deepagents -d deepagents_prod -c "VACUUM ANALYZE;"
```

**3. Application Functionality**
```bash
# Run smoke tests
cd infrastructure/scripts
./smoke-test.sh production

# Manual tests:
# - Login
# - Create agent
# - Execute agent
# - View analytics
```

**4. Data Consistency**
```bash
# Check for orphaned records
docker-compose exec postgres \
    psql -U deepagents -d deepagents_prod << EOF
    -- Check for agents without users
    SELECT COUNT(*) FROM agents WHERE user_id NOT IN (SELECT id FROM users);

    -- Check for executions without agents
    SELECT COUNT(*) FROM executions WHERE agent_id NOT IN (SELECT id FROM agents);
EOF
```

**5. Performance**
```bash
# Check query performance in Grafana
# Database Performance dashboard

# Run sample queries and verify response times
```

## Rollback Procedures

### If Restore Fails or Data is Incorrect

**Option 1: Restore Previous State**

If you created a safety backup:
```bash
./restore.sh /tmp/before-restore-20250108.dump
```

**Option 2: Try Different Backup**

Use older backup:
```bash
# List available backups
ls -lh /var/backups/deepagents/

# Restore from older backup
./restore.sh /var/backups/deepagents/backup-20250107-020000.tar.gz
```

**Option 3: Restore from S3**

Download and restore from S3:
```bash
# List S3 backups
aws s3 ls s3://deepagents-backups/postgresql/

# Download specific backup
aws s3 cp s3://deepagents-backups/postgresql/backup-20250106.tar.gz \
    /var/backups/deepagents/

# Restore
./restore.sh /var/backups/deepagents/backup-20250106.tar.gz
```

## Testing Restore Procedures

### Regular Testing Schedule

- **Monthly**: Test full restore on staging
- **Quarterly**: Test disaster recovery drill
- **Annually**: Test point-in-time recovery

### Test Procedure

```bash
# 1. Reset staging
cd infrastructure/scripts
./reset-staging.sh

# 2. Restore production backup to staging
./restore.sh /var/backups/deepagents/production-backup-latest.tar.gz

# 3. Verify data
# Check record counts match production

# 4. Test functionality
./smoke-test.sh staging

# 5. Document results
# Record time taken, issues encountered
```

## Recovery Time Objectives

| Scenario | RTO | RPO | Complexity |
|----------|-----|-----|------------|
| Full database restore | 4 hours | 24 hours | Medium |
| Selective table restore | 2 hours | 24 hours | Low |
| Point-in-time recovery | 6 hours | Minutes | High |
| Configuration restore | 30 minutes | N/A | Low |
| Disaster recovery | 8 hours | 24 hours | High |

## Troubleshooting Restore Issues

### Restore Script Fails

**Check logs**:
```bash
docker-compose logs postgres
```

**Common issues**:
- Incorrect database name
- Permission errors
- Disk space full
- Corrupted backup file

**Solutions**:
```bash
# Verify backup integrity
gzip -t backup.sql.gz

# Check disk space
df -h

# Check PostgreSQL logs
docker-compose logs postgres | grep ERROR
```

### Data Missing After Restore

**Possible causes**:
- Wrong backup file used
- Backup is older than expected
- Partial backup

**Verify**:
```bash
# Check backup date
stat -c %y backup.sql.gz

# Check what's in backup
pg_restore --list backup.dump | grep -i agents
```

### Performance Issues After Restore

**Run maintenance**:
```bash
docker-compose exec postgres \
    psql -U deepagents -d deepagents_prod << EOF
    VACUUM FULL ANALYZE;
    REINDEX DATABASE deepagents_prod;
EOF
```

## Emergency Contacts

- **Database Admin**: dba@yourdomain.com
- **DevOps Lead**: devops-lead@yourdomain.com
- **On-Call Engineer**: +1-555-ONCALL

## Related Documentation

- [Backup Strategy](../BACKUP_RECOVERY.md)
- [Disaster Recovery](../RUNBOOK.md#disaster-recovery)
- [Test Backup Script](../scripts/test-backup.sh)
