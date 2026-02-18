import { Router, Response, NextFunction } from "express";
import { v1 as uuidv1 } from "uuid";
import { AuthenticatedRequest } from "../middleware/auth";
import { AppError } from "../middleware/error-handler";

const yamlRouter = Router();

// In-memory registry (production: Consul + Supabase)
const serviceRegistry = new Map<string, ServiceRecord>();

interface ServiceRecord {
  id: string;
  serviceName: string;
  endpoint: string;
  uri: string;
  urn: string;
  discoveryProtocol: string;
  healthCheckPath: string;
  registryTtl: number;
  health: string;
  registeredAt: string;
  lastHeartbeat: string;
}

interface GovernanceBlock {
  document_metadata: {
    unique_id: string;
    uri: string;
    urn: string;
    target_system: string;
    cross_layer_binding: string[];
    schema_version: string;
    generated_by: string;
    created_at: string;
  };
  governance_info: {
    owner: string;
    approval_chain: string[];
    compliance_tags: string[];
    lifecycle_policy: string;
  };
  registry_binding: {
    service_endpoint: string;
    discovery_protocol: string;
    health_check_path: string;
    registry_ttl: number;
  };
  vector_alignment_map: {
    alignment_model: string;
    coherence_vector_dim: number;
    function_keyword: string[];
    contextual_binding: string;
  };
}

function buildGovernanceBlock(
  name: string,
  namespace: string,
  kind: string,
  targetSystem: string,
  dependsOn: string[],
  keywords: string[]
): GovernanceBlock {
  const uid = uuidv1();
  return {
    document_metadata: {
      unique_id: uid,
      uri: `indestructibleeco://k8s/${namespace}/${kind.toLowerCase()}/${name}`,
      urn: `urn:indestructibleeco:k8s:${namespace}:${kind.toLowerCase()}:${name}:${uid}`,
      target_system: targetSystem,
      cross_layer_binding: dependsOn,
      schema_version: "v1",
      generated_by: "yaml-toolkit-v1",
      created_at: new Date().toISOString(),
    },
    governance_info: {
      owner: "platform-team",
      approval_chain: ["platform-team"],
      compliance_tags: ["zero-trust", "soc2", "internal"],
      lifecycle_policy: "active",
    },
    registry_binding: {
      service_endpoint: `http://${name}.${namespace}.svc.cluster.local`,
      discovery_protocol: "consul",
      health_check_path: "/health",
      registry_ttl: 30,
    },
    vector_alignment_map: {
      alignment_model: "quantum-bert-xxl-v1",
      coherence_vector_dim: 1024,
      function_keyword: keywords,
      contextual_binding: `${name} -> [${dependsOn.join(", ")}]`,
    },
  };
}

