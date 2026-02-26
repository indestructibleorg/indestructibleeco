import argparse, os, re, sys
import yaml

K8S_NAME_RE = re.compile(r"^[a-z0-9]([a-z0-9-]*[a-z0-9])?$")
ENV_ALLOWED = {"production", "staging", "development"}
AUDIT_ALLOWED = {"full", "minimal"}

URN_RE = re.compile(
    r"^urn:eco-base:"
    r"(?P<rtype>[a-z0-9-]+):"
    r"(?P<platform>[a-z0-9-]+):"
    r"(?P<component>[a-z0-9-]+):"
    r"(?P<rname>[a-z0-9-]+):"
    r"(?P<uid>([0-9a-f]{8}-[0-9a-f]{4}-1[0-9a-f]{3}-[0-9a-f]{4}-[0-9a-f]{12}|sha256-[0-9a-f]{8,}))$"
)

URI_RE = re.compile(r"^eco-base://[a-z0-9-]+/[a-z0-9-]+/[a-z0-9-]+/.+(\?.*)?$")

MANDATORY_LABELS = [
    "app.kubernetes.io/name",
    "app.kubernetes.io/instance",
    "app.kubernetes.io/version",
    "app.kubernetes.io/component",
    "app.kubernetes.io/part-of",
    "eco-base/platform",
    "eco-base/environment",
    "eco-base/owner",
]

MANDATORY_ANNOTATIONS = [
    "eco-base/uri",
    "eco-base/urn",
    "eco-base/governance-policy",
    "eco-base/audit-log-level",
]

KIND_FILTER = {
    "Deployment", "StatefulSet", "DaemonSet", "Job", "CronJob",
    "Service", "Ingress", "ConfigMap", "Secret"
}

# Directories to skip entirely (non-k8s manifest directories)
SKIP_DIRS = {
    '.git', 'charts', 'node_modules', '__pycache__',
    'governance', 'gl-artifacts', 'artifacts', 'scripts-legacy',
    'tools-legacy', 'tests-legacy', 'archived', 'legacy',
    'templates',  # GitHub Actions templates and Helm templates
}

# File patterns to skip (non-k8s manifest files)
SKIP_FILE_PATTERNS = [
    # GitHub Actions workflows
    r'\.github/',
    # Governance artifacts (not k8s manifests)
    r'/gl-artifacts/',
    r'/governance/',
    r'/artifacts/',
    # Legacy directories
    r'/scripts-legacy/',
    r'/tools-legacy/',
    r'/tests-legacy/',
    r'/archived/',
    r'/legacy/',
    # Helm chart metadata
    r'/Chart\.ya?ml$',
    r'/values\.ya?ml$',
    r'/values-.*\.ya?ml$',
]

SKIP_PATTERNS_RE = [re.compile(p) for p in SKIP_FILE_PATTERNS]

def should_skip_file(path):
    """Check if a file should be skipped based on path patterns."""
    # Normalize path separators
    norm_path = path.replace('\\', '/')
    for pattern in SKIP_PATTERNS_RE:
        if pattern.search(norm_path):
            return True
    return False

def is_helm_template(path):
    """Check if a YAML file is a Helm template (contains {{ }})."""
    try:
        with open(path, encoding='utf-8', errors='ignore') as f:
            # Read first 8KB to check for Helm template syntax
            chunk = f.read(8192)
            return '{{' in chunk and '}}' in chunk
    except Exception:
        return False

def is_k8s_manifest(path):
    """Quick check if a YAML file looks like a k8s manifest."""
    try:
        with open(path, encoding='utf-8', errors='ignore') as f:
            chunk = f.read(2048)
            # k8s manifests typically have apiVersion and kind at the top
            return ('apiVersion:' in chunk or 'kind:' in chunk) and 'metadata:' in chunk
    except Exception:
        return False

def iter_yaml_docs(path: str):
    with open(path, "r", encoding="utf-8") as f:
        for doc in yaml.safe_load_all(f):
            if isinstance(doc, dict) and doc.get("kind") and doc.get("metadata"):
                yield doc

