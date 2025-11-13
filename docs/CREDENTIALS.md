# Credentials Management Guide

**DeepAgents Control Platform** - Secure credential management for all services

⚠️ **CRITICAL SECURITY**: Change ALL default credentials before deploying to production!

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Services Overview](#services-overview)
3. [Credential Generation](#credential-generation)
4. [PostgreSQL Database](#postgresql-database)
5. [Redis Cache](#redis-cache)
6. [Grafana Monitoring](#grafana-monitoring)
7. [JWT Secrets](#jwt-secrets)
8. [Credential Encryption](#credential-encryption)
9. [Rotation Schedule](#rotation-schedule)
10. [Emergency Procedures](#emergency-procedures)

---

## Quick Start

### 🚨 Before First Deployment

```bash
# 1. Copy environment template
cp infrastructure/.env.prod.example infrastructure/.env.prod

# 2. Generate strong passwords
./infrastructure/scripts/generate-credentials.sh

# 3. Edit .env.prod with generated credentials
nano infrastructure/.env.prod

# 4. Secure the file
chmod 600 infrastructure/.env.prod
```

### ⚠️ Default Credentials (MUST CHANGE)

| Service | Default Username | Default Password | Location |
|---------|-----------------|------------------|----------|
| **PostgreSQL** | `deepagents` | `dev_password_change_in_production` | `docker-compose.yml` |
| **Redis** | *(no user)* | `changeme_use_strong_password_here` | `redis/redis-ssl.conf` |
| **Grafana** | `admin` | `admin` | `monitoring/docker-compose.monitoring.yml` |

---

## Services Overview

### Critical Services (External Access)

1. **PostgreSQL** (Port 5432)
   - Stores all application data
   - User account information
   - Agent configurations
   - Execution history
   - **Risk Level**: CRITICAL

2. **Redis** (Port 6379/6380)
   - Caches session data
   - Stores account lockout information
   - Rate limiting counters
   - **Risk Level**: HIGH

3. **Grafana** (Port 3000)
   - Admin dashboard
   - Metrics visualization
   - User management
   - **Risk Level**: MEDIUM

### Internal Services (No Direct Access)

4. **Prometheus** - No authentication (internal only)
5. **Alertmanager** - No authentication (internal only)
6. **Exporters** - No authentication (internal only)

---

## Credential Generation

### Automated Generation (Recommended)

```bash
# Generate all credentials automatically
./infrastructure/scripts/generate-credentials.sh
```

This script creates:
- 32-character PostgreSQL password
- 64-character Redis password
- 24-character Grafana password
- 64-character JWT secret
- 44-character encryption key
- Outputs to `.env.prod.generated`

### Manual Generation

#### PostgreSQL Password
```bash
# 32+ characters, alphanumeric + symbols
openssl rand -base64 24
# Example: jK7mN4pQ9rS2tU6vW8xY0zA1bC3dE5fG
```

#### Redis Password
```bash
# 64+ characters for Redis
openssl rand -base64 48
# Example: vW8xY0zA1bC3dE5fGjK7mN4pQ9rS2tU6vW8xY0zA1bC3dE5fGjK7mN4pQ9rS2tU6==
```

#### Grafana Password
```bash
# 24+ characters, alphanumeric + symbols
openssl rand -base64 18
# Example: pQ9rS2tU6vW8xY0zA1bC3d==
```

#### JWT Secret Key
```bash
# 64-character hex string
openssl rand -hex 32
# Example: a1b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef123456
```

#### Credential Encryption Key (Fernet)
```bash
# Fernet key for encrypting external tool credentials
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
# Example: gAAAAAB... (44 characters)
```

---

## PostgreSQL Database

### Configuration Location

**Development**: `infrastructure/docker-compose.yml`
```yaml
environment:
  POSTGRES_USER: deepagents
  POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}  # From .env file
```

**Production**: `infrastructure/docker-compose.prod.yml`
```yaml
environment:
  POSTGRES_USER: deepagents
  POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}  # From .env.prod file
```

### Connection String Format

```bash
# Without SSL
DATABASE_URL=postgresql+asyncpg://deepagents:YOUR_PASSWORD@localhost:5432/deepagents_prod

# With SSL (Recommended for production)
DATABASE_URL=postgresql+asyncpg://deepagents:YOUR_PASSWORD@localhost:5432/deepagents_prod?sslmode=require
```

### Changing PostgreSQL Password

#### Step 1: Update Environment Variable
```bash
# Edit .env.prod
POSTGRES_PASSWORD=your_new_strong_password_here
```

#### Step 2: Update Database
```bash
# Connect to PostgreSQL
docker exec -it deepagents-postgres psql -U deepagents

# Change password
ALTER USER deepagents WITH PASSWORD 'your_new_strong_password_here';

# Exit
\q
```

#### Step 3: Restart Services
```bash
docker-compose -f docker-compose.prod.yml restart
```

### Security Best Practices

- ✅ Use passwords of 32+ characters
- ✅ Include uppercase, lowercase, digits, symbols
- ✅ Enable SSL/TLS (see `docs/DATABASE_SSL_SETUP.md`)
- ✅ Rotate password every 90 days
- ✅ Never commit passwords to git
- ✅ Use different passwords per environment
- ❌ Don't use dictionary words
- ❌ Don't reuse passwords from other systems

---

## Redis Cache

### Configuration Location

**Development**: Uses default Redis (no password)

**Production**: `infrastructure/redis/redis-ssl.conf`
```ini
requirepass YOUR_REDIS_PASSWORD_HERE
```

### Connection String Format

```bash
# Without password (development)
REDIS_URL=redis://localhost:6379

# With password (production)
REDIS_URL=redis://:YOUR_PASSWORD@localhost:6379

# With SSL/TLS (recommended)
REDIS_URL=rediss://:YOUR_PASSWORD@localhost:6380?ssl_cert_reqs=required
```

### Changing Redis Password

#### Step 1: Update Configuration
```bash
# Edit infrastructure/redis/redis-ssl.conf
requirepass your_new_strong_password_here
```

#### Step 2: Update Environment Variable
```bash
# Edit backend/.env or infrastructure/.env.prod
REDIS_PASSWORD=your_new_strong_password_here
REDIS_URL=redis://:your_new_strong_password_here@redis:6379
```

#### Step 3: Restart Redis
```bash
docker-compose -f docker-compose.prod.yml restart redis
```

### Security Best Practices

- ✅ Use passwords of 64+ characters
- ✅ Include random characters (base64 encoded)
- ✅ Enable TLS (port 6380)
- ✅ Disable dangerous commands (FLUSHDB, KEYS, CONFIG)
- ✅ Rotate password every 60 days
- ❌ Don't expose Redis port publicly (use internal network)

---

## Grafana Monitoring

### Configuration Location

**Monitoring Stack**: `infrastructure/monitoring/docker-compose.monitoring.yml`
```yaml
environment:
  GF_SECURITY_ADMIN_USER: ${GRAFANA_ADMIN_USER:-admin}
  GF_SECURITY_ADMIN_PASSWORD: ${GRAFANA_ADMIN_PASSWORD:-admin}
```

### Default Credentials

⚠️ **CRITICAL**: Change immediately on first login!

- **Username**: `admin`
- **Password**: `admin`

### Changing Grafana Password

#### Option 1: Via Environment Variable (Recommended)
```bash
# Edit .env.prod or monitoring/.env
GRAFANA_ADMIN_USER=your_admin_username
GRAFANA_ADMIN_PASSWORD=your_strong_password_here

# Restart Grafana
docker-compose -f monitoring/docker-compose.monitoring.yml restart grafana
```

#### Option 2: Via Web Interface
1. Login to Grafana: http://localhost:3000
2. Click profile icon (bottom left)
3. Go to "Change Password"
4. Enter current password: `admin`
5. Enter new strong password
6. Click "Change Password"

#### Option 3: Via CLI
```bash
# Reset admin password
docker exec -it deepagents-grafana grafana-cli admin reset-admin-password YOUR_NEW_PASSWORD
```

### Security Best Practices

- ✅ Change default `admin` username
- ✅ Use passwords of 24+ characters
- ✅ Enable HTTPS (reverse proxy)
- ✅ Disable anonymous access in production
- ✅ Set up SSO/OAuth if available
- ✅ Rotate password every 90 days
- ❌ Don't use default `admin/admin`
- ❌ Don't expose port 3000 publicly (use reverse proxy)

---

## JWT Secrets

### Backend Secret Key

**Location**: `backend/.env` or `infrastructure/.env.prod`

```bash
# Generate with:
SECRET_KEY=$(openssl rand -hex 32)

# Example:
SECRET_KEY=a1b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef123456
```

### Purpose

- Signs JWT access tokens
- Validates token authenticity
- Prevents token forgery

### Changing JWT Secret

⚠️ **WARNING**: Changing this invalidates ALL existing user sessions!

```bash
# 1. Generate new secret
NEW_SECRET=$(openssl rand -hex 32)

# 2. Update .env.prod
SECRET_KEY=$NEW_SECRET

# 3. Restart backend
docker-compose -f docker-compose.prod.yml restart backend

# 4. All users must re-login
```

### Security Best Practices

- ✅ Use 64-character hex strings
- ✅ Never commit to version control
- ✅ Use different secrets per environment
- ✅ Rotate every 6-12 months
- ❌ Don't share secrets between environments
- ❌ Don't use short or predictable secrets

---

## Credential Encryption

### Encryption Key (Fernet)

**Location**: `backend/.env` or `infrastructure/.env.prod`

```bash
# Generate with:
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Example:
CREDENTIAL_ENCRYPTION_KEY=gAAAAABf... (44 characters)
```

### Purpose

- Encrypts external tool credentials (PostgreSQL, GitLab, Elasticsearch)
- Protects sensitive API keys
- Enables secure credential storage

### Changing Encryption Key

⚠️ **WARNING**: Changing this makes existing encrypted credentials unreadable!

**Migration Required**:
1. Decrypt all external tool credentials with old key
2. Update encryption key
3. Re-encrypt all credentials with new key
4. Or: Ask users to re-enter credentials

```bash
# Migration script (if implemented)
python backend/scripts/rotate_encryption_key.py \
  --old-key="OLD_FERNET_KEY" \
  --new-key="NEW_FERNET_KEY"
```

### Security Best Practices

- ✅ Use Fernet-generated keys
- ✅ Store separately from encrypted data
- ✅ Backup old key before rotation
- ✅ Rotate every 12 months
- ❌ Don't lose the encryption key (data will be unrecoverable)

---

## Rotation Schedule

### Recommended Password Rotation

| Service | Frequency | Priority |
|---------|-----------|----------|
| PostgreSQL | 90 days | CRITICAL |
| Redis | 60 days | HIGH |
| Grafana | 90 days | MEDIUM |
| JWT Secret | 6-12 months | HIGH |
| Encryption Key | 12 months | CRITICAL |

### Rotation Checklist

- [ ] Generate new strong password/secret
- [ ] Update configuration files
- [ ] Update environment variables
- [ ] Restart affected services
- [ ] Test connectivity
- [ ] Update documentation
- [ ] Notify team members
- [ ] Archive old credentials securely

---

## Emergency Procedures

### Suspected Credential Compromise

#### Immediate Actions (Within 5 minutes)

1. **Isolate System**
   ```bash
   # Stop all services
   docker-compose -f docker-compose.prod.yml down
   ```

2. **Disable External Access**
   ```bash
   # Block ports with firewall
   sudo ufw deny 5432
   sudo ufw deny 6379
   sudo ufw deny 3000
   ```

3. **Review Access Logs**
   ```bash
   # Check PostgreSQL logs
   docker logs deepagents-postgres | grep "authentication failed"

   # Check application logs
   docker logs deepagents-backend | grep "unauthorized"
   ```

#### Recovery Actions (Within 1 hour)

4. **Rotate ALL Credentials**
   ```bash
   # Generate new credentials
   ./infrastructure/scripts/generate-credentials.sh

   # Apply new credentials
   ./infrastructure/scripts/apply-new-credentials.sh
   ```

5. **Force User Re-authentication**
   ```bash
   # Clear Redis sessions
   docker exec -it deepagents-redis redis-cli FLUSHDB

   # Restart backend (invalidates JWT tokens)
   docker-compose -f docker-compose.prod.yml restart backend
   ```

6. **Audit User Accounts**
   ```bash
   # Connect to database
   docker exec -it deepagents-postgres psql -U deepagents

   # List all users
   SELECT id, username, email, created_at, updated_at FROM users;

   # Disable suspicious accounts
   UPDATE users SET is_active = false WHERE username = 'suspicious_user';
   ```

### Lost/Forgotten Credentials

#### PostgreSQL Password Recovery

```bash
# 1. Edit pg_hba.conf to allow passwordless local connections
docker exec -it deepagents-postgres sed -i 's/md5/trust/g' /var/lib/postgresql/data/pg_hba.conf

# 2. Restart PostgreSQL
docker-compose restart postgres

# 3. Reset password
docker exec -it deepagents-postgres psql -U deepagents -c "ALTER USER deepagents WITH PASSWORD 'new_password';"

# 4. Restore pg_hba.conf
docker exec -it deepagents-postgres sed -i 's/trust/md5/g' /var/lib/postgresql/data/pg_hba.conf

# 5. Restart PostgreSQL
docker-compose restart postgres
```

#### Grafana Password Reset

```bash
# Reset admin password
docker exec -it deepagents-grafana grafana-cli admin reset-admin-password NEW_PASSWORD
```

#### Redis Password Reset

```bash
# 1. Edit redis.conf, comment out requirepass
docker exec -it deepagents-redis sed -i 's/requirepass/# requirepass/' /etc/redis/redis.conf

# 2. Restart Redis
docker-compose restart redis

# 3. Set new password via CLI
docker exec -it deepagents-redis redis-cli CONFIG SET requirepass "new_password"

# 4. Uncomment requirepass in config
docker exec -it deepagents-redis sed -i 's/# requirepass/requirepass/' /etc/redis/redis.conf

# 5. Restart Redis
docker-compose restart redis
```

---

## Security Checklist

### Pre-Production Deployment

- [ ] All default passwords changed
- [ ] Strong passwords generated (32+ chars)
- [ ] Environment variables set in .env.prod
- [ ] .env.prod has 600 permissions (chmod 600)
- [ ] .env.prod added to .gitignore
- [ ] SSL/TLS enabled for PostgreSQL
- [ ] TLS enabled for Redis (port 6380)
- [ ] Grafana default admin credentials changed
- [ ] JWT secret key generated and set
- [ ] Credential encryption key generated
- [ ] Password rotation schedule documented
- [ ] Backup encryption key stored securely
- [ ] Emergency procedures tested

### Monthly Review

- [ ] Review access logs for suspicious activity
- [ ] Check for failed authentication attempts
- [ ] Verify all services using strong credentials
- [ ] Test credential rotation procedures
- [ ] Update rotation schedule documentation

### Quarterly Actions

- [ ] Rotate PostgreSQL password
- [ ] Rotate Grafana password
- [ ] Audit user accounts in database
- [ ] Review and update security policies

---

## Support and Resources

### Internal Documentation

- [DATABASE_SSL_SETUP.md](./DATABASE_SSL_SETUP.md) - PostgreSQL and Redis SSL/TLS setup
- [PRODUCTION_CHECKLIST.md](../infrastructure/PRODUCTION_CHECKLIST.md) - Pre-deployment checklist
- [SECURITY_AUDIT_REPORT.md](../SECURITY_AUDIT_REPORT.md) - Security audit findings

### External Resources

- [PostgreSQL Security](https://www.postgresql.org/docs/current/auth-password.html)
- [Redis Security](https://redis.io/topics/security)
- [Grafana Security](https://grafana.com/docs/grafana/latest/administration/security/)
- [OWASP Password Storage](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html)

### Emergency Contacts

- **Security Team**: security@your-organization.com
- **DevOps Team**: devops@your-organization.com
- **On-Call**: pagerduty/oncall-link

---

**Last Updated**: 2025-01-13
**Version**: 1.0.0
**Maintainer**: DevOps Team
