# DeepAgents Control Platform - Infrastructure

This directory contains all infrastructure configuration and deployment scripts for production deployment.

## Directory Structure

```
infrastructure/
├── docker-compose.yml              # Development environment
├── docker-compose.prod.yml         # Production environment
├── .env.prod.example               # Production environment template
├── DEPLOYMENT.md                   # Comprehensive deployment guide
├── PRODUCTION_CHECKLIST.md         # Production readiness checklist
├── nginx/                          # Nginx reverse proxy configuration
│   ├── nginx.conf                  # Main nginx configuration
│   └── ssl.conf                    # SSL/TLS configuration
├── postgres/                       # PostgreSQL configuration
│   ├── postgresql.conf             # Production PostgreSQL settings
│   └── init/                       # Database initialization scripts
│       └── 01-init.sql             # Initial database setup
├── scripts/                        # Deployment and maintenance scripts
│   ├── deploy.sh                   # Automated deployment script
│   ├── backup.sh                   # Database backup script
│   └── restore.sh                  # Database restore script
├── ssl/                            # SSL certificates (not in git)
│   ├── certs/                      # Certificate files
│   └── certbot-www/                # Let's Encrypt challenge files
└── backups/                        # Database backups (not in git)
```

## Quick Start

### Development Environment

```bash
# Start development services (PostgreSQL + Redis)
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f
```

### Production Deployment

