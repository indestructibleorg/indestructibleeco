# GitHub Actions Policy

## Overview

This repository enforces strict GitHub Actions usage policies for security, reproducibility, and organizational control.

## Policy Requirements

### 1. Organization Ownership

**All GitHub Actions must be from repositories owned by `indestructibleorg`.**

❌ **NOT ALLOWED:**
```yaml
- uses: actions/checkout@v4
- uses: actions/setup-node@v4
- uses: github/codeql-action/init@v3
```

✅ **ALLOWED:**
```yaml
# Actions from indestructibleorg (when available)
- uses: indestructibleorg/checkout-action@a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0

# Better: Use manual commands
- name: Checkout
  run: |
    git clone --depth 1 https://github.com/${{ github.repository }}.git .
    git checkout ${{ github.sha }}
```

### 2. SHA Pinning

**All actions must be pinned to full-length commit SHAs (40 characters), not tags or branch names.**

❌ **NOT ALLOWED:**
```yaml
- uses: indestructibleorg/my-action@v1
- uses: indestructibleorg/my-action@main
- uses: indestructibleorg/my-action@1.0.0
```

✅ **ALLOWED:**
```yaml
- uses: indestructibleorg/my-action@a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0
```

### 3. Explicitly Blocked Actions

The following popular actions are explicitly blocked and should be replaced with manual commands:

| Blocked Action | Alternative |
|----------------|-------------|
| `actions/checkout` | Use `git clone` and `git checkout` commands |
| `actions/github-script` | Use `gh` CLI or direct API calls with `curl` |
| `actions/upload-artifact` | Use manual artifact handling or GitHub Releases API |
| `actions/download-artifact` | Use manual artifact download with `gh` CLI or API |
| `actions/setup-node` | Use container with pre-installed Node.js |
| `actions/setup-python` | Use container with pre-installed Python |
| `actions/cache` | Use manual caching or BuildKit cache mounts |
| `github/codeql-action/*` | Use manual CodeQL CLI setup and execution |

## Rationale

### Why Restrict to Organization Actions?

1. **Supply Chain Security**: External actions can be compromised or introduce malicious code
2. **Consistency**: Ensures all workflows use approved, audited actions
3. **Control**: Organization maintains full control over action behavior and updates
4. **Compliance**: Meets enterprise security requirements for software supply chain

### Why Require SHA Pinning?

1. **Immutability**: Tags and branches can be moved or deleted
2. **Reproducibility**: Same SHA always refers to exact same code
3. **Security**: Prevents tag poisoning attacks
4. **Auditability**: Clear trail of exactly what code ran in each workflow

## Implementation

### Current Workflows

Current workflows in this repository use manual commands instead of external actions:

```yaml
# Example: ci.yaml
- name: Checkout
  run: |
    git clone --depth 1 https://github.com/${{ github.repository }}.git .
    git checkout ${{ github.sha }}

- name: Python compile check
  run: |
    python3 -m py_compile backend/ai/src/app.py
    # ... more compile checks
```

### Validation

Policy compliance is enforced by:

1. **CI Validator Engine**: `tools/ci-validator/validate.py`
   - Runs on every PR and push
   - Validates all workflow files
   - Reports violations with line numbers

2. **Standalone Validator**: `tools/ci-validator/validate_actions_policy.py`
   - Can be run independently
   - Useful for pre-commit checks

3. **Policy Configuration**: `.github/allowed-actions.yaml`
   - Defines policy rules
   - Lists approved actions (when available)
   - Configurable enforcement level

### Running Validation Locally

```bash
# Run full CI validation (includes actions policy)
python3 tools/ci-validator/validate.py

# Run only actions policy validation
python3 tools/ci-validator/validate_actions_policy.py

# Check a specific repository
python3 tools/ci-validator/validate_actions_policy.py --repo-root=/path/to/repo
```

## Alternative Approaches

### Manual Commands

For most GitHub Actions, manual commands provide equivalent functionality:

**Checkout Code:**
```yaml
- name: Checkout
  run: |
    git clone --depth 1 https://github.com/${{ github.repository }}.git .
    git checkout ${{ github.sha }}
```

**Setup Language Runtime:**
```yaml
# Use container with pre-installed runtime
jobs:
  build:
    runs-on: ubuntu-latest
    container:
      image: node:20-alpine
```

**Cache Dependencies:**
```yaml
# Use BuildKit cache mounts
- name: Build with cache
  run: |
    docker build \
      --cache-from ghcr.io/myorg/myapp:cache \
      --cache-to ghcr.io/myorg/myapp:cache \
      -t myapp .
```

**Upload Artifacts:**
```yaml
- name: Upload artifact
  env:
    GH_TOKEN: ${{ github.token }}
  run: |
    gh release create v1.0.0 ./dist/app.tar.gz --repo ${{ github.repository }}
```

### Creating Organization Actions

If manual commands become too complex, create a wrapper action in `indestructibleorg`:

1. Create new repository: `indestructibleorg/my-action`
2. Implement action using Docker or JavaScript
3. Tag with semantic version
4. Add to approved actions list with full SHA
5. Use in workflows: `uses: indestructibleorg/my-action@<full-sha>`

## Exceptions

If you believe an exception to this policy is necessary:

1. Document the business justification
2. Propose alternative security measures
3. Open an issue for discussion
4. Get approval from security team
5. Track the approved exception via an issue and/or pull request (note: automated validators currently do not support an exceptions list).

## Resources

- [GitHub Actions Security Best Practices](https://docs.github.com/en/actions/security-guides/security-hardening-for-github-actions)
- [Supply Chain Security](https://slsa.dev/)
- Policy Configuration: `.github/allowed-actions.yaml`
- Validator: `tools/ci-validator/validate_actions_policy.py`

## Support

For questions or issues with this policy:
- Check existing documentation
- Review current workflow implementations
- Open an issue with tag `github-actions-policy`
