#!/usr/bin/env python3
"""Parse a JSON file and extract a field value.

Usage:
  python3 tools/ci-helpers/parse_json_field.py <file> <dotted.path> [default]

Examples:
  python3 tools/ci-helpers/parse_json_field.py report.json fixed 0
  python3 tools/ci-helpers/parse_json_field.py sbom.json components.__len__ 0
"""
import json
import sys


def get_nested(data, path, default=None):
    parts = path.split(".")
    current = data
    for part in parts:
        if part == "__len__":
            return len(current) if isinstance(current, (list, dict)) else default
        if isinstance(current, dict):
            current = current.get(part, default)
        else:
            return default
    return current


def main():
    if len(sys.argv) < 3:
        print(__doc__, file=sys.stderr)
        sys.exit(1)

    filepath = sys.argv[1]
    field_path = sys.argv[2]
    default = sys.argv[3] if len(sys.argv) > 3 else ""

    try:
        with open(filepath) as f:
            data = json.load(f)
        result = get_nested(data, field_path, default)
        print(result)
    except Exception:
        print(default)


if __name__ == "__main__":
    main()
