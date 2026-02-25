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
            out.append(p)
            continue
        for root, _, files in os.walk(p):
            for fn in files:
                if fn.endswith(".yml") or fn.endswith(".yaml"):
                    out.append(os.path.join(root, fn))
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
        fails.append(err(f"{src}: {kind}/{name}: app.kubernetes.io/part-of must be \'eco-base\'"))

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
    for f in files:
        try:
            for obj in iter_yaml_docs(f):
                all_fails.extend(validate_obj(obj, f))
                if args.fail_fast and all_fails:
                    raise SystemExit(1)
        except yaml.YAMLError as e:
            all_fails.append(err(f"{f}: yaml parse error: {e}"))

    if all_fails:
        for x in all_fails:
            print(x)
        return 1

    print("[ECO-SPEC] OK")
    return 0

if __name__ == "__main__":
    sys.exit(main())
