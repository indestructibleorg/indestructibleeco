create extension if not exists "uuid-ossp";
create table public.profiles (id uuid primary key, email text unique not null, role text not null default 'member', created_at timestamptz default now());
create table public.platforms (id uuid default uuid_generate_v4() primary key, name text not null, slug text unique not null, type text not null, status text not null default 'inactive', created_at timestamptz default now());
create table public.yaml_documents (id uuid default uuid_generate_v4() primary key, unique_id text unique not null, target_system text not null, schema_version text not null default 'v8', generated_by text not null, qyaml_content jsonb not null, created_at timestamptz default now());
create table public.ai_jobs (id uuid default uuid_generate_v4() primary key, status text not null default 'pending', prompt text not null, model_id text not null, result text, error text, created_at timestamptz default now());
alter table public.profiles enable row level security;
alter table public.platforms enable row level security;
alter table public.yaml_documents enable row level security;
alter table public.ai_jobs enable row level security;
