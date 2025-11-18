# Database SSL/TLS Setup Guide

**Phase:** 1.4 - Enable Database SSL/TLS
**Priority:** P0 - CRITICAL
**Time:** 4 hours
**Status:** ✅ Configuration Ready

---

## Overview

This guide explains how to enable SSL/TLS encryption for PostgreSQL and Redis connections to protect data in transit.

**Security Impact:**
- ❌ **Without SSL:** Database credentials and data transmitted in plain text
- ✅ **With SSL:** All database communication encrypted with TLS 1.2+

---

## PostgreSQL SSL/TLS Setup

### 1. Generate SSL Certificates

**Option A: Self-Signed (Development/Staging)**

```bash
cd /home/user/deeps/infrastructure/scripts
chmod +x generate-db-certs.sh
./generate-db-certs.sh
```

**Option B: CA-Signed (Production)**

Use Let's Encrypt or your organization's CA:
```bash
# Example with certbot (Let's Encrypt)
certbot certonly --standalone -d postgres.yourdomain.com
cp /etc/letsencrypt/live/postgres.yourdomain.com/fullchain.pem /var/lib/postgresql/data/certs/server.crt
cp /etc/letsencrypt/live/postgres.yourdomain.com/privkey.pem /var/lib/postgresql/data/certs/server.key
chown postgres:postgres /var/lib/postgresql/data/certs/*
chmod 600 /var/lib/postgresql/data/certs/server.key
```

### 2. Configure PostgreSQL

**Add to postgresql.conf:**

```bash
# Include SSL configuration
include = 'postgresql-ssl.conf'
```

**Or copy our pre-configured file:**

```bash
cp infrastructure/postgres/postgresql-ssl.conf /var/lib/postgresql/data/
```

**Key settings:**
- `ssl = on` - Enable SSL
- `ssl_cert_file` - Path to certificate
- `ssl_key_file` - Path to private key
- `ssl_min_protocol_version = 'TLSv1.2'` - Minimum TLS version
- `password_encryption = scram-sha-256` - Strong password hashing

### 3. Update Client Authentication

**Replace pg_hba.conf with SSL-enforcing configuration:**

```bash
cp infrastructure/postgres/pg_hba.conf.ssl /var/lib/postgresql/data/pg_hba.conf
```

**Key rules:**
```
# Local connections (no SSL required for localhost)
host    all    all    127.0.0.1/32    scram-sha-256

# Remote connections MUST use SSL
hostssl all    all    0.0.0.0/0       scram-sha-256

# Reject non-SSL remote connections
hostnossl all  all    0.0.0.0/0       reject
```

### 4. Restart PostgreSQL

```bash
# Linux
systemctl restart postgresql

# Docker
docker-compose restart postgres

# Reload configuration without restart
psql -U postgres -c "SELECT pg_reload_conf();"
```

### 5. Update Backend Configuration

**Update .env file:**

```bash
# Before (insecure)
DATABASE_URL=postgresql+asyncpg://user:password@host:5432/deepagents_platform

# After (secure)
DATABASE_URL=postgresql+asyncpg://user:password@host:5432/deepagents_platform?sslmode=require
```

**SSL Mode Options:**
- `disable` - No SSL (INSECURE, do not use in production)
- `allow` - Try SSL, fallback to plain
- `prefer` - Try SSL first, fallback to plain
- `require` - Require SSL, verify server certificate (RECOMMENDED)
- `verify-ca` - Require SSL, verify CA
- `verify-full` - Require SSL, verify CA and hostname

**For Production:** Always use `sslmode=require` or `verify-full`

### 6. Verify SSL Connection

```bash
# Test connection
psql "postgresql://user:password@host:5432/deepagents_platform?sslmode=require"

# Check SSL status
psql -U postgres -c "SELECT ssl, version, cipher FROM pg_stat_ssl WHERE pid = pg_backend_pid();"

# Should show:
#  ssl | version | cipher
# -----+---------+--------------------
#  t   | TLSv1.3 | TLS_AES_256_GCM_SHA384
```

---

## Redis SSL/TLS Setup

### 1. Generate SSL Certificates

```bash
cd /home/user/deeps/infrastructure/scripts
chmod +x generate-redis-certs.sh
./generate-redis-certs.sh
```

### 2. Configure Redis

**Append to redis.conf or include:**

