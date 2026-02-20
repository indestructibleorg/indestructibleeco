#!/usr/bin/env node
"use strict";

const fs = require("fs");
const path = require("path");
const crypto = require("crypto");

// ─── UUID v1 Generator (time-based) ───
function uuidV1() {
  const now = BigInt(Date.now());
  const uuidTime = now * 10000n + 0x01b21dd213814000n;
  const timeLow = Number(uuidTime & 0xffffffffn) >>> 0;
  const timeMid = Number((uuidTime >> 32n) & 0xffffn);
  const timeHi = Number((uuidTime >> 48n) & 0x0fffn) | 0x1000;
  const clockSeq = (crypto.randomInt(0x3fff) & 0x3fff) | 0x8000;
  const node = crypto.randomBytes(6);
  const hex = (n, len) => n.toString(16).padStart(len, "0");
  return [
    hex(timeLow, 8),
    hex(timeMid, 4),
    hex(timeHi, 4),
    hex(clockSeq, 4),
    node.toString("hex"),
  ].join("-");
}

// ─── URI / URN Builders ───
function buildURI(namespace, kind, name) {
  return `indestructibleeco://k8s/${namespace}/${kind}/${name}`;
}

function buildURN(namespace, kind, name, uid) {
  return `urn:indestructibleeco:k8s:${namespace}:${kind}:${name}:${uid}`;
}

// ─── Schema: Mandatory .qyaml Governance Blocks ───
const REQUIRED_GOVERNANCE_BLOCKS = [
  "document_metadata",
  "governance_info",
  "registry_binding",
  "vector_alignment_map",
];

const REQUIRED_METADATA_FIELDS = [
  "unique_id",
  "uri",
  "urn",
  "target_system",
  "cross_layer_binding",
  "schema_version",
  "generated_by",
  "created_at",
];

const REQUIRED_GOVERNANCE_FIELDS = [
  "owner",
  "approval_chain",
  "compliance_tags",
  "lifecycle_policy",
];

const REQUIRED_REGISTRY_FIELDS = [
  "service_endpoint",
  "discovery_protocol",
  "health_check_path",
  "registry_ttl",
];

const REQUIRED_VECTOR_FIELDS = [
  "alignment_model",
  "coherence_vector_dim",
  "function_keyword",
  "contextual_binding",
];

// ─── Generator ───
function generateQYAML(input, targetSystem) {
  const uid = uuidV1();
  const namespace = input.namespace || "indestructibleeco";
  const kind = input.kind || "Deployment";
  const name = input.name;
  const uri = buildURI(namespace, kind.toLowerCase(), name);
  const urn = buildURN(namespace, kind.toLowerCase(), name, uid);
  const now = new Date().toISOString();

  const governanceBlock = [
    "---",
    "# YAML Toolkit v1 — Governance Block (auto-generated, manual editing prohibited)",
    "document_metadata:",
    `  unique_id: "${uid}"`,
    `  uri: "${uri}"`,
    `  urn: "${urn}"`,
    `  target_system: ${targetSystem}`,
    `  cross_layer_binding: [${(input.depends_on || []).join(", ")}]`,
    "  schema_version: v8",
    "  generated_by: yaml-toolkit-v8",
    `  created_at: "${now}"`,
    "governance_info:",
    `  owner: ${input.owner || "platform-team"}`,
    `  approval_chain: [${input.owner || "platform-team"}]`,
    `  compliance_tags: [zero-trust, soc2, internal]`,
    "  lifecycle_policy: active",
    "registry_binding:",
    `  service_endpoint: "http://${name}.${namespace}.svc.cluster.local"`,
    "  discovery_protocol: consul",
    `  health_check_path: "${input.health_check || "/health"}"`,
    "  registry_ttl: 30",
    "vector_alignment_map:",
    "  alignment_model: quantum-bert-xxl-v1",
    "  coherence_vector_dim: 1024",
    `  function_keyword: [${(input.keywords || [name, kind.toLowerCase()]).join(", ")}]`,
    `  contextual_binding: "${name} -> [${(input.depends_on || []).join(", ")}]"`,
  ];

  let k8sManifest;
  if (kind === "Deployment") {
    k8sManifest = generateDeployment(input, uid, uri, urn, namespace);
  } else if (kind === "Service") {
    k8sManifest = generateService(input, uid, uri, urn, namespace);
  } else if (kind === "Namespace") {
    k8sManifest = generateNamespace(input, uid, uri, urn);
  } else if (kind === "ConfigMap") {
    k8sManifest = generateConfigMap(input, uid, uri, urn, namespace);
  } else if (kind === "Ingress") {
    k8sManifest = generateIngress(input, uid, uri, urn, namespace);
  } else {
    k8sManifest = [`# Unsupported kind: ${kind}`];
  }

  return k8sManifest.join("\n") + "\n" + governanceBlock.join("\n") + "\n";
}

