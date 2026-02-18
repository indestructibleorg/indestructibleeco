import fs from "fs";
import path from "path";

/**
 * OpenAPI 3.1 specification generator for IndestructibleEco API.
 * Run: tsx src/openapi-gen.ts
 */
const spec = {
  openapi: "3.1.0",
  info: {
    title: "IndestructibleEco API",
    version: "1.0.0",
    description: "Enterprise cloud-native platform API — REST + WebSocket",
    contact: { name: "Platform Team", url: "https://indestructibleeco.io" },
  },
  servers: [
    { url: "https://api.indestructibleeco.io", description: "Production" },
    { url: "http://localhost:3000", description: "Local Development" },
  ],
  paths: {
    "/auth/signup": {
      post: {
        tags: ["Authentication"],
        summary: "Register new user",
        requestBody: {
          required: true,
          content: {
            "application/json": {
              schema: {
                type: "object",
                required: ["email", "password"],
                properties: {
                  email: { type: "string", format: "email" },
                  password: { type: "string", minLength: 8 },
                },
              },
            },
          },
        },
        responses: {
          "201": { description: "User created successfully" },
          "400": { description: "Validation error" },
        },
      },
    },
    "/auth/login": {
      post: {
        tags: ["Authentication"],
        summary: "Email/password login → JWT",
        requestBody: {
          required: true,
          content: {
            "application/json": {
              schema: {
                type: "object",
                required: ["email", "password"],
                properties: {
                  email: { type: "string", format: "email" },
                  password: { type: "string" },
                },
              },
            },
          },
        },
        responses: {
          "200": { description: "Login successful" },
          "401": { description: "Invalid credentials" },
        },
      },
    },
    "/auth/refresh": {
      post: {
        tags: ["Authentication"],
        summary: "Refresh access token",
        requestBody: {
          required: true,
          content: {
            "application/json": {
              schema: {
                type: "object",
                required: ["refreshToken"],
                properties: { refreshToken: { type: "string" } },
              },
            },
          },
        },
        responses: {
          "200": { description: "Token refreshed" },
          "401": { description: "Invalid refresh token" },
        },
      },
    },
    "/auth/logout": {
      post: {
        tags: ["Authentication"],
        summary: "Invalidate session",
        security: [{ bearerAuth: [] }],
        responses: { "200": { description: "Logged out" } },
      },
    },
    "/auth/me": {
      get: {
        tags: ["Authentication"],
        summary: "Current user profile",
        security: [{ bearerAuth: [] }],
        responses: { "200": { description: "User profile" } },
      },
    },
    "/api/v1/platforms": {
      get: {
        tags: ["Platforms"],
        summary: "List all platform modules",
        security: [{ bearerAuth: [] }],
        responses: { "200": { description: "Platform list" } },
      },
      post: {
        tags: ["Platforms"],
        summary: "Register new platform",
        security: [{ bearerAuth: [] }],
        requestBody: {
          required: true,
          content: {
            "application/json": {
              schema: {
                type: "object",
                required: ["name", "slug"],
                properties: {
                  name: { type: "string" },
                  slug: { type: "string" },
                  config: { type: "object" },
                  capabilities: { type: "array", items: { type: "string" } },
                  deployTarget: { type: "string" },
                },
              },
            },
          },
        },
        responses: {
          "201": { description: "Platform registered" },
          "400": { description: "Validation error" },
          "403": { description: "Admin access required" },
          "409": { description: "Slug conflict" },
        },
      },
    },
    "/api/v1/platforms/{id}": {
      get: {
        tags: ["Platforms"],
        summary: "Get platform detail",
        security: [{ bearerAuth: [] }],
        parameters: [{ name: "id", in: "path", required: true, schema: { type: "string" } }],
        responses: { "200": { description: "Platform detail" }, "404": { description: "Not found" } },
      },
      patch: {
        tags: ["Platforms"],
        summary: "Update platform config",
        security: [{ bearerAuth: [] }],
        parameters: [{ name: "id", in: "path", required: true, schema: { type: "string" } }],
        responses: { "200": { description: "Updated" }, "403": { description: "Admin only" }, "404": { description: "Not found" } },
      },
      delete: {
        tags: ["Platforms"],
        summary: "Deregister platform",
        security: [{ bearerAuth: [] }],
        parameters: [{ name: "id", in: "path", required: true, schema: { type: "string" } }],
        responses: { "200": { description: "Deregistered" }, "403": { description: "Admin only" }, "404": { description: "Not found" } },
      },
    },
    "/api/v1/yaml/generate": {
      post: {
        tags: ["YAML Governance"],
        summary: "Generate .qyaml from module JSON",
        security: [{ bearerAuth: [] }],
        requestBody: {
          required: true,
          content: {
            "application/json": {
              schema: {
                type: "object",
                required: ["name"],
                properties: {
                  name: { type: "string" },
                  image: { type: "string" },
                  replicas: { type: "integer" },
                  ports: { type: "array", items: { type: "integer" } },
                  depends_on: { type: "array", items: { type: "string" } },
                  target_system: { type: "string" },
                  kind: { type: "string" },
                },
              },
            },
          },
        },
        responses: { "200": { description: "Generated .qyaml" } },
      },
    },
    "/api/v1/yaml/validate": {
      post: {
        tags: ["YAML Governance"],
        summary: "Validate .qyaml document",
        security: [{ bearerAuth: [] }],
        responses: { "200": { description: "Validation result" } },
      },
    },
    "/api/v1/yaml/registry": {
      get: {
        tags: ["YAML Governance"],
        summary: "List all registered services",
        security: [{ bearerAuth: [] }],
        responses: { "200": { description: "Service registry" } },
      },
    },
    "/api/v1/yaml/vector/{id}": {
      get: {
        tags: ["YAML Governance"],
        summary: "Get vector alignment for service",
        security: [{ bearerAuth: [] }],
        parameters: [{ name: "id", in: "path", required: true, schema: { type: "string" } }],
        responses: { "200": { description: "Vector alignment" }, "404": { description: "Not found" } },
      },
    },
    "/api/v1/ai/generate": {
      post: {
        tags: ["AI Generation"],
        summary: "Submit generation job (async)",
        security: [{ bearerAuth: [] }],
        requestBody: {
          required: true,
          content: {
            "application/json": {
              schema: {
                type: "object",
                required: ["prompt"],
                properties: {
                  prompt: { type: "string" },
                  model_id: { type: "string" },
                  params: { type: "object" },
                },
              },
            },
          },
        },
        responses: { "202": { description: "Job accepted" } },
      },
    },
    "/api/v1/ai/jobs/{jobId}": {
      get: {
        tags: ["AI Generation"],
        summary: "Poll job status + result",
        security: [{ bearerAuth: [] }],
        parameters: [{ name: "jobId", in: "path", required: true, schema: { type: "string" } }],
        responses: { "200": { description: "Job status" }, "404": { description: "Not found" } },
      },
    },
    "/api/v1/ai/vector/align": {
      post: {
        tags: ["AI Generation"],
        summary: "Compute vector alignment",
        security: [{ bearerAuth: [] }],
        responses: { "200": { description: "Vector alignment result" } },
      },
    },
    "/api/v1/ai/models": {
      get: {
        tags: ["AI Generation"],
        summary: "List available inference models",
        security: [{ bearerAuth: [] }],
        responses: { "200": { description: "Model list" } },
      },
    },
    "/health": {
      get: {
        tags: ["Health"],
        summary: "Liveness probe",
        responses: { "200": { description: "Service healthy" } },
      },
    },
    "/ready": {
      get: {
        tags: ["Health"],
        summary: "Readiness probe (checks dependencies)",
        responses: { "200": { description: "Service ready" }, "503": { description: "Service not ready" } },
      },
    },
  },
  components: {
    securitySchemes: {
      bearerAuth: {
        type: "http",
        scheme: "bearer",
        bearerFormat: "JWT",
      },
    },
  },
};

const outPath = path.join(__dirname, "..", "openapi.json");
fs.writeFileSync(outPath, JSON.stringify(spec, null, 2));
console.log(`OpenAPI spec written to ${outPath}`);