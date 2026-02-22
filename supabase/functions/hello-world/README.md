# Hello World Edge Function

## Overview
IndestructibleEco hello-world edge function deployed on Supabase.

## Function Details
- **Name**: hello-world
- **Runtime**: Deno 2
- **Entry Point**: index.ts
- **URI**: indestructibleeco://functions/hello-world
- **URN**: urn:indestructibleeco:functions:hello-world:v1

## API Endpoint
```
POST /functions/v1/hello-world
Content-Type: application/json

{
  "name": "World"
}
```

## Response
```json
{
  "message": "Hello World!",
  "service": "indestructibleeco",
  "timestamp": "2024-02-21T09:00:00.000Z",
  "uri": "indestructibleeco://functions/hello-world",
  "urn": "urn:indestructibleeco:functions:hello-world:v1"
}
```

## Local Development
```bash
# Install Supabase CLI
npm install -g supabase

# Start local development
supabase start

# Deploy function locally
supabase functions serve hello-world --no-verify-jwt

# Test locally
curl -X POST http://localhost:54321/functions/v1/hello-world \
  -H "Content-Type: application/json" \
  -d '{"name": "Local"}'
```

## Deployment
```bash
# Set project reference
export SUPABASE_PROJECT_REF=your-project-ref

# Deploy to production
supabase functions deploy hello-world --project-ref $SUPABASE_PROJECT_REF

# Verify deployment
supabase functions list hello-world --project-ref $SUPABASE_PROJECT_REF
```

## Environment Variables
Required environment variables (set in Supabase dashboard):
- `SUPABASE_URL`: Supabase project URL
- `SUPABASE_ANON_KEY`: Supabase anonymous key

## Security
- JWT verification enabled by default
- CORS configured for allowed origins
- Rate limiting applied via Supabase platform

## Monitoring
- View logs: `supabase functions logs hello-world --project-ref $SUPABASE_PROJECT_REF`
- Metrics available in Supabase dashboard

## Governance
- **Owner**: indestructibleorg
- **Policy**: zero-trust
- **Compliance**: indestructibleeco v1.0