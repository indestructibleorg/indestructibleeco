import argparse, json, os, re, sys, hashlib
from datetime import datetime, timezone
import yaml

KIND_TO_COMPONENT = {
    "Deployment": "deployment",
    "StatefulSet": "statefulset",
    "DaemonSet": "daemonset",
    "Job": "job",
    "CronJob": "cronjob",
    "Service": "service",
    "Ingress": "ingress",
    "ConfigMap": "configmap",
    "Secret": "secret",
}

# 僅針對治理範圍內的 K8s 物件做供應鏈鎖定
GOVERNED_KINDS = set(KIND_TO_COMPONENT.keys())

# canonicalization：排除會造成非決定性的欄位（避免漂移誤報）
EXCLUDE_METADATA_FIELDS = {
    "creationTimestamp",
    "generation",
    "managedFields",
    "resourceVersion",
    "uid",
}

EXCLUDE_TOP_LEVEL_FIELDS = {
    "status",  # status 永遠由 controller 填，必排除
}

URN_RE = re.compile(
    r"^urn:eco-base:k8s:[a-z0-9-]+:[a-z0-9-]+:[a-z0-9-]+:sha256-[0-9a-f]{64}$"
)
URI_RE = re.compile(r"^eco-base://k8s/[a-z0-9-]+/[a-z0-9-]+/[a-z0-9-]+$")

def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def stable_json(obj) -> bytes:
    # JSON canonical：排序 key、固定分隔符、UTF-8、無多餘空白
    s = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return s.encode("utf-8")

def canonicalize_k8s(obj: dict) -> dict:
    o = json.loads(json.dumps(obj))  # deep copy via json
    # remove top-level excluded fields
    for k in list(o.keys()):
        if k in EXCLUDE_TOP_LEVEL_FIELDS:
            o.pop(k, None)

    meta = o.get("metadata") or {}
    # remove noisy metadata
    for k in EXCLUDE_METADATA_FIELDS:
        meta.pop(k, None)

    o["metadata"] = meta
    return o

def load_yaml_docs(path: str):
    with open(path, "r", encoding="utf-8") as f:
        try:
            return list(yaml.safe_load_all(f))
        except yaml.YAMLError as e:
            print(f"[ECO-HASHLOCK-ERROR] {path}: yaml parse error: {e}")
            return []

