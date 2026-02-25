# SuperAI Platform — Security Policy

> Version 1.0 | Classification: Internal

---

## 1. Authentication

### 1.1 JWT Token Configuration

| Parameter | Value | Notes |
|-----------|-------|-------|
| Algorithm | HS256 / RS256 | RS256 for production |
| Access Token TTL | 30 minutes | Short-lived |
| Refresh Token TTL | 7 days | Stored in HttpOnly cookie |
| Issuer | `superai-platform` | Validated on every request |

### 1.2 Password Policy

- Minimum 12 characters
- Must contain: uppercase, lowercase, digit, special character
- Bcrypt hashing with cost factor 12
- Password history: last 5 passwords cannot be reused
- Account lockout after 5 failed attempts (15-minute cooldown)

---

## 2. Authorization (RBAC)

### 2.1 Role Hierarchy

| Role | Permissions |
|------|------------|
| `viewer` | Read-only access to public endpoints |
| `researcher` | Execute quantum/AI/scientific jobs, manage own data |
| `operator` | All researcher permissions + system monitoring |
| `admin` | Full system access including user management, config, audit logs |

### 2.2 Endpoint Protection Matrix

| Endpoint Group | viewer | researcher | operator | admin |
|---------------|--------|-----------|----------|-------|
| `/health` | ✅ | ✅ | ✅ | ✅ |
| `/users` (own) | ✅ | ✅ | ✅ | ✅ |
| `/users` (all) | ❌ | ❌ | ✅ | ✅ |
| `/quantum/*` | ❌ | ✅ | ✅ | ✅ |
| `/ai/*` | ❌ | ✅ | ✅ | ✅ |
| `/scientific/*` | ❌ | ✅ | ✅ | ✅ |
| `/admin/*` | ❌ | ❌ | ❌ | ✅ |

---

## 3. Network Security

### 3.1 TLS Configuration
- Minimum TLS 1.2, prefer TLS 1.3
- Strong cipher suites only (ECDHE+AESGCM)
- HSTS enabled with 1-year max-age
- Certificate rotation every 90 days (Let's Encrypt / cert-manager)

### 3.2 CORS Policy
```python
ALLOWED_ORIGINS = ["https://app.superai.example.com"]
ALLOWED_METHODS = ["GET", "POST", "PUT", "DELETE"]
ALLOWED_HEADERS = ["Authorization", "Content-Type"]
ALLOW_CREDENTIALS = True
```

### 3.3 Rate Limiting
- Per-IP: 100 requests/minute (unauthenticated)
- Per-User: 300 requests/minute (authenticated)
- Per-Endpoint: Configurable per route
- Response: 429 Too Many Requests with `Retry-After` header

---

## 4. Data Protection

### 4.1 Encryption
- **At Rest**: AES-256 for sensitive fields (API keys, tokens)
- **In Transit**: TLS 1.3 for all connections
- **Database**: PostgreSQL SSL mode `verify-full`
- **Redis**: TLS-enabled connections in production

### 4.2 Sensitive Data Handling
- PII fields are encrypted before storage
- API keys are hashed (SHA-256) and only prefix is stored in plain text
- Logs are sanitized — no passwords, tokens, or PII in log output
- Database backups are encrypted with AES-256

---

## 5. Secret Management

### 5.1 Development
- `.env` file (git-ignored) for local secrets
- `.env.example` contains only placeholder values

### 5.2 Production
- Kubernetes Secrets (encrypted at rest via etcd encryption)
- Optional: HashiCorp Vault integration for dynamic secrets
- Secret rotation policy: every 90 days
- No secrets in Docker images, environment variables, or source code

---

## 6. Vulnerability Management

### 6.1 Automated Scanning
- **SAST**: Bandit (Python security linter) in CI pipeline
- **Dependency Scanning**: `pip-audit` for known CVEs
- **Container Scanning**: Trivy for Docker image vulnerabilities
- **Secret Detection**: detect-secrets pre-commit hook

### 6.2 Patch Policy
| Severity | Response Time |
|----------|--------------|
| Critical (CVSS 9.0+) | 24 hours |
| High (CVSS 7.0-8.9) | 7 days |
| Medium (CVSS 4.0-6.9) | 30 days |
| Low (CVSS < 4.0) | Next release |

---

## 7. Reporting Security Issues

If you discover a security vulnerability, please report it responsibly:

- **Email**: security@superai.example.com
- **Do NOT** open a public GitHub issue
- Include: description, reproduction steps, potential impact
- Expected response: acknowledgment within 24 hours, fix timeline within 72 hours