function generateDeployment(input, uid, uri, urn, namespace) {
  const ports = (input.ports || [3000]).map(
    (p) => `        - containerPort: ${p}`
  );
  return [
    "---",
    "apiVersion: apps/v1",
    "kind: Deployment",
    "metadata:",
    `  name: ${input.name}`,
    `  namespace: ${namespace}`,
    "  labels:",
    `    app: ${input.name}`,
    "    tier: backend",
    "    generated-by: yaml-toolkit-v8",
    `    unique-id: "${uid}"`,
    "  annotations:",
    `    indestructibleeco/uri: "${uri}"`,
    `    indestructibleeco/urn: "${urn}"`,
    "spec:",
    `  replicas: ${input.replicas || 3}`,
    "  selector:",
    "    matchLabels:",
    `      app: ${input.name}`,
    "  template:",
    "    metadata:",
    "      labels:",
    `        app: ${input.name}`,
    `        version: ${input.version || "v1.0.0"}`,
    "    spec:",
    `      serviceAccountName: ${input.name}-sa`,
    "      containers:",
    `      - name: ${input.name}`,
    `        image: ${input.image}`,
    "        ports:",
    ...ports,
    "        livenessProbe:",
    "          httpGet:",
    `            path: ${input.health_check || "/health"}`,
    `            port: ${(input.ports || [3000])[0]}`,
    "          initialDelaySeconds: 15",
    "        readinessProbe:",
    "          httpGet:",
    `            path: ${input.ready_check || "/ready"}`,
    `            port: ${(input.ports || [3000])[0]}`,
    "        resources:",
    "          requests:",
    `            cpu: ${input.cpu_request || "100m"}`,
    `            memory: ${input.mem_request || "256Mi"}`,
    "          limits:",
    `            cpu: ${input.cpu_limit || "500m"}`,
    `            memory: ${input.mem_limit || "512Mi"}`,
  ];
}

function generateService(input, uid, uri, urn, namespace) {
  const ports = (input.ports || [3000]).map(
    (p, i) =>
      `    - name: port-${i}\n      port: ${p}\n      targetPort: ${p}\n      protocol: TCP`
  );
  return [
    "---",
    "apiVersion: v1",
    "kind: Service",
    "metadata:",
    `  name: ${input.name}-svc`,
    `  namespace: ${namespace}`,
    "  labels:",
    `    app: ${input.name}`,
    "    generated-by: yaml-toolkit-v8",
    `    unique-id: "${uid}"`,
    "  annotations:",
    `    indestructibleeco/uri: "${uri}"`,
    `    indestructibleeco/urn: "${urn}"`,
    "spec:",
    "  type: ClusterIP",
    "  selector:",
    `    app: ${input.name}`,
    "  ports:",
    ...ports,
  ];
}

function generateNamespace(input, uid, uri, urn) {
  return [
    "---",
    "apiVersion: v1",
    "kind: Namespace",
    "metadata:",
    `  name: ${input.name}`,
    "  labels:",
    "    generated-by: yaml-toolkit-v8",
    `    unique-id: "${uid}"`,
    "  annotations:",
    `    indestructibleeco/uri: "${uri}"`,
    `    indestructibleeco/urn: "${urn}"`,
  ];
}

function generateConfigMap(input, uid, uri, urn, namespace) {
  const dataEntries = Object.entries(input.data || {}).map(
    ([k, v]) => `  ${k}: "${v}"`
  );
  return [
    "---",
    "apiVersion: v1",
    "kind: ConfigMap",
    "metadata:",
    `  name: ${input.name}`,
    `  namespace: ${namespace}`,
    "  labels:",
    "    generated-by: yaml-toolkit-v8",
    `    unique-id: "${uid}"`,
    "  annotations:",
    `    indestructibleeco/uri: "${uri}"`,
    `    indestructibleeco/urn: "${urn}"`,
    "data:",
    ...dataEntries,
  ];
}