def dump_yaml_docs(path: str, docs):
    # 以安全的方式回寫（保留多文件結構），排序 key 以提升穩定性
    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump_all(
            docs, f,
            sort_keys=True,
            default_flow_style=False,
            explicit_start=True,  # --- 每份文件都有明確起始
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

def compute_identity(obj: dict):
    kind = obj.get("kind")
    api_version = obj.get("apiVersion", "")
    meta = obj.get("metadata") or {}
    name = meta.get("name", "")
    namespace = meta.get("namespace", "")
    return api_version, kind, namespace, name

def ensure_annotations(obj: dict):
    obj.setdefault("metadata", {})
    obj["metadata"].setdefault("annotations", {})
    obj["metadata"].setdefault("labels", {})
    return obj

def build_uri(platform: str, component: str, resource_name: str) -> str:
    return f"eco-base://k8s/{platform}/{component}/{resource_name}"

def build_urn(platform: str, component: str, resource_name: str, content_hash: str) -> str:
    return f"urn:eco-base:k8s:{platform}:{component}:{resource_name}:sha256-{content_hash}"

def governed(obj: dict) -> bool:
    return isinstance(obj, dict) and obj.get("kind") in GOVERNED_KINDS and obj.get("metadata", {}).get("name")

def get_platform_label(obj: dict) -> str:
    labels = (obj.get("metadata") or {}).get("labels") or {}
    return str(labels.get("eco-base/platform") or "").strip()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--paths", nargs="+", default=["manifests", "k8s", "charts", "platforms"], help="directories/files to scan")
    ap.add_argument("--hashlock", default="hashlock.json", help="hashlock output path")
    ap.add_argument("--mode", choices=["update", "verify"], required=True)
    ap.add_argument("--fail-fast", action="store_true")
    args = ap.parse_args()

    files = find_yaml_files(args.paths)
    if not files:
        print("[ECO-HASHLOCK] no yaml files found; OK")
        return 0

    hashlock_entries = []
    any_changes = False
    failures = []

    for fpath in files:
        docs = load_yaml_docs(fpath)
        if not docs:
            continue

        file_changed = False
        for i, doc in enumerate(docs):
            if not governed(doc):
                continue

            api_version, kind, namespace, name = compute_identity(doc)
            component = KIND_TO_COMPONENT[kind]
            platform = get_platform_label(doc)
            if not platform:
                # 強制修補：系統類資源統一歸 core，避免 unknown 污染
                if any(x in fpath for x in ["k8s/argocd", "k8s/circleci", "monitoring", "ingress", "infrastructure"]):
                    platform = "core"
                else:
                    print(f"[ECO-HASHLOCK-WARN] {fpath}: {kind}/{name}: missing label eco-base/platform, defaulting to core")
                    platform = "core"

            # 計算 content hash（在回寫 URN/URI 前）
            canon = canonicalize_k8s(doc)
            content_hash = sha256_hex(stable_json(canon))

            computed_uri = build_uri(platform, component, name)
            computed_urn = build_urn(platform, component, name, content_hash)

            ensure_annotations(doc)
            ann = doc["metadata"]["annotations"]

            existing_urn = str(ann.get("eco-base/urn") or "").strip()
            existing_uri = str(ann.get("eco-base/uri") or "").strip()

            if args.mode == "update":
                if existing_uri != computed_uri:
                    ann["eco-base/uri"] = computed_uri
                    file_changed = True

                if existing_urn != computed_urn:
                    ann["eco-base/urn"] = computed_urn
                    file_changed = True

            else:  # verify
                if existing_uri != computed_uri:
                    failures.append(f"[ECO-HASHLOCK-FAIL] {fpath}: {kind}/{name}: eco-base/uri drift\n  expected: {computed_uri}\n  actual:   {existing_uri or '<missing>'}")
                if existing_urn != computed_urn:
                    failures.append(f"[ECO-HASHLOCK-FAIL] {fpath}: {kind}/{name}: eco-base/urn drift\n  expected: {computed_urn}\n  actual:   {existing_urn or '<missing>'}")

            hashlock_entries.append({
                "apiVersion": api_version,
                "kind": kind,
                "namespace": namespace,
                "name": name,
                "platform": platform,
                "component": component,
                "uri": computed_uri,
                "urn": computed_urn,
                "contentSha256": content_hash,
                "source": fpath,
            })

        if args.fail_fast and failures:
            break

        if args.mode == "update" and file_changed:
            dump_yaml_docs(fpath, docs)
            any_changes = True

    # 生成/驗證 hashlock
    hashlock = {
        "specVersion": "eco-hashlock/v1",
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "hashAlgorithm": "sha256",
        "entries": sorted(hashlock_entries, key=lambda x: (x["source"], x["kind"], x["namespace"], x["name"])),
    }

    if args.mode == "update":
        with open(args.hashlock, "w", encoding="utf-8") as f:
            json.dump(hashlock, f, ensure_ascii=False, indent=2, sort_keys=True)
        any_changes = True
    else:
        if not os.path.exists(args.hashlock):
            failures.append(f"[ECO-HASHLOCK-FAIL] missing {args.hashlock}. Run update mode to generate.")
        else:
            with open(args.hashlock, "r", encoding="utf-8") as f:
                locked = json.load(f)
            locked_map = {e["urn"]: e["contentSha256"] for e in locked.get("entries", [])}
            computed_map = {e["urn"]: e["contentSha256"] for e in hashlock["entries"]}

            for urn, h in computed_map.items():
                if urn not in locked_map:
                    failures.append(f"[ECO-HASHLOCK-FAIL] hashlock missing entry: {urn}")
                elif locked_map[urn] != h:
                    failures.append(f"[ECO-HASHLOCK-FAIL] hashlock drift: {urn}\n  expected: {h}\n  locked:   {locked_map[urn]}")

            for urn in locked_map.keys():
                if urn not in computed_map:
                    failures.append(f"[ECO-HASHLOCK-FAIL] hashlock has extra (resource removed or renamed?): {urn}")

    if failures:
        for x in failures:
            print(x)
        return 1

    if args.mode == "update":
        print("[ECO-HASHLOCK] update OK (manifests + hashlock written)")
    else:
        print("[ECO-HASHLOCK] verify OK (no drift)")
    return 0

if __name__ == "__main__":
    sys.exit(main())
