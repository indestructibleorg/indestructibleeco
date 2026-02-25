import json, os, hashlib, sys
from datetime import datetime, timezone

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            h.update(chunk)
    return h.hexdigest()

def main():
    hashlock_path = "supplychain/hashlock.json"
    attestation_path = "supplychain/hashlock.attestation.intoto.json"
    
    if not os.path.exists(hashlock_path):
        print(f"Error: {hashlock_path} not found")
        sys.exit(1)
        
    with open(hashlock_path, "r") as f:
        hashlock_data = json.load(f)
        
    hashlock_sha = sha256_file(hashlock_path)
    
    # 構建 in-toto statement
    statement = {
        "_type": "https://in-toto.io/Statement/v0.1",
        "subject": [
            {
                "name": hashlock_path,
                "digest": {"sha256": hashlock_sha}
            }
        ],
        "predicateType": "https://eco-base.io/Attestation/SupplyChain/v1",
        "predicate": {
            "generator": "eco-supplychain-attest-tool",
            "generatedAt": datetime.now(timezone.utc).isoformat(),
            "workflowRunId": os.environ.get("GITHUB_RUN_ID", "local"),
            "commitSha": os.environ.get("GITHUB_SHA", "local"),
            "entriesCount": len(hashlock_data.get("entries", [])),
            "hashlockSha256": hashlock_sha
        }
    }
    
    with open(attestation_path, "w") as f:
        json.dump(statement, f, indent=2)
        
    print(f"Attestation generated: {attestation_path}")

if __name__ == "__main__":
    main()
