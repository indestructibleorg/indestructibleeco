/**
 * IndestructibleEco — Supabase Client Service
 * URI: indestructibleeco://backend/api/services/supabase
 *
 * Wraps @supabase/supabase-js for typed CRUD on all platform tables.
 * Uses service_role key for server-side operations with RLS bypass.
 */

import { createClient, SupabaseClient } from "@supabase/supabase-js";
import { config } from "../config";

// ── Singleton ────────────────────────────────────────────────────────────────

let _client: SupabaseClient | null = null;

export function getSupabase(): SupabaseClient | null {
  if (!_client) {
    if (!config.supabaseUrl || !config.supabaseUrl.startsWith("http")) {
      return null;
    }
    _client = createClient(
      config.supabaseUrl,
      config.supabaseServiceRoleKey || config.supabaseKey,
      {
        auth: { autoRefreshToken: false, persistSession: false },
        db: { schema: "public" },
      }
    );
  }
  return _client;
}

/**
 * Returns the Supabase client or throws if not configured.
 * Use this in all DB operations that require a valid client.
 */
export function getSupabaseOrThrow(): SupabaseClient {
  const client = getSupabase();
  if (!client) {
    throw new Error("Supabase client not initialized — check SUPABASE_URL and SUPABASE_KEY env vars");
  }
  return client;
}

// ── Row Types ────────────────────────────────────────────────────────────────

export interface UserRow {
  id: string;
  email: string;
  role: string;
  display_name: string | null;
  avatar_url: string | null;
  metadata: Record<string, unknown>;
  last_sign_in_at: string | null;
  urn: string;
  created_at: string;
  updated_at: string;
}

