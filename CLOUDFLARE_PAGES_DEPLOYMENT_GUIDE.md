# Cloudflare Pages Deployment Guide

**Document Version:** 1.0  
**Last Updated:** 2026-02-12  
**Author:** Manus AI  
**Repository:** autoecoops/ecosystem

---

## Executive Summary

This guide provides a comprehensive overview of deploying the AutoEcoOps Ecosystem frontend application to Cloudflare Pages. The deployment process encompasses repository configuration, build system setup, environment variable management, custom domain binding, and monitoring. This document serves as the authoritative reference for all stakeholders involved in the deployment lifecycle.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Prerequisites & Requirements](#prerequisites--requirements)
3. [Initial Setup & Configuration](#initial-setup--configuration)
4. [Build Configuration](#build-configuration)
5. [Environment Variables](#environment-variables)
6. [Custom Domain Setup](#custom-domain-setup)
7. [Deployment Process](#deployment-process)
8. [Monitoring & Troubleshooting](#monitoring--troubleshooting)
9. [Rollback Procedures](#rollback-procedures)
10. [Best Practices](#best-practices)

---

## Architecture Overview

The AutoEcoOps Ecosystem deployment architecture consists of multiple interconnected components working in concert to deliver a reliable, scalable frontend application on Cloudflare Pages.

### Deployment Stack

The deployment leverages the following technology stack:

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Frontend Framework** | Next.js 15.0.8 | React-based application framework with SSR/SSG capabilities |
| **Package Manager** | pnpm 8.15.0 | Fast, disk-space efficient package manager for monorepo |
| **Build Tool** | Cloudflare Pages | Serverless platform for static and dynamic content |
| **Build Adapter** | @cloudflare/next-on-pages | Adapter converting Next.js output to Cloudflare Workers format |
| **DNS Provider** | Cloudflare | Authoritative DNS and edge caching infrastructure |
| **Version Control** | GitHub | Source code repository and CI/CD orchestration |

### Monorepo Structure

The project uses a monorepo architecture with the following directory layout:

```
autoecoops/ecosystem/
├── frontend/
│   └── project-01/                 # Main Next.js application
│       ├── package.json            # Frontend-specific dependencies
│       ├── next.config.js          # Next.js configuration
│       ├── tsconfig.json           # TypeScript configuration
│       ├── src/                    # Application source code
│       └── public/                 # Static assets
├── platforms/                      # Platform-specific implementations
├── package.json                    # Root monorepo configuration
├── pnpm-workspace.yaml             # Workspace definition
├── wrangler.toml                   # Cloudflare Pages configuration
├── .npmrc                          # npm/pnpm settings
└── pnpm-lock.yaml                  # Dependency lock file
```

### Deployment Flow

The deployment process follows this sequence:

1. **Code Push** - Developer pushes changes to GitHub main branch
2. **GitHub Actions Trigger** - Automated workflows begin execution
3. **Dependency Resolution** - pnpm installs dependencies from lock file
4. **Build Execution** - Next.js builds application using @cloudflare/next-on-pages adapter
5. **Output Generation** - Build produces Cloudflare Workers-compatible output in `vercel/output/static`
6. **Deployment** - Cloudflare Pages publishes output to global edge network
7. **DNS Resolution** - Custom domain resolves to Cloudflare Pages endpoint
8. **HTTPS Provisioning** - Automatic SSL/TLS certificate issuance and renewal

---

## Prerequisites & Requirements

Before deploying to Cloudflare Pages, ensure the following prerequisites are met:

### Account & Access Requirements

- **Cloudflare Account** - Active Cloudflare account with Pages enabled
- **GitHub Account** - Organization account with repository access
- **Domain Registration** - Custom domain registered (optional, Cloudflare Pages provides default domain)
- **GitHub Token** - Personal access token with `repo` and `workflow` scopes for CI/CD
- **Cloudflare API Token** - Token with Pages deployment permissions (if using automated deployments)

### Technical Requirements

- **Node.js Version** - Node.js 20.0.0 or higher
- **pnpm Version** - pnpm 8.0.0 or higher
- **Git** - Git 2.30.0 or higher for version control
- **Next.js Version** - Next.js 15.0.8 (as specified in root package.json)

### Repository Configuration

The repository must contain the following configuration files:

1. **package.json** - Root monorepo package definition with Next.js dependency
2. **pnpm-workspace.yaml** - Defines workspace structure and included packages
3. **wrangler.toml** - Cloudflare Pages build configuration
4. **.npmrc** - npm/pnpm configuration enforcing package manager consistency
5. **pnpm-lock.yaml** - Locked dependency versions for reproducible builds

### Cloudflare Configuration

- **Nameservers** - Domain nameservers pointed to Cloudflare (if using custom domain)
- **SSL/TLS Mode** - Set to "Full" or "Full (strict)" for secure connections
- **Page Rules** - Optional caching and security rules configured as needed

---

## Initial Setup & Configuration

### Step 1: Connect GitHub Repository to Cloudflare Pages

1. **Log into Cloudflare Dashboard** - Navigate to [dash.cloudflare.com](https://dash.cloudflare.com)
2. **Select Account** - Choose the appropriate Cloudflare account
3. **Navigate to Pages** - Click "Pages" in the left sidebar
4. **Create Project** - Click "Create a project" → "Connect to Git"
5. **Authorize GitHub** - Grant Cloudflare permission to access GitHub repositories
6. **Select Repository** - Choose `autoecoops/ecosystem` from the list
7. **Confirm Connection** - Review and confirm the repository connection

### Step 2: Configure Build Settings

In the Cloudflare Pages project settings:

1. **Framework Preset** - Select "Next.js"
2. **Build Command** - Enter: `npx @cloudflare/next-on-pages@1`
3. **Build Output Directory** - Enter: `vercel/output/static`
4. **Root Directory** - Enter: `frontend/project-01` (if deploying only frontend)
5. **Environment** - Leave blank for now (configure in Step 3)

### Step 3: Add Environment Variables

1. **Navigate to Settings** - In the Pages project, click "Settings"
2. **Environment Variables** - Click "Environment variables"
3. **Add Variables** - For each required variable:
   - Click "Add variable"
   - Enter variable name (e.g., `NEXT_PUBLIC_API_URL`)
   - Enter variable value
   - Select "Production" environment
   - Click "Save"

### Step 4: Verify Initial Deployment

1. **Trigger Deployment** - Push a test commit to main branch
2. **Monitor Build** - Watch the build progress in Cloudflare Pages dashboard
3. **Check Build Logs** - Review logs for any errors or warnings
4. **Access Site** - Visit the assigned Cloudflare Pages URL (e.g., `project-name.pages.dev`)

---

## Build Configuration

### wrangler.toml Configuration

The `wrangler.toml` file at the repository root defines the build process:

```toml
name = "autoecoops-ecosystem"
type = "javascript"
account_id = ""
workers_dev = true

[build]
command = "cd frontend/project-01 && pnpm install && pnpm run build"
cwd = "."
watch_paths = ["frontend/project-01/**/*.{ts,tsx,js,jsx,json}"]

[build.upload]
format = "service-worker"

[env.production]
vars = { ENVIRONMENT = "production" }

[env.staging]
vars = { ENVIRONMENT = "staging" }
```

**Configuration Explanation:**

- **name** - Project identifier used by Cloudflare
- **type** - Specifies JavaScript/Workers project type
- **build.command** - Shell command executed to build the application
- **build.cwd** - Working directory for build execution (repository root)
- **build.watch_paths** - File patterns triggering rebuilds on change
- **build.upload.format** - Output format compatible with Cloudflare Workers
- **env** - Environment-specific variables and configuration

### Next.js Configuration

The `frontend/project-01/next.config.js` must include Cloudflare Pages adapter:

```javascript
import { withPlainConfig } from '@cloudflare/next-on-pages/next-config';

export default withPlainConfig({
  // Next.js configuration options
  reactStrictMode: true,
  swcMinify: true,
  
  // Output directory for Cloudflare Pages
  distDir: '.next',
  
  // Image optimization (use external service for serverless)
  images: {
    unoptimized: true,
  },
});
```

### Package Manager Configuration

The `.npmrc` file enforces pnpm usage:

```
engine-strict=true
prefer-pnpm=true
legacy-peer-deps=false
strict-peer-dependencies=true
registry=https://registry.npmjs.org/
fetch-timeout=60000
fetch-retry-mintimeout=20000
fetch-retry-maxtimeout=120000
```

This configuration prevents npm fallback during Cloudflare Pages builds, ensuring consistent dependency resolution.

---

## Environment Variables

### Variable Categories

Environment variables are organized into three categories:

#### 1. Build-Time Variables (NEXT_PUBLIC_*)

Variables prefixed with `NEXT_PUBLIC_` are embedded in the client-side bundle:

| Variable | Purpose | Example |
|----------|---------|---------|
| `NEXT_PUBLIC_API_URL` | Backend API endpoint | `https://api.autoecoops.io` |
| `NEXT_PUBLIC_OAUTH_URL` | OAuth provider URL | `https://auth.autoecoops.io` |
| `NEXT_PUBLIC_APP_NAME` | Application display name | `AutoEcoOps Ecosystem` |
| `NEXT_PUBLIC_ENVIRONMENT` | Deployment environment | `production` |

#### 2. Runtime Variables (Server-Side)

Variables without `NEXT_PUBLIC_` prefix are only available on the server:

| Variable | Purpose | Example |
|----------|---------|---------|
| `DATABASE_URL` | Database connection string | `postgresql://user:pass@host/db` |
| `API_SECRET_KEY` | Secret authentication key | `sk_live_...` |
| `ENCRYPTION_KEY` | Data encryption key | `base64-encoded-key` |

#### 3. Cloudflare-Specific Variables

| Variable | Purpose | Example |
|----------|---------|---------|
| `CF_ACCOUNT_ID` | Cloudflare account identifier | `abc123def456` |
| `CF_API_TOKEN` | Cloudflare API token | `v1.0abc123...` |
| `CF_ZONE_ID` | DNS zone identifier | `xyz789abc123` |

### Setting Variables in Cloudflare Pages

1. **Access Settings** - Navigate to Pages project → Settings
2. **Environment Variables** - Click "Environment variables" section
3. **Add Variable** - Click "Add variable" button
4. **Enter Details**:
   - **Variable name** - Exact name (case-sensitive)
   - **Value** - Variable value
   - **Environment** - Select "Production" or "Preview"
5. **Save** - Click "Save" to apply immediately

### Local Development Variables

For local development, create `frontend/project-01/.env.local`:

```bash
# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:3001
NEXT_PUBLIC_OAUTH_URL=http://localhost:8080

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/autoecoops_dev

# Secrets
API_SECRET_KEY=dev-secret-key-change-in-production
ENCRYPTION_KEY=dev-encryption-key-change-in-production
```

**Important:** Never commit `.env.local` to version control. Add to `.gitignore`.

---

## Custom Domain Setup

### DNS Configuration

To bind a custom domain to Cloudflare Pages:

#### Option 1: Cloudflare Nameservers (Recommended)

1. **Update Domain Registrar** - Change nameservers to Cloudflare:
   - `ns1.cloudflare.com`
   - `ns2.cloudflare.com`
   - `ns3.cloudflare.com`
   - `ns4.cloudflare.com`

2. **Wait for Propagation** - DNS changes propagate within 24-48 hours

3. **Verify in Cloudflare** - Dashboard shows domain as "Active"

#### Option 2: CNAME Record (Partial Setup)

If you cannot change nameservers:

1. **Add CNAME Record** - In your domain registrar's DNS settings:
   - **Name:** `app` (or subdomain)
   - **Target:** `autoecoops-ecosystem.pages.dev`
   - **TTL:** 3600 (1 hour)

2. **Verify** - After propagation, access `app.yourdomain.com`

### Adding Domain to Cloudflare Pages

1. **Access Pages Project** - Navigate to the Pages project in Cloudflare
2. **Custom Domains** - Click "Custom domains" tab
3. **Add Domain** - Click "Add a custom domain"
4. **Enter Domain** - Type the custom domain (e.g., `app.autoecoops.io`)
5. **Verify Ownership** - Follow verification steps (usually automatic with Cloudflare nameservers)
6. **Confirm** - Click "Activate domain"

### HTTPS & SSL/TLS

Cloudflare automatically provisions and renews SSL/TLS certificates:

- **Certificate Type** - Universal SSL (included free)
- **Renewal** - Automatic, no action required
- **SSL/TLS Mode** - Set to "Full" or "Full (strict)" in Cloudflare dashboard
- **HSTS** - Enable HTTP Strict Transport Security for enhanced security

### WWW Subdomain Handling

To redirect `www.yourdomain.com` to `yourdomain.com`:

1. **Create CNAME Record** - In Cloudflare DNS:
   - **Name:** `www`
   - **Target:** `yourdomain.com`
   - **Proxied:** Yes (orange cloud)

2. **Configure Page Rule** - In Cloudflare:
   - **URL Pattern:** `www.yourdomain.com/*`
   - **Forwarding URL:** `301 - Permanent Redirect` to `https://yourdomain.com/$1`

---

## Deployment Process

### Automated Deployment (Main Branch)

The deployment process is fully automated:

1. **Code Push** - Developer commits and pushes to `main` branch
2. **GitHub Webhook** - Cloudflare receives push notification
3. **Build Trigger** - Cloudflare Pages initiates build process
4. **Dependency Installation** - `pnpm install` resolves dependencies
5. **Build Execution** - `pnpm run build` compiles Next.js application
6. **Adapter Processing** - @cloudflare/next-on-pages converts output
7. **Deployment** - Output deployed to Cloudflare global edge network
8. **Propagation** - Changes propagate globally within seconds

### Manual Deployment

To manually trigger a deployment:

1. **Access Pages Dashboard** - Navigate to the Pages project
2. **Deployments Tab** - Click "Deployments" section
3. **Redeploy** - Click "Redeploy" next to a previous deployment
4. **Confirm** - Confirm redeployment of selected commit

### Preview Deployments

Preview deployments are automatically created for pull requests:

1. **Create Pull Request** - Open PR against `main` branch
2. **Automatic Build** - Cloudflare builds PR changes
3. **Preview URL** - Unique URL provided for testing (e.g., `pr-123.autoecoops-ecosystem.pages.dev`)
4. **Review Changes** - Test functionality before merging
5. **Merge & Deploy** - Merge PR to trigger production deployment

---

## Monitoring & Troubleshooting

### Build Monitoring

#### Accessing Build Logs

1. **Navigate to Deployments** - In Pages project, click "Deployments"
2. **Select Deployment** - Click on a deployment to view details
3. **View Logs** - Click "View build log" to see detailed output

#### Common Build Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `No Next.js version detected` | Next.js not in dependencies | Add `next` to root `package.json` |
| `The project is set up for pnpm but running via npm` | Package manager mismatch | Ensure `.npmrc` exists with `prefer-pnpm=true` |
| `Cannot find module '@cloudflare/next-on-pages'` | Missing adapter | Run `pnpm install --frozen-lockfile=false` |
| `Build command failed: ENOENT` | Incorrect directory path | Verify `wrangler.toml` build command path |
| `Timeout during build` | Build exceeding time limit | Optimize build process or increase timeout |

### Runtime Monitoring

#### Cloudflare Analytics

1. **Access Analytics** - In Pages project, click "Analytics"
2. **View Metrics**:
   - **Requests** - Total requests to the site
   - **Data Transfer** - Bandwidth consumed
   - **Cache Hit Ratio** - Percentage of cached responses
   - **Status Codes** - Distribution of HTTP response codes

#### Error Tracking

1. **Monitor Errors** - Check "Errors" section in Analytics
2. **Identify Issues** - Review error patterns and affected pages
3. **Investigate** - Check application logs and browser console
4. **Fix & Deploy** - Resolve issues and redeploy

### Performance Optimization

#### Caching Strategy

Cloudflare Pages automatically caches static assets:

- **HTML Files** - Cached with short TTL (5 minutes)
- **CSS/JS Files** - Cached with long TTL (1 year) if versioned
- **Images** - Cached with long TTL (1 month)
- **API Responses** - Not cached by default

#### Image Optimization

Since Cloudflare Pages doesn't support Next.js Image Optimization:

1. **Set `unoptimized: true`** - In `next.config.js`
2. **Use External Service** - Integrate with Cloudflare Image Optimization or similar
3. **Optimize Locally** - Pre-optimize images before deployment

---

## Rollback Procedures

### Rolling Back to Previous Deployment

If a deployment introduces issues:

1. **Access Deployments** - Navigate to Pages project → Deployments
2. **Select Previous** - Click on a previous stable deployment
3. **Rollback** - Click "Rollback to this deployment"
4. **Confirm** - Confirm the rollback action
5. **Verify** - Test the site to confirm rollback success

### Git-Based Rollback

To rollback via Git:

```bash
# Identify problematic commit
git log --oneline -10

# Revert commit (creates new commit that undoes changes)
git revert <commit-hash>

# Push to main (triggers automatic deployment)
git push origin main
```

### Emergency Rollback

For critical issues requiring immediate action:

1. **Disable Custom Domain** - Temporarily point domain elsewhere
2. **Rollback Deployment** - Use Cloudflare Pages rollback feature
3. **Investigate** - Analyze logs to identify root cause
4. **Fix & Redeploy** - Commit fix and redeploy
5. **Restore Domain** - Point domain back to Cloudflare Pages

---

## Best Practices

### Development Workflow

1. **Create Feature Branch** - Branch from `main` for each feature
2. **Test Locally** - Run `pnpm run dev` and test thoroughly
3. **Run Linting** - Execute `pnpm run lint` to catch issues
4. **Create Pull Request** - Open PR for code review
5. **Review Preview** - Test preview deployment URL
6. **Merge & Deploy** - Merge PR to trigger production deployment

### Code Quality

- **Type Safety** - Use TypeScript for all new code
- **Linting** - Configure ESLint and enforce via CI/CD
- **Testing** - Write unit and integration tests for critical paths
- **Code Review** - Require peer review before merging
- **Commit Messages** - Follow conventional commit format

### Security

- **Environment Secrets** - Never commit secrets to version control
- **HTTPS Only** - Enforce HTTPS for all connections
- **Security Headers** - Configure HSTS, CSP, and X-Frame-Options
- **Dependency Updates** - Regularly update dependencies and monitor vulnerabilities
- **Access Control** - Limit deployment access to authorized personnel

### Performance

- **Bundle Analysis** - Monitor bundle size with each deployment
- **Lazy Loading** - Implement code splitting for large components
- **Image Optimization** - Compress and optimize images before deployment
- **Caching Strategy** - Configure appropriate cache headers
- **Monitoring** - Track Core Web Vitals and performance metrics

### Disaster Recovery

- **Backup Strategy** - Maintain Git history for recovery
- **Monitoring Alerts** - Configure alerts for deployment failures
- **Incident Response** - Document procedures for common issues
- **Communication** - Notify stakeholders of major incidents
- **Post-Mortems** - Analyze incidents to prevent recurrence

---

## Appendix: Configuration Files

### Root package.json (Excerpt)

```json
{
  "name": "contracts-l1-monorepo",
  "version": "0.1.0",
  "packageManager": "pnpm@8.15.0",
  "scripts": {
    "dev:frontend": "cd frontend/project-01 && pnpm run dev",
    "build:frontend": "cd frontend/project-01 && pnpm run build"
  },
  "dependencies": {
    "next": "^15.0.8"
  }
}
```

### wrangler.toml (Complete)

```toml
name = "autoecoops-ecosystem"
type = "javascript"
account_id = ""
workers_dev = true

[build]
command = "cd frontend/project-01 && pnpm install && pnpm run build"
cwd = "."
watch_paths = ["frontend/project-01/**/*.{ts,tsx,js,jsx,json}"]

[build.upload]
format = "service-worker"

[env.production]
vars = { ENVIRONMENT = "production" }

[env.staging]
vars = { ENVIRONMENT = "staging" }
```

### .npmrc (Complete)

```
engine-strict=true
prefer-pnpm=true
legacy-peer-deps=false
strict-peer-dependencies=true
registry=https://registry.npmjs.org/
fetch-timeout=60000
fetch-retry-mintimeout=20000
fetch-retry-maxtimeout=120000
```

---

## Support & Resources

- **Cloudflare Pages Documentation** - https://developers.cloudflare.com/pages/
- **Next.js Documentation** - https://nextjs.org/docs
- **Cloudflare Next.js Adapter** - https://github.com/cloudflare/next-on-pages
- **GitHub Actions** - https://docs.github.com/en/actions
- **pnpm Documentation** - https://pnpm.io/

---

**Document Revision History**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-02-12 | Manus AI | Initial comprehensive deployment guide |

