# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 1.0.x   | ✅        |
| < 1.0   | ❌        |

## Reporting a Vulnerability

1. **Do NOT** open a public issue for security vulnerabilities
2. Use [GitHub Security Advisories](https://github.com/indestructibleorg/indestructibleeco/security/advisories/new)
3. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Impact assessment
   - Suggested fix (if any)

## Security Measures

### Dependencies

- All dependencies pinned to specific versions
- Trivy scanning for CRITICAL and HIGH vulnerabilities
- CycloneDX SBOM at `sbom.json`

### Infrastructure

- OPA policies in `policy/` for .qyaml governance
- Network policies for namespace isolation
- mTLS between services
- RBAC with least-privilege

### CI/CD

- All GitHub Actions pinned to SHA
- Docker images from `ghcr.io/indestructibleorg/*`
- Automated security scanning in CI pipeline

### Configuration

- All secrets via environment variables (`ECO_*` prefix)
- No hardcoded credentials
- `.env.example` for reference (no real values)

## Contact

security@autoecoops.io
