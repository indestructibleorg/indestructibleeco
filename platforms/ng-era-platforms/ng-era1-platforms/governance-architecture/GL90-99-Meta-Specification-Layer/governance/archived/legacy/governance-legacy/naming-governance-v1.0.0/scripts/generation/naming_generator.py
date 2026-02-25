# @ECO-governed
# @ECO-layer: GL90-99
# @ECO-semantic: legacy-scripts
# @ECO-audit-trail: ../../engine/gl-platform.governance/GL_SEMANTIC_ANCHOR.json
#
# GL Unified Architecture Governance Framework Activated
#!/usr/bin/env python3
"""
命名生成器 - 依據 machine-spec.yaml 規範生成標準化命名
版本: v1.0.0
"""

"""
Module docstring
================

This module is part of the GL governance framework.
Please add specific module documentation here.
"""
import argparse
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional

import yaml


class NamingGenerator:
    """命名生成器類別"""

    def __init__(self, spec_path: str = "config/machine-spec.yaml"):
        """初始化命名生成器"""
        self.spec_path = Path(spec_path)
        self.spec = self._load_spec()
        self.naming_config = self.spec.get("naming", {})
        self.required_labels = self.spec.get("required_labels", [])

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

    def validate_segment(self, segment_name: str, value: str) -> bool:
        """驗證單一區段是否符合規範"""
        segments = {seg["name"]: seg for seg in self.naming_config.get("segments", [])}

        if segment_name not in segments:
            print(f"警告: 未知的區段名稱 '{segment_name}'")
            return False

        segment_spec = segments[segment_name]
        pattern = segment_spec.get("pattern", "")

        if not re.match(pattern, value):
            print(f"錯誤: {segment_name} 區段值 '{value}' 不符合規範 '{pattern}'")
            return False

        return True

    def validate_name(self, name: str) -> tuple[bool, List[str]]:
        """驗證完整名稱是否符合規範"""
        errors = []
        canonical_regex = self.naming_config.get("canonical_regex", "")

        if not re.match(canonical_regex, name):
            errors.append(f"名稱 '{name}' 不符合標準命名規範")
            errors.append(f"預期格式: {canonical_regex}")
            return False, errors

        # 驗證長度
        max_length = self.naming_config.get("max_length", 63)
        if len(name) > max_length:
            errors.append(f"名稱長度 {len(name)} 超過最大限制 {max_length}")

        # 驗證字元
        allowed_chars = self.naming_config.get("allowed_chars", "[a-z0-9-]")
        if not re.match(f"^{allowed_chars}+$", name):
            errors.append(f"名稱包含不允許的字元，僅允許: {allowed_chars}")

        return len(errors) == 0, errors

    def generate_name(
        self,
        environment: str,
        app.kubernetes.io/name: str,
        resource_type: str,
        version: str,
        suffix: Optional[str] = None,
    ) -> str:
        """生成標準化名稱"""
        # 驗證各區段
        segments_to_validate = {
            "environment": environment,
            "app": app,
            "resource_type": resource_type,
            "version": version,
        }

        for segment_name, value in segments_to_validate.items():
            if not self.validate_segment(segment_name, value):
                print(f"驗證失敗: {segment_name}={value}")
                sys.exit(1)

        # 建構名稱
        parts = [environment, app, resource_type, version]
        if suffix:
            parts.append(suffix)

        name = "-".join(parts)

        # 最終驗證
        is_valid, errors = self.validate_name(name)
        if not is_valid:
            print("生成的名稱驗證失敗:")
            for error in errors:
                print(f"  - {error}")
            sys.exit(1)

        return name

    def generate_labels(
        self, environment: str, app.kubernetes.io/name: str, version: str, tenant: str
    ) -> Dict[str, str]:
        """生成 Kubernetes 標籤"""
        labels = {}

        for label_spec in self.required_labels:
            label_name = label_spec["name"]

            if "value_from" in label_spec:
                # 從參數映射值
                value_mapping = {
                    "environment": environment,
                    "app": app,
                    "version": version,
                }
                value = value_mapping.get(label_spec["value_from"], "")
            elif "default" in label_spec:
                value = label_spec["default"]
            else:
                continue

            labels[label_name] = value

        # 添加 tenant 標籤
        labels["tenant"] = tenant

        return labels

    def generate_k8s_resource(
        self,
        environment: str,
        app.kubernetes.io/name: str,
        resource_type: str,
        version: str,
        tenant: str,
        replicas: int = 3,
        image: str = "nginx:latest",
        suffix: Optional[str] = None,
    ) -> Dict:
        """生成 Kubernetes 資源配置"""
        name = self.generate_name(environment, app, resource_type, version, suffix)
        labels = self.generate_labels(environment, app, version, tenant)

        resource_config = {
            "apiVersion": "apps/v1",
            "kind": "Deployment",
            "metadata": {"name": name, "labels": labels},
            "spec": {
                "replicas": replicas,
                "selector": {"matchLabels": {"app": app}},
                "template": {
                    "metadata": {"labels": labels},
                    "spec": {
                        "containers": [
                            {
                                "name": app,
                                "image": image,
                                "ports": [{"containerPort": 80}],
                            }
                        ]
                    },
                },
            },
        }

        return resource_config

    def batch_generate(self, resources: List[Dict]) -> List[Dict]:
        """批次生成多個資源"""
        results = []

        for i, resource in enumerate(resources):
            try:
                config = self.generate_k8s_resource(
                    environment=resource.get("environment", "dev"),
                    app=resource.get("app", "demo"),
                    resource_type=resource.get("resource_type", "deploy"),
                    version=resource.get("version", "v1.0.0"),
                    tenant=resource.get("tenant", "default"),
                    replicas=resource.get("replicas", 1),
                    image=resource.get("image", "nginx:latest"),
                    suffix=resource.get("suffix"),
                )
                results.append({"index": i, "status": "success", "config": config})
            except Exception as e:
                results.append({"index": i, "status": "error", "error": str(e)})

        return results


