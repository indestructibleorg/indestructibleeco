-- eco-base v1.1 — Pro Plan Enhancements Migration
-- URI: eco-base://supabase/migrations/003
-- Enables: Database Webhooks, PITR-optimized indexes, Realtime subscriptions, Storage buckets

-- ─── Enable required extensions ─────────────────────────────────────────
create extension if not exists "pg_net" with schema extensions;
create extension if not exists "pg_cron" with schema extensions;

-- ─── Storage Buckets ────────────────────────────────────────────────────
-- Audit attachments bucket (for compliance documents)
insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values (
  'audit-attachments',
  'audit-attachments',
  false,
  52428800,  -- 50MB
  array['application/pdf', 'image/png', 'image/jpeg', 'application/json', 'text/plain']
)
on conflict (id) do nothing;

-- Platform assets bucket (logos, configs)
insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values (
  'platform-assets',
  'platform-assets',
  true,
  10485760,  -- 10MB
  array['image/png', 'image/jpeg', 'image/svg+xml', 'image/webp', 'application/json']
)
on conflict (id) do nothing;

-- ─── Storage RLS Policies ───────────────────────────────────────────────
-- Audit attachments: only service_role and admins
create policy "Service role can manage audit attachments"
  on storage.objects for all
  using (bucket_id = 'audit-attachments' and auth.role() = 'service_role')
  with check (bucket_id = 'audit-attachments' and auth.role() = 'service_role');

-- Platform assets: public read, admin write
create policy "Anyone can read platform assets"
  on storage.objects for select
  using (bucket_id = 'platform-assets');

create policy "Admins can manage platform assets"
  on storage.objects for insert
  using (bucket_id = 'platform-assets')
  with check (
    bucket_id = 'platform-assets' and
    exists (select 1 from public.users where id = auth.uid() and role = 'admin')
  );

-- ─── Deployment History Table ───────────────────────────────────────────
-- Tracks all deployments for DORA metrics and audit compliance
create table if not exists public.deployment_history (
  id             uuid default uuid_generate_v4() primary key,
  platform_id    uuid references public.platforms(id) on delete set null,
  environment    text not null check (environment in ('staging', 'production', 'preview')),
  deploy_type    text not null check (deploy_type in ('full', 'canary', 'rollback', 'hotfix')),
  status         text not null default 'pending'
                 check (status in ('pending', 'in_progress', 'success', 'failed', 'rolled_back')),
  commit_sha     text not null,
  image_tag      text,
  deploy_source  text not null default 'github_actions',
  started_at     timestamptz not null default now(),
  completed_at   timestamptz,
  duration_ms    integer generated always as (
    case when completed_at is not null
      then extract(epoch from (completed_at - started_at))::integer * 1000
      else null
    end
  ) stored,
  details        jsonb not null default '{}',
  uri            text generated always as (
    'eco-base://deployment/' || environment || '/' || id::text
  ) stored,
  urn            text generated always as (
    'urn:eco-base:deployment:' || environment || ':' || id::text
  ) stored,
  created_at     timestamptz not null default now()
);

create index if not exists idx_deployment_history_env
  on public.deployment_history(environment, started_at desc);
create index if not exists idx_deployment_history_status
  on public.deployment_history(status);
create index if not exists idx_deployment_history_platform
  on public.deployment_history(platform_id);

alter table public.deployment_history enable row level security;

create policy "Authenticated users can read deployments"
  on public.deployment_history for select
  using (auth.role() = 'authenticated');

create policy "Service role can manage deployments"
  on public.deployment_history for all
  using (auth.role() = 'service_role')
  with check (auth.role() = 'service_role');

-- ─── SLO Metrics Table ──────────────────────────────────────────────────
-- Stores SLO measurements for availability, latency, error rate
create table if not exists public.slo_metrics (
  id              uuid default uuid_generate_v4() primary key,
  service_name    text not null,
  metric_type     text not null check (metric_type in ('availability', 'latency_p95', 'latency_p99', 'error_rate')),
  value           numeric not null,
  target          numeric not null,
  within_slo      boolean generated always as (
    case
      when metric_type = 'availability' then value >= target
      when metric_type in ('latency_p95', 'latency_p99') then value <= target
      when metric_type = 'error_rate' then value <= target
      else false
    end
  ) stored,
  window_start    timestamptz not null,
  window_end      timestamptz not null,
  details         jsonb not null default '{}',
  uri             text generated always as (
    'eco-base://slo/' || service_name || '/' || metric_type
  ) stored,
  created_at      timestamptz not null default now()
);

create index if not exists idx_slo_metrics_service
  on public.slo_metrics(service_name, metric_type, window_start desc);
create index if not exists idx_slo_metrics_breach
  on public.slo_metrics(within_slo) where within_slo = false;

alter table public.slo_metrics enable row level security;

create policy "Authenticated users can read SLO metrics"
  on public.slo_metrics for select
  using (auth.role() = 'authenticated');

create policy "Service role can manage SLO metrics"
  on public.slo_metrics for all
  using (auth.role() = 'service_role')
  with check (auth.role() = 'service_role');

-- ─── Realtime Publication ───────────────────────────────────────────────
-- Enable Realtime for key tables (Pro feature: up to 500 concurrent connections)
alter publication supabase_realtime add table public.service_registry;
alter publication supabase_realtime add table public.deployment_history;
alter publication supabase_realtime add table public.slo_metrics;

-- ─── Database Webhook Trigger Functions ─────────────────────────────────
-- These functions call the webhook-handler Edge Function on data changes

create or replace function public.notify_webhook_handler()
returns trigger as $$
declare
  payload jsonb;
  edge_function_url text;
begin
  edge_function_url := current_setting('app.settings.supabase_url', true)
    || '/functions/v1/webhook-handler';

  payload := jsonb_build_object(
    'type', TG_OP,
    'table', TG_TABLE_NAME,
    'schema', TG_TABLE_SCHEMA,
    'record', case when TG_OP = 'DELETE' then null else row_to_json(NEW) end,
    'old_record', case when TG_OP = 'INSERT' then null else row_to_json(OLD) end
  );

  -- Use pg_net for async HTTP call (non-blocking)
  perform net.http_post(
    url := edge_function_url,
    headers := jsonb_build_object(
      'Content-Type', 'application/json',
      'Authorization', 'Bearer ' || current_setting('app.settings.service_role_key', true)
    ),
    body := payload
  );

  return coalesce(NEW, OLD);
end;
$$ language plpgsql security definer;

-- Webhook triggers for service_registry health changes
create trigger webhook_service_registry_changes
  after insert or update on public.service_registry
  for each row execute function public.notify_webhook_handler();

-- Webhook triggers for platform status changes
create trigger webhook_platform_changes
  after update on public.platforms
  for each row
  when (OLD.status is distinct from NEW.status)
  execute function public.notify_webhook_handler();

-- Webhook triggers for AI job completion
create trigger webhook_ai_job_completion
  after update on public.ai_jobs
  for each row
  when (OLD.status is distinct from NEW.status and NEW.status in ('completed', 'failed'))
  execute function public.notify_webhook_handler();

-- ─── Comment: migration complete ────────────────────────────────────────
-- This migration adds Pro-tier enhancements:
--   1. Storage buckets: audit-attachments (private), platform-assets (public)
--   2. deployment_history table for DORA metrics tracking
--   3. slo_metrics table for SLO compliance monitoring
--   4. Realtime subscriptions for service_registry, deployment_history, slo_metrics
--   5. Database webhooks via pg_net → Edge Functions for event-driven architecture
