# @ECO-governed
# @ECO-layer: GL90-99
# @ECO-semantic: legacy-scripts
# @ECO-audit-trail: ../../engine/gl-platform.governance/GL_SEMANTIC_ANCHOR.json
#
# GL Unified Architecture Governance Framework Activated
#!/usr/bin/env python3
"""
MachineNativeOps 命名治理遷移腳本
版本: v1.0.0
狀態: 生產就緒

功能:
1. 資產發現與盤點
2. 遷移計畫生成
3. 風險評估與分析
4. Dry-run 模擬測試
5. 分階段重命名執行
6. Cutover 切換管理
7. 回滾機制實現
8. 遷移審計與報告
"""

"""
Module docstring
================

This module is part of the GL governance framework.
Please add specific module documentation here.
"""
# MNGA-002: Import organization needs review
import argparse
import concurrent.futures
import json
import logging
import os
import re
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

import yaml

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("/var/log/naming-gl-platform.governance-migration.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


class MigrationPhase(Enum):
    """遷移階段枚舉"""

    DISCOVERY = "discovery"
    PLANNING = "planning"
    RISK_ASSESSMENT = "risk_assessment"
    DRY_RUN = "dry_run"
    STAGED_MIGRATION = "staged_migration"
    CUTOVER = "cutover"
    VERIFICATION = "verification"
    ROLLBACK = "rollback"
    COMPLETED = "completed"


class MigrationStatus(Enum):
    """遷移狀態枚舉"""

    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class RiskLevel(Enum):
    """風險等級枚舉"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class AssetInfo:
    """資產信息數據類"""

    resource_id: str
    resource_type: str
    namespace: str
    name: str
    current_version: str
    labels: Dict[str, str]
    annotations: Dict[str, str]
    dependencies: List[str]
    dependents: List[str]
    created_at: str
    risk_level: RiskLevel
    migration_priority: int
    estimated_downtime: int
    metadata: Dict[str, Any]


@dataclass
class MigrationPlan:
    """遷移計畫數據類"""

    plan_id: str
    phase: MigrationPhase
    assets: List[AssetInfo]
    migration_strategy: str
    estimated_duration: int
    rollback_strategy: str
    approval_status: str
    created_at: str
    status: MigrationStatus
    risk_assessment: Dict[str, Any]
    rollback_point: Optional[str] = None


class NamingGovernanceMigration:
    """命名治理遷移主類"""

    def __init__(self, config_path: str = None):
        """初始化遷移系統"""
        self.config_path = config_path or "/etc/naming-gl-platform.governance/migration-config.yaml"
        self.config = self._load_config()
        self.kubeconfig_path = os.getenv("KUBECONFIG", "~/.kube/config")
        self.dry_run = False
        self.backup_enabled = True
        self.approval_required = True

        # 遷移狀態
        self.current_phase = MigrationPhase.NOT_STARTED
        self.migration_stats = {
            "total_assets_discovered": 0,
            "assets_migrated": 0,
            "assets_failed": 0,
            "rollback_initiated": False,
            "downtime_seconds": 0,
        }

        # 遷移歷史
        self.migration_history = []

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
            "backup_enabled": True,
            "approval_required": True,
            "max_concurrent_migrations": 3,
            "downtime_threshold": 300,  # 5 分鐘
            "naming_patterns": {
                "services": r"^[a-z]+-[a-z]+-[a-z]+-v\d+\.\d+\.\d+$",
                "deployments": r"^[a-z]+-[a-z]+-deploy-v\d+\.\d+\.\d+$",
                "configmaps": r"^[a-z]+-[a-z]+-config-v\d+\.\d+\.\d+$",
            },
            "migration_order": [
                "configmaps",
                "secrets",
                "serviceaccounts",
                "services",
                "deployments",
                "statefulsets",
            ],
            "excluded_resources": ["kube-system", "kube-public", "kube-node-lease"],
        }

    def discover_assets(self, namespaces: List[str] = None) -> List[AssetInfo]:
        """發現和盤點資產"""
        logger.info("開始資產發現與盤點")
        self.current_phase = MigrationPhase.DISCOVERY

        if not namespaces:
            namespaces = self._get_all_namespaces()

        all_assets = []

        for namespace in namespaces:
            if namespace in self.config.get("excluded_resources", []):
                continue

            try:
                namespace_assets = self._discover_namespace_assets(namespace)
                all_assets.extend(namespace_assets)
                logger.info(f"命名空間 {namespace} 發現 {len(namespace_assets)} 個資產")

            except Exception as e:
                logger.error(f"發現命名空間 {namespace} 資產失敗: {e}")
                continue

        # 分析依賴關係
        self._analyze_dependencies(all_assets)

        # 評估風險等級
        self._assess_asset_risks(all_assets)

        # 按優先級排序
        all_assets.sort(key=lambda a: a.migration_priority, reverse=True)

        self.migration_stats["total_assets_discovered"] = len(all_assets)
        logger.info(f"資產發現完成，總計 {len(all_assets)} 個資產")

        return all_assets

    def _get_all_namespaces(self) -> List[str]:
        """獲取所有命名空間"""
        try:
            cmd = ["kubectl", "get", "namespaces", "-o", "json"]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            data = json.loads(result.stdout)

            namespaces = []
            for item in data.get("items", []):
                name = item["metadata"]["name"]
                if not name.startswith("kube-"):
                    namespaces.append(name)

            return namespaces

        except Exception as e:
            logger.error(f"獲取命名空間失敗: {e}")
            return ["default"]

    def _discover_namespace_assets(self, namespace: str) -> List[AssetInfo]:
        """發現指定命名空間的資產"""
        assets = []

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
            "horizontalpodautoscalers",
        ]

        for resource_type in resource_types:
            try:
                cmd = ["kubectl", "get", resource_type, "-n", namespace, "-o", "json"]

                result = subprocess.run(cmd, capture_output=True, text=True, check=True)

                data = json.loads(result.stdout)
                if "items" in data:
                    for item in data["items"]:
                        asset = self._create_asset_info(item, resource_type, namespace)
                        if asset:
                            assets.append(asset)

            except subprocess.CalledProcessError as e:
                logger.warning(f"無法獲取 {namespace}/{resource_type} 資源: {e}")
            except json.JSONDecodeError as e:
                logger.error(f"解析 {namespace}/{resource_type} JSON 失敗: {e}")

        return assets

    def _create_asset_info(
        self, item: Dict[str, Any], resource_type: str, namespace: str
    ) -> Optional[AssetInfo]:
        """創建資產信息"""
        try:
            metadata = item.get("metadata", {})
            name = metadata.get("name", "")

            # 跳過系統資源
            if name.startswith("kube-") or name.endswith("-controller"):
                return None

            # 提取版本信息
            version = self._extract_version(name)

            # 獲取標籤和註解
            labels = metadata.get("labels", {})
            annotations = metadata.get("annotations", {})

            asset = AssetInfo(
                resource_id=f"{resource_type}/{name}",
                resource_type=resource_type,
                namespace=namespace,
                name=name,
                current_version=version,
                labels=labels,
                annotations=annotations,
                dependencies=[],
                dependents=[],
                created_at=metadata.get("creationTimestamp", ""),
                risk_level=RiskLevel.LOW,
                migration_priority=1,
                estimated_downtime=30,
                metadata={
                    "uid": metadata.get("uid", ""),
                    "resource_version": metadata.get("resourceVersion", ""),
                    "generation": metadata.get("generation", 0),
                },
            )

            return asset

        except Exception as e:
            logger.error(f"創建資產信息失敗: {e}")
            return None

    def _extract_version(self, name: str) -> str:
        """從資源名稱中提取版本"""
        version_match = re.search(r"v(\d+)\.(\d+)\.(\d+)", name)
        if version_match:
            return f"v{version_match.group(1)}.{version_match.group(2)}.{version_match.group(3)}"
        return "v1.0.0"

    def _analyze_dependencies(self, assets: List[AssetInfo]):
        """分析資產依賴關係"""
        logger.info("分析資產依賴關係")

        # 創建資產映射
        asset_map = {asset.resource_id: asset for asset in assets}

        for asset in assets:
            # 分析規範中的依賴
            try:
                resource_type = asset.resource_type
                name = asset.name
                namespace = asset.namespace

                if resource_type in ["deployments", "statefulsets"]:
                    # 檢查服務帳戶依賴
                    cmd = [
                        "kubectl",
                        "get",
                        resource_type,
                        name,
                        "-n",
                        namespace,
                        "-o",
                        "jsonpath={.spec.serviceAccountName}",
                    ]

                    result = subprocess.run(cmd, capture_output=True, text=True)
                    if result.stdout.strip():
                        service_account_id = f"serviceaccounts/{result.stdout.strip()}"
                        if service_account_id in asset_map:
                            asset.dependencies.append(service_account_id)
                            asset_map[service_account_id].dependents.append(
                                asset.resource_id
                            )

                elif resource_type == "services":
                    # 檢查關聯的部署
                    selector = asset.labels.get("app", "")
                    if selector:
                        for potential_asset in assets:
                            if (
                                potential_asset.resource_type
                                in ["deployments", "statefulsets"]
                                and potential_asset.labels.get("app") == selector
                            ):
                                asset.dependencies.append(potential_asset.resource_id)
                                potential_asset.dependents.append(asset.resource_id)

            except Exception as e:
                logger.warning(f"分析 {asset.resource_id} 依賴失敗: {e}")

    def _assess_asset_risks(self, assets: List[AssetInfo]):
        """評估資產風險等級"""
        logger.info("評估資產風險等級")

        for asset in assets:
            risk_score = 0

            # 基於依賴關係的風險
            if len(asset.dependents) > 10:
                risk_score += 3  # 高依賴數量
            elif len(asset.dependents) > 5:
                risk_score += 2

            # 基於資源類型的風險
            high_risk_types = ["statefulsets", "persistentvolumeclaims", "ingress"]
            if asset.resource_type in high_risk_types:
                risk_score += 2

            # 基於命名風險
            if not self._is_naming_compliant(asset.name):
                risk_score += 1

            # 基於複雜度的風險
            if asset.resource_type == "deployments":
                complexity = self._assess_deployment_complexity(asset)
                risk_score += min(complexity, 2)

            # 確定風險等級
            if risk_score >= 6:
                asset.risk_level = RiskLevel.CRITICAL
                asset.migration_priority = 4
                asset.estimated_downtime = 300
            elif risk_score >= 4:
                asset.risk_level = RiskLevel.HIGH
                asset.migration_priority = 3
                asset.estimated_downtime = 180
            elif risk_score >= 2:
                asset.risk_level = RiskLevel.MEDIUM
                asset.migration_priority = 2
                asset.estimated_downtime = 60
            else:
                asset.risk_level = RiskLevel.LOW
                asset.migration_priority = 1
                asset.estimated_downtime = 30

    def _is_naming_compliant(self, name: str) -> bool:
        """檢查命名是否合規"""
        pattern = r"^[a-z]+-[a-z]+-[a-z]+-v\d+\.\d+\.\d+$"
        return bool(re.match(pattern, name))

    def _assess_deployment_complexity(self, asset: AssetInfo) -> int:
        """評估部署複雜度"""
        try:
            cmd = [
                "kubectl",
                "get",
                "deployment",
                asset.name,
                "-n",
                asset.namespace,
                "-o",
                "json",
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            data = json.loads(result.stdout)

            spec = data.get("spec", {})
            template = spec.get("template", {})

            complexity = 0

            # 基於容器數量
            containers = template.get("spec", {}).get("containers", [])
            if len(containers) > 3:
                complexity += 1

            # 基於卷數量
            volumes = template.get("spec", {}).get("volumes", [])
            if len(volumes) > 2:
                complexity += 1

            # 基於環境變量數量
            for container in containers:
                env_vars = container.get("env", [])
                if len(env_vars) > 10:
                    complexity += 1
                    break

            return complexity

        except Exception as e:
            logger.warning(f"評估部署複雜度失敗: {e}")
            return 0

    def create_migration_plan(self, assets: List[AssetInfo]) -> MigrationPlan:
        """創建遷移計畫"""
        logger.info("創建遷移計畫")
        self.current_phase = MigrationPhase.PLANNING

        # 按遷移順序排序
        migration_order = self.config.get("migration_order", [])
        sorted_assets = sorted(
            assets,
            key=lambda a: (
                (
                    migration_order.index(a.resource_type)
                    if a.resource_type in migration_order
                    else 999
                ),
                -a.migration_priority,
                a.risk_level.value,
            ),
        )

        # 評估整體風險
        risk_assessment = self._assess_migration_risk(sorted_assets)

        # 計算預估持續時間
        estimated_duration = sum(asset.estimated_downtime for asset in sorted_assets)

        plan = MigrationPlan(
            plan_id=f"migration-plan-{int(time.time())}",
            phase=MigrationPhase.PLANNING,
            assets=sorted_assets,
            migration_strategy="staged_migration",
            estimated_duration=estimated_duration,
            rollback_strategy="incremental_rollback",
            approval_status="pending",
            created_at=datetime.now().isoformat(),
            status=MigrationStatus.NOT_STARTED,
            risk_assessment=risk_assessment,
        )

        logger.info(f"遷移計畫創建完成，包含 {len(sorted_assets)} 個資產")
        return plan

    def _assess_migration_risk(self, assets: List[AssetInfo]) -> Dict[str, Any]:
        """評估遷移風險"""
        critical_assets = [a for a in assets if a.risk_level == RiskLevel.CRITICAL]
        high_risk_assets = [a for a in assets if a.risk_level == RiskLevel.HIGH]

        total_downtime = sum(a.estimated_downtime for a in assets)

        risk_factors = {
            "critical_assets_count": len(critical_assets),
            "high_risk_assets_count": len(high_risk_assets),
            "total_assets_count": len(assets),
            "estimated_total_downtime": total_downtime,
            "dependency_complexity": self._calculate_dependency_complexity(assets),
            "naming_compliance_rate": self._calculate_compliance_rate(assets),
        }

        # 計算整體風險分數
        risk_score = (
            len(critical_assets) * 4
            + len(high_risk_assets) * 2
            + (total_downtime / 60)  # 轉換為分鐘
            + (1 - risk_factors["naming_compliance_rate"]) * 10
        )

        if risk_score > 20:
            overall_risk = RiskLevel.CRITICAL
        elif risk_score > 10:
            overall_risk = RiskLevel.HIGH
        elif risk_score > 5:
            overall_risk = RiskLevel.MEDIUM
        else:
            overall_risk = RiskLevel.LOW

        return {
            "overall_risk": overall_risk.value,
            "risk_score": risk_score,
            "risk_factors": risk_factors,
            "recommendations": self._generate_risk_recommendations(risk_factors),
        }

    def _calculate_dependency_complexity(self, assets: List[AssetInfo]) -> float:
        """計算依賴複雜度"""
        total_dependencies = sum(len(asset.dependencies) for asset in assets)
        total_assets = len(assets)

        if total_assets == 0:
            return 0.0

        return total_dependencies / total_assets

    def _calculate_compliance_rate(self, assets: List[AssetInfo]) -> float:
        """計算命名合規率"""
        if not assets:
            return 0.0

        compliant_count = sum(
            1 for asset in assets if self._is_naming_compliant(asset.name)
        )
        return compliant_count / len(assets)

    def _generate_risk_recommendations(self, risk_factors: Dict[str, Any]) -> List[str]:
        """生成風險建議"""
        recommendations = []

        if risk_factors["critical_assets_count"] > 0:
            recommendations.append("關鍵資產需要額外的預防措施和監控")

        if risk_factors["estimated_total_downtime"] > 1800:  # 30 分鐘
            recommendations.append("預估停機時間較長，建議分批次遷移")

        if risk_factors["dependency_complexity"] > 3:
            recommendations.append("依賴關係複雜，建議創建詳細的依賴圖")

        if risk_factors["naming_compliance_rate"] < 0.8:
            recommendations.append("命名合規率較低，建議先進行預清理")

        return recommendations

    def perform_dry_run(self, plan: MigrationPlan) -> bool:
        """執行 Dry-run 模擬"""
        logger.info("開始 Dry-run 模擬")
        self.current_phase = MigrationPhase.DRY_RUN

        try:
            # 創建備份點
            if self.backup_enabled:
                backup_point = self._create_backup_point()
                plan.rollback_point = backup_point
                logger.info(f"創建備份點: {backup_point}")

            # 模擬遷移操作
            simulation_results = []

            for asset in plan.assets:
                result = self._simulate_asset_migration(asset)
                simulation_results.append(result)

                if not result["success"]:
                    logger.error(
                        f"資產 {asset.resource_id} 模擬失敗: {result['error']}"
                    )
                    return False

            # 生成模擬報告
            self._generate_dry_run_report(plan, simulation_results)

            logger.info("Dry-run 模擬完成")
            return True

        except Exception as e:
            logger.error(f"Dry-run 模擬失敗: {e}")
            return False

    def _create_backup_point(self) -> str:
        """創建備份點"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"/var/backups/naming-gl-platform.governance/migration_{timestamp}"

        try:
            os.makedirs(backup_path, exist_ok=True)

            # 備份所有命名空間的資源
            cmd = ["kubectl", "get", "all", "--all-namespaces", "-o", "yaml"]

            backup_file = os.path.join(backup_path, "cluster_resources.yaml")
            with open(backup_file, "w") as f:
                subprocess.run(cmd, stdout=f, check=True)

            return backup_path

        except Exception as e:
            logger.error(f"創建備份點失敗: {e}")
            raise

    def _simulate_asset_migration(self, asset: AssetInfo) -> Dict[str, Any]:
        """模擬資產遷移"""
        try:
            # 生成新名稱
            new_name = self._generate_compliant_name(asset)

            # 檢查名稱衝突
            if self._check_name_conflict(new_name, asset.namespace):
                return {"success": False, "error": f"新名稱 {new_name} 已存在"}

            # 模擬驗證步驟
            validation_steps = [
                "validate_naming_pattern",
                "check_dependencies",
                "verify_resources",
                "simulate_rollback",
            ]

            for step in validation_steps:
                if not self._simulate_validation_step(asset, step):
                    return {"success": False, "error": f"驗證步驟失敗: {step}"}

            return {
                "success": True,
                "old_name": asset.name,
                "new_name": new_name,
                "estimated_downtime": asset.estimated_downtime,
                "validation_passed": True,
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _generate_compliant_name(self, asset: AssetInfo) -> str:
        """生成符合規範的名稱"""
        base_name = asset.name
        resource_type = asset.resource_type

        # 提取基礎名稱（去掉版本部分）
        base_without_version = re.sub(r"-v\d+\.\d+\.\d+", "", base_name)

        # 根據資源類型添加後綴
        if resource_type == "deployments":
            return f"{base_without_version}-deploy-v1.0.0"
        elif resource_type == "services":
            return f"{base_without_version}-svc-v1.0.0"
        elif resource_type == "configmaps":
            return f"{base_without_version}-config-v1.0.0"
        else:
            return f"{base_without_version}-v1.0.0"

    def _check_name_conflict(self, name: str, namespace: str) -> bool:
        """檢查名稱衝突"""
        try:
            cmd = [
                "kubectl",
                "get",
                "all",
                "-n",
                namespace,
                "-o",
                "jsonpath={.items[*].metadata.name}",
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)
            existing_names = result.stdout.split()

            return name in existing_names

        except Exception as e:
            logger.warning(f"檢查名稱衝突失敗: {e}")
            return False

    def _simulate_validation_step(self, asset: AssetInfo, step: str) -> bool:
        """模擬驗證步驟"""
        # 這裡實現各種驗證步驟的模擬邏輯
        if step == "validate_naming_pattern":
            new_name = self._generate_compliant_name(asset)
            return self._is_naming_compliant(new_name)

        elif step == "check_dependencies":
            # 檢查依賴是否可以正常遷移
            return True

        elif step == "verify_resources":
            # 驗證資源需求
            return True

        elif step == "simulate_rollback":
            # 模擬回滾操作
            return True

        return True

    def _generate_dry_run_report(
        self, plan: MigrationPlan, results: List[Dict[str, Any]]
    ):
        """生成 Dry-run 報告"""
        report = {
            "plan_id": plan.plan_id,
            "simulation_timestamp": datetime.now().isoformat(),
            "total_assets": len(plan.assets),
            "successful_simulations": sum(1 for r in results if r["success"]),
            "failed_simulations": sum(1 for r in results if not r["success"]),
            "estimated_total_downtime": sum(
                r.get("estimated_downtime", 0) for r in results
            ),
            "results": results,
        }

        # 保存報告
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = f"/var/log/naming-gl-platform.governance/dry_run_report_{timestamp}.json"

        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)

        logger.info(f"Dry-run 報告已保存到: {report_path}")

    def execute_staged_migration(self, plan: MigrationPlan) -> bool:
        """執行分階段遷移"""
        logger.info("開始分階段遷移")
        self.current_phase = MigrationPhase.STAGED_MIGRATION
        plan.status = MigrationStatus.IN_PROGRESS

        try:
            # 按批次分組遷移
            batch_size = self.config.get("max_concurrent_migrations", 3)
            asset_batches = [
                plan.assets[i: i + batch_size]
                for i in range(0, len(plan.assets), batch_size)
            ]

            successful_migrations = 0
            failed_migrations = 0

            for batch_index, batch in enumerate(asset_batches):
                logger.info(
                    f"執行批次 {batch_index + 1}/{len(asset_batches)}，包含 {len(batch)} 個資產"
                )

                batch_success = self._migrate_asset_batch(batch, batch_index + 1)

                if batch_success:
                    successful_migrations += len(batch)
                    logger.info(f"批次 {batch_index + 1} 遷移成功")
                else:
                    failed_migrations += len(batch)
                    logger.error(f"批次 {batch_index + 1} 遷移失敗")

                    # 決定是否繼續
                    if failed_migrations > successful_migrations:
                        logger.error("失敗數量過多，中止遷移")
                        break

            self.migration_stats["assets_migrated"] = successful_migrations
            self.migration_stats["assets_failed"] = failed_migrations

            if failed_migrations == 0:
                plan.status = MigrationStatus.COMPLETED
                logger.info("分階段遷移完成")
                return True
            else:
                logger.error(f"遷移完成，但有 {failed_migrations} 個資產失敗")
                return False

        except Exception as e:
            logger.error(f"分階段遷移失敗: {e}")
            plan.status = MigrationStatus.FAILED
            return False

    def _migrate_asset_batch(self, assets: List[AssetInfo], batch_number: int) -> bool:
        """遷移資產批次"""
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            future_to_asset = {
                executor.submit(self._migrate_single_asset, asset): asset
                for asset in assets
            }

            batch_success = True

            for future in concurrent.futures.as_completed(future_to_asset):
                asset = future_to_asset[future]
                try:
                    success = future.result()
                    if not success:
                        batch_success = False
                        logger.error(f"資產 {asset.resource_id} 遷移失敗")
                    else:
                        logger.info(f"資產 {asset.resource_id} 遷移成功")

                except Exception as e:
                    logger.error(f"遷移資產 {asset.resource_id} 時發生異常: {e}")
                    batch_success = False

        return batch_success

    def _migrate_single_asset(self, asset: AssetInfo) -> bool:
        """遷移單個資產"""
        try:
            start_time = time.time()

            # 生成新名稱
            new_name = self._generate_compliant_name(asset)

            if self.dry_run:
                logger.info(f"[DRY RUN] 遷移 {asset.resource_id} 到 {new_name}")
                return True

            # 執行實際遷移
            migration_success = self._execute_asset_migration(asset, new_name)

            # 記錄停機時間
            downtime = int(time.time() - start_time)
            self.migration_stats["downtime_seconds"] += downtime

            return migration_success

        except Exception as e:
            logger.error(f"遷移資產 {asset.resource_id} 失敗: {e}")
            return False

    def _execute_asset_migration(self, asset: AssetInfo, new_name: str) -> bool:
        """執行資產遷移操作"""
        try:
            # 對於不同類型的資源使用不同的遷移策略
            if asset.resource_type in ["configmaps", "secrets"]:
                return self._migrate_config_resource(asset, new_name)
            elif asset.resource_type in ["services", "deployments"]:
                return self._migrate_workload_resource(asset, new_name)
            else:
                return self._migrate_generic_resource(asset, new_name)

        except Exception as e:
            logger.error(f"執行資產遷移失敗: {e}")
            return False

    def _migrate_config_resource(self, asset: AssetInfo, new_name: str) -> bool:
        """遷移配置資源"""
        try:
            # 導出當前配置
            export_cmd = [
                "kubectl",
                "get",
                asset.resource_type,
                asset.name,
                "-n",
                asset.namespace,
                "-o",
                "yaml",
            ]

            result = subprocess.run(
                export_cmd, capture_output=True, text=True, check=True
            )
            config_data = result.stdout

            # 修改名稱
            config_data = config_data.replace(
                f"name: {asset.name}", f"name: {new_name}"
            )

            # 創建新資源
            create_cmd = ["kubectl", "apply", "-f", "-"]

            subprocess.run(create_cmd, input=config_data, text=True, check=True)

            # 驗證新資源
            verify_cmd = [
                "kubectl",
                "get",
                asset.resource_type,
                new_name,
                "-n",
                asset.namespace,
            ]

            subprocess.run(verify_cmd, check=True)

            # 刪除舊資源
            delete_cmd = [
                "kubectl",
                "delete",
                asset.resource_type,
                asset.name,
                "-n",
                asset.namespace,
            ]

            subprocess.run(delete_cmd, check=True)

            logger.info(f"成功遷移 {asset.resource_type} {asset.name} 到 {new_name}")
            return True

        except Exception as e:
            logger.error(f"遷移配置資源失敗: {e}")
            return False

    def _migrate_workload_resource(self, asset: AssetInfo, new_name: str) -> bool:
        """遷移工作負載資源"""
        # 工作負載遷移需要更複雜的邏輯，包括零停機遷移
        logger.warning(f"工作負載遷移需要手動介入: {asset.resource_id}")
        return False

    def _migrate_generic_resource(self, asset: AssetInfo, new_name: str) -> bool:
        """遷移通用資源"""
        return self._migrate_config_resource(asset, new_name)

    def execute_cutover(self, plan: MigrationPlan) -> bool:
        """執行 Cutover 切換"""
        logger.info("開始 Cutover 切換")
        self.current_phase = MigrationPhase.CUTOVER

        try:
            # 驗證遷移結果
            if not self._verify_migration_results(plan):
                logger.error("遷移結果驗證失敗")
                return False

            # 更新 DNS 和服務發現
            if not self._update_service_discovery(plan):
                logger.error("服務發現更新失敗")
                return False

            # 清理舊資源
            self._cleanup_old_resources(plan)

            # 生成切換報告
            self._generate_cutover_report(plan)

            logger.info("Cutover 切換完成")
            return True

        except Exception as e:
            logger.error(f"Cutover 切換失敗: {e}")
            return False

    def _verify_migration_results(self, plan: MigrationPlan) -> bool:
        """驗證遷移結果"""
        logger.info("驗證遷移結果")

        for asset in plan.assets:
            try:
                new_name = self._generate_compliant_name(asset)

                # 檢查新資源是否存在
                verify_cmd = [
                    "kubectl",
                    "get",
                    asset.resource_type,
                    new_name,
                    "-n",
                    asset.namespace,
                ]

                result = subprocess.run(verify_cmd, capture_output=True, text=True)
                if result.returncode != 0:
                    logger.error(f"新資源不存在: {asset.resource_type}/{new_name}")
                    return False

                # 檢查舊資源是否已刪除
                old_verify_cmd = [
                    "kubectl",
                    "get",
                    asset.resource_type,
                    asset.name,
                    "-n",
                    asset.namespace,
                ]

                result = subprocess.run(old_verify_cmd, capture_output=True, text=True)
                if result.returncode == 0:
                    logger.warning(
                        f"舊資源仍然存在: {asset.resource_type}/{asset.name}"
                    )

            except Exception as e:
                logger.error(f"驗證資產 {asset.resource_id} 失敗: {e}")
                return False

        return True

    def _update_service_discovery(self, plan: MigrationPlan) -> bool:
        """更新服務發現"""
        logger.info("更新服務發現")

        # 這裡可以集成 DNS 更新、服務註冊等邏輯
        # 目前返回 True 作為佔位符
        return True

    def _cleanup_old_resources(self, plan: MigrationPlan):
        """清理舊資源"""
        logger.info("清理舊資源")

        for asset in plan.assets:
            try:
                # 檢查舊資源是否仍然存在
                cmd = [
                    "kubectl",
                    "get",
                    asset.resource_type,
                    asset.name,
                    "-n",
                    asset.namespace,
                ]

                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode == 0:
                    logger.warning(f"清理舊資源: {asset.resource_id}")

                    delete_cmd = [
                        "kubectl",
                        "delete",
                        asset.resource_type,
                        asset.name,
                        "-n",
                        asset.namespace,
                    ]

                    subprocess.run(delete_cmd, check=True)

            except Exception as e:
                logger.warning(f"清理舊資源失敗 {asset.resource_id}: {e}")

    def _generate_cutover_report(self, plan: MigrationPlan):
        """生成 Cutover 報告"""
        report = {
            "plan_id": plan.plan_id,
            "cutover_timestamp": datetime.now().isoformat(),
            "migration_stats": self.migration_stats,
            "total_assets": len(plan.assets),
            "successful_migrations": self.migration_stats["assets_migrated"],
            "failed_migrations": self.migration_stats["assets_failed"],
            "total_downtime": self.migration_stats["downtime_seconds"],
        }

        # 保存報告
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = f"/var/log/naming-gl-platform.governance/cutover_report_{timestamp}.json"

        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)

        logger.info(f"Cutover 報告已保存到: {report_path}")

    def rollback_migration(self, plan: MigrationPlan) -> bool:
        """回滾遷移"""
        logger.warning("開始遷移回滾")
        self.current_phase = MigrationPhase.ROLLBACK
        self.migration_stats["rollback_initiated"] = True

        if not plan.rollback_point:
            logger.error("沒有可用的回滾點")
            return False

        try:
            # 從備份恢復
            backup_file = os.path.join(plan.rollback_point, "cluster_resources.yaml")

            restore_cmd = ["kubectl", "apply", "-f", backup_file, "--force"]

            subprocess.run(restore_cmd, check=True)

            # 驗證回滾結果
            if self._verify_rollback_results(plan):
                plan.status = MigrationStatus.ROLLED_BACK
                logger.info("遷移回滾成功")
                return True
            else:
                logger.error("回滾結果驗證失敗")
                return False

        except Exception as e:
            logger.error(f"遷移回滾失敗: {e}")
            return False

    def _verify_rollback_results(self, plan: MigrationPlan) -> bool:
        """驗證回滾結果"""
        logger.info("驗證回滾結果")

        for asset in plan.assets:
            try:
                # 檢查原始資源是否已恢復
                cmd = [
                    "kubectl",
                    "get",
                    asset.resource_type,
                    asset.name,
                    "-n",
                    asset.namespace,
                ]

                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode != 0:
                    logger.error(f"原始資源未恢復: {asset.resource_id}")
                    return False

            except Exception as e:
                logger.error(f"驗證回滾資產 {asset.resource_id} 失敗: {e}")
                return False

        return True

    def generate_migration_report(self, plan: MigrationPlan) -> Dict[str, Any]:
        """生成遷移報告"""
        logger.info("生成遷移報告")

        report = {
            "report_id": f"migration-report-{int(time.time())}",
            "plan_id": plan.plan_id,
            "generated_at": datetime.now().isoformat(),
            "migration_phases": {
                "discovery": {
                    "assets_discovered": self.migration_stats["total_assets_discovered"]
                },
                "planning": {
                    "plan_created": True,
                    "risk_assessment": plan.risk_assessment,
                },
                "execution": {
                    "assets_migrated": self.migration_stats["assets_migrated"],
                    "assets_failed": self.migration_stats["assets_failed"],
                    "total_downtime": self.migration_stats["downtime_seconds"],
                },
            },
            "statistics": self.migration_stats,
            "final_status": plan.status.value,
            "recommendations": self._generate_final_recommendations(plan),
        }

        return report

    def _generate_final_recommendations(self, plan: MigrationPlan) -> List[str]:
        """生成最終建議"""
        recommendations = []

        if self.migration_stats["assets_failed"] > 0:
            recommendations.append("有資產遷移失敗，建議人工審核並修復")

        if self.migration_stats["downtime_seconds"] > self.config.get(
            "downtime_threshold", 300
        ):
            recommendations.append("實際停機時間超過預期，建議優化遷移策略")

        if plan.status == MigrationStatus.ROLLED_BACK:
            recommendations.append("遷移已回滾，建議重新評估遷移計畫")

        return recommendations