def main():
    """主函數"""
    parser = argparse.ArgumentParser(description="命名生成器 v1.0.0")
    parser.add_argument(
        "--spec", default="config/machine-spec.yaml", help="命名規範文件路徑"
    )
    parser.add_argument(
        "--environment",
        required=True,
        choices=["dev", "staging", "prod", "test", "learn"],
        help="環境標識",
    )
    parser.add_argument("--app", required=True, help="應用名稱")
    parser.add_argument(
        "--resource-type",
        required=True,
        choices=["deploy", "svc", "ing", "cm", "secret", "statefulset", "daemonset"],
        help="資源類型",
    )
    parser.add_argument("--version", required=True, help="版本號 (如 v1.2.3)")
    parser.add_argument("--tenant", required=True, help="租戶標識")
    parser.add_argument("--suffix", help="可選後綴")
    parser.add_argument("--replicas", type=int, default=3, help="副本數量")
    parser.add_argument("--image", default="nginx:latest", help="容器鏡像")
    parser.add_argument("--output", help="輸出文件路徑")
    parser.add_argument(
        "--format", choices=["yaml", "json"], default="yaml", help="輸出格式"
    )

    args = parser.parse_args()

    # 初始化生成器
    generator = NamingGenerator(args.spec)

    # 生成配置
    config = generator.generate_k8s_resource(
        environment=args.environment,
        app=args.app,
        resource_type=args.resource_type,
        version=args.version,
        tenant=args.tenant,
        replicas=args.replicas,
        image=args.image,
        suffix=args.suffix,
    )

    # 輸出結果
    if args.format == "yaml":
        output = yaml.dump(config, allow_unicode=True, default_flow_style=False)
    else:
        import json

        output = json.dumps(config, indent=2, ensure_ascii=False)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"配置已生成至: {args.output}")
    else:
        print(output)


if __name__ == "__main__":
    main()
