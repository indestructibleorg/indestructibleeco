# @ECO-governed
# @ECO-layer: GL90-99
# @ECO-semantic: legacy-scripts
# @ECO-audit-trail: ../../engine/gl-platform.governance/GL_SEMANTIC_ANCHOR.json
#
# GL Unified Architecture Governance Framework Activated
#!/usr/bin/env python3
"""
MachineNativeOps 命名治理自動修復腳本
版本: v1.0.0
狀態: 生產就緒

功能:
1. 自動檢測命名治理違規
2. 智能修復建議生成
3. 自動執行修復操作
4. 修復結果驗證
5. 審計日誌記錄
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
import logging
import os
import re
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

import yaml

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("/var/log/naming-gl-platform.governance-repair.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


class RepairStatus(Enum):
    """修復狀態枚舉"""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    VERIFIED = "verified"
    ROLLED_BACK = "rolled_back"


class ViolationType(Enum):
    """違規類型枚舉"""

    NAMING_PATTERN = "naming_pattern"
    VERSION_FORMAT = "version_format"
    MISSING_LABELS = "missing_labels"
    INCONSISTENT_VERSION = "inconsistent_version"
    CONFLICTING_NAMES = "conflicting_names"
    SECURITY_VIOLATION = "security_violation"
    COMPLIANCE_BREACH = "compliance_breach"


@dataclass
class ViolationReport:
    """違規報告數據類"""

    resource_id: str
    resource_type: str
    namespace: str
    violation_type: ViolationType
    severity: str
    description: str
    suggested_fix: str
    auto_repairable: bool
    repair_priority: int
    detected_at: str
    metadata: Dict[str, Any]


@dataclass
class RepairOperation:
    """修復操作數據類"""

    operation_id: str
    violation_reports: List[ViolationReport]
    repair_strategy: str
    estimated_duration: int
    risk_level: str
    requires_approval: bool
    created_at: str
    status: RepairStatus
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


class NamingGovernanceRepair:
    """命名治理自動修復主類"""

    def __init__(self, config_path: str = None):
        """初始化修復系統"""
        self.config_path = config_path or "/etc/naming-gl-platform.governance/config.yaml"
        self.config = self._load_config()
        self.kubeconfig_path = os.getenv("KUBECONFIG", "~/.kube/config")
        self.dry_run = False
        self.max_concurrent_repairs = self.config.get("max_concurrent_repairs", 5)
        self.approval_required = self.config.get("approval_required", False)

        # 初始化統計
        self.stats = {
            "total_violations_detected": 0,
            "repairs_attempted": 0,
            "repairs_successful": 0,
            "repairs_failed": 0,
            "auto_repaired": 0,
            "manual_intervention_required": 0,
        }

    def _load_config(self) -> Dict[str, Any]:
        """載入配置文件"""
        try:
            with open(self.config_path, "r") as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            logger.warning(f"配置文件未找到: {self.config_path}，使用默認配置")
            return self._get_default_config()
        except yaml.YAMLError as e:
            logger.error(f"配置文件解析錯誤: {e}")
            raise

    def _get_default_config(self) -> Dict[str, Any]:
        """獲取默認配置"""
        return {
            "max_concurrent_repairs": 5,
            "approval_required": False,
            "dry_run_default": False,
            "naming_patterns": {
                "services": r"^[a-z]+-[a-z]+-[a-z]+-v\d+\.\d+\.\d+$",
                "deployments": r"^[a-z]+-[a-z]+-deploy-v\d+\.\d+\.\d+$",
                "configmaps": r"^[a-z]+-[a-z]+-config-v\d+\.\d+\.\d+$",
            },
            "required_labels": ["app", "version", "environment", "managed-by"],
            "security_scan_enabled": True,
            "compliance_threshold": 0.95,
        }

    def detect_violations(
        self, namespace: str = "machine-native-ops"
    ) -> List[ViolationReport]:
        """檢測命名治理違規"""
        logger.info(f"開始檢測命名治理違規，命名空間: {namespace}")

        violations = []

        try:
            # 獲取所有 Kubernetes 資源
            resources = self._get_all_resources(namespace)

            for resource in resources:
                resource_violations = self._check_resource_violations(resource)
                violations.extend(resource_violations)

            # 按優先級排序
            violations.sort(key=lambda v: v.repair_priority, reverse=True)

            self.stats["total_violations_detected"] += len(violations)
            logger.info(f"檢測完成，發現 {len(violations)} 個違規")

            return violations

        except Exception as e:
            logger.error(f"檢測違規時發生錯誤: {e}")
            raise

    def _get_all_resources(self, namespace: str) -> List[Dict[str, Any]]:
        """獲取所有 Kubernetes 資源"""
        resources = []

        # 定義要檢查的資源類型
        resource_types = [
            "pods",
            "services",
            "deployments",
            "configmaps",
            "secrets",
            "persistentvolumeclaims",
            "ingress",
            "serviceaccounts",
            "statefulsets",
            "daemonsets",
            "replicasets",
        ]

        for resource_type in resource_types:
            try:
                cmd = ["kubectl", "get", resource_type, "-n", namespace, "-o", "json"]

                result = subprocess.run(cmd, capture_output=True, text=True, check=True)

                data = json.loads(result.stdout)
                if "items" in data:
                    for item in data["items"]:
                        resources.append(
                            {
                                "type": resource_type,
                                "data": item,
                                "namespace": namespace,
                            }
                        )

            except subprocess.CalledProcessError as e:
                logger.warning(f"無法獲取 {resource_type} 資源: {e}")
            except json.JSONDecodeError as e:
                logger.error(f"解析 {resource_type} 資源 JSON 失敗: {e}")

        return resources

    def _check_resource_violations(
        self, resource: Dict[str, Any]
    ) -> List[ViolationReport]:
        """檢查單個資源的違規"""
        violations = []
        resource["data"]
        resource["type"]

        # 檢查命名模式
        naming_violation = self._check_naming_pattern(resource)
        if naming_violation:
            violations.append(naming_violation)

        # 檢查版本格式
        version_violation = self._check_version_format(resource)
        if version_violation:
            violations.append(version_violation)

        # 檢查必需標籤
        label_violation = self._check_required_labels(resource)
        if label_violation:
            violations.append(label_violation)

        # 檢查安全配置
        if self.config.get("security_scan_enabled", True):
            security_violation = self._check_security_compliance(resource)
            if security_violation:
                violations.append(security_violation)

        return violations

    def _check_naming_pattern(
        self, resource: Dict[str, Any]
    ) -> Optional[ViolationReport]:
        """檢查命名模式違規"""
        metadata = resource["data"].get("metadata", {})
        name = metadata.get("name", "")
        resource_type = resource["type"]

        # 根據資源類型獲取對應的命名模式
        pattern_key = resource_type.rstrip("s")  # 移除複數形式
        pattern = self.config["naming_patterns"].get(pattern_key)

        if pattern and not re.match(pattern, name):
            return ViolationReport(
                resource_id=f"{resource_type}/{name}",
                resource_type=resource_type,
                namespace=resource["namespace"],
                violation_type=ViolationType.NAMING_PATTERN,
                severity="high",
                description=f"資源名稱 '{name}' 不符合命名模式 '{pattern}'",
                suggested_fix=self._generate_naming_suggestion(name, pattern_key),
                auto_repairable=True,
                repair_priority=3,
                detected_at=datetime.now().isoformat(),
                metadata={
                    "current_name": name,
                    "expected_pattern": pattern,
                    "pattern_key": pattern_key,
                },
            )

        return None

    def _check_version_format(
        self, resource: Dict[str, Any]
    ) -> Optional[ViolationReport]:
        """檢查版本格式違規"""
        metadata = resource["data"].get("metadata", {})
        name = metadata.get("name", "")
        labels = metadata.get("labels", {})

        # 從名稱中提取版本
        version_match = re.search(r"v(\d+)\.(\d+)\.(\d+)", name)
        if version_match:
            version = f"v{version_match.group(1)}.{version_match.group(2)}.{version_match.group(3)}"

            # 檢查標籤中的版本是否一致
            label_version = labels.get("version")
            if label_version and label_version != version:
                return ViolationReport(
                    resource_id=f"{resource['type']}/{name}",
                    resource_type=resource["type"],
                    namespace=resource["namespace"],
                    violation_type=ViolationType.INCONSISTENT_VERSION,
                    severity="medium",
                    description=f"名稱中的版本 '{version}' 與標籤中的版本 '{label_version}' 不一致",
                    suggested_fix=f"更新標籤版本為 {version}",
                    auto_repairable=True,
                    repair_priority=2,
                    detected_at=datetime.now().isoformat(),
                    metadata={
                        "name_version": version,
                        "label_version": label_version,
                        "correct_version": version,
                    },
                )

        return None

    def _check_required_labels(
        self, resource: Dict[str, Any]
    ) -> Optional[ViolationReport]:
        """檢查必需標籤"""
        metadata = resource["data"].get("metadata", {})
        name = metadata.get("name", "")
        labels = metadata.get("labels", {})

        required_labels = self.config.get("required_labels", [])
        missing_labels = [label for label in required_labels if label not in labels]

        if missing_labels:
            return ViolationReport(
                resource_id=f"{resource['type']}/{name}",
                resource_type=resource["type"],
                namespace=resource["namespace"],
                violation_type=ViolationType.MISSING_LABELS,
                severity="medium",
                description=f"缺少必需標籤: {', '.join(missing_labels)}",
                suggested_fix=f"添加缺少的標籤: {', '.join(missing_labels)}",
                auto_repairable=True,
                repair_priority=2,
                detected_at=datetime.now().isoformat(),
                metadata={
                    "missing_labels": missing_labels,
                    "existing_labels": list(labels.keys()),
                },
            )

        return None

    def _check_security_compliance(
        self, resource: Dict[str, Any]
    ) -> Optional[ViolationReport]:
        """檢查安全合規性"""
        data = resource["data"]
        metadata = data.get("metadata", {})
        name = metadata.get("name", "")
        resource_type = resource["type"]

        # 檢查敏感信息洩露
        if resource_type in ["configmaps", "secrets"]:
            string_data = data.get("data", {})
            sensitive_keys = ["password", "key", "token", "secret", "credential"]

            for key, value in string_data.items():
                if any(sensitive in key.lower() for sensitive in sensitive_keys):
                    if isinstance(value, str) and len(value) > 20:  # 可能的密碼
                        return ViolationReport(
                            resource_id=f"{resource_type}/{name}",
                            resource_type=resource_type,
                            namespace=resource["namespace"],
                            violation_type=ViolationType.SECURITY_VIOLATION,
                            severity="critical",
                            description=f"檢測到可能的敏感信息: {key}",
                            suggested_fix="將敏感信息移至專門的秘密管理系統",
                            auto_repairable=False,
                            repair_priority=1,
                            detected_at=datetime.now().isoformat(),
                            metadata={"sensitive_key": key, "key_length": len(value)},
                        )

        return None

    def _generate_naming_suggestion(self, current_name: str, pattern_key: str) -> str:
        """生成命名建議"""
        # 簡單的命名建議邏輯
        parts = current_name.split("-")
        if len(parts) >= 2:
            base_name = "-".join(parts[:2])
            return f"{base_name}-v1.0.0"
        return f"{pattern_key}-v1.0.0"

    def create_repair_plan(
        self, violations: List[ViolationReport]
    ) -> List[RepairOperation]:
        """創建修復計劃"""
        logger.info(f"為 {len(violations)} 個違規創建修復計劃")

        repair_operations = []

        # 按違規類型分組
        grouped_violations = self._group_violations(violations)

        for violation_type, violation_list in grouped_violations.items():
            operation = RepairOperation(
                operation_id=f"repair-{violation_type.value}-{int(time.time())}",
                violation_reports=violation_list,
                repair_strategy=self._determine_repair_strategy(violation_type),
                estimated_duration=self._estimate_repair_duration(violation_list),
                risk_level=self._assess_risk_level(violation_list),
                requires_approval=self._requires_approval(violation_list),
                created_at=datetime.now().isoformat(),
                status=RepairStatus.PENDING,
            )

            repair_operations.append(operation)

        return repair_operations

    def _group_violations(
        self, violations: List[ViolationReport]
    ) -> Dict[ViolationType, List[ViolationReport]]:
        """按違規類型分組"""
        grouped = {}
        for violation in violations:
            if violation.violation_type not in grouped:
                grouped[violation.violation_type] = []
            grouped[violation.violation_type].append(violation)
        return grouped

    def _determine_repair_strategy(self, violation_type: ViolationType) -> str:
        """確定修復策略"""
        strategies = {
            ViolationType.NAMING_PATTERN: "rename_resource",
            ViolationType.VERSION_FORMAT: "update_labels",
            ViolationType.MISSING_LABELS: "add_labels",
            ViolationType.INCONSISTENT_VERSION: "sync_version",
            ViolationType.SECURITY_VIOLATION: "security_fix",
            ViolationType.CONFLICTING_NAMES: "resolve_conflicts",
            ViolationType.COMPLIANCE_BREACH: "compliance_fix",
        }
        return strategies.get(violation_type, "manual_review")

    def _estimate_repair_duration(self, violations: List[ViolationReport]) -> int:
        """估計修復持續時間（秒）"""
        base_time = 60  # 基礎時間 60 秒
        per_violation_time = 30  # 每個違規額外 30 秒

        return base_time + (len(violations) * per_violation_time)

    def _assess_risk_level(self, violations: List[ViolationReport]) -> str:
        """評估風險等級"""
        if any(v.severity == "critical" for v in violations):
            return "high"
        elif any(v.severity == "high" for v in violations):
            return "medium"
        else:
            return "low"

    def _requires_approval(self, violations: List[ViolationReport]) -> bool:
        """判斷是否需要批准"""
        # 高風險或包含安全違規的修復需要批准
        return (
            self.approval_required
            or any(v.severity in ["critical", "high"] for v in violations)
            or any(
                v.violation_type == ViolationType.SECURITY_VIOLATION for v in violations
            )
        )

    def execute_repair(self, operation: RepairOperation) -> bool:
        """執行修復操作"""
        logger.info(f"開始執行修復操作: {operation.operation_id}")

        if operation.status != RepairStatus.PENDING:
            logger.warning(
                f"操作 {operation.operation_id} 狀態不正確: {operation.status}"
            )
            return False

        operation.status = RepairStatus.IN_PROGRESS
        self.stats["repairs_attempted"] += 1

        try:
            # 根據修復策略執行相應操作
            success = self._execute_repair_strategy(operation)

            if success:
                operation.status = RepairStatus.COMPLETED
                self.stats["repairs_successful"] += 1

                # 驗證修復結果
                if self._verify_repair_result(operation):
                    operation.status = RepairStatus.VERIFIED
                    logger.info(f"修復操作 {operation.operation_id} 完成並驗證成功")
                else:
                    logger.warning(f"修復操作 {operation.operation_id} 完成但驗證失敗")

                return True
            else:
                operation.status = RepairStatus.FAILED
                self.stats["repairs_failed"] += 1
                return False

        except Exception as e:
            logger.error(f"執行修復操作 {operation.operation_id} 時發生錯誤: {e}")
            operation.status = RepairStatus.FAILED
            operation.error_message = str(e)
            self.stats["repairs_failed"] += 1
            return False

    def _execute_repair_strategy(self, operation: RepairOperation) -> bool:
        """執行具體修復策略"""
        strategy = operation.repair_strategy

        if strategy == "rename_resource":
            return self._repair_naming_pattern(operation)
        elif strategy == "update_labels":
            return self._repair_version_format(operation)
        elif strategy == "add_labels":
            return self._repair_missing_labels(operation)
        elif strategy == "sync_version":
            return self._repair_inconsistent_version(operation)
        elif strategy == "security_fix":
            return self._repair_security_violation(operation)
        else:
            logger.warning(f"未實現的修復策略: {strategy}")
            return False

    def _repair_naming_pattern(self, operation: RepairOperation) -> bool:
        """修復命名模式違規"""
        logger.info("執行命名模式修復")

        for violation in operation.violation_reports:
            try:
                current_name = violation.metadata["current_name"]
                suggested_name = violation.suggested_fix
                resource_type = violation.resource_type
                namespace = violation.namespace

                if self.dry_run:
                    logger.info(
                        f"[DRY RUN] 將重命名 {resource_type}/{current_name} 為 {suggested_name}"
                    )
                    continue

                # 創建修復補丁
                patch = {
                    "metadata": {
                        "name": suggested_name,
                        "annotations": {
                            "machinenativeops.io/original-name": current_name,
                            "machinenativeops.io/repair-timestamp": datetime.now().isoformat(),
                            "machinenativeops.io/repair-operation": operation.operation_id,
                        },
                    }}

                # 執行重命名操作（注意：某些資源類型不支持直接重命名）
                cmd = [
                    "kubectl",
                    "patch",
                    resource_type,
                    current_name,
                    "-n",
                    namespace,
                    "-p",
                    json.dumps(patch),
                    "--type",
                    "merge",
                ]

                if not self.dry_run:
                    result = subprocess.run(cmd, capture_output=True, text=True)
                    if result.returncode != 0:
                        logger.error(f"重命名失敗: {result.stderr}")
                        continue

                logger.info(
                    f"成功重命名 {resource_type}/{current_name} 為 {suggested_name}"
                )

            except Exception as e:
                logger.error(f"修復命名模式失敗: {e}")
                continue

        return True

    def _repair_missing_labels(self, operation: RepairOperation) -> bool:
        """修復缺少標籤違規"""
        logger.info("執行缺少標籤修復")

        for violation in operation.violation_reports:
            try:
                resource_type = violation.resource_type
                resource_name = violation.resource_id.split("/")[-1]
                namespace = violation.namespace
                missing_labels = violation.metadata["missing_labels"]

                if self.dry_run:
                    logger.info(
                        f"[DRY RUN] 將為 {resource_type}/{resource_name} 添加標籤: {missing_labels}"
                    )
                    continue

                # 準備標籤補丁
                labels_to_add = {}
                for label in missing_labels:
                    if label == "managed-by":
                        labels_to_add[label] = "naming-gl-platform.governance"
                    elif label == "environment":
                        labels_to_add[label] = namespace
                    elif label == "version":
                        # 從資源名稱中提取版本
                        version_match = re.search(r"v(\d+\.\d+\.\d+)", resource_name)
                        if version_match:
                            labels_to_add[label] = f"v{version_match.group(1)}"
                    else:
                        labels_to_add[label] = "auto-generated"

                patch = {
                    "metadata": {
                        "labels": labels_to_add,
                        "annotations": {
                            "machinenativeops.io/repair-timestamp": datetime.now().isoformat(),
                            "machinenativeops.io/repair-operation": operation.operation_id,
                        },
                    }}

                # 執行標籤添加
                cmd = [
                    "kubectl",
                    "patch",
                    resource_type,
                    resource_name,
                    "-n",
                    namespace,
                    "-p",
                    json.dumps(patch),
                    "--type",
                    "merge",
                ]

                if not self.dry_run:
                    result = subprocess.run(cmd, capture_output=True, text=True)
                    if result.returncode != 0:
                        logger.error(f"添加標籤失敗: {result.stderr}")
                        continue

                logger.info(
                    f"成功為 {resource_type}/{resource_name} 添加標籤: {list(labels_to_add.keys())}"
                )

            except Exception as e:
                logger.error(f"修復缺少標籤失敗: {e}")
                continue

        return True

    def _repair_version_format(self, operation: RepairOperation) -> bool:
        """修復版本格式違規"""
        logger.info("執行版本格式修復")

        for violation in operation.violation_reports:
            try:
                resource_type = violation.resource_type
                resource_name = violation.resource_id.split("/")[-1]
                namespace = violation.namespace
                correct_version = violation.metadata["correct_version"]

                if self.dry_run:
                    logger.info(
                        f"[DRY RUN] 將為 {resource_type}/{resource_name} 更新版本標籤為 {correct_version}"
                    )
                    continue

                # 準備版本標籤補丁
                patch = {
                    "metadata": {
                        "labels": {
                            "version": correct_version},
                        "annotations": {
                            "machinenativeops.io/repair-timestamp": datetime.now().isoformat(),
                            "machinenativeops.io/repair-operation": operation.operation_id,
                        },
                    }}

                # 執行版本更新
                cmd = [
                    "kubectl",
                    "patch",
                    resource_type,
                    resource_name,
                    "-n",
                    namespace,
                    "-p",
                    json.dumps(patch),
                    "--type",
                    "merge",
                ]

                if not self.dry_run:
                    result = subprocess.run(cmd, capture_output=True, text=True)
                    if result.returncode != 0:
                        logger.error(f"更新版本標籤失敗: {result.stderr}")
                        continue

                logger.info(
                    f"成功更新 {resource_type}/{resource_name} 版本標籤為 {correct_version}"
                )

            except Exception as e:
                logger.error(f"修復版本格式失敗: {e}")
                continue

        return True

    def _repair_inconsistent_version(self, operation: RepairOperation) -> bool:
        """修復版本不一致違規"""
        # 與版本格式修復邏輯相同
        return self._repair_version_format(operation)

    def _repair_security_violation(self, operation: RepairOperation) -> bool:
        """修復安全違規"""
        logger.warning("安全違規需要人工干預，自動修復被禁用")

        for violation in operation.violation_reports:
            logger.error(f"安全違規: {violation.description} - 需要人工審核")

            # 發送安全告警
            self._send_security_alert(violation)

        return False

    def _verify_repair_result(self, operation: RepairOperation) -> bool:
        """驗證修復結果"""
        logger.info(f"驗證修復操作 {operation.operation_id} 的結果")

        try:
            # 重新檢測違規
            namespace = (
                operation.violation_reports[0].namespace
                if operation.violation_reports
                else "default"
            )
            current_violations = self.detect_violations(namespace)

            # 檢查修復的違規是否已解決
            original_violation_ids = {
                v.resource_id for v in operation.violation_reports
            }
            current_violation_ids = {v.resource_id for v in current_violations}

            remaining_violations = original_violation_ids.intersection(
                current_violation_ids
            )

            if not remaining_violations:
                logger.info(
                    f"修復操作 {operation.operation_id} 驗證成功：所有違規已解決"
                )
                return True
            else:
                logger.warning(
                    f"修復操作 {operation.operation_id} 驗證失敗：仍有 {len(remaining_violations)} 個違規未解決"
                )
                return False

        except Exception as e:
            logger.error(f"驗證修復結果時發生錯誤: {e}")
            return False

    def _send_security_alert(self, violation: ViolationReport):
        """發送安全告警"""
        try:
            alert_message = {
                "alert_type": "security_violation",
                "resource_id": violation.resource_id,
                "severity": violation.severity,
                "description": violation.description,
                "timestamp": datetime.now().isoformat(),
                "requires_immediate_action": True,
            }

            # 這裡可以集成實際的告警系統
            logger.warning(f"安全告警: {json.dumps(alert_message, indent=2)}")

        except Exception as e:
            logger.error(f"發送安全告警失敗: {e}")

    def generate_repair_report(
        self, operations: List[RepairOperation]
    ) -> Dict[str, Any]:
        """生成修復報告"""
        logger.info("生成修復報告")

        report = {
            "report_id": f"repair-report-{int(time.time())}",
            "generated_at": datetime.now().isoformat(),
            "summary": {
                "total_operations": len(operations),
                "completed_operations": len(
                    [op for op in operations if op.status == RepairStatus.COMPLETED]
                ),
                "failed_operations": len(
                    [op for op in operations if op.status == RepairStatus.FAILED]
                ),
                "auto_repaired": len(
                    [op for op in operations if op.status == RepairStatus.VERIFIED]
                ),
            },
            "operations": [asdict(op) for op in operations],
            "statistics": self.stats,
            "recommendations": self._generate_recommendations(operations),
        }

        return report

    def _generate_recommendations(self, operations: List[RepairOperation]) -> List[str]:
        """生成改進建議"""
        recommendations = []

        failed_ops = [op for op in operations if op.status == RepairStatus.FAILED]
        if failed_ops:
            recommendations.append("需要人工干預的修復操作較多，建議完善自動化修復邏輯")

        security_violations = []
        for op in operations:
            for violation in op.violation_reports:
                if violation.violation_type == ViolationType.SECURITY_VIOLATION:
                    security_violations.append(violation)

        if security_violations:
            recommendations.append("檢測到安全違規，建議加強安全培訓和審核流程")

        if self.stats["auto_repaired"] > self.stats["repairs_successful"] * 0.8:
            recommendations.append("自動修復成功率較高，可以考慮擴大自動修復範圍")

        return recommendations

    def save_report(self, report: Dict[str, Any], output_path: str = None):
        """保存修復報告"""
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"/var/log/naming-gl-platform.governance/repair_report_{timestamp}.json"

        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, "w") as f:
                json.dump(report, f, indent=2, default=str)
            logger.info(f"修復報告已保存到: {output_path}")
        except Exception as e:
            logger.error(f"保存修復報告失敗: {e}")


def main():
    """主函數"""
    parser = argparse.ArgumentParser(
        description="MachineNativeOps 命名治理自動修復工具"
    )
    parser.add_argument("--config", "-c", help="配置文件路徑")
    parser.add_argument(
        "--namespace", "-n", default="machine-native-ops", help="Kubernetes 命名空間"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="試運行模式，不執行實際修復"
    )
    parser.add_argument("--output", "-o", help="報告輸出路徑")
    parser.add_argument("--verbose", "-v", action="store_true", help="詳細輸出")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    try:
        # 初始化修復系統
        repair_system = NamingGovernanceRepair(args.config)
        repair_system.dry_run = args.dry_run

        logger.info("開始命名治理自動修復流程")

        # 檢測違規
        violations = repair_system.detect_violations(args.namespace)

        if not violations:
            logger.info("未檢測到違規，退出")
            return 0

        # 創建修復計劃
        repair_operations = repair_system.create_repair_plan(violations)

        # 執行修復
        successful_operations = []
        for operation in repair_operations:
            if repair_system.execute_repair(operation):
                successful_operations.append(operation)

        # 生成報告
        report = repair_system.generate_repair_report(repair_operations)
        repair_system.save_report(report, args.output)

        # 輸出摘要
        logger.info("修復完成摘要:")
        logger.info(f"  總違規數: {len(violations)}")
        logger.info(f"  修復操作: {len(repair_operations)}")
        logger.info(f"  成功修復: {len(successful_operations)}")
        logger.info(f"  統計數據: {repair_system.stats}")

        return (
            0
            if all(
                op.status in [RepairStatus.COMPLETED, RepairStatus.VERIFIED]
                for op in successful_operations
            )
            else 1
        )

    except Exception as e:
        logger.error(f"執行修復流程時發生錯誤: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
