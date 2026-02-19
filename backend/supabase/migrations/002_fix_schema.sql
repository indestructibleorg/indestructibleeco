-- IndestructibleEco v1.0 — Schema Alignment Migration
-- URI: indestructibleeco://backend/supabase/migrations/002
-- Aligns DB schema with packages/shared-types entities (Step 6 → Step 7)

-- ─── Users: add metadata + last_sign_in_at ─────────────────────────────────
alter table public.users
  add column if not exists metadata jsonb not null default '{}';

alter table public.users
  add column if not exists last_sign_in_at timestamptz;

-- ─── Platforms: expand type + status check constraints ──────────────────────
-- Drop and recreate type check to include 'extension'
alter table public.platforms drop constraint if exists platforms_type_check;
alter table public.platforms
  add constraint platforms_type_check
  check (type in ('web','desktop','im','api','worker','extension','custom'));

-- Drop and recreate status check to include 'deploying'
alter table public.platforms drop constraint if exists platforms_status_check;
alter table public.platforms
  add constraint platforms_status_check
  check (status in ('active','inactive','deploying','maintenance','deprecated'));

-- ─── AI Jobs: add usage, model_params, latency_ms ──────────────────────────
alter table public.ai_jobs
  add column if not exists usage jsonb default null;

alter table public.ai_jobs
  add column if not exists model_params jsonb not null default '{"temperature":0.7,"top_p":1.0,"max_tokens":2048,"stream":false}';

alter table public.ai_jobs
  add column if not exists latency_ms integer default null;

-- Create composite index for user+status queries (common dashboard pattern)
create index if not exists idx_ai_jobs_user_status
  on public.ai_jobs(user_id, status);

-- Create index on created_at for time-range queries
create index if not exists idx_ai_jobs_created
  on public.ai_jobs(created_at desc);

-- ─── Governance Records: add index on created_at for audit trail queries ────
create index if not exists idx_governance_created
  on public.governance_records(created_at desc);

-- ─── Service Registry: add metadata column for flexible config ──────────────
alter table public.service_registry
  add column if not exists metadata jsonb not null default '{}';

-- ─── YAML Documents: add validation_status for governance tracking ──────────
alter table public.yaml_documents
  add column if not exists validation_status text not null default 'pending'
  check (validation_status in ('pending','valid','invalid','warning'));

create index if not exists idx_yaml_docs_status
  on public.yaml_documents(validation_status);

-- ─── Comment: migration complete ────────────────────────────────────────────
-- This migration aligns the database schema with the TypeScript shared-types:
--   User      → metadata, last_sign_in_at
--   Platform  → type includes 'extension', status includes 'deploying'
--   AiJob     → usage (jsonb), model_params (jsonb), latency_ms (int)
--   ServiceRegistry → metadata (jsonb)
--   YamlDocuments   → validation_status