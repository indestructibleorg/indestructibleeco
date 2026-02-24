#!/usr/bin/env python3
"""Extract audit hash and stats from an issues-auto-engine audit JSON file.

Usage:
  python3 extract_audit.py <audit_file> hash     → prints audit_hash
  python3 extract_audit.py <audit_file> stats    → prints JSON stats
"""
import json
import sys


def main():
    if len(sys.argv) < 3:
        print("Usage: extract_audit.py <audit_file> <hash|stats>", file=sys.stderr)
        sys.exit(1)

    audit_file = sys.argv[1]
    mode = sys.argv[2]

    with open(audit_file) as f:
        data = json.load(f)

    if mode == "hash":
        print(data.get("audit", {}).get("audit_hash", "unknown"))
    elif mode == "stats":
        props = {p["name"]: p["value"] for p in data.get("properties", [])}
        print(json.dumps({
            "issues_processed": props.get("autoecops:issues_processed", "0"),
            "issues_closed": props.get("autoecops:issues_closed", "0"),
            "duplicates_closed": props.get("autoecops:duplicates_closed", "0"),
            "labels_applied": props.get("autoecops:labels_applied", "0"),
        }))
    else:
        print(f"Unknown mode: {mode}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
