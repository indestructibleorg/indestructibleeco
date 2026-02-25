#!/usr/bin/env python3
"""Count fixable vulnerabilities from pip-audit JSON output.

Usage:
  python3 tools/ci-helpers/count_vulns.py /tmp/python-audit.json
"""
import json
import sys


def main():
    filepath = sys.argv[1] if len(sys.argv) > 1 else "/tmp/python-audit.json"
    try:
        with open(filepath) as f:
            data = json.load(f)
        vulns = [
            v
            for dep in data.get("dependencies", [])
            for v in dep.get("vulns", [])
            if v.get("fix_versions")
        ]
        print(len(vulns))
    except Exception:
        print(0)


if __name__ == "__main__":
    main()
