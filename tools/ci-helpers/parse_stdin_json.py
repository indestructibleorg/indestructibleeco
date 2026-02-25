#!/usr/bin/env python3
"""Parse JSON from stdin and extract dotted field path.

Usage:
  echo '{"status":{"sync":{"status":"OutOfSync"}}}' | python3 tools/ci-helpers/parse_stdin_json.py status.sync.status Unknown

For ArgoCD responses:
  curl ... | python3 tools/ci-helpers/parse_stdin_json.py status.sync.status+status.health.status Unknown|Unknown
  (Use + to join multiple paths with |)
"""
import json
import sys


def get_nested(data, path, default=""):
    parts = path.split(".")
    current = data
    for part in parts:
        if isinstance(current, dict):
            current = current.get(part, default)
        else:
            return default
    return current


def main():
    if len(sys.argv) < 2:
        print(__doc__, file=sys.stderr)
        sys.exit(1)

    field_spec = sys.argv[1]
    default = sys.argv[2] if len(sys.argv) > 2 else ""

    try:
        data = json.load(sys.stdin)
        if "+" in field_spec:
            # Multiple paths joined with |
            paths = field_spec.split("+")
            defaults = default.split("|") if "|" in default else [default] * len(paths)
            results = []
            for i, path in enumerate(paths):
                d = defaults[i] if i < len(defaults) else ""
                results.append(str(get_nested(data, path, d)))
            print("|".join(results))
        else:
            print(get_nested(data, field_spec, default))
    except Exception:
        print(default)


if __name__ == "__main__":
    main()
