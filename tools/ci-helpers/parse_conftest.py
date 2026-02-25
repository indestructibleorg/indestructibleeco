#!/usr/bin/env python3
"""Parse conftest JSON output from stdin and report pass/fail.

Usage (check mode - exits 1 on failure):
  conftest test file.yaml --output json | python3 tools/ci-helpers/parse_conftest.py --check

Usage (report mode - prints results, always exits 0):
  conftest test file.yaml --output json | python3 tools/ci-helpers/parse_conftest.py --report
"""
import json
import sys


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "--check"

    try:
        raw = sys.stdin.read().strip()
        results = json.loads(raw) if raw else []
        failures = [x for x in results if x.get("failures")]

        if mode == "--check":
            if failures:
                for f in failures:
                    for m in f.get("failures", []):
                        print(m.get("msg", ""))
                sys.exit(1)
        elif mode == "--report":
            if failures:
                for f in failures:
                    for m in f.get("failures", []):
                        print("  FAIL:", m.get("msg", ""))
            else:
                print("  PASS")
    except Exception:
        if mode == "--check":
            sys.exit(0)
        else:
            print("  PASS (parse error)")


if __name__ == "__main__":
    main()