function generateIngress(input, uid, uri, urn, namespace) {
  return [
    "---",
    "apiVersion: networking.k8s.io/v1",
    "kind: Ingress",
    "metadata:",
    `  name: ${input.name}`,
    `  namespace: ${namespace}`,
    "  labels:",
    "    generated-by: yaml-toolkit-v8",
    `    unique-id: "${uid}"`,
    "  annotations:",
    `    indestructibleeco/uri: "${uri}"`,
    `    indestructibleeco/urn: "${urn}"`,
    '    nginx.ingress.kubernetes.io/ssl-redirect: "true"',
    "    cert-manager.io/cluster-issuer: letsencrypt-prod",
    "spec:",
    "  ingressClassName: nginx",
    "  tls:",
    `  - hosts:`,
    `    - ${input.host || "api.indestructibleeco.io"}`,
    `    secretName: ${input.name}-tls`,
    "  rules:",
    `  - host: ${input.host || "api.indestructibleeco.io"}`,
    "    http:",
    "      paths:",
    "      - path: /",
    "        pathType: Prefix",
    "        backend:",
    "          service:",
    `            name: ${input.backend_service || input.name + "-svc"}`,
    "            port:",
    `              number: ${(input.ports || [3000])[0]}`,
  ];
}

// ─── Validator ───
function validateQYAML(content) {
  const errors = [];
  for (const block of REQUIRED_GOVERNANCE_BLOCKS) {
    if (!content.includes(`${block}:`)) {
      errors.push({ path: block, message: `Missing mandatory governance block: ${block}`, severity: "error" });
    }
  }
  for (const field of REQUIRED_METADATA_FIELDS) {
    if (!content.includes(`  ${field}:`)) {
      errors.push({ path: `document_metadata.${field}`, message: `Missing required field: ${field}`, severity: "error" });
    }
  }
  if (/^%YAML/m.test(content)) {
    errors.push({ path: "header", message: "GKE incompatible: %YAML directive detected — must be removed", severity: "error" });
  }
  if (!content.includes("unique-id:") && !content.includes("unique_id:")) {
    errors.push({ path: "metadata", message: "No UUID v1 identifier found", severity: "error" });
  }
  if (!content.includes("indestructibleeco://")) {
    errors.push({ path: "metadata", message: "No URI identifier found", severity: "warning" });
  }
  if (!content.includes("urn:indestructibleeco:")) {
    errors.push({ path: "metadata", message: "No URN identifier found", severity: "warning" });
  }
  return { valid: errors.filter((e) => e.severity === "error").length === 0, errors };
}

// ─── Linter ───
function lintQYAML(filePath) {
  if (!filePath.endsWith(".qyaml")) {
    return { valid: false, errors: [{ path: filePath, message: "File must use .qyaml extension", severity: "error" }] };
  }
  const content = fs.readFileSync(filePath, "utf-8");
  const result = validateQYAML(content);
  result.file = filePath;
  return result;
}

// ─── CLI ───
const [, , command, ...args] = process.argv;

