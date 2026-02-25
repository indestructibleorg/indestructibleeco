// eco-base://supabase/functions/health-check
// Health check endpoint for monitoring and SLO validation
// Checks: database connectivity, auth service, storage service, edge runtime

import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
};

interface HealthStatus {
  service: string;
  status: "healthy" | "degraded" | "unhealthy";
  latency_ms: number;
  details?: string;
}

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") {
    return new Response("ok", { headers: corsHeaders });
  }

  const startTime = performance.now();
  const checks: HealthStatus[] = [];

  const supabaseUrl = Deno.env.get("SUPABASE_URL") ?? "";
  const supabaseKey = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY") ?? "";
  const supabase = createClient(supabaseUrl, supabaseKey);

  // Check 1: Database connectivity
  const dbStart = performance.now();
  try {
    const { data, error } = await supabase.from("service_registry").select("id").limit(1);
    const dbLatency = performance.now() - dbStart;
    checks.push({
      service: "database",
      status: error ? "degraded" : "healthy",
      latency_ms: Math.round(dbLatency),
      details: error ? error.message : undefined,
    });
  } catch (e) {
    checks.push({
      service: "database",
      status: "unhealthy",
      latency_ms: Math.round(performance.now() - dbStart),
      details: (e as Error).message,
    });
  }

  // Check 2: Auth service
  const authStart = performance.now();
  try {
    const { data, error } = await supabase.auth.getSession();
    const authLatency = performance.now() - authStart;
    checks.push({
      service: "auth",
      status: error ? "degraded" : "healthy",
      latency_ms: Math.round(authLatency),
      details: error ? error.message : undefined,
    });
  } catch (e) {
    checks.push({
      service: "auth",
      status: "unhealthy",
      latency_ms: Math.round(performance.now() - authStart),
      details: (e as Error).message,
    });
  }

  // Check 3: Storage service
  const storageStart = performance.now();
  try {
    const { data, error } = await supabase.storage.listBuckets();
    const storageLatency = performance.now() - storageStart;
    checks.push({
      service: "storage",
      status: error ? "degraded" : "healthy",
      latency_ms: Math.round(storageLatency),
      details: error ? error.message : undefined,
    });
  } catch (e) {
    checks.push({
      service: "storage",
      status: "unhealthy",
      latency_ms: Math.round(performance.now() - storageStart),
      details: (e as Error).message,
    });
  }

  // Check 4: Edge runtime self-check
  checks.push({
    service: "edge_runtime",
    status: "healthy",
    latency_ms: 0,
    details: `Deno ${Deno.version.deno}`,
  });

  const totalLatency = Math.round(performance.now() - startTime);
  const overallStatus = checks.every((c) => c.status === "healthy")
    ? "healthy"
    : checks.some((c) => c.status === "unhealthy")
    ? "unhealthy"
    : "degraded";

  const response = {
    status: overallStatus,
    timestamp: new Date().toISOString(),
    total_latency_ms: totalLatency,
    uri: "eco-base://supabase/functions/health-check",
    urn: "urn:eco-base:supabase:functions:health-check:v1",
    checks,
    slo: {
      availability_target: "99.99%",
      p95_latency_target_ms: 200,
      current_p95_latency_ms: totalLatency,
      within_slo: totalLatency <= 200,
    },
  };

  return new Response(JSON.stringify(response, null, 2), {
    headers: { ...corsHeaders, "Content-Type": "application/json" },
    status: overallStatus === "unhealthy" ? 503 : 200,
  });
});
