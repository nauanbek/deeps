# Critical Issues Report - DeepAgents Control Platform

**Scan Date:** November 25, 2025
**Severity Threshold:** CRITICAL and HIGH only
**Total Issues Found:** 10

---

## Executive Summary

A deep security and stability scan of the DeepAgents Control Platform revealed **10 critical issues** that require immediate attention before production deployment. These issues could lead to:

- **Security breaches** (credential theft, unauthorized access)
- **Data loss** (backup failures, data corruption)
- **Service outages** (memory exhaustion, authentication bypass)

---

## Top 10 Critical Issues

### 1. WebSocket Missing JWT Authentication
**Severity:** 🔴 CRITICAL
**File:** `frontend/src/hooks/useExecutionWebSocket.ts:26-75`
**Category:** Security - Authentication Bypass

**Issue:** WebSocket connections are established without sending JWT authentication token. The hook connects but never authenticates.

```typescript
// Line 30-31: Creates WebSocket without authentication
const ws = new WebSocket(wsUrl);
ws.onopen = () => {
  setIsConnected(true);  // Never sends token!
};
```

**Impact:**
- Unauthenticated access to real-time execution streams
- Potential access to other users' execution data
- Complete bypass of authentication on WebSocket endpoints

**Fix:**
```typescript
ws.onopen = () => {
  const token = localStorage.getItem('auth_token');
  if (token) {
    ws.send(JSON.stringify({ type: 'auth', token }));
  }
  setIsConnected(true);
};
```

---

### 2. Redis Failure Disables Account Lockout Protection
**Severity:** 🔴 CRITICAL
**File:** `backend/services/lockout_service.py:84-87`
**Category:** Security - Authentication Bypass

**Issue:** When Redis is unavailable, account lockout protection is completely disabled, allowing unlimited brute force attempts.

```python
async def is_locked(self, username: str) -> bool:
    redis_client = await self._get_redis()
    if redis_client is None:
        return False  # Allows unlimited login attempts!
```

**Impact:**
- Brute force attacks succeed when Redis is down
- Credential stuffing attacks unblocked
- Complete bypass of security control during maintenance

**Fix:** Implement fail-secure behavior - deny logins or use database fallback when Redis unavailable.

---

### 3. PostgreSQL Password Not URL-Encoded (Credential Exposure)
**Severity:** 🔴 CRITICAL
**File:** `backend/langchain_tools/postgresql_tool.py:246`
**Category:** Security - Credential Exposure

**Issue:** Database passwords are interpolated directly into connection URLs without encoding.

```python
url = f"postgresql://{username}:{password}@{host}:{port}/{database}"
```

**Impact:**
- Passwords with special characters break connections
- Plaintext passwords appear in logs and error messages
- Credential leak through SQLAlchemy debug output

**Fix:**
```python
from urllib.parse import quote
url = f"postgresql://{quote(username, safe='')}:{quote(password, safe='')}@{host}:{port}/{database}"
```

---

### 4. N+1 Query Memory Exhaustion in Analytics
**Severity:** 🔴 CRITICAL
**File:** `backend/services/analytics_service.py:215-226`
**Category:** Performance - Memory Exhaustion

**Issue:** Analytics loads ALL executions into memory, then filters in Python.

```python
executions = result.scalars().all()  # Loads entire dataset
for execution in executions:         # Filters in Python
    agent_data[execution.agent_id].append(execution)
```

**Impact:**
- Server out-of-memory crashes with large datasets
- Analytics endpoints become unavailable
- Database connection timeouts

**Fix:** Use SQL aggregation with `GROUP BY` instead of loading all records.

---

### 5. Hardcoded Default Credentials Printed to Console
**Severity:** 🔴 CRITICAL
**File:** `backend/init_db.py:126`
**Category:** Security - Credential Exposure

**Issue:** Default admin password "admin123" is printed to stdout during initialization.

```python
print(f"  - User: {admin_user.username} (password: admin123)")
```

**Impact:**
- Credentials exposed in container logs
- Accessible to anyone with log access
- Cached in shell history

**Fix:** Remove password from output, generate random temporary password, force change on first login.

---

### 6. Credentials Exposed in Password Input DOM
**Severity:** 🔴 CRITICAL
**File:** `frontend/src/components/externalTools/ExternalToolConfigModal.tsx:437-442`
**Category:** Security - Credential Exposure

**Issue:** Password fields contain actual credential values in the DOM during edit mode.

```typescript
<Input
  type={showPassword[field.name] ? 'text' : 'password'}
  value={String(configValue || '')}  // Contains plain credentials!
/>
```

**Impact:**
- Credentials visible in browser DevTools
- Values cached in DOM and memory
- Password managers may log values

