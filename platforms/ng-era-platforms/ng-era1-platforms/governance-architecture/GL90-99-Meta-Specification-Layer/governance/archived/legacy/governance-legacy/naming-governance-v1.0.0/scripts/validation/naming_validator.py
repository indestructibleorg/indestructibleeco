# @ECO-governed
# @ECO-layer: GL90-99
# @ECO-semantic: legacy-scripts
# @ECO-audit-trail: ../../engine/gl-platform.governance/GL_SEMANTIC_ANCHOR.json
#
# GL Unified Architecture Governance Framework Activated
#!/usr/bin/env python3
"""
命名稽核工具 - 自動化檢查資源命名合規性
版本: v1.0.0
"""

"""
Module docstring
================

This module is part of the GL governance framework.
Please add specific module documentation here.
"""
# MNGA-002: Import organization needs review
import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Tuple

import yaml


class ViolationSeverity(Enum):
    """違規嚴重程度"""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class Violation:
    """命名違規記錄"""

    resource_name: str
    resource_type: str
    namespace: str
    severity: ViolationSeverity
    rule: str
    description: str
    suggested_fix: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class NamingValidator:
    """命名驗證器類別"""

    def __init__(self, spec_path: str = "config/machine-spec.yaml"):
        """初始化驗證器"""
        self.spec_path = Path(spec_path)
        self.spec = self._load_spec()
        self.naming_config = self.spec.get("naming", {})
        self.violations: List[Violation] = []

    def _load_spec(self) -> Dict:
        """載入命名規範配置"""
        try:
            with open(self.spec_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            print(f"錯誤: 找不到規範文件 {self.spec_path}")
            sys.exit(1)
        except yaml.YAMLError as e:
            print(f"錯誤: YAML 解析失敗 - {e}")
            sys.exit(1)

    def validate_resource_name(
        self, name: str, resource_type: str, namespace: str = "default"
    ) -> List[Violation]:
        """驗證單一資源名稱"""
        violations = []

        # 檢查標準命名規範
        canonical_regex = self.naming_config.get("canonical_regex", "")
        if not re.match(canonical_regex, name):
            violations.append(
                Violation(
                    resource_name=name,
                    resource_type=resource_type,
                    namespace=namespace,
                    severity=ViolationSeverity.HIGH,
                    rule="canonical_naming_pattern",
                    description=f"名稱不符合標準命名規範: {canonical_regex}",
                    suggested_fix="請遵循格式: environment-app-resourceType-version (例: prod-payment-deploy-v1.2.3)",
                ))

        # 檢查長度限制
        max_length = self.naming_config.get("max_length", 63)
        if len(name) > max_length:
            violations.append(
                Violation(
                    resource_name=name,
                    resource_type=resource_type,
                    namespace=namespace,
                    severity=ViolationSeverity.MEDIUM,
                    rule="max_length",
                    description=f"名稱長度 {len(name)} 超過最大限制 {max_length}",
                    suggested_fix=f"縮短名稱至 {max_length} 字元以內",
                )
            )

        # 檢查字元限制
        allowed_chars = self.naming_config.get("allowed_chars", "[a-z0-9-]")
        if not re.match(f"^{allowed_chars}+$", name):
            violations.append(
                Violation(
                    resource_name=name,
                    resource_type=resource_type,
                    namespace=namespace,
                    severity=ViolationSeverity.HIGH,
                    rule="allowed_characters",
                    description=f"名稱包含不允許的字元，僅允許: {allowed_chars}",
                    suggested_fix="移除所有大寫字母、底線和特殊字元",
                )
            )

        # 檢查必要區段
        segments = self.naming_config.get("segments", [])
        name.split("-")

        for segment in segments:
            if segment.get("required", False):
                segment_name = segment["name"]
                if segment_name not in name:
                    violations.append(
                        Violation(
                            resource_name=name,
                            resource_type=resource_type,
                            namespace=namespace,
                            severity=ViolationSeverity.CRITICAL,
                            rule="required_segment",
                            description=f"缺少必要區段: {segment_name}",
                            suggested_fix=f"在名稱中添加 {segment_name} 區段",
                        )
                    )

        # 檢查版本號格式
        version_pattern = r"v\d+\.\d+\.\d+(-[a-zA-Z0-9]+)?"
        if not re.search(version_pattern, name):
            violations.append(
                Violation(
                    resource_name=name,
                    resource_type=resource_type,
                    namespace=namespace,
                    severity=ViolationSeverity.MEDIUM,
                    rule="version_format",
                    description="版本號格式不正確，應遵循 SemVer (vX.Y.Z)",
                    suggested_fix="添加正確的版本號格式 (例: v1.2.3)",
                )
            )

        return violations

    def validate_labels(
        self,
        labels: Dict[str, str],
        resource_name: str,
        resource_type: str,
        namespace: str = "default",
    ) -> List[Violation]:
        """驗證資源標籤"""
        violations = []
        required_labels = self.spec.get("required_labels", [])

        for label_spec in required_labels:
            label_name = label_spec["name"]

            if label_name not in labels:
                violations.append(
                    Violation(
                        resource_name=resource_name,
                        resource_type=resource_type,
                        namespace=namespace,
                        severity=ViolationSeverity.HIGH,
                        rule="required_label",
                        description=f"缺少必要標籤: {label_name}",
                        suggested_fix=f"添加標籤 {label_name}",
                    )
                )

            # 檢查標籤值驗證
            if "validation" in label_spec and label_name in labels:
                pattern = label_spec["validation"]
                if not re.match(pattern, labels[label_name]):
                    violations.append(
                        Violation(
                            resource_name=resource_name,
                            resource_type=resource_type,
                            namespace=namespace,
                            severity=ViolationSeverity.MEDIUM,
                            rule="label_validation",
                            description=f"標籤 {label_name} 的值 '{labels[label_name]}' 不符合規範 '{pattern}'",
                            suggested_fix="更新標籤值以符合規範",
                        ))

        return violations

    def validate_k8s_manifest(self, manifest_path: str) -> Tuple[bool, List[Violation]]:
        """驗證 Kubernetes Manifest 文件"""
        violations = []

        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                documents = list(yaml.safe_load_all(f))
        except FileNotFoundError:
            print(f"錯誤: 找不到文件 {manifest_path}")
            return False, []
        except yaml.YAMLError as e:
            print(f"錯誤: YAML 解析失敗 - {e}")
            return False, []

        for doc in documents:
            if not doc:
                continue

            metadata = doc.get("metadata", {})
            name = metadata.get("name", "")
            namespace = metadata.get("namespace", "default")
            kind = doc.get("kind", "")
            labels = metadata.get("labels", {})

            if not name:
                continue

            # 驗證資源名稱
            name_violations = self.validate_resource_name(name, kind, namespace)
            violations.extend(name_violations)

            # 驗證標籤
            label_violations = self.validate_labels(labels, name, kind, namespace)
            violations.extend(label_violations)

        is_compliant = len(violations) == 0
        return is_compliant, violations

    def validate_directory(
        self, directory: str, pattern: str = "*.yaml"
    ) -> Tuple[bool, List[Violation]]:
        """驗證目錄中的所有 YAML 文件"""
        all_violations = []
        dir_path = Path(directory)

        if not dir_path.exists():
            print(f"錯誤: 目錄不存在 {directory}")
            return False, []

        yaml_files = list(dir_path.glob(pattern))

        for yaml_file in yaml_files:
            print(f"正在驗證: {yaml_file}")
            is_compliant, violations = self.validate_k8s_manifest(str(yaml_file))

            if not is_compliant:
                all_violations.extend(violations)
                print(f"  ❌ 發現 {len(violations)} 個違規")
            else:
                print("  ✅ 通過驗證")

        return len(all_violations) == 0, all_violations

    def generate_report(
        self, violations: List[Violation], output_format: str = "text"
    ) -> str:
        """生成稽核報告"""
        if not violations:
            return "✅ 所有資源均符合命名規範！"

        # 按嚴重程度分組
        violations_by_severity = {
            ViolationSeverity.CRITICAL: [],
            ViolationSeverity.HIGH: [],
            ViolationSeverity.MEDIUM: [],
            ViolationSeverity.LOW: [],
        }

        for violation in violations:
            violations_by_severity[violation.severity].append(violation)

        # 統計資訊
        total_violations = len(violations)
        critical_count = len(violations_by_severity[ViolationSeverity.CRITICAL])
        high_count = len(violations_by_severity[ViolationSeverity.HIGH])
        medium_count = len(violations_by_severity[ViolationSeverity.MEDIUM])
        low_count = len(violations_by_severity[ViolationSeverity.LOW])


        if output_format == "text":
            report = []
            report.append("=" * 80)
            report.append("命名合規性稽核報告")
            report.append("=" * 80)
            report.append(f"生成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            report.append(f"規範版本: {self.spec.get('version', 'v1.0.0')}")
            report.append("")

            # 統計摘要
            report.append("📊 統計摘要")
            report.append("-" * 80)
            report.append(f"總違規數: {total_violations}")
            report.append(f"  🔴 CRITICAL: {critical_count}")
            report.append(f"  🟠 HIGH: {high_count}")
            report.append(f"  🟡 MEDIUM: {medium_count}")
            report.append(f"  🟢 LOW: {low_count}")
            report.append("")

            # 違規詳情
            report.append("📋 違規詳情")
            report.append("-" * 80)

            for severity in [
                ViolationSeverity.CRITICAL,
                ViolationSeverity.HIGH,
                ViolationSeverity.MEDIUM,
                ViolationSeverity.LOW,
            ]:
                severity_violations = violations_by_severity[severity]
                if severity_violations:
                    report.append(
                        f"\n{severity.value.upper()} ({len(severity_violations)}):"
                    )
                    report.append("")

                    for i, violation in enumerate(severity_violations, 1):
                        report.append(f"{i}. 資源: {violation.resource_name}")
                        report.append(f"   類型: {violation.resource_type}")
                        report.append(f"   命名空間: {violation.namespace}")
                        report.append(f"   規則: {violation.rule}")
                        report.append(f"   描述: {violation.description}")
                        report.append(f"   建議修正: {violation.suggested_fix}")
                        report.append("")

            report.append("=" * 80)

            return "\n".join(report)

        elif output_format == "json":
            report = {
                "timestamp": datetime.now().isoformat(),
                "spec_version": self.spec.get("version", "v1.0.0"),
                "summary": {
                    "total_violations": total_violations,
                    "critical": critical_count,
                    "high": high_count,
                    "medium": medium_count,
                    "low": low_count,
                },
                "violations": [
                    {
                        "resource_name": v.resource_name,
                        "resource_type": v.resource_type,
                        "namespace": v.namespace,
                        "severity": v.severity.value,
                        "rule": v.rule,
                        "description": v.description,
                        "suggested_fix": v.suggested_fix,
                        "timestamp": v.timestamp,
                    }
                    for v in violations
                ],
            }
            return json.dumps(report, indent=2, ensure_ascii=False)

        elif output_format == "yaml":
            report_data = {
                "timestamp": datetime.now().isoformat(),
                "spec_version": self.spec.get("version", "v1.0.0"),
                "summary": {
                    "total_violations": total_violations,
                    "critical": critical_count,
                    "high": high_count,
                    "medium": medium_count,
                    "low": low_count,
                },
                "violations": [
                    {
                        "resource_name": v.resource_name,
                        "resource_type": v.resource_type,
                        "namespace": v.namespace,
                        "severity": v.severity.value,
                        "rule": v.rule,
                        "description": v.description,
                        "suggested_fix": v.suggested_fix,
                        "timestamp": v.timestamp,
                    }
                    for v in violations
                ],
            }
            return yaml.dump(report_data, allow_unicode=True, default_flow_style=False)


def main():
    """主函數"""
    parser = argparse.ArgumentParser(description="命名稽核工具 v1.0.0")
    parser.add_argument(
        "--spec", default="config/machine-spec.yaml", help="命名規範文件路徑"
    )
    parser.add_argument("--file", help="驗證單一 YAML 文件")
    parser.add_argument("--directory", help="驗證目錄中的所有 YAML 文件")
    parser.add_argument(
        "--pattern", default="*.yaml", help="目錄驗證的文件模式 (預設: *.yaml)"
    )
    parser.add_argument("--output", help="輸出報告文件路徑")
    parser.add_argument(
        "--format",
        choices=["text", "json", "yaml"],
        default="text",
        help="輸出格式 (預設: text)",
    )
    parser.add_argument(
        "--strict", action="store_true", help="嚴格模式，任何違規都返回非零退出碼"
    )

    args = parser.parse_args()

    # 初始化驗證器
    validator = NamingValidator(args.spec)

    # 執行驗證
    all_violations = []

    if args.file:
        is_compliant, violations = validator.validate_k8s_manifest(args.file)
        all_violations.extend(violations)
    elif args.directory:
        is_compliant, violations = validator.validate_directory(
            args.directory, args.pattern
        )
        all_violations.extend(violations)
    else:
        parser.print_help()
        sys.exit(1)

    # 生成報告
    report = validator.generate_report(all_violations, args.format)

    # 輸出報告
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"報告已生成至: {args.output}")
    else:
        print("\n" + report)

    # 返回退出碼
    if args.strict and all_violations:
        sys.exit(1)
    elif not all_violations:
        sys.exit(0)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
