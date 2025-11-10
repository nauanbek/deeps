# DeepAgents Control Platform - Production Deployment Guide

This guide provides comprehensive instructions for deploying the DeepAgents Control Platform to production.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Initial Setup](#initial-setup)
- [SSL/TLS Configuration](#ssltls-configuration)
- [Environment Configuration](#environment-configuration)
- [Database Initialization](#database-initialization)
- [Deployment](#deployment)
- [Post-Deployment](#post-deployment)
- [Monitoring and Logging](#monitoring-and-logging)
- [Backup and Restore](#backup-and-restore)
- [Troubleshooting](#troubleshooting)
- [Security Best Practices](#security-best-practices)

## Prerequisites

### System Requirements

**Minimum Requirements:**
- CPU: 4 cores
- RAM: 8 GB
- Disk: 50 GB SSD
- OS: Ubuntu 20.04+ / Debian 11+ / RHEL 8+ / CentOS 8+

**Recommended for Production:**
- CPU: 8 cores
- RAM: 16 GB
- Disk: 100 GB SSD
- OS: Ubuntu 22.04 LTS

### Required Software

1. **Docker** (20.10+)
   ```bash
   # Install Docker
   curl -fsSL https://get.docker.com -o get-docker.sh
   sh get-docker.sh

   # Add user to docker group
   sudo usermod -aG docker $USER
   newgrp docker
   ```

2. **Docker Compose** (2.0+)
   ```bash
   # Install Docker Compose
   sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
   sudo chmod +x /usr/local/bin/docker-compose

   # Verify installation
   docker-compose --version
   ```

3. **Git**
   ```bash
   sudo apt-get update
   sudo apt-get install -y git
   ```

4. **OpenSSL** (for generating secrets)
   ```bash
   sudo apt-get install -y openssl
   ```

5. **AWS CLI** (optional, for S3 backups)
   ```bash
   curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
   unzip awscliv2.zip
   sudo ./aws/install
   ```

### Domain and DNS

1. Register a domain name (e.g., `yourdomain.com`)
2. Configure DNS A records pointing to your server's IP:
   - `yourdomain.com` → `your.server.ip`
   - `www.yourdomain.com` → `your.server.ip`

3. Wait for DNS propagation (check with `dig yourdomain.com`)

### Firewall Configuration

```bash
# Allow HTTP (port 80) for Let's Encrypt challenges
sudo ufw allow 80/tcp

# Allow HTTPS (port 443) for secure traffic
sudo ufw allow 443/tcp

# Allow SSH (port 22) for remote access
sudo ufw allow 22/tcp

# Enable firewall
sudo ufw enable
```

## Initial Setup

### 1. Clone Repository

```bash
# Clone the repository
git clone <your-repo-url> /opt/deepagents
cd /opt/deepagents

# Checkout production branch (if applicable)
git checkout main
```

### 2. Create Required Directories

```bash
# Create SSL certificate directory
mkdir -p infrastructure/ssl/certs
mkdir -p infrastructure/ssl/certbot-www

# Create backup directory
mkdir -p infrastructure/backups

# Set proper permissions
chmod 700 infrastructure/ssl/certs
chmod 755 infrastructure/backups
```

## SSL/TLS Configuration

### Option 1: Let's Encrypt (Recommended)

**Initial Certificate Acquisition:**

```bash
cd infrastructure

# Create initial environment file
cp .env.prod.example .env.prod

# Edit .env.prod and set DOMAIN and LETSENCRYPT_EMAIL
nano .env.prod

# Start nginx temporarily to obtain certificate
docker-compose -f docker-compose.prod.yml up -d nginx

# Obtain certificate
docker-compose -f docker-compose.prod.yml run --rm certbot certonly \
  --webroot \
  --webroot-path=/var/www/certbot \
  --email ${LETSENCRYPT_EMAIL} \
  --agree-tos \
  --no-eff-email \
  -d ${DOMAIN} \
  -d www.${DOMAIN}

# Link certificates to nginx SSL directory
ln -sf /etc/letsencrypt/live/${DOMAIN}/fullchain.pem ssl/certs/fullchain.pem
ln -sf /etc/letsencrypt/live/${DOMAIN}/privkey.pem ssl/certs/privkey.pem

# Restart nginx with SSL
docker-compose -f docker-compose.prod.yml restart nginx
```

**Certificate Auto-Renewal:**

Add to crontab (`crontab -e`):
```bash
0 3 * * * cd /opt/deepagents/infrastructure && docker-compose -f docker-compose.prod.yml run --rm certbot renew && docker-compose -f docker-compose.prod.yml restart nginx
```

### Option 2: Custom SSL Certificate

```bash
# Copy your certificate files
cp your-certificate.crt infrastructure/ssl/certs/fullchain.pem
cp your-private-key.key infrastructure/ssl/certs/privkey.pem

# Set proper permissions
chmod 600 infrastructure/ssl/certs/privkey.pem
chmod 644 infrastructure/ssl/certs/fullchain.pem
```

### Option 3: Self-Signed Certificate (Development/Testing Only)

```bash
# Generate self-signed certificate (valid for 365 days)
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout infrastructure/ssl/certs/privkey.pem \
  -out infrastructure/ssl/certs/fullchain.pem \
  -subj "/C=US/ST=State/L=City/O=Organization/CN=yourdomain.com"

# Set proper permissions
chmod 600 infrastructure/ssl/certs/privkey.pem
chmod 644 infrastructure/ssl/certs/fullchain.pem
```

## Environment Configuration

### 1. Backend Configuration

```bash
cd backend

# Copy template
cp .env.prod.example .env.prod

# Generate secure SECRET_KEY
SECRET_KEY=$(openssl rand -hex 32)

# Edit configuration
nano .env.prod
```

**Required Variables:**
```bash
# Database
POSTGRES_PASSWORD=<generate-strong-password>

# Security
SECRET_KEY=<generated-from-openssl>

# AI Providers
ANTHROPIC_API_KEY=<your-anthropic-api-key>
OPENAI_API_KEY=<your-openai-api-key>

# CORS
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

### 2. Frontend Configuration

```bash
cd ../frontend

# Copy template
cp .env.prod.example .env.prod

# Edit configuration
nano .env.prod
```

**Configuration:**
```bash
REACT_APP_API_URL=/api
REACT_APP_WS_URL=/api
REACT_APP_ENV=production
```

### 3. Infrastructure Configuration

```bash
cd ../infrastructure

# Copy template
cp .env.prod.example .env.prod

# Edit configuration (should match backend config)
nano .env.prod
```

### 4. Secure Your Environment Files

```bash
# Set restrictive permissions
chmod 600 backend/.env.prod
chmod 600 frontend/.env.prod
chmod 600 infrastructure/.env.prod

# Verify they're in .gitignore
grep -q ".env.prod" ../.gitignore || echo ".env.prod" >> ../.gitignore
```

## Database Initialization

### 1. Start Database Services

```bash
cd infrastructure

# Start PostgreSQL and Redis
docker-compose -f docker-compose.prod.yml up -d postgres redis

# Wait for services to be ready
sleep 10

# Check health
docker-compose -f docker-compose.prod.yml ps
```

### 2. Run Database Migrations

```bash
# Run migrations in a temporary backend container
docker-compose -f docker-compose.prod.yml run --rm backend alembic upgrade head

# Verify migrations
docker-compose -f docker-compose.prod.yml run --rm backend alembic current
```

### 3. Create Initial Admin User (Optional)

```bash
# Connect to database
docker-compose -f docker-compose.prod.yml exec postgres \
  psql -U deepagents -d deepagents_prod

# In PostgreSQL prompt, create admin user (adjust based on your schema)
-- Example: INSERT INTO users (email, hashed_password, is_active, is_admin) VALUES (...);
```

## Deployment

### Automated Deployment (Recommended)

```bash
cd infrastructure

# Run deployment script
./scripts/deploy.sh

# With options
./scripts/deploy.sh --force  # Skip confirmations
./scripts/deploy.sh --no-backup  # Skip pre-deployment backup
./scripts/deploy.sh --skip-migrations  # Skip database migrations
```

The deployment script will:
1. Validate environment configuration
2. Create database backup
3. Pull latest code from git
4. Build Docker images
5. Run database migrations
6. Start all services
7. Perform health checks
8. Clean up old images

### Manual Deployment

```bash
cd infrastructure

# 1. Create backup
./scripts/backup.sh

# 2. Build images
docker-compose -f docker-compose.prod.yml build

# 3. Run migrations
docker-compose -f docker-compose.prod.yml run --rm backend alembic upgrade head

# 4. Start services
docker-compose -f docker-compose.prod.yml up -d

# 5. Check health
docker-compose -f docker-compose.prod.yml ps
docker-compose -f docker-compose.prod.yml logs -f
```

## Post-Deployment

### 1. Verify Services

```bash
# Check all services are running
docker-compose -f docker-compose.prod.yml ps

# Check logs
docker-compose -f docker-compose.prod.yml logs backend
docker-compose -f docker-compose.prod.yml logs frontend
docker-compose -f docker-compose.prod.yml logs nginx

# Test health endpoint
curl https://yourdomain.com/health
```

### 2. Test API

```bash
# Test API root
curl https://yourdomain.com/api/

# Test API documentation
curl https://yourdomain.com/docs

# Test WebSocket (using wscat)
npm install -g wscat
wscat -c wss://yourdomain.com/api/v1/executions/test/stream
```

### 3. Access Application

Open in browser: `https://yourdomain.com`

### 4. Monitor Resources

```bash
# View resource usage
docker stats

# View disk usage
docker system df

# View logs
docker-compose -f docker-compose.prod.yml logs -f --tail=100
```

## Monitoring and Logging

### View Logs

```bash
# All services
docker-compose -f docker-compose.prod.yml logs -f

# Specific service
docker-compose -f docker-compose.prod.yml logs -f backend

# Last 100 lines
docker-compose -f docker-compose.prod.yml logs --tail=100 backend

# Follow logs with timestamps
docker-compose -f docker-compose.prod.yml logs -f -t backend
```

### Log Rotation

Logs are automatically rotated by Docker. Configure in `/etc/docker/daemon.json`:

```json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "100m",
    "max-file": "10"
  }
}
```

Restart Docker after changes:
```bash
sudo systemctl restart docker
```

### Resource Monitoring

```bash
# Container stats
docker stats

# Disk usage
df -h
docker system df

# Database size
docker-compose -f docker-compose.prod.yml exec postgres \
  psql -U deepagents -d deepagents_prod -c "SELECT pg_size_pretty(pg_database_size('deepagents_prod'));"
```

## Backup and Restore

### Automated Backups

**Create Backup:**
```bash
cd infrastructure

# Full backup (PostgreSQL + Redis)
./scripts/backup.sh

# Upload to S3
./scripts/backup.sh --upload-s3

# Custom retention period
./scripts/backup.sh --retention-days 30
```

**Schedule Automated Backups:**

Add to crontab (`crontab -e`):
```bash
# Daily backup at 2 AM
0 2 * * * cd /opt/deepagents/infrastructure && ./scripts/backup.sh --upload-s3

# Weekly backup on Sunday at 3 AM with 30-day retention
0 3 * * 0 cd /opt/deepagents/infrastructure && ./scripts/backup.sh --upload-s3 --retention-days 30
```

### Restore from Backup

```bash
cd infrastructure

# List available backups
ls -lh backups/

# Restore from specific backup
./scripts/restore.sh 20240101_120000

# Restore only PostgreSQL
./scripts/restore.sh 20240101_120000 --postgres-only

# Force restore without prompts
./scripts/restore.sh 20240101_120000 --force
```

### Manual Database Backup

```bash
# PostgreSQL
docker-compose -f docker-compose.prod.yml exec postgres \
  pg_dump -U deepagents deepagents_prod > backup.sql

# Redis
docker-compose -f docker-compose.prod.yml exec redis redis-cli SAVE
docker cp deepagents-redis:/data/dump.rdb redis_backup.rdb
```

## Troubleshooting

### Service Won't Start

```bash
# Check service status
docker-compose -f docker-compose.prod.yml ps

# Check logs
docker-compose -f docker-compose.prod.yml logs service-name

# Restart service
docker-compose -f docker-compose.prod.yml restart service-name

# Recreate service
docker-compose -f docker-compose.prod.yml up -d --force-recreate service-name
```

### Database Connection Issues

```bash
# Check database is running
docker-compose -f docker-compose.prod.yml ps postgres

# Check database logs
docker-compose -f docker-compose.prod.yml logs postgres

# Test connection
docker-compose -f docker-compose.prod.yml exec postgres \
  psql -U deepagents -d deepagents_prod -c "SELECT 1;"

# Verify DATABASE_URL in backend
docker-compose -f docker-compose.prod.yml exec backend env | grep DATABASE_URL
```

### SSL/TLS Issues

```bash
# Check certificate validity
openssl x509 -in infrastructure/ssl/certs/fullchain.pem -text -noout

# Test SSL connection
openssl s_client -connect yourdomain.com:443 -servername yourdomain.com

# Check nginx configuration
docker-compose -f docker-compose.prod.yml exec nginx nginx -t

# Reload nginx
docker-compose -f docker-compose.prod.yml exec nginx nginx -s reload
```

### High Memory Usage

```bash
# Check container resource usage
docker stats

# Increase resource limits in docker-compose.prod.yml
# Restart services
docker-compose -f docker-compose.prod.yml restart
```

### Disk Space Issues

```bash
# Check disk usage
df -h
docker system df

# Clean up unused resources
docker system prune -a --volumes

# Remove old backups
find infrastructure/backups -mtime +30 -delete
```

### Performance Issues

```bash
# Check PostgreSQL slow queries
docker-compose -f docker-compose.prod.yml exec postgres \
  psql -U deepagents -d deepagents_prod -c \
  "SELECT query, calls, total_time, mean_time FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;"

# Monitor PostgreSQL connections
docker-compose -f docker-compose.prod.yml exec postgres \
  psql -U deepagents -d deepagents_prod -c \
  "SELECT count(*) FROM pg_stat_activity;"

# Check Redis memory
docker-compose -f docker-compose.prod.yml exec redis redis-cli INFO memory
```

## Security Best Practices

### 1. Secrets Management

- ✅ Use strong, unique passwords (min 32 characters)
- ✅ Generate SECRET_KEY with `openssl rand -hex 32`
- ✅ Store secrets in environment files with 600 permissions
- ✅ Never commit `.env.prod` files to git
- ✅ Rotate secrets regularly (every 90 days)
- ✅ Use AWS Secrets Manager or HashiCorp Vault for production

### 2. Network Security

- ✅ Use HTTPS only (HTTP redirects to HTTPS)
- ✅ Enable HSTS headers
- ✅ Configure firewall (ufw/iptables)
- ✅ Don't expose database ports externally
- ✅ Use VPN for administrative access
- ✅ Enable rate limiting in nginx

### 3. Database Security

- ✅ Use strong PostgreSQL password
- ✅ Don't use default usernames
- ✅ Enable SSL for database connections (optional)
- ✅ Regular security updates
- ✅ Limit database permissions
- ✅ Enable query logging for auditing

### 4. Container Security

- ✅ Run containers as non-root users
- ✅ Use minimal base images (alpine)
- ✅ Regular security updates
- ✅ Scan images for vulnerabilities
- ✅ Use resource limits
- ✅ Enable Docker security features (AppArmor, SELinux)

### 5. Application Security

- ✅ Enable CORS with specific origins only
- ✅ Implement rate limiting
- ✅ Use JWT with expiration
- ✅ Validate all inputs
- ✅ Regular dependency updates
- ✅ Enable security headers

### 6. Monitoring and Auditing

- ✅ Enable comprehensive logging
- ✅ Monitor failed login attempts
- ✅ Set up alerts for anomalies
- ✅ Regular security audits
- ✅ Backup encryption
- ✅ Access logs retention

### 7. Regular Maintenance

```bash
# Update system packages
sudo apt-get update && sudo apt-get upgrade -y

# Update Docker images
cd infrastructure
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d

# Update application
git pull origin main
./scripts/deploy.sh
```

## Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Nginx Documentation](https://nginx.org/en/docs/)
- [Let's Encrypt Documentation](https://letsencrypt.org/docs/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://react.dev/)

## Support

For issues and questions:
- Check the troubleshooting section above
- Review application logs
- Search existing GitHub issues
- Create a new issue with detailed information

## License

[Your License Here]