**Prerequisites:**
- Server with Docker and Docker Compose installed
- Domain name with DNS configured
- SSL certificate (Let's Encrypt recommended)

**Initial Setup:**

1. **Configure Environment:**
   ```bash
   cp .env.prod.example .env.prod
   # Edit .env.prod with production values
   nano .env.prod
   ```

2. **Set Up SSL:**
   ```bash
   # Option 1: Let's Encrypt (recommended)
   # See DEPLOYMENT.md for detailed instructions

   # Option 2: Custom certificate
   cp your-cert.pem ssl/certs/fullchain.pem
   cp your-key.pem ssl/certs/privkey.pem
   ```

3. **Deploy:**
   ```bash
   ./scripts/deploy.sh
   ```

For detailed instructions, see [DEPLOYMENT.md](DEPLOYMENT.md).

## Configuration Files

### docker-compose.yml (Development)

Services:
- **postgres**: PostgreSQL 17 database
- **redis**: Redis 7.4 cache

Exposed ports:
- PostgreSQL: 5432
- Redis: 6379

### docker-compose.prod.yml (Production)

Services:
- **postgres**: PostgreSQL 17 with production configuration
- **redis**: Redis 7.4 with AOF persistence
- **backend**: FastAPI application
- **frontend**: React application (served by nginx)
- **nginx**: Reverse proxy with SSL termination
- **certbot**: Let's Encrypt certificate management

Exposed ports:
- HTTP: 80 (redirects to HTTPS)
- HTTPS: 443

### Environment Variables

Required variables in `.env.prod`:

```bash
# Database
POSTGRES_DB=deepagents_prod
POSTGRES_USER=deepagents
POSTGRES_PASSWORD=<strong-password>

# Security
SECRET_KEY=<generated-secret>
ACCESS_TOKEN_EXPIRE_MINUTES=30

# API Keys
ANTHROPIC_API_KEY=<your-api-key>
OPENAI_API_KEY=<your-api-key>

# CORS
ALLOWED_ORIGINS=https://yourdomain.com

# Workers
BACKEND_WORKERS=4
```

See `.env.prod.example` for all available options.

## Scripts

### deploy.sh

Automated deployment script with zero-downtime deployment.

```bash
# Standard deployment
./scripts/deploy.sh

# Skip backup
./scripts/deploy.sh --no-backup

# Skip migrations
./scripts/deploy.sh --skip-migrations

# Force (skip confirmations)
./scripts/deploy.sh --force
```

Features:
- Environment validation
- Automatic backups
- Git pull (if in repo)
- Docker image builds
- Database migrations
- Health checks
- Rollback capability

### backup.sh

Database backup script with S3 upload support.

```bash
# Create backup
./scripts/backup.sh

# Upload to S3
./scripts/backup.sh --upload-s3

# Custom retention
./scripts/backup.sh --retention-days 30
```

Features:
- PostgreSQL full dump
- Redis RDB snapshot
- Compression (gzip)
- Automatic cleanup
- S3 upload (optional)
- Backup manifest

**Automated Backups:**

Add to crontab:
```bash
# Daily at 2 AM
0 2 * * * cd /opt/deepagents/infrastructure && ./scripts/backup.sh --upload-s3
```

### restore.sh

Database restore script with safety backup.

```bash
# List backups
ls backups/

# Restore from backup
./scripts/restore.sh 20240101_120000

# Restore only PostgreSQL
./scripts/restore.sh 20240101_120000 --postgres-only

# Force restore
./scripts/restore.sh 20240101_120000 --force
```

Features:
- Safety backup before restore
- PostgreSQL database restore
- Redis data restore
- Health checks
- Service restart

## Nginx Configuration

### nginx.conf

Main reverse proxy configuration with:
- SSL/TLS termination
- Reverse proxy to backend API
- WebSocket support for execution streaming
- Rate limiting (100 req/min for API, 5 req/min for auth)
- Gzip compression
- Security headers
- Static file caching

### ssl.conf

Modern SSL/TLS configuration with:
- TLS 1.2 and 1.3 only
- Strong cipher suites
- HSTS header (1 year)
- OCSP stapling
- Session caching

**SSL Test:** [SSL Labs](https://www.ssllabs.com/ssltest/)

## PostgreSQL Configuration

### postgresql.conf

Production-optimized settings for 4GB RAM server:
- `shared_buffers = 1GB` (25% of RAM)
- `effective_cache_size = 2560MB` (65% of RAM)
- `work_mem = 10MB`
- `maintenance_work_mem = 256MB`
- Connection pooling support
- Query performance monitoring
- Autovacuum configuration
- Logging for slow queries

Adjust settings based on your server resources.

### init/01-init.sql

Initial database setup:
- Enable required extensions (pg_stat_statements, uuid-ossp, pgcrypto)
- Set permissions
- Database initialization logging

## Monitoring

### View Logs

```bash
# All services
docker-compose -f docker-compose.prod.yml logs -f

# Specific service
docker-compose -f docker-compose.prod.yml logs -f backend

# Last 100 lines
docker-compose -f docker-compose.prod.yml logs --tail=100 backend
```

### Resource Usage

```bash
# Container stats
docker stats

# Disk usage
docker system df

# Database size
docker-compose -f docker-compose.prod.yml exec postgres \
  psql -U deepagents -d deepagents_prod \
  -c "SELECT pg_size_pretty(pg_database_size('deepagents_prod'));"
```

### Health Checks

```bash
# Backend health
curl https://yourdomain.com/health

# All services
docker-compose -f docker-compose.prod.yml ps
```

## Troubleshooting

### Common Issues

**Service won't start:**
```bash
docker-compose -f docker-compose.prod.yml logs service-name
docker-compose -f docker-compose.prod.yml restart service-name
```

**Database connection failed:**
```bash
# Check database is running
docker-compose -f docker-compose.prod.yml ps postgres

# Test connection
docker-compose -f docker-compose.prod.yml exec postgres \
  psql -U deepagents -d deepagents_prod -c "SELECT 1;"
```

**SSL certificate issues:**
```bash
# Check certificate
openssl x509 -in ssl/certs/fullchain.pem -text -noout

# Renew Let's Encrypt
docker-compose -f docker-compose.prod.yml run --rm certbot renew
```

For more troubleshooting, see [DEPLOYMENT.md](DEPLOYMENT.md#troubleshooting).

## Security Best Practices

- ✅ Use strong passwords (min 32 characters)
- ✅ Enable HTTPS only (no HTTP)
- ✅ Configure CORS with specific origins
- ✅ Enable rate limiting
- ✅ Regular security updates
- ✅ Automated backups
- ✅ Restrict database access
- ✅ Use non-root users in containers
- ✅ Monitor logs for suspicious activity
- ✅ Regular security audits

See [PRODUCTION_CHECKLIST.md](PRODUCTION_CHECKLIST.md) for complete checklist.

## Documentation

- **[DEPLOYMENT.md](DEPLOYMENT.md)**: Comprehensive deployment guide
- **[PRODUCTION_CHECKLIST.md](PRODUCTION_CHECKLIST.md)**: Production readiness checklist

## Support

For issues and questions:
1. Check [DEPLOYMENT.md](DEPLOYMENT.md#troubleshooting)
2. Review service logs
3. Check [GitHub issues](https://github.com/your-repo/issues)
4. Create new issue with logs and configuration

## License

[Your License Here]
