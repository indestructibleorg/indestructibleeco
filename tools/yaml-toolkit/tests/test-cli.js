const { describe, it } = require("node:test");
const assert = require("node:assert/strict");
const { execSync } = require("child_process");
const fs = require("fs");
const path = require("path");
const os = require("os");

const CLI = path.join(__dirname, "..", "bin", "cli.js");
const REPO_ROOT = path.resolve(__dirname, "..", "..", "..");

function run(cmd) {
  return execSync(`node "${CLI}" ${cmd}`, {
    encoding: "utf-8",
    cwd: REPO_ROOT,
    timeout: 10000,
  });
}

function runExit(cmd) {
  try {
    const out = execSync(`node "${CLI}" ${cmd}`, {
      encoding: "utf-8",
      cwd: REPO_ROOT,
      timeout: 10000,
    });
    return { code: 0, stdout: out };
  } catch (e) {
    return { code: e.status, stdout: e.stdout || "", stderr: e.stderr || "" };
  }
}

describe("yaml-toolkit CLI", () => {
  it("shows help with no args", () => {
    const out = run("");
    assert.ok(out.includes("YAML Toolkit"));
    assert.ok(out.includes("gen"));
    assert.ok(out.includes("validate"));
    assert.ok(out.includes("lint"));
  });

  it("shows help for unknown command", () => {
    const out = run("unknown");
    assert.ok(out.includes("YAML Toolkit"));
  });
});

describe("yaml-toolkit generate", () => {
  const tmpDir = path.join(os.tmpdir(), "eco-yaml-test-" + Date.now());

  it("generates a valid .qyaml from module.json", () => {
    const inputPath = path.join(tmpDir, "input.json");
    fs.mkdirSync(tmpDir, { recursive: true });
    fs.writeFileSync(inputPath, JSON.stringify({
      name: "eco-test-svc",
      kind: "Deployment",
      namespace: "indestructibleeco",
      image: "ghcr.io/indestructibleorg/test:1.0.0",
      ports: [8080],
      depends_on: ["redis", "postgres"],
      health_check: "/health",
      owner: "test-team",
    }));

    const outDir = path.join(tmpDir, "output");
    const out = run(`gen --input=${inputPath} --output=${outDir}`);
    assert.ok(out.includes("Generated:"));
    assert.ok(out.includes("valid=true"));

    const generated = fs.readFileSync(path.join(outDir, "eco-test-svc.qyaml"), "utf-8");
    assert.ok(generated.includes("document_metadata:"));
    assert.ok(generated.includes("governance_info:"));
    assert.ok(generated.includes("registry_binding:"));
    assert.ok(generated.includes("vector_alignment_map:"));
    assert.ok(generated.includes("schema_version: v8"));
    assert.ok(generated.includes("yaml-toolkit-v8"));
    assert.ok(generated.includes("indestructibleeco://"));
    assert.ok(generated.includes("urn:indestructibleeco:"));
    assert.ok(generated.includes("eco-test-svc"));
  });

  it("fails without --input", () => {
    const result = runExit("gen");
    assert.notEqual(result.code, 0);
  });

  it("generates Service kind", () => {
    const inputPath = path.join(tmpDir, "svc-input.json");
    fs.writeFileSync(inputPath, JSON.stringify({
      name: "eco-svc-test",
      kind: "Service",
      ports: [3000],
    }));
    const outDir = path.join(tmpDir, "svc-output");
    const out = run(`gen --input=${inputPath} --output=${outDir}`);
    assert.ok(out.includes("valid=true"));
    const content = fs.readFileSync(path.join(outDir, "eco-svc-test.qyaml"), "utf-8");
    assert.ok(content.includes("kind: Service"));
  });

  it("generates Namespace kind", () => {
    const inputPath = path.join(tmpDir, "ns-input.json");
    fs.writeFileSync(inputPath, JSON.stringify({
      name: "eco-test-ns",
      kind: "Namespace",
    }));
    const outDir = path.join(tmpDir, "ns-output");
    const out = run(`gen --input=${inputPath} --output=${outDir}`);
    assert.ok(out.includes("valid=true"));
  });

  it("generates ConfigMap kind", () => {
    const inputPath = path.join(tmpDir, "cm-input.json");
    fs.writeFileSync(inputPath, JSON.stringify({
      name: "eco-test-cm",
      kind: "ConfigMap",
      data: { ECO_ENV: "test", ECO_PORT: "8080" },
    }));
    const outDir = path.join(tmpDir, "cm-output");
    const out = run(`gen --input=${inputPath} --output=${outDir}`);
    assert.ok(out.includes("valid=true"));
  });

  it("generates Ingress kind", () => {
    const inputPath = path.join(tmpDir, "ing-input.json");
    fs.writeFileSync(inputPath, JSON.stringify({
      name: "eco-test-ing",
      kind: "Ingress",
      host: "test.indestructibleeco.io",
      ports: [8080],
    }));
    const outDir = path.join(tmpDir, "ing-output");
    const out = run(`gen --input=${inputPath} --output=${outDir}`);
    assert.ok(out.includes("valid=true"));
  });
});

describe("yaml-toolkit validate", () => {
  it("validates existing .qyaml files", () => {
    const files = [
      "k8s/base/api-gateway.qyaml",
      "k8s/base/namespace.qyaml",
      "k8s/base/vllm-engine.qyaml",
      "backend/k8s/deployments/ai.qyaml",
    ];
    for (const f of files) {
      const full = path.join(REPO_ROOT, f);
      if (fs.existsSync(full)) {
        const out = run(`validate ${full}`);
        assert.ok(out.includes("valid=true"), `${f} should be valid`);
      }
    }
  });

  it("fails on missing file", () => {
    const result = runExit("validate /nonexistent/file.qyaml");
    assert.notEqual(result.code, 0);
  });
});

describe("yaml-toolkit lint", () => {
  it("lints k8s/base/ directory", () => {
    const dir = path.join(REPO_ROOT, "k8s/base");
    const out = run(`lint ${dir}`);
    assert.ok(out.includes("Linted"));
    assert.ok(out.includes("PASS"));
  });

  it("lints backend/k8s/ directory", () => {
    const dir = path.join(REPO_ROOT, "backend/k8s");
    const out = run(`lint ${dir}`);
    assert.ok(out.includes("Linted"));
  });

  it("handles empty directory gracefully", () => {
    const emptyDir = path.join(os.tmpdir(), "eco-empty-" + Date.now());
    fs.mkdirSync(emptyDir, { recursive: true });
    const out = run(`lint ${emptyDir}`);
    assert.ok(out.includes("No .qyaml files found"));
  });
});

describe("yaml-toolkit convert", () => {
  it("converts .qyaml to standard .yaml", () => {
    const src = path.join(REPO_ROOT, "k8s/base/namespace.qyaml");
    if (!fs.existsSync(src)) return;
    const outDir = path.join(os.tmpdir(), "eco-convert-" + Date.now());
    fs.mkdirSync(outDir, { recursive: true });
    const out = run(`convert ${src} --output=${outDir}`);
    assert.ok(out.includes("Converted:") || out.includes("converted"));
    const outFile = path.join(outDir, "namespace.yaml");
    assert.ok(fs.existsSync(outFile), "Output .yaml file should exist");
    const content = fs.readFileSync(outFile, "utf-8");
    assert.ok(!content.includes("document_metadata:"), "Should not contain governance blocks");
    assert.ok(!content.includes("vector_alignment_map:"), "Should not contain governance blocks");
  });
});
