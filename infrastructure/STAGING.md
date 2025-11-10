# Staging Environment Guide - DeepAgents Control Platform

This document explains the staging environment, how to use it, and best practices.

## Table of Contents

- [Purpose of Staging](#purpose-of-staging)
- [Environment Differences](#environment-differences)
- [Getting Started](#getting-started)
- [Deployment Process](#deployment-process)
- [Testing on Staging](#testing-on-staging)
- [Resetting Staging](#resetting-staging)
- [Promoting to Production](#promoting-to-production)
- [Common Tasks](#common-tasks)
- [Troubleshooting](#troubleshooting)

## Purpose of Staging

The staging environment serves as a pre-production testing ground where you can:

- **Test new features** before they reach production
- **Validate deployments** and ensure zero-downtime upgrades work
- **Run integration tests** with production-like data
- **Train team members** without affecting live users
- **Reproduce production bugs** in a safe environment
- **Test database migrations** before applying to production
- **Validate monitoring and alerting** configurations

**Key Principle**: Staging should mirror production as closely as possible while allowing for safe experimentation.

## Environment Differences

### Similarities to Production
- Same Docker images and configurations
- Same database schema (migrations applied)
- Same Redis configuration
- Similar resource allocations (scaled down)
- Same monitoring stack available

### Differences from Production

| Aspect | Staging | Production |
|--------|---------|------------|
| **Resource Limits** | 50% of production | Full allocation |
| **Database Name** | `deepagents_staging` | `deepagents_prod` |
| **Ports** | 8080-8081, 8444 | 80, 443 |
| **Debug Mode** | Enabled | Disabled |
| **Log Level** | DEBUG | INFO |
| **Data** | Test/synthetic | Real user data |
| **SSL Certificates** | Self-signed OK | Valid certificates required |
| **Backup Frequency** | Less frequent | Daily |
| **Monitoring Retention** | 7 days | 30 days |

## Getting Started

### Initial Setup

1. **Create environment file**:
   ```bash
   cd infrastructure
   cp .env.staging.example .env.staging
   ```

2. **Configure variables**:
   ```bash
   # Edit .env.staging with your values
   vim .env.staging

   # Required changes:
   # - POSTGRES_PASSWORD (unique from production)
   # - SECRET_KEY (unique from production)
   # - ANTHROPIC_API_KEY
   # - OPENAI_API_KEY (optional)
   ```

3. **Start staging environment**:
   ```bash
   ./scripts/deploy-staging.sh
   ```

### Accessing Staging

- **Frontend**: http://localhost:8081
- **Backend API**: http://localhost:8080
- **API Docs**: http://localhost:8080/docs
- **Health Check**: http://localhost:8080/api/v1/health

### Verify Deployment

```bash
# Check all services are running
docker-compose -f docker-compose.staging.yml ps

# Check backend health
curl http://localhost:8080/api/v1/health/deep

# View logs
docker-compose -f docker-compose.staging.yml logs -f backend
```

## Deployment Process

### Automated Deployment

The `deploy-staging.sh` script handles the entire deployment process:

```bash
cd infrastructure
./scripts/deploy-staging.sh
```

**What it does**:
1. Pulls latest code from `develop` branch (default)
2. Creates backup of current database (optional)
3. Builds Docker images with staging tag
4. Runs database migrations
5. Deploys services with zero downtime
6. Runs smoke tests
7. Sends notification (if configured)

### Manual Deployment Steps

If you need to deploy manually:

```bash
cd infrastructure

# 1. Pull latest code
cd ..
git pull origin develop

# 2. Build images
cd infrastructure
docker-compose -f docker-compose.staging.yml build

# 3. Run migrations
docker-compose -f docker-compose.staging.yml run --rm backend alembic upgrade head

# 4. Deploy services
docker-compose -f docker-compose.staging.yml up -d

# 5. Wait for health
sleep 20

# 6. Verify
curl http://localhost:8080/health
```

### Deploying Specific Branch

```bash
# Set the branch to deploy
export DEPLOY_BRANCH=feature/new-feature

# Run deployment
./scripts/deploy-staging.sh
```

## Testing on Staging

### Pre-Deployment Testing Checklist

Before deploying to staging:

- [ ] All tests passing locally
- [ ] Code review completed
- [ ] Database migrations tested
- [ ] API documentation updated
- [ ] Feature flags configured (if applicable)

### Post-Deployment Testing

After deploying to staging:

1. **Smoke Tests** (automated):
   ```bash
   ./scripts/smoke-test.sh staging
   ```

2. **Manual Testing**:
   - Create test agent
   - Execute agent with different models
   - Test tool integrations
   - Verify WebSocket streaming
   - Test template system
   - Check analytics dashboard

3. **Performance Testing**:
   ```bash
   # Load test with Apache Bench
   ab -n 1000 -c 10 http://localhost:8080/api/v1/agents

   # Monitor metrics
   open http://localhost:3000  # Grafana
   ```

4. **Database Migration Testing**:
   ```bash
   # Apply migration
   docker-compose -f docker-compose.staging.yml run --rm backend \
       alembic upgrade head

   # Verify schema
   docker-compose -f docker-compose.staging.yml exec postgres \
       psql -U deepagents_staging -d deepagents_staging -c "\dt"

   # Test rollback (if needed)
   docker-compose -f docker-compose.staging.yml run --rm backend \
       alembic downgrade -1
   ```

### Integration Testing

Run integration tests against staging:

```bash
cd backend

# Set staging API URL
export API_BASE_URL=http://localhost:8080

# Run integration tests
pytest tests/integration/
```

## Resetting Staging

### When to Reset Staging

- Corrupted test data
- Need clean slate for testing
- Database migration issues
- After major feature testing
- Monthly maintenance

### How to Reset

**Automated Reset** (recommended):
```bash
cd infrastructure
./scripts/reset-staging.sh
```

This will:
1. Prompt for confirmation (type 'RESET')
2. Stop all services
3. Remove all data volumes
4. Start fresh databases
5. Run migrations
6. Seed test data (if configured)
7. Restart all services

**Manual Reset**:
```bash
# Stop and remove everything
docker-compose -f docker-compose.staging.yml down -v

# Start fresh
docker-compose -f docker-compose.staging.yml up -d

# Wait for services
sleep 20

# Run migrations
docker-compose -f docker-compose.staging.yml run --rm backend \
    alembic upgrade head
```

### Seeding Test Data

Enable test data seeding in `.env.staging`:
```bash
SEED_TEST_DATA=True
TEST_AGENTS_COUNT=5
TEST_USERS_COUNT=3
```

## Promoting to Production

### Pre-Promotion Checklist

Before promoting staging to production:

- [ ] All staging tests passing
- [ ] No critical bugs found
- [ ] Performance acceptable
- [ ] Database migrations tested
- [ ] Rollback plan documented
- [ ] Team notified of deployment
- [ ] Maintenance window scheduled (if needed)
- [ ] Backup verified

### Promotion Process

1. **Create Production Backup**:
   ```bash
   cd infrastructure/scripts
   ./backup.sh
   ```

2. **Tag Release**:
   ```bash
   git tag -a v1.2.3 -m "Release v1.2.3"
   git push origin v1.2.3
   ```

3. **Deploy to Production**:
   ```bash
   cd infrastructure/scripts
   ./deploy.sh
   ```

4. **Monitor Deployment**:
   - Watch Grafana dashboards
   - Monitor error rates
   - Check application logs
   - Verify user-facing features

5. **Smoke Test Production**:
   ```bash
   ./scripts/smoke-test.sh production
   ```

### Rollback Plan

If issues arise after promotion:

```bash
cd infrastructure/scripts

# 1. Rollback code
git checkout v1.2.2  # Previous stable version
./deploy.sh

# 2. Rollback database (if needed)
./restore.sh /var/backups/deepagents/backup-before-v1.2.3.sql.gz

# 3. Verify
./smoke-test.sh production
```

## Common Tasks

### Viewing Logs

```bash
# All services
docker-compose -f docker-compose.staging.yml logs -f

# Specific service
docker-compose -f docker-compose.staging.yml logs -f backend

# With grep
docker-compose -f docker-compose.staging.yml logs backend | grep ERROR
```

### Accessing Database

```bash
# PostgreSQL shell
docker-compose -f docker-compose.staging.yml exec postgres \
    psql -U deepagents_staging -d deepagents_staging

# Run SQL query
docker-compose -f docker-compose.staging.yml exec postgres \
    psql -U deepagents_staging -d deepagents_staging \
    -c "SELECT COUNT(*) FROM agents;"
```

### Accessing Redis

```bash
# Redis CLI
docker-compose -f docker-compose.staging.yml exec redis redis-cli

# Get all keys
docker-compose -f docker-compose.staging.yml exec redis \
    redis-cli KEYS '*'

# Flush all data
docker-compose -f docker-compose.staging.yml exec redis \
    redis-cli FLUSHALL
```

### Running Migrations

```bash
# Apply all pending migrations
docker-compose -f docker-compose.staging.yml run --rm backend \
    alembic upgrade head

# Create new migration
docker-compose -f docker-compose.staging.yml run --rm backend \
    alembic revision --autogenerate -m "description"

# Rollback one migration
docker-compose -f docker-compose.staging.yml run --rm backend \
    alembic downgrade -1
```

### Updating Environment Variables

```bash
# 1. Edit .env.staging
vim .env.staging

# 2. Restart affected services
docker-compose -f docker-compose.staging.yml restart backend

# 3. Verify changes
docker-compose -f docker-compose.staging.yml exec backend env | grep NEW_VAR
```

## Troubleshooting

### Staging Won't Start

**Symptoms**: Services fail to start or crash immediately

**Diagnosis**:
```bash
# Check service status
docker-compose -f docker-compose.staging.yml ps

# View recent logs
docker-compose -f docker-compose.staging.yml logs --tail=50
```

**Common Causes**:
- Port conflicts with production
- Missing environment variables
- Database migration failures
- Insufficient resources

**Solutions**:
```bash
# Check port conflicts
lsof -i :8080
lsof -i :5433

# Verify environment file
cat .env.staging | grep -v "^#" | grep "="

# Check available resources
docker system df
```

### Database Connection Errors

**Symptoms**: Backend can't connect to database

**Solutions**:
```bash
# Check database is running
docker-compose -f docker-compose.staging.yml ps postgres

# Test connection
docker-compose -f docker-compose.staging.yml exec postgres \
    pg_isready -U deepagents_staging

# Check connection string in .env.staging
echo $DATABASE_URL
```

### Slow Performance

**Causes**: Resource constraints, inefficient queries

**Solutions**:
```bash
# Increase resource limits in docker-compose.staging.yml
# Check slow queries in PostgreSQL
docker-compose -f docker-compose.staging.yml exec postgres \
    psql -U deepagents_staging -d deepagents_staging \
    -c "SELECT * FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;"
```

## Best Practices

1. **Keep staging up-to-date**: Deploy to staging daily
2. **Use realistic test data**: Mirror production data patterns
3. **Test destructive operations**: Practice backups and restores
4. **Share staging access**: Ensure team can test
5. **Document test scenarios**: Maintain test case library
6. **Monitor staging**: Use same monitoring as production
7. **Automate testing**: Run automated tests on every deploy
8. **Reset regularly**: Monthly resets prevent data drift
9. **Test failure scenarios**: Practice incident response
10. **Version control changes**: Track all configuration changes

## Environment Variables Reference

See `.env.staging.example` for full list of variables.

**Critical Variables**:
- `POSTGRES_PASSWORD`: Database password (unique from production)
- `SECRET_KEY`: JWT secret (unique from production)
- `ANTHROPIC_API_KEY`: API key for Claude
- `ALLOWED_ORIGINS`: CORS origins (include localhost)
- `DEBUG`: Set to `True` for verbose logging
- `SEED_TEST_DATA`: Set to `True` to populate test data

## Additional Resources

- [Deployment Guide](DEPLOYMENT.md)
- [Production Checklist](PRODUCTION_CHECKLIST.md)
- [Monitoring Guide](MONITORING.md)
- [Runbook](RUNBOOK.md)