switch (command) {
  case "gen":
  case "generate": {
    const inputPath = args.find((a) => a.startsWith("--input="))?.split("=")[1];
    const target = args.find((a) => a.startsWith("--target="))?.split("=")[1] || "gke-production";
    const outputDir = args.find((a) => a.startsWith("--output="))?.split("=")[1] || "output";
    if (!inputPath) {
      console.error("Usage: yaml-toolkit gen --input=module.json [--target=gke-production] [--output=output/]");
      process.exit(1);
    }
    const input = JSON.parse(fs.readFileSync(inputPath, "utf-8"));
    const qyaml = generateQYAML(input, target);
    fs.mkdirSync(outputDir, { recursive: true });
    const outFile = path.join(outputDir, `${input.name}.qyaml`);
    fs.writeFileSync(outFile, qyaml);
    const validation = validateQYAML(qyaml);
    console.log(`Generated: ${outFile} [valid=${validation.valid}]`);
    if (!validation.valid) {
      validation.errors.forEach((e) => console.error(`  ${e.severity}: ${e.path} — ${e.message}`));
      process.exit(1);
    }
    break;
  }
  case "validate": {
    const filePath = args[0];
    const strict = args.includes("--strict");
    if (!filePath) {
      console.error("Usage: yaml-toolkit validate <file.qyaml> [--strict]");
      process.exit(1);
    }
    const content = fs.readFileSync(filePath, "utf-8");
    const result = validateQYAML(content);
    if (strict) {
      result.valid = result.errors.length === 0;
    }
    console.log(`Validate: ${filePath} [valid=${result.valid}]`);
    result.errors.forEach((e) => console.log(`  ${e.severity}: ${e.path} — ${e.message}`));
    process.exit(result.valid ? 0 : 1);
    break;
  }
  case "lint": {
    const dir = args[0] || ".";
    const files = [];
    function walk(d) {
      for (const entry of fs.readdirSync(d, { withFileTypes: true })) {
        const full = path.join(d, entry.name);
        if (entry.isDirectory()) walk(full);
        else if (entry.name.endsWith(".qyaml")) files.push(full);
      }
    }
    walk(dir);
    if (files.length === 0) {
      console.log("No .qyaml files found.");
      process.exit(0);
    }
    let allValid = true;
    for (const f of files) {
      const result = lintQYAML(f);
      const status = result.valid ? "PASS" : "FAIL";
      console.log(`[${status}] ${f}`);
      result.errors.forEach((e) => console.log(`  ${e.severity}: ${e.path} — ${e.message}`));
      if (!result.valid) allValid = false;
    }
    console.log(`\nLinted ${files.length} files. ${allValid ? "All passed." : "Some failed."}`);
    process.exit(allValid ? 0 : 1);
    break;
  }
  case "validate-schema": {
    // Delegate to the full schema validator (validate-qyaml.js)
    const vqArgs = args.join(" ");
    const vqPath = path.join(__dirname, "validate-qyaml.js");
    if (!fs.existsSync(vqPath)) {
      console.error("ERROR: validate-qyaml.js not found at " + vqPath);
      process.exit(2);
    }
    const { execSync } = require("child_process");
    try {
      execSync(`node "${vqPath}" ${vqArgs}`, { stdio: "inherit" });
    } catch (e) {
      process.exit(e.status || 1);
    }
    break;
  }
  case "convert": {
    const srcFile = args.find((a) => !a.startsWith("--"));
    const outDir = args.find((a) => a.startsWith("--output="))?.split("=")[1] || ".";
    if (!srcFile) {
      console.error("Usage: yaml-toolkit convert <file.qyaml> [--output=dir]");
      process.exit(1);
    }
    if (!fs.existsSync(srcFile)) {
      console.error(`File not found: ${srcFile}`);
      process.exit(1);
    }
    const raw = fs.readFileSync(srcFile, "utf-8");
    const docs = raw.split(/^---$/m).filter((d) => d.trim());
    const k8sDocs = [];
    const governanceBlocks = ["document_metadata:", "governance_info:", "registry_binding:", "vector_alignment_map:"];
    for (const doc of docs) {
      const trimmed = doc.trim();
      if (!trimmed) continue;
      const isGovernance = governanceBlocks.some((b) => trimmed.startsWith(b) || trimmed.startsWith("# YAML Toolkit"));
      if (!isGovernance) {
        k8sDocs.push(trimmed);
      }
    }
    const output = k8sDocs.map((d) => "---\n" + d).join("\n");
    fs.mkdirSync(outDir, { recursive: true });
    const baseName = path.basename(srcFile, ".qyaml") + ".yaml";
    const outFile = path.join(outDir, baseName);
    fs.writeFileSync(outFile, output + "\n");
    console.log(`Converted: ${srcFile} -> ${outFile}`);
    break;
  }
  default:
    console.log("IndestructibleEco YAML Toolkit v8");
    console.log("Commands: gen | validate | validate-schema | lint | convert");
    console.log("  gen              --input=module.json [--target=gke-production] [--output=output/]");
    console.log("  validate         <file.qyaml> [--strict]");
    console.log("  validate-schema  <file.qyaml> [--dir path] [--json] [--strict]");
    console.log("  lint             [directory]");
    console.log("  convert          <file.qyaml> [--output=dir]  Strip governance -> standard .yaml");
    break;
}