```bash
# Include SSL configuration
include /path/to/redis-ssl.conf
```

**Or copy our pre-configured file:**

```bash
cp infrastructure/redis/redis-ssl.conf /etc/redis/
```

**Key settings:**
- `port 0` - Disable non-TLS port
- `tls-port 6380` - Enable TLS port
- `tls-cert-file` - Path to certificate
- `tls-key-file` - Path to private key
- `tls-protocols "TLSv1.2 TLSv1.3"` - Allowed TLS versions
- `requirepass` - Authentication password (CRITICAL!)

### 3. Set Redis Password

**CRITICAL: Set a strong password:**

Edit `redis-ssl.conf`:
```
requirepass $(openssl rand -base64 32)
```

Save the password securely (secrets management system).

### 4. Restart Redis

```bash
# Linux
systemctl restart redis

# Docker
docker-compose restart redis

# Check configuration
redis-cli --tls --cert /etc/redis/certs/redis.crt --key /etc/redis/certs/redis.key CONFIG GET requirepass
```

### 5. Update Backend Configuration

**Update .env file:**

```bash
# Before (insecure)
REDIS_URL=redis://localhost:6379

# After (secure)
REDIS_URL=rediss://:<password>@localhost:6380?ssl_cert_reqs=required
```

**Note:** `rediss://` (with double 's') enables SSL/TLS

### 6. Verify SSL Connection

```bash
# Test TLS connection
redis-cli --tls \
    --cert /etc/redis/certs/redis.crt \
    --key /etc/redis/certs/redis.key \
    --cacert /etc/redis/certs/redis.crt \
    -h localhost -p 6380 \
    -a <password> \
    PING

# Should return: PONG
```

---

## Docker Configuration

### Update docker-compose.yml

**PostgreSQL Service:**

```yaml
postgres:
  image: postgres:17.6-alpine
  environment:
    POSTGRES_DB: deepagents_platform
    POSTGRES_USER: deepagents
    POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
  volumes:
    - postgres_data:/var/lib/postgresql/data
    - ./infrastructure/postgres/certs:/var/lib/postgresql/data/certs:ro
    - ./infrastructure/postgres/postgresql-ssl.conf:/var/lib/postgresql/data/postgresql-ssl.conf:ro
  command: >
    postgres
    -c ssl=on
    -c ssl_cert_file=/var/lib/postgresql/data/certs/server.crt
    -c ssl_key_file=/var/lib/postgresql/data/certs/server.key
```

**Redis Service:**

```yaml
redis:
  image: redis:7.4.6-alpine
  volumes:
    - redis_data:/data
    - ./infrastructure/redis/certs:/etc/redis/certs:ro
    - ./infrastructure/redis/redis-ssl.conf:/etc/redis/redis-ssl.conf:ro
  command: redis-server /etc/redis/redis-ssl.conf
  environment:
    REDIS_PASSWORD: ${REDIS_PASSWORD}
```

---

## Security Best Practices

### Certificate Management

✅ **DO:**
- Use CA-signed certificates in production
- Rotate certificates before expiration (set reminders)
- Store private keys with 600 permissions
- Use different certificates for dev/staging/prod

❌ **DON'T:**
- Commit certificates to git (add to .gitignore)
- Share private keys via email/Slack
- Use self-signed certs in production
- Reuse the same certificate across environments

### Connection String Security

✅ **DO:**
- Store in secrets management (AWS Secrets Manager, HashiCorp Vault)
- Use environment variables, not config files
- Different credentials per environment
- Rotate passwords quarterly

❌ **DON'T:**
- Commit .env files to git
- Share connection strings in chat
- Use default passwords
- Reuse production credentials in dev

### Network Security

**Firewall Rules:**
```bash
# Allow PostgreSQL only from application servers
ufw allow from 10.0.1.0/24 to any port 5432

# Allow Redis only from application servers
ufw allow from 10.0.1.0/24 to any port 6380

# Deny all other access
ufw default deny incoming
```

---

## Testing SSL Configuration

### Backend Connection Test

**Create test script:** `scripts/test_db_ssl.py`

