// eco-base://supabase/functions/hello-world
// Basic hello-world endpoint for connectivity verification

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
};

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") {
    return new Response("ok", { headers: corsHeaders });
  }

  const { name } = await req.json().catch(() => ({ name: "World" }));

  const data = {
    message: `Hello ${name}!`,
    service: "eco-base",
    version: "1.1.0",
    timestamp: new Date().toISOString(),
    uri: "eco-base://functions/hello-world",
    urn: "urn:eco-base:functions:hello-world:v1",
  };

  return new Response(JSON.stringify(data, null, 2), {
    headers: { ...corsHeaders, "Content-Type": "application/json" },
  });
});
