// eco-base://supabase/functions/webhook-handler
// Database webhook handler for event-driven architecture
// Receives Supabase Database Webhooks and routes events to appropriate handlers
// Supports: INSERT/UPDATE/DELETE on governance_records, service_registry, platforms

import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
};

interface WebhookPayload {
  type: "INSERT" | "UPDATE" | "DELETE";
  table: string;
  schema: string;
  record: Record<string, unknown> | null;
  old_record: Record<string, unknown> | null;
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
    const payload: WebhookPayload = await req.json();
    const { type, table, record, old_record } = payload;

    console.log(`Webhook received: ${type} on ${table}`);

    // Route based on table and event type
    switch (table) {
      case "service_registry": {
        if (type === "UPDATE" && record) {
          const oldStatus = (old_record as Record<string, unknown>)?.health_status;
          const newStatus = record.health_status;
          if (oldStatus !== newStatus && newStatus === "unhealthy") {
            // Service went unhealthy — log governance event
            await supabase.from("governance_records").insert({
              action: "service_health_degraded",
              resource_type: "service",
              resource_id: record.service_name as string,
              details: {
                old_status: oldStatus,
                new_status: newStatus,
                service_endpoint: record.service_endpoint,
                detected_at: new Date().toISOString(),
              },
              compliance_tags: ["slo-breach", "auto-detected"],
              uri: `eco-base://webhook/service-health/${record.service_name}/${Date.now()}`,
              urn: `urn:eco-base:webhook:service-health:${record.service_name}`,
            });
          }
        }
        break;
      }

      case "platforms": {
        if (type === "UPDATE" && record) {
          const oldStatus = (old_record as Record<string, unknown>)?.status;
          const newStatus = record.status;
          if (oldStatus !== newStatus) {
            await supabase.from("governance_records").insert({
              action: "platform_status_changed",
              resource_type: "platform",
              resource_id: record.slug as string,
              details: {
                old_status: oldStatus,
                new_status: newStatus,
                changed_at: new Date().toISOString(),
              },
              compliance_tags: ["platform-lifecycle"],
              uri: `eco-base://webhook/platform-status/${record.slug}/${Date.now()}`,
              urn: `urn:eco-base:webhook:platform-status:${record.slug}`,
            });
          }
        }
        break;
      }

      case "ai_jobs": {
        if (type === "UPDATE" && record) {
          const newStatus = record.status;
          if (newStatus === "completed" || newStatus === "failed") {
            await supabase.from("governance_records").insert({
              action: `ai_job_${newStatus}`,
              resource_type: "ai_job",
              resource_id: record.id as string,
              actor_id: record.user_id as string,
              details: {
                model_id: record.model_id,
                tokens_used: record.tokens_used,
                latency_ms: record.latency_ms,
                status: newStatus,
                error: record.error,
              },
              compliance_tags: ["ai-usage-tracking"],
              uri: `eco-base://webhook/ai-job/${record.id}/${Date.now()}`,
              urn: `urn:eco-base:webhook:ai-job:${record.id}`,
            });
          }
        }
        break;
      }

      default:
        console.log(`No handler for table: ${table}`);
    }

    return new Response(
      JSON.stringify({
        status: "processed",
        event_type: type,
        table,
        timestamp: new Date().toISOString(),
        uri: "eco-base://supabase/functions/webhook-handler",
        urn: "urn:eco-base:supabase:functions:webhook-handler:v1",
      }),
      { headers: { ...corsHeaders, "Content-Type": "application/json" } }
    );
  } catch (e) {
    console.error("Webhook handler error:", e);
    return new Response(
      JSON.stringify({ error: "Webhook processing failed", details: (e as Error).message }),
      { status: 500, headers: { ...corsHeaders, "Content-Type": "application/json" } }
    );
  }
});
