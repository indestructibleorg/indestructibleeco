-- IndestructibleEco v1.0 — Unified Database Schema
-- URI: indestructibleeco://backend/supabase/schema
-- Target: Supabase PostgreSQL 15+

create extension if not exists "uuid-ossp";
create extension if not exists "pgcrypto";

-- ─── Users ───────────────────────────────────────────────────────────
create table public.users (
  id           uuid primary key references auth.users(id) on delete cascade,
  email        text unique not null,
  role         text not null default 'member'
               check (role in ('admin','member','viewer','service_role')),
  display_name text,
  avatar_url   text,
  urn          text generated always as
               ('urn:indestructibleeco:iam:user:' || id::text) stored,
  created_at   timestamptz not null default now(),
  updated_at   timestamptz not null default now()
);

create index idx_users_email on public.users(email);
create index idx_users_role  on public.users(role);

-- ─── Platforms ───────────────────────────────────────────────────────
create table public.platforms (
  id             uuid default uuid_generate_v4() primary key,
  name           text not null,
  slug           text unique not null,
  type           text not null default 'custom'
                 check (type in ('web','desktop','im','api','worker','custom')),
  status         text not null default 'inactive'
                 check (status in ('active','inactive','maintenance','deprecated')),
  config         jsonb not null default '{}',
  capabilities   text[] not null default '{}',
  k8s_namespace  text not null default 'indestructibleeco',
  deploy_target  text not null default '',
  uri            text generated always as
                 ('indestructibleeco://platform/module/' || slug) stored,
  urn            text,
  owner_id       uuid references public.users(id) on delete set null,
  created_at     timestamptz not null default now(),
  updated_at     timestamptz not null default now()
);

create index idx_platforms_slug   on public.platforms(slug);
create index idx_platforms_status on public.platforms(status);
create index idx_platforms_owner  on public.platforms(owner_id);

-- ─── AI Jobs ─────────────────────────────────────────────────────────
create table public.ai_jobs (
  id           uuid default uuid_generate_v4() primary key,
  user_id      uuid not null references public.users(id) on delete cascade,
  status       text not null default 'pending'
               check (status in ('pending','running','completed','failed','cancelled')),
  prompt       text not null,
  model_id     text not null,
  engine       text,
  result       text,
  error        text,
  tokens_used  integer default 0,
  uri          text,
  urn          text,
  created_at   timestamptz not null default now(),
  completed_at timestamptz
);

create index idx_ai_jobs_user   on public.ai_jobs(user_id);
create index idx_ai_jobs_status on public.ai_jobs(status);

-- ─── YAML Documents ──────────────────────────────────────────────────
create table public.yaml_documents (
  id             uuid default uuid_generate_v4() primary key,
  unique_id      text unique not null,
  target_system  text not null,
  schema_version text not null default 'v8',
  generated_by   text not null default 'yaml-toolkit-v8',
  qyaml_content  jsonb not null,
  owner_id       uuid references public.users(id) on delete set null,
  uri            text,
  urn            text,
  created_at     timestamptz not null default now()
);

create index idx_yaml_docs_unique on public.yaml_documents(unique_id);

-- ─── Service Registry ────────────────────────────────────────────────
create table public.service_registry (
  id                 uuid default uuid_generate_v4() primary key,
  service_name       text unique not null,
  service_endpoint   text not null,
  discovery_protocol text not null default 'consul',
  health_check_path  text not null default '/health',
  health_status      text not null default 'unknown'
                     check (health_status in ('healthy','degraded','unhealthy','unknown')),
  registry_ttl       integer not null default 30,
  k8s_namespace      text not null default 'indestructibleeco',
  uri                text,
  urn                text,
  last_heartbeat     timestamptz,
  created_at         timestamptz not null default now()
);

create index idx_service_registry_name on public.service_registry(service_name);

-- ─── Governance Records ──────────────────────────────────────────────
create table public.governance_records (
  id              uuid default uuid_generate_v4() primary key,
  action          text not null,
  resource_type   text not null,
  resource_id     text not null,
  actor_id        uuid references public.users(id) on delete set null,
  details         jsonb not null default '{}',
  compliance_tags text[] not null default '{}',
  uri             text,
  urn             text,
  created_at      timestamptz not null default now()
);

create index idx_governance_action   on public.governance_records(action);
create index idx_governance_resource on public.governance_records(resource_type, resource_id);

-- ─── Enable RLS ──────────────────────────────────────────────────────
alter table public.users enable row level security;
alter table public.platforms enable row level security;
alter table public.ai_jobs enable row level security;
alter table public.yaml_documents enable row level security;
alter table public.service_registry enable row level security;
alter table public.governance_records enable row level security;

-- ─── Updated-at trigger ──────────────────────────────────────────────
create or replace function public.handle_updated_at()
returns trigger as $$
begin
  new.updated_at = now();
  return new;
end;
$$ language plpgsql;

create trigger set_users_updated_at
  before update on public.users
  for each row execute function public.handle_updated_at();

create trigger set_platforms_updated_at
  before update on public.platforms
  for each row execute function public.handle_updated_at();
