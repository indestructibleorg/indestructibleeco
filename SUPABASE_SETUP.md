# Supabase Setup Guide

Complete guide to setting up and using Supabase in the ecosystem application.

## Table of Contents

1. [Project Structure](#project-structure)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Local Development](#local-development)
5. [Production Deployment](#production-deployment)
6. [Integration with Existing Code](#integration-with-existing-code)
7. [Troubleshooting](#troubleshooting)

## Project Structure

The Supabase configuration is organized as follows:

```text
ecosystem/
├── supabase/                              # Supabase configuration
│   ├── config.toml                       # Local development config
│   ├── migrations/                       # SQL migration files
│   │   ├── .gitkeep
│   │   └── 001_init.sql                 # Initial schema
│   ├── seed.sql                          # Development seed data
│   └── README.md                         # Supabase docs
│
├── shared/supabase/                      # Supabase client code
│   ├── client.ts                         # Public browser client
│   ├── server.ts                         # Private server client
│   ├── types.ts                          # TypeScript types
│   ├── hooks.ts                          # React hooks
│   └── index.ts                          # Main exports
│
└── .env.example                          # Environment template
```

## Installation

### Step 1: Install Supabase CLI

```bash
# Using npm
npm install -g supabase

# Or using pnpm
pnpm add -g supabase
```

### Step 2: Install Supabase Client Library

```bash
# Already included in ecosystem dependencies
# If needed, run:
pnpm add @supabase/supabase-js
```

## Configuration

### Step 1: Create Supabase Project

1. Visit [app.supabase.com](https://app.supabase.com)
2. Create a new project
3. Note your project ID and API keys

### Step 2: Set Environment Variables

Create `.env.local` in the project root:

```bash
cp .env.example .env.local
```

Fill in your Supabase credentials:

```env
# Client-side (public - safe for browser)
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=sb_publishable_xxxxx

# Server-side (secret - API routes only)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Step 3: Link Supabase Project

```bash
supabase link --project-ref your-project-id
```

When prompted for the password, use your Supabase database password.

## Local Development

### Start Local Supabase

```bash
supabase start
```

This initializes:
- PostgreSQL database (port 5432)
- Supabase Studio dashboard (port 54323)
- Auth API (port 54321)
- Realtime service (port 54322)
- Email testing with Inbucket (port 54324)

### Verify Setup

1. Open Supabase Studio: http://localhost:54323
2. Check Tables > users to see test data from seed.sql
3. Browse other tables to verify schema

### Stop Local Supabase

```bash
supabase stop
```

## Production Deployment

### Deploy Schema to Production

```bash
# Ensure migrations are up to date locally
supabase db push

# Deploy to production
supabase db push --linked
```

### Enable Row Level Security (RLS)

RLS policies are configured in `migrations/001_init.sql`.

To verify in production:

1. Go to [app.supabase.com](https://app.supabase.com) > SQL Editor
2. Verify RLS is enabled on all tables
3. Test policies with different user roles

### Set Production Environment Variables

In your deployment platform (Vercel, Railway, etc.), set:

```env
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=sb_publishable_xxxxx
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

## Integration with Existing Code

### Option 1: Keep Existing MySQL/Drizzle

If maintaining MySQL database:

1. Supabase serves as additional data store
2. Use `shared/supabase/` for Supabase-specific queries
3. Use `server/db.ts` for existing MySQL queries
4. Gradually migrate to Supabase

### Option 2: Migrate to Supabase PostgreSQL

To fully migrate to Supabase:

1. Update `server/db.ts` to use Supabase admin client:

```typescript
import { supabaseAdmin } from '@shared/supabase/server';

export async function getDb() {
  return supabaseAdmin;
}
```

2. Update environment to use Supabase PostgreSQL:

```env
DATABASE_URL=postgresql://user:password@aws-0-region.pooler.supabase.com:6543/postgres
```

3. Remove MySQL dependencies:

```bash
pnpm remove mysql2
```

### Using Supabase Client in React Components

```typescript
import { useAuth, useRealtimeSubscription } from '@shared/supabase/hooks';

export function Dashboard() {
  const { user, loading } = useAuth();
  const { data: users } = useRealtimeSubscription('users');

  if (loading) return <div>Loading...</div>;

  return (
    <div>
      <h1>Welcome, {user?.name}</h1>
      <UserList users={users} />
    </div>
  );
}
```

## Troubleshooting

### Port Already in Use

If ports are already in use:

```bash
# Stop existing Supabase instance
supabase stop

# Change ports in supabase/config.toml
# Then restart
supabase start
```

### Cannot Connect to Database

```bash
# Check Supabase status
supabase status

# View logs
supabase logs

# Reset database
supabase db reset
```

### Environment Variables Not Loading

1. Verify `.env.local` exists
2. Check variable names match exactly (case-sensitive)
3. Restart development server after changing `.env.local`

```bash
# Restart server
pnpm run dev
```

### Migration Conflicts

```bash
# Reset database to latest migration
supabase db reset

# Or reapply migrations
supabase db push --dry-run  # Preview changes
supabase db push             # Apply changes
```

### TypeScript Errors

Generate types from Supabase schema:

```bash
supabase gen types typescript --linked > shared/supabase/database.types.ts
```

Then import in code:

```typescript
import type { Database } from '@shared/supabase/database.types';
```

## Next Steps

1. Update application code to use Supabase clients from `shared/supabase/`
2. Create additional migrations as schema evolves
3. Set up authentication with Supabase Auth (optional)
4. Configure backup and disaster recovery in Supabase dashboard
5. Enable point-in-time recovery for production

## Resources

- [Supabase Documentation](https://supabase.com/docs)
- [Supabase CLI Reference](https://supabase.com/docs/reference/cli/introduction)
- [PostgreSQL Best Practices](https://wiki.postgresql.org/wiki/Performance_Optimization)
- [Row Level Security Guide](https://supabase.com/docs/guides/auth/row-level-security)