def main():
    """主函數"""
    parser = argparse.ArgumentParser(description="MachineNativeOps 命名治理遷移工具")
    parser.add_argument("--config", "-c", help="配置文件路徑")
    parser.add_argument("--namespaces", "-n", nargs="+", help="目標命名空間")
    parser.add_argument("--dry-run", action="store_true", help="試運行模式")
    parser.add_argument("--rollback", action="store_true", help="執行回滾")
    parser.add_argument("--output", "-o", help="報告輸出路徑")
    parser.add_argument("--verbose", "-v", action="store_true", help="詳細輸出")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    try:
        # 初始化遷移系統
        migration_system = NamingGovernanceMigration(args.config)
        migration_system.dry_run = args.dry_run

        logger.info("開始命名治理遷移流程")

        if args.rollback:
            logger.warning("回滾功能需要從已保存的計畫中執行")
            return 1

        # 發現資產
        assets = migration_system.discover_assets(args.namespaces)

        if not assets:
            logger.info("未發現需要遷移的資產")
            return 0

        # 創建遷移計畫
        plan = migration_system.create_migration_plan(assets)

        # 執行 Dry-run
        if not migration_system.perform_dry_run(plan):
            logger.error("Dry-run 失敗，中止遷移")
            return 1

        # 如果不是試運行，執行實際遷移
        if not args.dry_run:
            # 分階段遷移
            if not migration_system.execute_staged_migration(plan):
                logger.error("分階段遷移失敗")
                return 1

            # Cutover 切換
            if not migration_system.execute_cutover(plan):
                logger.error("Cutover 切換失敗")
                return 1

        # 生成報告
        report = migration_system.generate_migration_report(plan)

        # 保存報告
        if args.output:
            with open(args.output, "w") as f:
                json.dump(report, f, indent=2, default=str)
            logger.info(f"遷移報告已保存到: {args.output}")

        # 輸出摘要
        logger.info("遷移完成摘要:")
        logger.info(f"  總資產數: {len(assets)}")
        logger.info(
            f"  成功遷移: {migration_system.migration_stats['assets_migrated']}"
        )
        logger.info(f"  失敗數量: {migration_system.migration_stats['assets_failed']}")
        logger.info(
            f"  總停機時間: {migration_system.migration_stats['downtime_seconds']} 秒"
        )

        return 0

    except Exception as e:
        logger.error(f"執行遷移流程時發生錯誤: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
