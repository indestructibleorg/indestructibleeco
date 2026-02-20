/**
 * IndestructibleEco — YAML Routes
 * URI: indestructibleeco://backend/api/routes/yaml
 *
 * Proxies YAML generation/validation to backend/ai YAML Toolkit.
 * Falls back to local generation when AI service is unavailable.
 */

import { Router, Request, Response, NextFunction } from "express";
import { requireAuth, AuthenticatedRequest } from "../middleware/auth";
import { config } from "../config";
import { v4 as uuidv4 } from "uuid";

export const yamlRouter = Router();
yamlRouter.use(requireAuth);

// POST /api/v1/yaml/generate — Generate .qyaml manifest
yamlRouter.post("/generate", async (req: AuthenticatedRequest, res: Response, next: NextFunction): Promise<void> => {
  try {
    const { module: mod, target = "k8s" } = req.body;
    if (!mod?.name) {
      res.status(400).json({ error: "validation_error", message: "module.name is required" });
      return;
    }

    // Attempt upstream AI service
    try {
      const upstream = await fetch(`${config.aiServiceHttp}/api/v1/yaml/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ module: mod, target }),
        signal: AbortSignal.timeout(10000),
      });

      if (upstream.ok) {
        const data = await upstream.json();
        res.status(200).json(data);
        return;
      }
    } catch {
      // AI service unavailable — fall back to local generation
    }

    // Local fallback generation
    const uniqueId = uuidv4();
    const qyaml = {
      document_metadata: {
        unique_id: uniqueId,
        target_system: target,
        cross_layer_binding: mod.depends_on ?? [],
        schema_version: "v8",
        generated_by: "yaml-toolkit-v8",
        uri: `indestructibleeco://yaml/document/${uniqueId}`,
        urn: `urn:indestructibleeco:yaml:document:${uniqueId}`,
        created_at: new Date().toISOString(),
      },
      governance_info: {
        owner: "platform-team",
        approval_chain: [],
        compliance_tags: ["internal"],
        lifecycle_policy: "standard",
      },
      registry_binding: {
        service_endpoint: `http://${mod.name}:${mod.ports?.[0] ?? 80}`,
        discovery_protocol: "consul",
        health_check_path: "/health",
        registry_ttl: 30,
        k8s_namespace: "indestructibleeco",
      },
      vector_alignment_map: {
        alignment_model: "quantum-bert-xxl-v1",
        coherence_vector: [],
        function_keyword: [mod.name],
        contextual_binding: `${mod.name} -> [${(mod.depends_on ?? []).join(", ")}]`,
      },
    };

    res.status(200).json({
      qyaml_content: JSON.stringify(qyaml, null, 2),
      valid: true,
      warnings: ["Generated locally — AI service unavailable"],
      source: "local-fallback",
    });
  } catch (err) {
    next(err);
  }
});

// POST /api/v1/yaml/validate — Validate .qyaml content
yamlRouter.post("/validate", async (req: AuthenticatedRequest, res: Response, next: NextFunction): Promise<void> => {
  try {
    const content = req.body?.content;
    let parsed: Record<string, unknown>;

    try {
      parsed = typeof content === "string" ? JSON.parse(content) : (content || req.body);
    } catch {
      res.status(400).json({ valid: false, missing_blocks: [], error: "Invalid JSON content" });
      return;
    }

    // Attempt upstream AI service
    try {
      const upstream = await fetch(`${config.aiServiceHttp}/api/v1/yaml/validate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ content: typeof parsed === "string" ? parsed : JSON.stringify(parsed) }),
        signal: AbortSignal.timeout(5000),
      });

      if (upstream.ok) {
        const data = await upstream.json();
        res.status(200).json(data);
        return;
      }
    } catch {
      // AI service unavailable — fall back to local validation
    }

    // Local fallback validation
    const requiredBlocks = ["document_metadata", "governance_info", "registry_binding", "vector_alignment_map"];
    const missing = requiredBlocks.filter((k) => !(k in parsed));

    const requiredFields = ["unique_id", "schema_version", "generated_by"];
    const missingFields: string[] = [];
    const meta = parsed.document_metadata as Record<string, unknown> | undefined;
    if (meta) {
      for (const field of requiredFields) {
        if (!(field in meta)) missingFields.push(`document_metadata.${field}`);
      }
    }

    res.status(200).json({
      valid: missing.length === 0 && missingFields.length === 0,
      missing_blocks: missing,
      missing_fields: missingFields,
      source: "local-fallback",
    });
  } catch (err) {
    next(err);
  }
});

// GET /api/v1/yaml/registry — List registered services
yamlRouter.get("/registry", async (req: AuthenticatedRequest, res: Response, next: NextFunction): Promise<void> => {
  try {
    const upstream = await fetch(`${config.aiServiceHttp}/api/v1/yaml/registry`, {
      method: "GET",
      headers: { "Content-Type": "application/json" },
      signal: AbortSignal.timeout(5000),
    });

    if (upstream.ok) {
      const data = await upstream.json();
      res.status(200).json(data);
      return;
    }

    res.status(200).json({ services: [] });
  } catch {
    res.status(200).json({ services: [] });
  }
});

// GET /api/v1/yaml/vector/:id — Get vector alignment for a document
yamlRouter.get("/vector/:id", async (req: AuthenticatedRequest, res: Response, next: NextFunction): Promise<void> => {
  try {
    const upstream = await fetch(`${config.aiServiceHttp}/api/v1/yaml/vector/${req.params.id as string}`, {
      method: "GET",
      headers: { "Content-Type": "application/json" },
      signal: AbortSignal.timeout(5000),
    });

    if (upstream.ok) {
      const data = await upstream.json();
      res.status(200).json(data);
      return;
    }

    res.status(200).json({ id: req.params.id as string, vector: [], source: "local-fallback" });
  } catch {
    res.status(200).json({ id: req.params.id as string, vector: [], source: "local-fallback" });
  }
});