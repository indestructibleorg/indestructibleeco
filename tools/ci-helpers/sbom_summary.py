#!/usr/bin/env python3
"""Print SBOM component count.

Usage:
  python3 tools/ci-helpers/sbom_summary.py <sbom_file>
  python3 tools/ci-helpers/sbom_summary.py <sbom_file> --count-only
"""
import json
import sys


def main():
    if len(sys.argv) < 2:
        print("Usage: sbom_summary.py <sbom_file> [--count-only]", file=sys.stderr)
        sys.exit(1)

    filepath = sys.argv[1]
    count_only = "--count-only" in sys.argv

    try:
        with open(filepath) as f:
            data = json.load(f)
        count = len(data.get("components", []))
        if count_only:
            print(count)
        else:
            print(f"Components: {count}")
    except Exception as e:
        if count_only:
            print(0)
        else:
            print(f"SBOM parse error: {e}")


if __name__ == "__main__":
    main()