// POST /api/v1/yaml/generate
yamlRouter.post("/generate", async (req: AuthenticatedRequest, res: Response, next: NextFunction) => {
  try {
    const { name, image, replicas, ports, depends_on, target_system, kind } = req.body;
    if (!name) {
      throw new AppError(400, "validation_error", "Module name is required");
    }

    const namespace = "indestructibleeco";
    const k8sKind = kind || "Deployment";
    const targetSys = target_system || "gke-production";
    const keywords = [name, k8sKind.toLowerCase(), "backend"];
    const governance = buildGovernanceBlock(name, namespace, k8sKind, targetSys, depends_on || [], keywords);

    const uid = governance.document_metadata.unique_id;
    const uri = governance.document_metadata.uri;
    const urn = governance.document_metadata.urn;

    // Build K8s manifest
    const portEntries = (ports || [3000])
      .map((p: number) => `        - containerPort: ${p}`)
      .join("\n");

    const manifest = [
      "---",
      `apiVersion: apps/v1`,
      `kind: ${k8sKind}`,
      `metadata:`,
      `  name: ${name}`,
      `  namespace: ${namespace}`,
      `  labels:`,
      `    app: ${name}`,
      `    tier: backend`,
      `    generated-by: yaml-toolkit-v1`,
      `    unique-id: "${uid}"`,
      `  annotations:`,
      `    indestructibleeco/uri: "${uri}"`,
      `    indestructibleeco/urn: "${urn}"`,
      `spec:`,
      `  replicas: ${replicas || 3}`,
      `  selector:`,
      `    matchLabels:`,
      `      app: ${name}`,
      `  template:`,
      `    metadata:`,
      `      labels:`,
      `        app: ${name}`,
      `        version: v1.0.0`,
      `    spec:`,
      `      serviceAccountName: ${name}-sa`,
      `      containers:`,
      `      - name: ${name}`,
      `        image: ${image || `ghcr.io/indestructibleorg/${name}:v1.0.0`}`,
      `        ports:`,
      portEntries,
      `        resources:`,
      `          requests:`,
      `            cpu: 100m`,
      `            memory: 256Mi`,
      `          limits:`,
      `            cpu: 500m`,
      `            memory: 512Mi`,
    ].join("\n");

    const governanceYaml = [
      "---",
      "# YAML Toolkit v1 — Governance Block (auto-generated, manual editing prohibited)",
      `document_metadata:`,
      `  unique_id: "${governance.document_metadata.unique_id}"`,
      `  uri: "${governance.document_metadata.uri}"`,
      `  urn: "${governance.document_metadata.urn}"`,
      `  target_system: ${governance.document_metadata.target_system}`,
      `  cross_layer_binding: [${governance.document_metadata.cross_layer_binding.join(", ")}]`,
      `  schema_version: v1`,
      `  generated_by: yaml-toolkit-v1`,
      `  created_at: "${governance.document_metadata.created_at}"`,
      `governance_info:`,
      `  owner: ${governance.governance_info.owner}`,
      `  approval_chain: [${governance.governance_info.approval_chain.join(", ")}]`,
      `  compliance_tags: [${governance.governance_info.compliance_tags.join(", ")}]`,
      `  lifecycle_policy: ${governance.governance_info.lifecycle_policy}`,
      `registry_binding:`,
      `  service_endpoint: "${governance.registry_binding.service_endpoint}"`,
      `  discovery_protocol: ${governance.registry_binding.discovery_protocol}`,
      `  health_check_path: "${governance.registry_binding.health_check_path}"`,
      `  registry_ttl: ${governance.registry_binding.registry_ttl}`,
      `vector_alignment_map:`,
      `  alignment_model: ${governance.vector_alignment_map.alignment_model}`,
      `  coherence_vector_dim: ${governance.vector_alignment_map.coherence_vector_dim}`,
      `  function_keyword: [${governance.vector_alignment_map.function_keyword.join(", ")}]`,
      `  contextual_binding: "${governance.vector_alignment_map.contextual_binding}"`,
    ].join("\n");

    const qyamlContent = manifest + "\n" + governanceYaml + "\n";

    res.status(200).json({
      qyaml_content: qyamlContent,
      qyaml_uri: uri,
      unique_id: uid,
      valid: true,
      governance: governance,
    });
  } catch (err) {
    next(err);
  }
});

// POST /api/v1/yaml/validate
yamlRouter.post("/validate", async (req: AuthenticatedRequest, res: Response, next: NextFunction) => {
  try {
    const { qyaml_content } = req.body;
    if (!qyaml_content) {
      throw new AppError(400, "validation_error", "qyaml_content is required");
    }

    const errors: { path: string; message: string; severity: string }[] = [];
    const requiredBlocks = ["document_metadata", "governance_info", "registry_binding", "vector_alignment_map"];

    for (const block of requiredBlocks) {
      if (!qyaml_content.includes(`${block}:`)) {
        errors.push({ path: block, message: `Missing mandatory governance block: ${block}`, severity: "error" });
      }
    }

    const requiredFields = ["unique_id", "uri", "urn", "target_system", "schema_version", "generated_by"];
    for (const field of requiredFields) {
      if (!qyaml_content.includes(`${field}:`)) {
        errors.push({ path: `document_metadata.${field}`, message: `Missing required field: ${field}`, severity: "error" });
      }
    }

    if (qyaml_content.includes("%YAML")) {
      errors.push({ path: "header", message: "GKE incompatible: %YAML directive detected", severity: "error" });
    }

    const valid = errors.filter((e) => e.severity === "error").length === 0;

    res.status(200).json({ valid, errors });
  } catch (err) {
    next(err);
  }
});

// GET /api/v1/yaml/registry
yamlRouter.get("/registry", async (_req: AuthenticatedRequest, res: Response) => {
  const services = Array.from(serviceRegistry.values());
  res.status(200).json({ services, total: services.length });
});

// GET /api/v1/yaml/vector/:id
yamlRouter.get("/vector/:id", async (req: AuthenticatedRequest, res: Response, next: NextFunction) => {
  try {
    const service = serviceRegistry.get(req.params.id);
    if (!service) {
      throw new AppError(404, "not_found", "Service not found in registry");
    }

    res.status(200).json({
      serviceId: service.id,
      uri: service.uri,
      urn: service.urn,
      vector_alignment: {
        alignment_model: "quantum-bert-xxl-v1",
        coherence_vector_dim: 1024,
        function_keyword: [service.serviceName, "service"],
        contextual_binding: `${service.serviceName} -> []`,
      },
    });
  } catch (err) {
    next(err);
  }
});

export { yamlRouter };