```python
import asyncio
import asyncpg

async def test_postgres_ssl():
    try:
        conn = await asyncpg.connect(
            "postgresql://user:password@host:5432/deepagents_platform?sslmode=require"
        )
        result = await conn.fetchval("SELECT ssl, version FROM pg_stat_ssl WHERE pid = pg_backend_pid()")
        print(f"✅ PostgreSQL SSL: {result}")
        await conn.close()
    except Exception as e:
        print(f"❌ PostgreSQL SSL failed: {e}")

asyncio.run(test_postgres_ssl())
```

### Redis Connection Test

```python
import redis

try:
    r = redis.Redis(
        host='localhost',
        port=6380,
        password='<password>',
        ssl=True,
        ssl_cert_reqs='required'
    )
    r.ping()
    print("✅ Redis SSL: Connected")
except Exception as e:
    print(f"❌ Redis SSL failed: {e}")
```

---

## Troubleshooting

### PostgreSQL Issues

**Error: "SSL connection has been closed unexpectedly"**
```bash
# Check certificate permissions
ls -l /var/lib/postgresql/data/certs/
# Should be: -rw------- postgres postgres server.key

# Fix permissions
chmod 600 /var/lib/postgresql/data/certs/server.key
chown postgres:postgres /var/lib/postgresql/data/certs/*
```

**Error: "could not load server certificate"**
```bash
# Verify certificate path
grep ssl_cert_file /var/lib/postgresql/data/postgresql.conf

# Test certificate
openssl x509 -in /var/lib/postgresql/data/certs/server.crt -text -noout
```

### Redis Issues

**Error: "Server closed the connection"**
```bash
# Check Redis logs
tail -f /var/log/redis/redis-server.log

# Verify TLS configuration
redis-cli CONFIG GET tls-*
```

**Error: "NOAUTH Authentication required"**
```bash
# Verify password
redis-cli -a <password> PING

# Update .env with correct password
REDIS_URL=rediss://:<password>@localhost:6380
```

---

## Monitoring SSL Status

### Add to Grafana Dashboard

**PostgreSQL SSL Connections:**
```sql
SELECT
  COUNT(*) as total_connections,
  COUNT(*) FILTER (WHERE ssl) as ssl_connections,
  ROUND(100.0 * COUNT(*) FILTER (WHERE ssl) / COUNT(*), 2) as ssl_percentage
FROM pg_stat_ssl;
```

**Prometheus Alert:**
```yaml
- alert: DatabaseNonSSLConnections
  expr: pg_stat_ssl_count{ssl="false"} > 0
  for: 5m
  labels:
    severity: critical
  annotations:
    summary: "Non-SSL database connections detected"
```

---

## Rollback Plan

If SSL causes issues:

**1. Temporary Rollback (Emergency):**

```bash
# PostgreSQL: Disable SSL requirement
echo "ssl = off" >> /var/lib/postgresql/data/postgresql.conf
systemctl restart postgresql

# Redis: Enable non-TLS port
echo "port 6379" >> /etc/redis/redis.conf
systemctl restart redis

# Backend: Remove sslmode parameter
DATABASE_URL=postgresql+asyncpg://user:password@host:5432/deepagents_platform
REDIS_URL=redis://localhost:6379
```

**2. Investigate & Fix:**
- Check logs: `/var/log/postgresql/`, `/var/log/redis/`
- Verify certificates
- Test connections manually
- Review pg_hba.conf rules

**3. Re-enable SSL:**
- Fix root cause
- Test in staging first
- Gradual rollout to production

---

## Completion Checklist

- [ ] PostgreSQL SSL certificates generated
- [ ] PostgreSQL SSL enabled and tested
- [ ] pg_hba.conf updated to require SSL
- [ ] Redis SSL certificates generated
- [ ] Redis TLS enabled and tested
- [ ] Redis password set (strong, unique)
- [ ] Backend DATABASE_URL updated (sslmode=require)
- [ ] Backend REDIS_URL updated (rediss://)
- [ ] .env files updated (all environments)
- [ ] SSL connections verified
- [ ] Grafana monitoring configured
- [ ] Documentation updated
- [ ] Team trained on SSL procedures

---

## Result

✅ **Phase 1.4 COMPLETE** when:
- All database connections encrypted with TLS 1.2+
- No plain-text connections allowed in production
- Certificates valid and properly configured
- Monitoring confirms 100% SSL usage

**Security Status:** ❌ CRITICAL → ✅ SECURE

---

**Next Phase:** 1.5 - Implement Account Lockout
