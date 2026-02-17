# Environment Variables Configuration Best Practices

## 🔐 Security Principles

### 1. Never Hardcode Secrets
```typescript
// ❌ WRONG - Never hardcode secrets
const apiKey = "ghp_your_actual_token_here"

// ✅ CORRECT - Use environment variables
const apiKey = process.env.GITHUB_API_KEY
```

### 2. Use Environment-Specific Prefixes
```bash
# Browser-safe (NEXT_PUBLIC_*)
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=sb_publishable_your_anon_key_here

# Server-side only
SUPABASE_SECRET_KEY=sb_secret_your_secret_key_here
GITHUB_TOKEN=ghp_your_actual_token_here
```

### 3. Validation and Defaults
```typescript
// config/env.ts
const env = {
  NEXT_PUBLIC_SUPABASE_URL: process.env.NEXT_PUBLIC_SUPABASE_URL || '',
  SUPABASE_SECRET_KEY: process.env.SUPABASE_SECRET_KEY || '',
}

// Validate
if (!env.NEXT_PUBLIC_SUPABASE_URL) {
  throw new Error('NEXT_PUBLIC_SUPABASE_URL is required')
}
```

## 🛠️ Implementation Strategies

### Strategy 1: GitHub Actions Secrets
```yaml
# .github/workflows/ci.yml
jobs:
  build:
    steps:
      - uses: actions/checkout@v4
      - name: Setup environment
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
        run: |
          echo "Environment configured"
```

### Strategy 2: .env Files with Validation
```bash
# .env.example (committed to git)
NEXT_PUBLIC_SUPABASE_URL=
NEXT_PUBLIC_SUPABASE_ANON_KEY=
SUPABASE_SECRET_KEY=
GITHUB_TOKEN=

# .env.local (not committed - in .gitignore)
NEXT_PUBLIC_SUPABASE_URL=https://yrfxijooswpvdpdseswy.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=sb_publishable_rhTyBa4IqqV14nV_B87S7g_zKzDSYTd
SUPABASE_SECRET_KEY=sb_secret_your_secret_key_here
GITHUB_TOKEN=ghp_your_actual_token_here
```

### Strategy 3: TypeScript Environment Schema
```typescript
// env.ts
import { z } from 'zod'

const envSchema = z.object({
  NEXT_PUBLIC_SUPABASE_URL: z.string().url(),
  NEXT_PUBLIC_SUPABASE_ANON_KEY: z.string(),
  SUPABASE_SECRET_KEY: z.string(),
  GITHUB_TOKEN: z.string().startsWith('ghp_'),
})

export const env = envSchema.parse({
  NEXT_PUBLIC_SUPABASE_URL: process.env.NEXT_PUBLIC_SUPABASE_URL,
  NEXT_PUBLIC_SUPABASE_ANON_KEY: process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY,
  SUPABASE_SECRET_KEY: process.env.SUPABASE_SECRET_KEY,
  GITHUB_TOKEN: process.env.GITHUB_TOKEN,
})
```

## 🔍 Git Ignore Configuration
```gitignore
# .gitignore
.env
.env.local
.env.production.local
.env.test.local
*.key
*.pem
secrets/
credentials/
```

## 🚀 CI/CD Best Practices

### GitHub Actions Secrets Setup
```bash
# Set secrets via GitHub CLI
gh secret set NEXT_PUBLIC_SUPABASE_URL -b "https://your-project.supabase.co"
gh secret set SUPABASE_SECRET_KEY -b "sb_secret_your_secret_key_here"
gh secret set GITHUB_TOKEN -b "ghp_your_actual_token_here"

# List secrets
gh secret list

# Remove secrets
gh secret remove OLD_SECRET
```

### Workflow Configuration
```yaml
# .github/workflows/ci.yml
name: CI Pipeline

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  lint-and-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          
      - name: Install dependencies
        run: pnpm install
        
      - name: Lint
        run: pnpm run lint
        
      - name: Test
        env:
          SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
          SUPABASE_ANON_KEY: ${{ secrets.SUPABASE_ANON_KEY }}
        run: pnpm run test
```

## 📊 Environment File Templates

### Development (.env.development)
```bash
NODE_ENV=development
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=sb_publishable_your_anon_key_here
SUPABASE_SECRET_KEY=sb_secret_your_secret_key_here
GITHUB_TOKEN=ghp_your_actual_token_here
ANTHROPIC_API_KEY=sk-ant-your_anthropic_key_here
GROQ_API_KEY=gsk_your_groq_key_here
CLOUDFLARE_API_TOKEN=your_cloudflare_token_here
```

### Production (.env.production)
```bash
NODE_ENV=production
# Only use GitHub Secrets in production, never .env files
```

## 🛡️ Security Checklist

- [ ] Never commit `.env` files to version control
- [ ] Use GitHub Actions Secrets for CI/CD
- [ ] Rotate secrets regularly
- [ ] Use principle of least privilege
- [ ] Implement secret scanning (Dependabot)
- [ ] Validate environment variables at startup
- [ ] Use environment-specific configurations
- [ ] Document required environment variables in README
- [ ] Use environment variable prefixes for clarity
- [ ] Implement fallback values for non-sensitive data

## 🔄 Secret Rotation Strategy

1. **Identify Secrets**: List all secrets in use
2. **Generate New Secrets**: Create new tokens/keys
3. **Update Configuration**: Update CI/CD and deployment scripts
4. **Test Verification**: Ensure new secrets work
5. **Deploy**: Deploy to production
6. **Monitor**: Verify systems work correctly
7. **Remove Old Secrets**: Delete old tokens from platforms

## 📝 Documentation Template

```markdown
# Environment Variables

## Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| NEXT_PUBLIC_SUPABASE_URL | Supabase project URL | https://your-project.supabase.co |
| SUPABASE_SECRET_KEY | Supabase secret key | sb_secret_your_key_here |
| GITHUB_TOKEN | GitHub personal access token | ghp_your_token_here |

## Setup Instructions

1. Copy `.env.example` to `.env.local`
2. Fill in the required values
3. Never commit `.env.local` to git
```