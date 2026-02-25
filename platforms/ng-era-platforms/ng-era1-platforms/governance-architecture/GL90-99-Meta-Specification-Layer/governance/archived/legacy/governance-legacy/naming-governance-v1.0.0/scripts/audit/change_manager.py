# @ECO-governed
# @ECO-layer: GL90-99
# @ECO-semantic: legacy-scripts
# @ECO-audit-trail: ../../engine/gl-platform.governance/GL_SEMANTIC_ANCHOR.json
#
# GL Unified Architecture Governance Framework Activated
#!/usr/bin/env python3
"""
變更管理工具 - RFC 變更請求生成與管理
版本: v1.0.0
"""

"""
Module docstring
================

This module is part of the GL governance framework.
Please add specific module documentation here.
"""
import argparse
import sys
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import yaml


class ChangeType(Enum):
    """變更類型"""

    STANDARD = "standard"
    NORMAL = "normal"
    EMERGENCY = "emergency"


class RiskLevel(Enum):
    """風險等級"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class ImpactAssessment:
    """影響評估"""

    services_affected: List[str] = field(default_factory=list)
    downtime_expected: str = "0 min"
    data_migration_required: bool = False
    rollback_complexity: str = "low"
    user_impact: str = "none"


@dataclass
class ChangeRequest:
    """變更請求"""

    id: str
    title: str
    type: ChangeType
    requester: str
    risk_level: RiskLevel
    impact_assessment: ImpactAssessment
    implementation_plan: List[str] = field(default_factory=list)
    rollback_plan: List[str] = field(default_factory=list)
    approval_method: str = "CAB"
    status: str = "Pending"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    approved_by: Optional[str] = None
    approved_at: Optional[str] = None
    metrics: Dict = field(default_factory=dict)


class ChangeManager:
    """變更管理器類別"""

    def __init__(self, spec_path: str = "config/machine-spec.yaml"):
        """初始化變更管理器"""
        self.spec_path = Path(spec_path)
        self.spec = self._load_spec()
        self.change_config = self.spec.get("change_management", {})

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

    def validate_change_type(
        self, change_type: ChangeType, risk_level: RiskLevel
    ) -> bool:
        """驗證變更類型與風險等級的匹配性"""
        type_config = self.change_config.get("types", [])

        for type_def in type_config:
            if type_def["name"] == change_type.value:
                expected_risk = type_def.get("risk_level", "")
                if expected_risk != risk_level.value:
                    print(
                        f"警告: {change_type.value} 變更通常風險等級為 {expected_risk}，但指定為 {risk_level.value}"
                    )
                return True

        return False

    def generate_rfc(self, change_request: ChangeRequest) -> str:
        """生成 RFC 變更請求文檔"""
        # 轉換為字典
        rfc_dict = {
            "change_request": {
                "id": change_request.id,
                "title": change_request.title,
                "type": change_request.type.value,
                "requester": change_request.requester,
                "risk_level": change_request.risk_level.value,
                "status": change_request.status,
                "created_at": change_request.created_at,
                "approval": {
                    "method": change_request.approval_method,
                    "status": change_request.status,
                    "approved_by": change_request.approved_by,
                    "approved_at": change_request.approved_at,
                },
                "impact_assessment": {
                    "services_affected": change_request.impact_assessment.services_affected,
                    "downtime_expected": change_request.impact_assessment.downtime_expected,
                    "data_migration_required": change_request.impact_assessment.data_migration_required,
                    "rollback_complexity": change_request.impact_assessment.rollback_complexity,
                    "user_impact": change_request.impact_assessment.user_impact,
                },
                "implementation_plan": {
                    "steps": change_request.implementation_plan},
                "rollback_plan": {
                    "steps": change_request.rollback_plan},
                "metrics": change_request.metrics,
            }}

        return yaml.dump(
            rfc_dict, allow_unicode=True, default_flow_style=False, sort_keys=False
        )

    def load_rfc(self, rfc_path: str) -> Optional[ChangeRequest]:
        """載入 RFC 變更請求文檔"""
        try:
            with open(rfc_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            cr_data = data.get("change_request", {})
            impact_data = cr_data.get("impact_assessment", {})

            change_request = ChangeRequest(
                id=cr_data.get("id", ""),
                title=cr_data.get("title", ""),
                type=ChangeType(cr_data.get("type", "normal")),
                requester=cr_data.get("requester", ""),
                risk_level=RiskLevel(cr_data.get("risk_level", "medium")),
                impact_assessment=ImpactAssessment(
                    services_affected=impact_data.get("services_affected", []),
                    downtime_expected=impact_data.get("downtime_expected", "0 min"),
                    data_migration_required=impact_data.get(
                        "data_migration_required", False
                    ),
                    rollback_complexity=impact_data.get("rollback_complexity", "low"),
                    user_impact=impact_data.get("user_impact", "none"),
                ),
                implementation_plan=cr_data.get("implementation_plan", {}).get(
                    "steps", []
                ),
                rollback_plan=cr_data.get("rollback_plan", {}).get("steps", []),
                approval_method=cr_data.get("approval", {}).get("method", "CAB"),
                status=cr_data.get("status", "Pending"),
                created_at=cr_data.get("created_at", datetime.now().isoformat()),
                approved_by=cr_data.get("approval", {}).get("approved_by"),
                approved_at=cr_data.get("approval", {}).get("approved_at"),
                metrics=cr_data.get("metrics", {}),
            )

            return change_request

        except Exception as e:
            print(f"錯誤: 無法載入 RFC - {e}")
            return None

    def approve_change(
        self, change_request: ChangeRequest, approver: str
    ) -> ChangeRequest:
        """批准變更請求"""
        change_request.status = "Approved"
        change_request.approved_by = approver
        change_request.approved_at = datetime.now().isoformat()

        return change_request

    def reject_change(
        self, change_request: ChangeRequest, reason: str
    ) -> ChangeRequest:
        """拒絕變更請求"""
        change_request.status = "Rejected"
        change_request.metrics["rejection_reason"] = reason

        return change_request

    def generate_change_id(self, prefix: str = "CHG") -> str:
        """生成變更請求 ID"""
        year = datetime.now().year
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"{prefix}-{year}-{timestamp}"

    def validate_rfc(self, rfc_path: str) -> Tuple[bool, List[str]]:
        """驗證 RFC 變更請求"""
        errors = []

        change_request = self.load_rfc(rfc_path)
        if not change_request:
            errors.append("無法載入 RFC 文檔")
            return False, errors

        # 驗證必要欄位
        required_fields = ["id", "title", "type", "requester", "risk_level"]
        for field in required_fields:
            if not getattr(change_request, field, None):
                errors.append(f"缺少必要欄位: {field}")

        # 驗證變更類型與風險等級
        if not self.validate_change_type(
            change_request.type, change_request.risk_level
        ):
            errors.append("變更類型與風險等級不匹配")

        # 驗證實施計畫
        if not change_request.implementation_plan:
            errors.append("缺少實施計畫")

        # 驗證回滾計畫
        if not change_request.rollback_plan:
            errors.append("缺少回滾計畫")

        # 驗證影響評估
        if not change_request.impact_assessment.services_affected:
            errors.append("缺少受影響的服務列表")

        return len(errors) == 0, errors


def main():
    """主函數"""
    parser = argparse.ArgumentParser(description="變更管理工具 v1.0.0")
    parser.add_argument(
        "--spec", default="config/machine-spec.yaml", help="命名規範文件路徑"
    )

    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # 創建 RFC 子命令
    create_parser = subparsers.add_parser("create", help="創建新的變更請求")
    create_parser.add_argument("--title", required=True, help="變更標題")
    create_parser.add_argument(
        "--type",
        required=True,
        choices=["standard", "normal", "emergency"],
        help="變更類型",
    )
    create_parser.add_argument("--requester", required=True, help="請求人")
    create_parser.add_argument(
        "--risk", required=True, choices=["low", "medium", "high"], help="風險等級"
    )
    create_parser.add_argument("--output", required=True, help="輸出文件路徑")

    # 驗證 RFC 子命令
    validate_parser = subparsers.add_parser("validate", help="驗證變更請求")
    validate_parser.add_argument("--rfc", required=True, help="RFC 文件路徑")

    # 批准變更子命令
    approve_parser = subparsers.add_parser("approve", help="批准變更請求")
    approve_parser.add_argument("--rfc", required=True, help="RFC 文件路徑")
    approve_parser.add_argument("--approver", required=True, help="批准人")
    approve_parser.add_argument("--output", help="輸出更新後的 RFC 文件路徑")

    # 顯示 RFC 子命令
    show_parser = subparsers.add_parser("show", help="顯示變更請求")
    show_parser.add_argument("--rfc", required=True, help="RFC 文件路徑")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # 初始化變更管理器
    manager = ChangeManager(args.spec)

    if args.command == "create":
        # 創建新的變更請求
        change_request = ChangeRequest(
            id=manager.generate_change_id(),
            title=args.title,
            type=ChangeType(args.type),
            requester=args.requester,
            risk_level=RiskLevel(args.risk),
            impact_assessment=ImpactAssessment(),
            implementation_plan=["備份現有資料", "部署新版本", "執行測試驗證"],
            rollback_plan=["回復備份資料", "通知相關團隊", "發布事故報告"],
            metrics={
                "kpi": ["deployment_success_rate", "incident_count"],
                "audit": {"log_enabled": True, "reviewer": "it-ops"},
            },
        )

        # 生成 RFC 文檔
        rfc_content = manager.generate_rfc(change_request)

        # 保存到文件
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(rfc_content)

        print(f"✅ RFC 變更請求已創建: {args.output}")
        print(f"   變更 ID: {change_request.id}")

    elif args.command == "validate":
        # 驗證 RFC
        is_valid, errors = manager.validate_rfc(args.rfc)

        if is_valid:
            print("✅ RFC 驗證通過")
        else:
            print("❌ RFC 驗證失敗:")
            for error in errors:
                print(f"   - {error}")
            sys.exit(1)

    elif args.command == "approve":
        # 批准變更請求
        change_request = manager.load_rfc(args.rfc)
        if not change_request:
            print("錯誤: 無法載入 RFC")
            sys.exit(1)

        approved_request = manager.approve_change(change_request, args.approver)
        rfc_content = manager.generate_rfc(approved_request)

        # 保存更新後的 RFC
        output_path = args.output or args.rfc
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(rfc_content)

        print(f"✅ 變更請求已批准: {approved_request.id}")
        print(f"   批准人: {args.approver}")
        print(f"   批准時間: {approved_request.approved_at}")

    elif args.command == "show":
        # 顯示 RFC 詳情
        change_request = manager.load_rfc(args.rfc)
        if not change_request:
            print("錯誤: 無法載入 RFC")
            sys.exit(1)

        rfc_content = manager.generate_rfc(change_request)
        print(rfc_content)


if __name__ == "__main__":
    main()
