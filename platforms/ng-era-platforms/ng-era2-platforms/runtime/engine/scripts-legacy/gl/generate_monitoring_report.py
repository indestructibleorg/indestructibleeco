#
# @ECO-governed
# @ECO-layer: gl-platform.gl-platform.governance
# @ECO-semantic: generate-monitoring-report
# @ECO-audit-trail: ../../engine/gl-platform.gl-platform.governance/GL_SEMANTIC_ANCHOR.json
#
#!/usr/bin/env python3
"""
GL Monitoring Report Generator
Generates monitoring reports for GL layers
"""
# MNGA-002: Import organization needs review
import argparse
import json
import os
import shutil
import subprocess
from typing import Optional
from datetime import datetime
from pathlib import Path
def generate_monitoring_report(layer: str, output_dir: str) -> dict:
    """Generate monitoring report for a GL layer"""
    report = {
        "report_id": f"ECO-MONITORING-{layer}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "layer": layer,
        "timestamp": datetime.now().isoformat(),
        "metrics": {
            "gpu_utilization": 0.0,
            "memory_usage": 0.0,
            "job_queue_length": 0
        },
        "alerts": []
    }
    gpu_utilization = _get_gpu_utilization_percent()
    memory_usage = _get_memory_usage_percent()
    job_queue_length = _get_job_queue_length()
    report["metrics"]["gpu_utilization"] = gpu_utilization
    report["metrics"]["memory_usage"] = memory_usage
    report["metrics"]["job_queue_length"] = job_queue_length
    _add_alerts(report["alerts"], gpu_utilization, memory_usage, job_queue_length)
    return report


def _get_memory_usage_percent() -> float:
    meminfo_path = Path("/proc/meminfo")
    if not meminfo_path.exists():
        return 0.0
    total_kb = None
    available_kb = None
    with meminfo_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.startswith("MemTotal:"):
                total_kb = _parse_meminfo_value(line)
            elif line.startswith("MemAvailable:"):
                available_kb = _parse_meminfo_value(line)
            if total_kb is not None and available_kb is not None:
                break
    if total_kb is None or available_kb is None or total_kb == 0:
        return 0.0
    used_kb = total_kb - available_kb
    return round((used_kb / total_kb) * 100.0, 2)


def _parse_meminfo_value(line: str) -> Optional[int]:
    parts = line.split()
    if len(parts) < 2:
        return None
    try:
        return int(parts[1])
    except ValueError:
        return None


def _get_gpu_utilization_percent() -> float:
    nvidia_smi = shutil.which("nvidia-smi")
    if not nvidia_smi:
        return 0.0
    try:
        result = subprocess.run(
            [nvidia_smi, "--query-gpu=utilization.gpu", "--format=csv,noheader,nounits"],
            capture_output=True,
            text=True,
            check=False,
            timeout=2,
        )
    except (OSError, subprocess.TimeoutExpired):
        return 0.0
    if result.returncode != 0:
        return 0.0
    values = []
    for line in result.stdout.splitlines():
        value = _parse_int(line.strip())
        if value is not None:
            values.append(value)
    if not values:
        return 0.0
    return round(sum(values) / len(values), 2)


def _parse_int(value: str) -> Optional[int]:
    try:
        return int(value)
    except ValueError:
        return None


def _get_job_queue_length() -> int:
    env_value = os.getenv("GL_JOB_QUEUE_LENGTH")
    if not env_value:
        return 0
    try:
        return max(int(env_value), 0)
    except ValueError:
        return 0


def _add_alerts(alerts: list, gpu_utilization: float, memory_usage: float, job_queue_length: int) -> None:
    if memory_usage >= 95:
        alerts.append(
            {
                "type": "memory",
                "severity": "critical",
                "message": f"Memory usage at {memory_usage}%",
                "value": memory_usage,
            }
        )
    elif memory_usage >= 85:
        alerts.append(
            {
                "type": "memory",
                "severity": "warning",
                "message": f"Memory usage at {memory_usage}%",
                "value": memory_usage,
            }
        )

    if gpu_utilization >= 98:
        alerts.append(
            {
                "type": "gpu",
                "severity": "critical",
                "message": f"GPU utilization at {gpu_utilization}%",
                "value": gpu_utilization,
            }
        )
    elif gpu_utilization >= 90:
        alerts.append(
            {
                "type": "gpu",
                "severity": "warning",
                "message": f"GPU utilization at {gpu_utilization}%",
                "value": gpu_utilization,
            }
        )

    if job_queue_length >= 200:
        alerts.append(
            {
                "type": "queue",
                "severity": "critical",
                "message": f"Job queue length at {job_queue_length}",
                "value": job_queue_length,
            }
        )
    elif job_queue_length >= 50:
        alerts.append(
            {
                "type": "queue",
                "severity": "warning",
                "message": f"Job queue length at {job_queue_length}",
                "value": job_queue_length,
            }
        )
def main():
    parser = argparse.ArgumentParser(description='Generate GL monitoring report')
    parser.add_argument('--layer', required=True, help='GL layer (e.g., GL50-59)')
    parser.add_argument('--output', required=True, help='Output directory')
    args = parser.parse_args()
    output_path = Path(args.output)
    output_path.mkdir(parents=True, exist_ok=True)
    report = generate_monitoring_report(args.layer, args.output)
    report_file = output_path / f"monitoring-{args.layer}-{datetime.now().strftime('%Y%m%d%H%M%S')}.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    print(f"Monitoring report generated: {report_file}")
if __name__ == "__main__":
    main()