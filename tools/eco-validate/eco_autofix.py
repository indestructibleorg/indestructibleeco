import argparse, os, sys, yaml

MANDATORY_LABELS = {
    "app.kubernetes.io/name": "eco-resource",
    "app.kubernetes.io/instance": "eco-instance",
    "app.kubernetes.io/version": "1.0.0",
    "app.kubernetes.io/component": "eco-component",
    "app.kubernetes.io/part-of": "eco-base",
    "eco-base/platform": "core",
    "eco-base/environment": "development",
    "eco-base/owner": "eco-system",
}

MANDATORY_ANNOTATIONS = {
    "eco-base/governance-policy": "standard-v1",
    "eco-base/audit-log-level": "minimal",
}

KIND_FILTER = {
    "Deployment", "StatefulSet", "DaemonSet", "Job", "CronJob",
    "Service", "Ingress", "ConfigMap", "Secret"
}

def load_yaml_docs(path: str):
    with open(path, "r", encoding="utf-8") as f:
        try:
            return list(yaml.safe_load_all(f))
        except yaml.YAMLError as e:
            print(f"[ECO-AUTOFIX-ERROR] {path}: yaml parse error: {e}")
            return []

def dump_yaml_docs(path: str, docs):
    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump_all(
            docs, f,
            sort_keys=True,
            default_flow_style=False,
            explicit_start=True,
            allow_unicode=True
        )

def find_yaml_files(paths):
    out = []
    for p in paths:
        if not os.path.exists(p):
            continue
        if os.path.isfile(p) and p.endswith((".yml", ".yaml")):
            out.append(p)
            continue
        for root, _, files in os.walk(p):
            for fn in files:
                if fn.endswith((".yml", ".yaml")):
                    out.append(os.path.join(root, fn))
    return sorted(set(out))

def fix_obj(obj):
    if not isinstance(obj, dict) or obj.get("kind") not in KIND_FILTER:
        return False

    changed = False
    meta = obj.setdefault("metadata", {})
    labels = meta.setdefault("labels", {})
    ann = meta.setdefault("annotations", {})

    # Fix labels
    for k, v in MANDATORY_LABELS.items():
        if k not in labels or str(labels.get(k)).strip() == "":
            # Try to infer name if missing
            if k == "app.kubernetes.io/name" and meta.get("name"):
                labels[k] = meta["name"]
            else:
                labels[k] = v
            changed = True

    # Fix annotations
    for k, v in MANDATORY_ANNOTATIONS.items():
        if k not in ann or str(ann.get(k)).strip() == "":
            ann[k] = v
            changed = True

    return changed

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--paths", nargs="+", default=["."], help="paths to scan")
    args = ap.parse_args()

    files = find_yaml_files(args.paths)
    if not files:
        print("[ECO-AUTOFIX] no yaml files found.")
        return 0

    total_fixed = 0
    for fpath in files:
        docs = load_yaml_docs(fpath)
        if not docs:
            continue

        file_changed = False
        for doc in docs:
            if fix_obj(doc):
                file_changed = True

        if file_changed:
            dump_yaml_docs(fpath, docs)
            total_fixed += 1
            print(f"[ECO-AUTOFIX] Fixed: {fpath}")

    print(f"[ECO-AUTOFIX] Done. Fixed {total_fixed} files.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
