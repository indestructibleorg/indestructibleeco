// eco-base://supabase/functions/audit-log
// Audit log ingestion endpoint for governance compliance
// Accepts structured audit events and writes to governance_records table
// Supports: SOC2, ISO27001 audit trail requirements

import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
};

interface AuditEvent {
  action: string;
  resource_type: string;
  resource_id: string;
  actor_id?: string;
  details?: Record<string, unknown>;
  compliance_tags?: string[];
  trace_id?: string;
  span_id?: string;
  session_id?: string;
}

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") {
    return new Response("ok", { headers: corsHeaders });
  }

  if (req.method !== "POST") {
    return new Response(
      JSON.stringify({ error: "Method not allowed" }),
      { status: 405, headers: { ...corsHeaders, "Content-Type": "application/json" } }
    );
  }

  const supabaseUrl = Deno.env.get("SUPABASE_URL") ?? "";
  const supabaseKey = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY") ?? "";
  const supabase = createClient(supabaseUrl, supabaseKey);

  try {
    const body = await req.json();

    // Support single event or batch
    const events: AuditEvent[] = Array.isArray(body) ? body : [body];

    if (events.length === 0) {
      return new Response(
        JSON.stringify({ error: "No events provided" }),
        { status: 400, headers: { ...corsHeaders, "Content-Type": "application/json" } }
      );
    }

    if (events.length > 100) {
      return new Response(
        JSON.stringify({ error: "Batch size exceeds maximum of 100 events" }),
        { status: 400, headers: { ...corsHeaders, "Content-Type": "application/json" } }
      );
    }

    const records = events.map((event) => ({
      action: event.action,
      resource_type: event.resource_type,
      resource_id: event.resource_id,
      actor_id: event.actor_id || null,
      details: {
        ...event.details,
        trace_id: event.trace_id,
        span_id: event.span_id,
        session_id: event.session_id,
        ingested_at: new Date().toISOString(),
        source: "edge-function",
      },
      compliance_tags: event.compliance_tags || [],
      uri: `eco-base://audit/${event.resource_type}/${event.resource_id}/${Date.now()}`,
      urn: `urn:eco-base:audit:${event.resource_type}:${event.resource_id}`,
    }));

    const { data, error } = await supabase
      .from("governance_records")
      .insert(records)
      .select("id, action, resource_type, resource_id, created_at");

    if (error) {
      console.error("Audit log insert error:", error);
      return new Response(
        JSON.stringify({
          error: "Failed to insert audit records",
          details: error.message,
        }),
        { status: 500, headers: { ...corsHeaders, "Content-Type": "application/json" } }
      );
    }

    return new Response(
      JSON.stringify({
        status: "success",
        inserted: data?.length ?? 0,
        records: data,
        uri: "eco-base://supabase/functions/audit-log",
        urn: "urn:eco-base:supabase:functions:audit-log:v1",
      }),
      { headers: { ...corsHeaders, "Content-Type": "application/json" } }
    );
  } catch (e) {
    return new Response(
      JSON.stringify({ error: "Invalid request body", details: (e as Error).message }),
      { status: 400, headers: { ...corsHeaders, "Content-Type": "application/json" } }
    );
  }
});
