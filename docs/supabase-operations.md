# Supabase Operations Guide - IndestructibleEco

## Edge Functions

### hello-world Function

**Function Details:**

- **Name**: hello-world
- **Runtime**: Deno 2
- **Entry Point**: supabase/functions/hello-world/index.ts
- **URI**: indestructibleeco://functions/hello-world
- **URN**: urn:indestructibleeco:functions:hello-world:v1

**Deployment Status:**

- [x] Function code implemented
- [x] Deno configuration created
- [x] Deployment script created
- [x] CI/CD workflow configured
- [ ] Deployed to production (requires SUPABASE_PROJECT_REF and SUPABASE_ACCESS_TOKEN)

### Manual Deployment

```bash
# Set environment variables
export SUPABASE_PROJECT_REF=your-project-ref
export SUPABASE_ACCESS_TOKEN=your-access-token

# Deploy function
supabase functions deploy hello-world --project-ref $SUPABASE_PROJECT_REF

# Or use deployment script
chmod +x scripts/deploy-supabase-function.sh
./scripts/deploy-supabase-function.sh
```

### Testing

```bash
# Local testing
supabase functions serve hello-world --no-verify-jwt

# Test endpoint
curl -X POST http://localhost:54321/functions/v1/hello-world \
  -H "Content-Type: application/json" \
  -d '{"name": "Test"}'

# Production testing
curl -X POST https://your-project-ref.supabase.co/functions/v1/hello-world \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ANON_KEY" \
  -d '{"name": "Production"}'
```

### Monitoring

```bash
# View logs
supabase functions logs hello-world --project-ref $SUPABASE_PROJECT_REF

# View function list
supabase functions list --project-ref $SUPABASE_PROJECT_REF
```

## Configuration

### Required Secrets

Add these secrets to GitHub repository settings:

| Secret | Description | Required |
|--------|-------------|----------|
| `SUPABASE_PROJECT_REF` | Supabase project reference ID | Yes |
| `SUPABASE_ACCESS_TOKEN` | Supabase access token for deployment | Yes |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Supabase anonymous key (already exists) | Yes |

### Environment Variables

The function uses the following environment variables (configured in Supabase dashboard):

- `SUPABASE_URL`: Supabase project URL
- `SUPABASE_ANON_KEY`: Supabase anonymous key

## Security

### JWT Verification

- JWT verification is enabled by default
- For testing, use `--no-verify-jwt` flag
- For production, ensure proper JWT configuration

### CORS

- Configure allowed origins in Supabase dashboard
- Default: All origins allowed for development

### Rate Limiting

- Rate limiting is applied at the Supabase platform level
- Configure limits in Supabase dashboard

## Troubleshooting

### Deployment Fails

1. Verify SUPABASE_PROJECT_REF is correct
2. Verify SUPABASE_ACCESS_TOKEN has proper permissions
3. Check Supabase CLI version: `supabase --version`
4. View detailed logs: `supabase functions deploy hello-world --debug`

### Function Not Responding

1. Check function logs: `supabase functions logs hello-world`
2. Verify function is deployed: `supabase functions list`
3. Test with `--no-verify-jwt` to rule out JWT issues
4. Check Supabase dashboard for function status

### CORS Errors

1. Configure allowed origins in Supabase dashboard
2. Verify CORS headers in function response
3. Check browser console for specific CORS errors

## Governance

- **Owner**: indestructibleorg
- **Policy**: zero-trust
- **Compliance**: indestructibleeco v1.0
- **Audit**: All deployments logged via GitHub Actions

## Next Steps

1. Set SUPABASE_PROJECT_REF and SUPABASE_ACCESS_TOKEN in GitHub secrets
2. Deploy function manually or via CI/CD
3. Configure JWT verification for production
4. Set up monitoring and alerting
5. Add additional edge functions as needed
