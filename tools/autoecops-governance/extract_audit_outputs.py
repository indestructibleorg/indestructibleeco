#!/usr/bin/env python3
"""
Extract governance outputs from a CycloneDX audit trail JSON file.
Used by replay.yaml to set GitHub Actions step outputs.

Usage:
  python3 extract_audit_outputs.py artifacts/audit/pr-114-audit.json
"""
import json
import os
import sys


def main():
    if len(sys.argv) < 2:
        print("Usage: extract_audit_outputs.py <audit_file>")
        sys.exit(1)

    audit_file = sys.argv[1]

    if not os.path.exists(audit_file):
        print(f"Audit file not found: {audit_file}")
        # Write safe defaults
        write_outputs("NONE", "unknown", "")
        return

    try:
        with open(audit_file) as f:
            d = json.load(f)
    except Exception as e:
        print(f"Could not parse audit file: {e}")
        write_outputs("NONE", "unknown", "")
        return

    props = d.get("properties", [])
    action = next(
        (p["value"] for p in props if "final_action" in p.get("name", "")),
        "NONE"
    )
    outcome = next(
        (p["value"] for p in props if "final_outcome" in p.get("name", "")),
        "unknown"
    )
    audit_hash = d.get("audit", {}).get("audit_hash", "")[:16]

    print(f"action={action}")
    print(f"outcome={outcome}")
    print(f"audit_hash={audit_hash}")

    write_outputs(action, outcome, audit_hash)


def write_outputs(action: str, outcome: str, audit_hash: str):
    github_output = os.environ.get("GITHUB_OUTPUT", "")
    if github_output:
        with open(github_output, "a") as f:
            f.write(f"action={action}\n")
            f.write(f"outcome={outcome}\n")
            f.write(f"audit_hash={audit_hash}\n")


if __name__ == "__main__":
    main()