**Fix:** Don't populate password values in edit mode, show placeholder instead.

---

### 7. Bare Exception in Password Verification
**Severity:** 🟠 HIGH
**File:** `backend/core/security.py:32-36`
**Category:** Security - Authentication Weakness

**Issue:** All exceptions in password verification are silently caught and return False.

```python
def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        return False  # Masks all errors
```

**Impact:**
- Cannot distinguish "wrong password" from "verification failure"
- Masks potential authentication bypass attempts
- Poor security audit trail

**Fix:** Catch specific exceptions (`ValueError`, `TypeError`), log security-relevant failures.

---

### 8. No Automated Backup Validation
**Severity:** 🟠 HIGH
**File:** `infrastructure/scripts/test-backup.sh`
**Category:** Operations - Data Loss Risk

**Issue:** Backup validation is manual only, no CI/CD integration or scheduled integrity checks.

**Impact:**
- Corrupted backups discovered only when restore needed
- Silent backup failures
- Complete data loss on disaster recovery

**Fix:** Add backup validation to CI/CD, schedule integrity checks, add monitoring alerts.

---

### 9. Bare Exception Handler in Store Module
**Severity:** 🟠 HIGH
**File:** `backend/deepagents_integration/store.py:85`
**Category:** Stability - Data Corruption

**Issue:** Bare exception silently falls back to UTF-8 encoding on any error.

```python
try:
    return base64.b64decode(file_record.value)
except Exception:  # Catches everything
    return file_record.value.encode('utf-8')
```

**Impact:**
- Silent data corruption in agent memory operations
- Impossible to debug - errors are hidden
- May corrupt binary data

**Fix:** Catch specific exceptions, log errors, don't silently corrupt data.

---

### 10. Insecure Default Password in Docker-Compose
**Severity:** 🟠 HIGH
**File:** `infrastructure/docker-compose.yml:10`
**Category:** Security - Credential Exposure

**Issue:** Default database password exposed in version control.

```yaml
POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-CHANGE_ME_INSECURE_DEFAULT}
```

**Impact:**
- Database credentials exposed in repository
- Developers may accidentally use in production
- Container logs may leak password

**Fix:** Remove default value, require explicit environment variable, add startup validation.

---

## Summary Table

| # | Issue | File | Severity | Category |
|---|-------|------|----------|----------|
| 1 | WebSocket no authentication | `useExecutionWebSocket.ts` | 🔴 CRITICAL | Auth Bypass |
| 2 | Redis failure disables lockout | `lockout_service.py` | 🔴 CRITICAL | Auth Bypass |
| 3 | Password not URL-encoded | `postgresql_tool.py` | 🔴 CRITICAL | Credential Exposure |
| 4 | N+1 query memory exhaustion | `analytics_service.py` | 🔴 CRITICAL | Memory/DoS |
| 5 | Credentials printed to console | `init_db.py` | 🔴 CRITICAL | Credential Exposure |
| 6 | Credentials in DOM | `ExternalToolConfigModal.tsx` | 🔴 CRITICAL | Credential Exposure |
| 7 | Bare exception in auth | `security.py` | 🟠 HIGH | Auth Weakness |
| 8 | No backup validation | `test-backup.sh` | 🟠 HIGH | Data Loss |
| 9 | Bare exception in store | `store.py` | 🟠 HIGH | Data Corruption |
| 10 | Insecure default password | `docker-compose.yml` | 🟠 HIGH | Credential Exposure |

---

## Priority Matrix

### Immediate (Before Production)
1. WebSocket authentication (#1)
2. Redis lockout fail-secure (#2)
3. PostgreSQL password encoding (#3)
4. Credentials in console/DOM (#5, #6)

### This Sprint
5. Analytics N+1 query (#4)
6. Bare exception handlers (#7, #9)
7. Default password removal (#10)

### Next Sprint
8. Backup validation automation (#8)

---

## Estimated Fix Effort

| Issue | Effort | Files Changed |
|-------|--------|---------------|
| #1 WebSocket auth | 1-2 hours | 1 |
| #2 Redis fail-secure | 2-3 hours | 1 |
| #3 URL encoding | 30 min | 1 |
| #4 Analytics N+1 | 3-4 hours | 1 |
| #5 Console output | 30 min | 2 |
| #6 DOM credentials | 1-2 hours | 1 |
| #7 Exception handling | 1 hour | 1 |
| #8 Backup automation | 4-6 hours | 3 |
| #9 Store exceptions | 1 hour | 1 |
| #10 Default password | 30 min | 1 |

**Total Estimated Effort:** 15-20 hours

---

**Report Generated:** November 25, 2025
**Next Review:** After fixes applied