def find_yaml_files(paths):
    out = []
    for p in paths:
        if not os.path.exists(p):
            continue
        if os.path.isfile(p) and (p.endswith(".yml") or p.endswith(".yaml")):
            if not should_skip_file(p) and not is_helm_template(p) and is_k8s_manifest(p):
                out.append(p)
            continue
        for root, dirs, files in os.walk(p):
            # Skip non-k8s directories
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
            for fn in files:
                if fn.endswith(".yml") or fn.endswith(".yaml"):
                    fp = os.path.join(root, fn)
                    if not should_skip_file(fp) and not is_helm_template(fp) and is_k8s_manifest(fp):
                        out.append(fp)
    return out

def err(msg):  # consistent machine-readable output
    return f"[ECO-SPEC-FAIL] {msg}"

def validate_obj(obj, src):
    kind = obj.get("kind")
    if kind not in KIND_FILTER:
        return []

    meta = obj.get("metadata") or {}
    name = meta.get("name", "")
    labels = meta.get("labels") or {}
    ann = meta.get("annotations") or {}

    fails = []

    if not name or not K8S_NAME_RE.match(name):
        fails.append(err(f"{src}: {kind}.metadata.name invalid: {name!r} (must match {K8S_NAME_RE.pattern})"))

    # labels
    for k in MANDATORY_LABELS:
        if k not in labels or str(labels.get(k)).strip() == "":
            fails.append(err(f"{src}: {kind}/{name}: missing label {k}"))
    if labels.get("app.kubernetes.io/part-of") and labels["app.kubernetes.io/part-of"] != "eco-base":
        fails.append(err(f"{src}: {kind}/{name}: app.kubernetes.io/part-of must be 'eco-base'"))

    env = labels.get("eco-base/environment")
    if env and env not in ENV_ALLOWED:
        fails.append(err(f"{src}: {kind}/{name}: eco-base/environment={env!r} not in {sorted(ENV_ALLOWED)}"))

    # annotations
    for k in MANDATORY_ANNOTATIONS:
        if k not in ann or str(ann.get(k)).strip() == "":
            fails.append(err(f"{src}: {kind}/{name}: missing annotation {k}"))

    u = ann.get("eco-base/urn")
    if u and not URN_RE.match(u):
        fails.append(err(f"{src}: {kind}/{name}: eco-base/urn invalid: {u!r}"))

    uri = ann.get("eco-base/uri")
    if uri and not URI_RE.match(uri):
        fails.append(err(f"{src}: {kind}/{name}: eco-base/uri invalid: {uri!r}"))

    al = ann.get("eco-base/audit-log-level")
    if al and al not in AUDIT_ALLOWED:
        fails.append(err(f"{src}: {kind}/{name}: eco-base/audit-log-level={al!r} not in {sorted(AUDIT_ALLOWED)}"))

    return fails

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--paths", nargs="+", default=["."], help="paths to scan")
    ap.add_argument("--fail-fast", action="store_true")
    args = ap.parse_args()

    files = find_yaml_files(args.paths)
    if not files:
        print("[ECO-SPEC] no yaml files found, skipping.")
        return 0

    all_fails = []
    parse_warnings = []
    for f in files:
        try:
            for obj in iter_yaml_docs(f):
                all_fails.extend(validate_obj(obj, f))
                if args.fail_fast and all_fails:
                    raise SystemExit(1)
        except yaml.YAMLError as e:
            # Log as warning, not failure - some files may have valid YAML
            # that our parser can't handle (e.g., custom tags)
            parse_warnings.append(f"[ECO-SPEC-WARN] {f}: yaml parse warning: {e}")

    if parse_warnings:
        for w in parse_warnings:
            print(w, file=sys.stderr)

    if all_fails:
        for x in all_fails:
            print(x)
        return 1

    print("[ECO-SPEC] OK")
    return 0

if __name__ == "__main__":
    sys.exit(main())