export interface PlatformRow {
  id: string;
  name: string;
  slug: string;
  type: string;
  status: string;
  config: Record<string, unknown>;
  capabilities: string[];
  k8s_namespace: string;
  deploy_target: string;
  uri: string;
  urn: string | null;
  owner_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface AiJobRow {
  id: string;
  user_id: string;
  status: string;
  prompt: string;
  model_id: string;
  engine: string | null;
  result: string | null;
  error: string | null;
  tokens_used: number;
  usage: Record<string, unknown> | null;
  model_params: Record<string, unknown>;
  latency_ms: number | null;
  uri: string | null;
  urn: string | null;
  created_at: string;
  completed_at: string | null;
}

export interface GovernanceRow {
  id: string;
  action: string;
  resource_type: string;
  resource_id: string;
  actor_id: string | null;
  details: Record<string, unknown>;
  compliance_tags: string[];
  uri: string | null;
  urn: string | null;
  created_at: string;
}

// ── Users ────────────────────────────────────────────────────────────────────

export async function getUserById(userId: string): Promise<UserRow | null> {
  const supabase = getSupabase();
  if (!supabase) {
    console.error("Supabase client not initialized");
    return null;
  }

  const { data, error } = await supabase
  const { data, error } = await getSupabaseOrThrow()
    .from("users")
    .select("*")
    .eq("id", userId)
    .single();

  if (error) {
    console.error(`Failed to get user ${userId}:`, error.message);
    return null;
  }
  return data as UserRow;
}

export async function updateUser(
  userId: string,
  updates: Partial<Pick<UserRow, "display_name" | "avatar_url" | "metadata">>
): Promise<UserRow | null> {
  const supabase = getSupabase();
  if (!supabase) {
    throw new Error("Supabase client not initialized");
  }

  const { data, error } = await supabase
  const { data, error } = await getSupabaseOrThrow()
    .from("users")
    .update(updates)
    .eq("id", userId)
    .select()
    .single();
  if (error) throw new Error(`Failed to update user: ${error.message}`);
  return data as UserRow;
}

// ── Platforms ────────────────────────────────────────────────────────────────

export async function listPlatforms(): Promise<PlatformRow[]> {
  const supabase = getSupabase();
  if (!supabase) {
    throw new Error("Supabase client not initialized");
  }

  const { data, error } = await supabase
  const { data, error } = await getSupabaseOrThrow()
    .from("platforms")
    .select("*")
    .order("created_at", { ascending: false });
  if (error) throw new Error(`Failed to list platforms: ${error.message}`);
  return (data ?? []) as PlatformRow[];
}

export async function getPlatformById(id: string): Promise<PlatformRow | null> {
  const supabase = getSupabase();
  if (!supabase) {
    console.error("Supabase client not initialized");
    return null;
  }

  const { data, error } = await supabase
  const { data, error } = await getSupabaseOrThrow()
    .from("platforms")
    .select("*")
    .eq("id", id)
    .single();

  if (error) {
    console.error(`Failed to get platform ${id}:`, error.message);
    return null;
  }
  return data as PlatformRow;
}

export async function createPlatform(
  record: Pick<PlatformRow, "name" | "slug" | "type" | "config" | "capabilities" | "owner_id"> &
    Partial<Pick<PlatformRow, "k8s_namespace" | "deploy_target" | "urn">>
): Promise<PlatformRow> {
  const supabase = getSupabase();
  if (!supabase) {
    throw new Error("Supabase client not initialized");
  }

  const { data, error } = await supabase
  const { data, error } = await getSupabaseOrThrow()
    .from("platforms")
    .insert(record)
    .select()
    .single();
  if (error) throw new Error(`Failed to create platform: ${error.message}`);
  return data as PlatformRow;
}

export async function updatePlatform(
  id: string,
  updates: Partial<Pick<PlatformRow, "name" | "status" | "config" | "capabilities" | "deploy_target">>
): Promise<PlatformRow> {
  const supabase = getSupabase();
  if (!supabase) {
    throw new Error("Supabase client not initialized");
  }

  const { data, error } = await supabase
  const { data, error } = await getSupabaseOrThrow()
    .from("platforms")
    .update(updates)
    .eq("id", id)
    .select()
    .single();
  if (error) throw new Error(`Failed to update platform: ${error.message}`);
  return data as PlatformRow;
}

export async function deletePlatform(id: string): Promise<void> {
  const supabase = getSupabase();
  if (!supabase) {
    throw new Error("Supabase client not initialized");
  }

  const { error } = await supabase
  const { error } = await getSupabaseOrThrow()
    .from("platforms")
    .delete()
    .eq("id", id);
  if (error) throw new Error(`Failed to delete platform: ${error.message}`);
}

// ── AI Jobs ──────────────────────────────────────────────────────────────────

export async function createAiJob(
  record: Pick<AiJobRow, "user_id" | "prompt" | "model_id"> &
    Partial<Pick<AiJobRow, "model_params" | "uri" | "urn">>
): Promise<AiJobRow> {
  const supabase = getSupabase();
  if (!supabase) {
    throw new Error("Supabase client not initialized");
  }

  const { data, error } = await supabase
  const { data, error } = await getSupabaseOrThrow()
    .from("ai_jobs")
    .insert({ ...record, status: "pending" })
    .select()
    .single();
  if (error) throw new Error(`Failed to create AI job: ${error.message}`);
  return data as AiJobRow;
}

export async function getAiJob(jobId: string): Promise<AiJobRow | null> {
  const supabase = getSupabase();
  if (!supabase) {
    console.error("Supabase client not initialized");
    return null;
  }

  const { data, error } = await supabase
  const { data, error } = await getSupabaseOrThrow()
    .from("ai_jobs")
    .select("*")
    .eq("id", jobId)
    .single();

  if (error) {
    console.error(`Failed to get AI job ${jobId}:`, error.message);
    return null;
  }
  return data as AiJobRow;
}

export async function updateAiJob(
  jobId: string,
  updates: Partial<Pick<AiJobRow, "status" | "result" | "error" | "engine" | "tokens_used" | "usage" | "latency_ms" | "completed_at">>
): Promise<AiJobRow> {
  const supabase = getSupabase();
  if (!supabase) {
    throw new Error("Supabase client not initialized");
  }

  const { data, error } = await supabase
  const { data, error } = await getSupabaseOrThrow()
    .from("ai_jobs")
    .update(updates)
    .eq("id", jobId)
    .select()
    .single();
  if (error) throw new Error(`Failed to update AI job: ${error.message}`);
  return data as AiJobRow;
}

export async function listAiJobsByUser(
  userId: string,
  limit = 50
): Promise<AiJobRow[]> {
  const supabase = getSupabase();
  if (!supabase) {
    throw new Error("Supabase client not initialized");
  }

  const { data, error } = await supabase
  const { data, error } = await getSupabaseOrThrow()
    .from("ai_jobs")
    .select("*")
    .eq("user_id", userId)
    .order("created_at", { ascending: false })
    .limit(limit);
  if (error) throw new Error(`Failed to list AI jobs: ${error.message}`);
  return (data ?? []) as AiJobRow[];
}

export async function getPendingJobs(limit = 20): Promise<AiJobRow[]> {
  const supabase = getSupabase();
  if (!supabase) {
    throw new Error("Supabase client not initialized");
  }

  const { data, error } = await supabase
  const { data, error } = await getSupabaseOrThrow()
    .from("ai_jobs")
    .select("*")
    .in("status", ["pending", "running"])
    .order("created_at", { ascending: true })
    .limit(limit);
  if (error) throw new Error(`Failed to list pending jobs: ${error.message}`);
  return (data ?? []) as AiJobRow[];
}

// ── Governance ───────────────────────────────────────────────────────────────

export async function insertGovernanceRecord(
  record: Pick<GovernanceRow, "action" | "resource_type" | "resource_id"> &
    Partial<Pick<GovernanceRow, "actor_id" | "details" | "compliance_tags" | "uri" | "urn">>
): Promise<GovernanceRow> {
  const supabase = getSupabase();
  if (!supabase) {
    throw new Error("Supabase client not initialized");
  }

  const { data, error } = await supabase
  const { data, error } = await getSupabaseOrThrow()
    .from("governance_records")
    .insert(record)
    .select()
    .single();
  if (error) throw new Error(`Failed to insert governance record: ${error.message}`);
  return data as GovernanceRow;
}

export async function listGovernanceRecords(
  filters?: { resource_type?: string; resource_id?: string; action?: string },
  limit = 100
): Promise<GovernanceRow[]> {
  const supabase = getSupabase();
  if (!supabase) {
    throw new Error("Supabase client not initialized");
  }

  let query = supabase
  let query = getSupabaseOrThrow()
    .from("governance_records")
    .select("*")
    .order("created_at", { ascending: false })
    .limit(limit);

  if (filters?.resource_type) query = query.eq("resource_type", filters.resource_type);
  if (filters?.resource_id) query = query.eq("resource_id", filters.resource_id);
  if (filters?.action) query = query.eq("action", filters.action);

  const { data, error } = await query;
  if (error) throw new Error(`Failed to list governance records: ${error.message}`);
  return (data ?? []) as GovernanceRow[];
}