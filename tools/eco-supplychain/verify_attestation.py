import argparse, json, hashlib, sys

def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hashlock", default="supplychain/hashlock.json")
    ap.add_argument("--attestation", default="supplychain/hashlock.attestation.intoto.json")
    args = ap.parse_args()

    try:
        with open(args.hashlock, "r", encoding="utf-8") as f:
            hashlock = json.load(f)

        with open(args.attestation, "r", encoding="utf-8") as f:
            att = json.load(f)
    except FileNotFoundError as e:
        print(f"[ECO-ATTEST-FAIL] file not found: {e}")
        return 1
    except json.JSONDecodeError as e:
        print(f"[ECO-ATTEST-FAIL] json decode error: {e}")
        return 1

    actual_hash = sha256_file(args.hashlock)
    subj = (att.get("subject") or [])
    if not subj:
        print("[ECO-ATTEST-FAIL] missing subject"); return 1

    # 支援 in-toto subject digest 常見格式：{"name":"hashlock.json","digest":{"sha256":"..."}}
    subj_digest = subj[0].get("digest", {}).get("sha256", "")
    if subj_digest != actual_hash:
        print("[ECO-ATTEST-FAIL] subject sha256 mismatch")
        print(f"  expected(actual file): {actual_hash}")
        print(f"  attested(subject):     {subj_digest or '<missing>'}")
        return 1

    pred = att.get("predicate") or {}
    pred_hash = pred.get("hashlockSha256", "")
    if pred_hash != actual_hash:
        print("[ECO-ATTEST-FAIL] predicate.hashlockSha256 mismatch")
        print(f"  expected(actual file): {actual_hash}")
        print(f"  attested(predicate):   {pred_hash or '<missing>'}")
        return 1

    pred_count = int(pred.get("entriesCount", -1))
    actual_count = len(hashlock.get("entries") or [])
    if pred_count != actual_count:
        print("[ECO-ATTEST-FAIL] entriesCount mismatch")
        print(f"  expected(actual): {actual_count}")
        print(f"  attested:         {pred_count}")
        return 1

    print("[ECO-ATTEST] OK")
    return 0

if __name__ == "__main__":
    sys.exit(main())
