#!/usr/bin/env python3
"""Parse CI validator report and write to GITHUB_OUTPUT."""
import json, os, re, sys

try:
    with open('/tmp/validation-report.json', encoding='utf-8') as _f:
        report = json.load(_f)
    error_count = report.get('error_count', 0)
    warning_count = report.get('warning_count', 0)
    total = error_count + warning_count
except Exception as e:
    print(f'Could not parse report: {e}', file=sys.stderr)
    try:
        with open('/tmp/validator-output.txt', encoding='utf-8') as _f:
            output = _f.read()
        m = re.search(r'Total:\s*(\d+)\s*errors?,\s*(\d+)\s*warnings?', output)
        if m:
            error_count = int(m.group(1))
            warning_count = int(m.group(2))
            total = error_count + warning_count
        else:
            error_count = 0
            warning_count = 0
            total = 0
    except Exception:
        error_count = 0
        warning_count = 0
        total = 0

print(f'Errors: {error_count}, Warnings: {warning_count}, Total: {total}')

github_output = os.environ.get('GITHUB_OUTPUT', '')
if github_output:
    with open(github_output, 'a', encoding='utf-8') as f:
        f.write(f'total_issues={total}\n')
        f.write(f'error_count={error_count}\n')
        f.write(f'warning_count={warning_count}\n')
        f.write(f'has_issues={"true" if total > 0 else "false"}\n')
