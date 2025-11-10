# Operational Runbook - DeepAgents Control Platform

This runbook provides step-by-step procedures for common operational tasks, incident response, and maintenance operations.

## Table of Contents

- [Quick Reference](#quick-reference)
- [Daily Operations](#daily-operations)
- [Deployment Procedures](#deployment-procedures)
- [Incident Response](#incident-response)
- [Maintenance Tasks](#maintenance-tasks)
- [Scaling Operations](#scaling-operations)
- [Emergency Procedures](#emergency-procedures)
- [On-Call Playbook](#on-call-playbook)

## Quick Reference

### Service URLs

| Service | Production | Staging |
|---------|------------|---------|
| Frontend | https://yourdomain.com | http://localhost:8081 |
| Backend API | https://yourdomain.com/api | http://localhost:8080 |
| API Docs | https://yourdomain.com/docs | http://localhost:8080/docs |
| Grafana | http://localhost:3000 | http://localhost:3000 |
| Prometheus | http://localhost:9090 | http://localhost:9090 |
| Alertmanager | http://localhost:9093 | http://localhost:9093 |

### Key Commands

```bash
# View service status
docker-compose -f infrastructure/docker-compose.prod.yml ps

# View logs
docker-compose -f infrastructure/docker-compose.prod.yml logs -f [service]

# Restart service
docker-compose -f infrastructure/docker-compose.prod.yml restart [service]

# Deploy to production
cd infrastructure/scripts && ./deploy.sh

# Deploy to staging
cd infrastructure/scripts && ./deploy-staging.sh

# Create backup
cd infrastructure/scripts && ./backup.sh

# Restore from backup
cd infrastructure/scripts && ./restore.sh [backup-file]
```

### Emergency Contacts

- **On-Call Engineer**: +1-555-ONCALL
- **Engineering Lead**: eng-lead@yourdomain.com
- **DevOps Team**: devops@yourdomain.com
- **CTO (Escalation)**: cto@yourdomain.com

### Status Page

- **URL**: https://status.yourdomain.com
- **Update procedure**: See [Status Page Updates](#status-page-updates)

## Daily Operations

### Morning Checklist

Run this checklist every morning:

```bash
# 1. Check service health
curl https://yourdomain.com/api/v1/health/deep

# 2. Review Grafana dashboards
open http://localhost:3000
# Check: System Overview, Application Metrics, Database Performance

# 3. Check for active alerts
open http://localhost:9093

# 4. Review error logs (last 24h)
docker-compose -f infrastructure/docker-compose.prod.yml logs --since 24h backend | grep ERROR

# 5. Verify backups completed
ls -lh /var/backups/deepagents/ | tail -5

# 6. Check disk space
df -h

# 7. Review slow queries
# In Grafana: Database Performance → Query Duration panel
```

### Daily Health Report

Generate automated health report:

```bash
#!/bin/bash
# Save as: infrastructure/scripts/daily-health-report.sh

echo "=== DeepAgents Daily Health Report $(date) ==="
echo ""
echo "Service Status:"
curl -s http://localhost:8000/api/v1/health | jq .
echo ""
echo "Disk Usage:"
df -h / | grep -v Filesystem
echo ""
echo "Latest Backup:"
ls -lh /var/backups/deepagents/ | tail -1
echo ""
echo "Active Alerts:"
curl -s http://localhost:9093/api/v1/alerts | jq '.data[] | select(.status.state=="firing") | {alertname: .labels.alertname, severity: .labels.severity}'
```

## Deployment Procedures

### Standard Deployment (Production)

**Prerequisites**:
- All tests passing
- Code reviewed and approved
- Staging deployment successful
- Change request approved (if required)

**Steps**:

1. **Pre-deployment** (10 minutes before):
   ```bash
   # Notify team
   # Post in #deployments Slack channel

   # Create backup
   cd infrastructure/scripts
   ./backup.sh

   # Verify staging
   ./smoke-test.sh staging
   ```

2. **Deploy** (5-10 minutes):
   ```bash
   # Run deployment script
   ./deploy.sh

   # Monitor deployment
   watch -n 2 'docker-compose -f infrastructure/docker-compose.prod.yml ps'
   ```

3. **Post-deployment** (5 minutes):
   ```bash
   # Run smoke tests
   ./smoke-test.sh production

   # Verify in Grafana
   # Check error rates, response times, active connections

   # Notify team of completion
   ```

### Zero-Downtime Deployment

For critical deployments with zero downtime:

```bash
# 1. Start new backend alongside old one
docker-compose -f infrastructure/docker-compose.prod.yml up -d --scale backend=2

# 2. Wait for new backend to be healthy
sleep 30

# 3. Update nginx to point to new backend

# 4. Monitor traffic shifting

# 5. Stop old backend
docker-compose -f infrastructure/docker-compose.prod.yml up -d --scale backend=1
```

### Rollback Procedure

If deployment fails:

```bash
# 1. Immediate rollback
cd infrastructure/scripts
git checkout [previous-tag]
./deploy.sh

# 2. Restore database (if schema changed)
./restore.sh /var/backups/deepagents/pre-deployment-backup.sql.gz

# 3. Verify rollback
./smoke-test.sh production

# 4. Notify team
# 5. Post-mortem within 24 hours
```

## Incident Response

### Incident Severity Levels

| Severity | Impact | Response Time | Examples |
|----------|--------|---------------|----------|
| **P0** | Complete outage | Immediate | Service down, data loss |
| **P1** | Major degradation | <15 minutes | High error rate, slow responses |
| **P2** | Minor degradation | <1 hour | Single feature broken |
| **P3** | Cosmetic issue | <24 hours | UI glitch, logging errors |

### P0: Complete Outage

**Symptoms**: Service completely unavailable, health checks failing

**Immediate Actions** (first 5 minutes):

```bash
# 1. Acknowledge incident
# Post in #incidents channel
# Update status page

# 2. Check if service is running
docker-compose -f infrastructure/docker-compose.prod.yml ps

# 3. Check for recent deployments
git log --oneline -10

# 4. Review recent alerts
curl http://localhost:9093/api/v1/alerts | jq

# 5. Check logs for errors
docker-compose logs --tail=100 backend | grep -i error
```

**Investigation** (5-15 minutes):

```bash
# Check database connectivity
docker-compose exec postgres pg_isready

# Check Redis connectivity
docker-compose exec redis redis-cli PING

# Check disk space
df -h

# Check memory
free -h

# Review system logs
dmesg | tail -50
```

**Recovery**:

Option A - Service restart:
```bash
docker-compose restart backend
```

Option B - Full restart:
```bash
docker-compose down
docker-compose up -d
```

Option C - Rollback:
```bash
./scripts/deploy.sh [previous-version]
```

Option D - Disaster recovery:
```bash
./scripts/disaster-recovery.sh
```

**Post-Incident**:
- Update status page
- Post resolution in #incidents
- Schedule post-mortem
- Document in incident log

### P1: Major Degradation

**Symptoms**: High error rate (>5%), slow responses (>5s), partial functionality

**Response**:

```bash
# 1. Identify source
# Check Grafana dashboards
open http://localhost:3000

# 2. Review application logs
docker-compose logs --tail=500 backend | grep ERROR

# 3. Check database performance
# Grafana → Database Performance dashboard
# Look for slow queries, high connection count

# 4. Check for resource exhaustion
docker stats

# 5. Mitigation
# Restart affected service
docker-compose restart backend

# Or scale up
docker-compose up -d --scale backend=2
```

### P2: Minor Issues

**Response**:

```bash
# 1. Document issue
# Create ticket with details

# 2. Investigate non-urgently
# Review logs
# Check metrics

# 3. Plan fix
# Create PR with fix
# Test in staging

# 4. Deploy in next release window
./scripts/deploy-staging.sh
# Test, then deploy to production
```

## Maintenance Tasks

### Weekly Tasks (Every Monday)

```bash
# 1. Review and clean old Docker images
docker system prune -a --filter "until=168h"

# 2. Review disk usage trends
df -h
du -sh /var/lib/docker/*

# 3. Update dependencies (in staging first)
cd backend
pip list --outdated

cd ../frontend
npm outdated

# 4. Review and close old alerts
# Check Alertmanager for silenced alerts that can be removed

# 5. Review slow queries
# Export slow query report from Grafana
```

### Monthly Tasks (First of Month)

```bash
# 1. Backup verification test
cd infrastructure/scripts
./test-backup.sh

# 2. Review and rotate logs
find /var/log -name "*.log" -mtime +30 -delete

# 3. Update SSL certificates (if needed)
certbot renew

# 4. Review capacity metrics
# Check Grafana for resource usage trends
# Plan for scaling if needed

# 5. Security updates
apt update && apt upgrade  # or yum update

# 6. Dependency updates
# Update patch versions in staging
# Test thoroughly
# Deploy to production

# 7. Review monitoring dashboards
# Ensure all panels showing data
# Update thresholds if needed

# 8. Disaster recovery drill (quarterly)
# Run on staging
./scripts/disaster-recovery.sh
```

### Certificate Renewal

```bash
# Manual renewal (if certbot cron fails)
certbot renew --force-renewal

# Verify new certificate
openssl x509 -in /etc/letsencrypt/live/yourdomain.com/cert.pem -text -noout

# Reload nginx
docker-compose restart nginx
```

### Database Maintenance

```bash
# Vacuum and analyze (weekly)
docker-compose exec postgres \
    psql -U deepagents -d deepagents_prod -c "VACUUM ANALYZE;"

# Reindex (monthly)
docker-compose exec postgres \
    psql -U deepagents -d deepagents_prod -c "REINDEX DATABASE deepagents_prod;"

# Check for bloat
docker-compose exec postgres \
    psql -U deepagents -d deepagents_prod -f check_bloat.sql

# Update statistics
docker-compose exec postgres \
    psql -U deepagents -d deepagents_prod -c "ANALYZE;"
```

## Scaling Operations

### Horizontal Scaling (More Instances)

**Scale backend**:
```bash
# Increase backend instances
docker-compose up -d --scale backend=4

# Verify load balancing
watch -n 1 'curl -s http://localhost/api/v1/health | jq .hostname'

# Monitor performance
# Check Grafana for request distribution
```

**Scale workers** (if applicable):
```bash
# Scale background workers
docker-compose up -d --scale worker=3
```

### Vertical Scaling (More Resources)

**Increase container resources**:

Edit `docker-compose.prod.yml`:
```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '4'      # Increase from 2
          memory: 4G     # Increase from 2G
```

Apply changes:
```bash
docker-compose up -d
```

**Increase database resources**:

Edit `postgresql.conf`:
```conf
shared_buffers = 2GB         # Increase from 1GB
max_connections = 200        # Increase from 100
work_mem = 16MB              # Increase from 8MB
```

Restart PostgreSQL:
```bash
docker-compose restart postgres
```

### Auto-Scaling (Future)

Set up auto-scaling based on metrics:
- CPU usage >70% for 5 minutes → scale up
- Request queue depth >100 → scale up
- CPU usage <30% for 10 minutes → scale down

## Emergency Procedures

### Complete Data Loss

See [Disaster Recovery](BACKUP_RECOVERY.md#disaster-recovery)

### Database Corruption

```bash
# 1. Stop backend to prevent writes
docker-compose stop backend

# 2. Attempt repair
docker-compose exec postgres \
    pg_resetwal /var/lib/postgresql/data

# 3. If repair fails, restore from backup
./scripts/restore.sh /var/backups/deepagents/latest.sql.gz

# 4. Restart services
docker-compose up -d
```

### Security Breach

```bash
# 1. Isolate affected systems
docker-compose down

# 2. Preserve logs for forensics
cp -r /var/log/deepagents /secure/location/incident-$(date +%Y%m%d)

# 3. Rotate all secrets
# Generate new SECRET_KEY
# Rotate API keys
# Invalidate all sessions

# 4. Review access logs
# Identify scope of breach

# 5. Notify security team and legal
# Follow incident response plan

# 6. Apply patches and redeploy
# Fix vulnerability
# Deploy to production

# 7. Monitor for suspicious activity
# Enhanced logging for 30 days
```

## On-Call Playbook

### On-Call Responsibilities

- Respond to alerts within 15 minutes
- Acknowledge and triage incidents
- Escalate to engineering lead if needed
- Document all actions taken
- Handoff status to next on-call

### Alert Response

**When you receive an alert**:

1. **Acknowledge immediately**
   - Click acknowledge in PagerDuty/Alertmanager
   - Post in #incidents if P0/P1

2. **Assess severity**
   - Check Grafana dashboards
   - Review recent deployments
   - Check service health

3. **Take action**
   - Follow incident procedures above
   - Document actions in incident channel

4. **Resolve and notify**
   - Verify resolution
   - Update status page
   - Post resolution message

### Common Alerts and Responses

**BackendDown**:
```bash
# Check if running
docker-compose ps backend

# View logs
docker-compose logs backend --tail=100

# Restart if crashed
docker-compose restart backend
```

**HighCPUUsage**:
```bash
# Identify process
docker stats

# Check for runaway queries
# Grafana → Database → Active Queries

# Scale if needed
docker-compose up -d --scale backend=2
```

**DiskSpaceLow**:
```bash
# Check usage
df -h

# Clean Docker artifacts
docker system prune -a

# Clean old logs
find /var/log -name "*.log" -mtime +7 -delete

# Remove old backups (keep last 7)
cd /var/backups/deepagents
ls -t | tail -n +8 | xargs rm -f
```

### Handoff Checklist

When going off-call:

- [ ] Resolve or handoff all open incidents
- [ ] Document status of ongoing issues
- [ ] Brief next on-call engineer
- [ ] Ensure contact info is current
- [ ] Clear all acknowledged alerts

## Status Page Updates

### Posting Incident

```bash
# Template for incident post
Title: [Platform Issue] Service Degradation
Status: Investigating
Message: We are investigating reports of slow response times.
         Updates will be posted every 15 minutes.
Affected Components: API, Web Application
```

### Updating Incident

```bash
Status: Identified
Message: We have identified the issue as high database load.
         Scaling database resources now.
```

### Resolving Incident

```bash
Status: Resolved
Message: The issue has been resolved. All services operating normally.
         We will post a post-mortem within 24 hours.
```

## Appendix

### Log Locations

- Backend: `docker-compose logs backend`
- Database: `docker-compose logs postgres`
- Nginx: `docker-compose logs nginx`
- Redis: `docker-compose logs redis`
- Backups: `/var/log/deepagents/backup.log`
- System: `/var/log/syslog`

### Configuration Files

- Environment: `/infrastructure/.env.prod`
- Nginx: `/infrastructure/nginx/nginx.conf`
- PostgreSQL: `/infrastructure/postgres/postgresql.conf`
- Prometheus: `/infrastructure/monitoring/prometheus/prometheus.yml`
- Alerts: `/infrastructure/monitoring/prometheus/alerts.yml`

### Useful Queries

**PostgreSQL**:
```sql
-- Active connections
SELECT count(*) FROM pg_stat_activity;

-- Long-running queries
SELECT pid, now() - query_start as duration, query
FROM pg_stat_activity
WHERE state = 'active' AND now() - query_start > interval '1 minute';

-- Database size
SELECT pg_size_pretty(pg_database_size('deepagents_prod'));

-- Table sizes
SELECT schemaname, tablename,
       pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

**Redis**:
```bash
# Memory usage
INFO memory

# Connected clients
CLIENT LIST

# Slow log
SLOWLOG GET 10

# Key count
DBSIZE
```

### Related Documentation

- [Deployment Guide](DEPLOYMENT.md)
- [Monitoring Guide](MONITORING.md)
- [Staging Guide](STAGING.md)
- [Backup and Recovery](BACKUP_RECOVERY.md)
- [Production Checklist](PRODUCTION_CHECKLIST.md)
