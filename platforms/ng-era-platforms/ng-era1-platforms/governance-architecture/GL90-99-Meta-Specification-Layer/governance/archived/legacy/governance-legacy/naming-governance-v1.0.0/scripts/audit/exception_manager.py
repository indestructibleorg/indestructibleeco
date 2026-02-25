# @ECO-governed
# @ECO-layer: GL90-99
# @ECO-semantic: legacy-scripts
# @ECO-audit-trail: ../../engine/gl-platform.governance/GL_SEMANTIC_ANCHOR.json
#
# GL Unified Architecture Governance Framework Activated
#!/usr/bin/env python3
"""
合規例外管理工具 - 例外申請、審核與到期管理
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
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import yaml


class ExceptionStatus(Enum):
    """例外狀態"""

    PENDING = "UnderReview"
    APPROVED = "Approved"
    REJECTED = "Rejected"
    EXPIRED = "Expired"
    REVOKED = "Revoked"


class RiskLevel(Enum):
    """風險等級"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ComplianceException:
    """合規例外"""

    id: str
    applicant: str
    exception_type: str
    justification: str
    risk_assessment: str
    expiry_date: str
    status: ExceptionStatus
    reviewer: Optional[str] = None
    reviewed_at: Optional[str] = None
    approval_notes: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    resources_affected: List[str] = field(default_factory=list)
    mitigation_measures: List[str] = field(default_factory=list)
    periodic_review_required: bool = True
    review_frequency_days: int = 30


class ExceptionManager:
    """例外管理器類別"""

    def __init__(
        self,
        spec_path: str = "config/machine-spec.yaml",
        exceptions_db: str = "exceptions-db.yaml",
    ):
        """初始化例外管理器"""
        self.spec_path = Path(spec_path)
        self.exceptions_db_path = Path(exceptions_db)
        self.spec = self._load_spec()
        self.exception_config = self.spec.get("compliance_exceptions", {})
        self.exceptions = self._load_exceptions_db()

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

    def _load_exceptions_db(self) -> List[Dict]:
        """載入例外資料庫"""
        if not self.exceptions_db_path.exists():
            return []

        try:
            with open(self.exceptions_db_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                return data.get("exceptions", [])
        except Exception as e:
            print(f"警告: 無法載入例外資料庫 - {e}")
            return []

    def _save_exceptions_db(self):
        """保存例外資料庫"""
        data = {
            "version": "v1.0.0",
            "last_updated": datetime.now().isoformat(),
            "exceptions": self.exceptions,
        }

        with open(self.exceptions_db_path, "w", encoding="utf-8") as f:
            yaml.dump(
                data, f, allow_unicode=True, default_flow_style=False, sort_keys=False
            )

    def validate_exception_request(
        self, exception: ComplianceException
    ) -> Tuple[bool, List[str]]:
        """驗證例外申請"""
        errors = []

        # 驗證必要欄位
        required_fields = [
            "applicant",
            "exception_type",
            "justification",
            "risk_assessment",
            "expiry_date",
        ]

        for field in required_fields:
            if not getattr(exception, field, None):
                errors.append(f"缺少必要欄位: {field}")

        # 驗證到期日期格式
        try:
            expiry = datetime.fromisoformat(exception.expiry_date)
            if expiry <= datetime.now():
                errors.append("到期日期必須在未來")
        except ValueError:
            errors.append("到期日期格式無效，應為 ISO 8601 格式")

        # 驗證風險評估
        if exception.risk_assessment.lower() not in [
            "low",
            "medium",
            "high",
            "critical",
        ]:
            errors.append("風險評估必須為: low, medium, high, 或 critical")

        # 驗證緩解措施
        if exception.periodic_review_required and not exception.mitigation_measures:
            errors.append("需要定期審查的例外必須提供緩解措施")

        return len(errors) == 0, errors

    def create_exception(self, exception: ComplianceException) -> bool:
        """創建新的例外申請"""
        is_valid, errors = self.validate_exception_request(exception)

        if not is_valid:
            print("❌ 例外申請驗證失敗:")
            for error in errors:
                print(f"   - {error}")
            return False

        # 添加到資料庫
        exception_dict = asdict(exception)
        exception_dict["status"] = exception.status.value
        self.exceptions.append(exception_dict)

        # 保存資料庫
        self._save_exceptions_db()

        print(f"✅ 例外申請已創建: {exception.id}")
        return True

    def approve_exception(
        self, exception_id: str, reviewer: str, notes: Optional[str] = None
    ) -> bool:
        """批准例外申請"""
        for exc in self.exceptions:
            if exc["id"] == exception_id:
                if exc["status"] != ExceptionStatus.PENDING.value:
                    print(f"錯誤: 例外 {exception_id} 已經是 {exc['status']} 狀態")
                    return False

                exc["status"] = ExceptionStatus.APPROVED.value
                exc["reviewer"] = reviewer
                exc["reviewed_at"] = datetime.now().isoformat()
                exc["approval_notes"] = notes

                self._save_exceptions_db()
                print(f"✅ 例外申請已批准: {exception_id}")
                return True

        print(f"錯誤: 找不到例外申請 {exception_id}")
        return False

    def reject_exception(self, exception_id: str, reviewer: str, reason: str) -> bool:
        """拒絕例外申請"""
        for exc in self.exceptions:
            if exc["id"] == exception_id:
                if exc["status"] != ExceptionStatus.PENDING.value:
                    print(f"錯誤: 例外 {exception_id} 已經是 {exc['status']} 狀態")
                    return False

                exc["status"] = ExceptionStatus.REJECTED.value
                exc["reviewer"] = reviewer
                exc["reviewed_at"] = datetime.now().isoformat()
                exc["approval_notes"] = reason

                self._save_exceptions_db()
                print(f"❌ 例外申請已拒絕: {exception_id}")
                return True

        print(f"錯誤: 找不到例外申請 {exception_id}")
        return False

    def check_expired_exceptions(self) -> List[Dict]:
        """檢查已到期的例外"""
        expired = []
        today = datetime.now()

        for exc in self.exceptions:
            if exc["status"] == ExceptionStatus.APPROVED.value:
                expiry = datetime.fromisoformat(exc["expiry_date"])
                if expiry < today:
                    exc["status"] = ExceptionStatus.EXPIRED.value
                    expired.append(exc)

        if expired:
            self._save_exceptions_db()

        return expired

    def revoke_exception(self, exception_id: str, reason: str) -> bool:
        """撤銷例外"""
        for exc in self.exceptions:
            if exc["id"] == exception_id:
                exc["status"] = ExceptionStatus.REVOKED.value
                exc["approval_notes"] = f"撤銷原因: {reason}"

                self._save_exceptions_db()
                print(f"⚠️  例外已撤銷: {exception_id}")
                return True

        print(f"錯誤: 找不到例外申請 {exception_id}")
        return False

    def generate_exception_report(self, status_filter: Optional[str] = None) -> Dict:
        """生成例外報告"""
        filtered_exceptions = self.exceptions

        if status_filter:
            filtered_exceptions = [
                exc for exc in self.exceptions if exc["status"] == status_filter
            ]

        report = {
            "generated_at": datetime.now().isoformat(),
            "total_exceptions": len(self.exceptions),
            "by_status": {
                "pending": len(
                    [
                        e
                        for e in self.exceptions
                        if e["status"] == ExceptionStatus.PENDING.value
                    ]
                ),
                "approved": len(
                    [
                        e
                        for e in self.exceptions
                        if e["status"] == ExceptionStatus.APPROVED.value
                    ]
                ),
                "rejected": len(
                    [
                        e
                        for e in self.exceptions
                        if e["status"] == ExceptionStatus.REJECTED.value
                    ]
                ),
                "expired": len(
                    [
                        e
                        for e in self.exceptions
                        if e["status"] == ExceptionStatus.EXPIRED.value
                    ]
                ),
                "revoked": len(
                    [
                        e
                        for e in self.exceptions
                        if e["status"] == ExceptionStatus.REVOKED.value
                    ]
                ),
            },
            "exceptions": filtered_exceptions,
        }

        return report

    def generate_exception_id(self) -> str:
        """生成例外 ID"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"EXC-{timestamp}"

    def export_exception_form(self, exception_id: str, format: str = "yaml") -> str:
        """匯出例外申請表單"""
        for exc in self.exceptions:
            if exc["id"] == exception_id:
                if format == "yaml":
                    return yaml.dump(
                        exc,
                        allow_unicode=True,
                        default_flow_style=False,
                        sort_keys=False,
                    )
                elif format == "json":
                    return json.dumps(exc, indent=2, ensure_ascii=False)

        return ""


def main():
    """主函數"""
    parser = argparse.ArgumentParser(description="合規例外管理工具 v1.0.0")
    parser.add_argument(
        "--spec", default="config/machine-spec.yaml", help="命名規範文件路徑"
    )
    parser.add_argument("--db", default="exceptions-db.yaml", help="例外資料庫文件路徑")

    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # 創建例外申請
    create_parser = subparsers.add_parser("create", help="創建新的例外申請")
    create_parser.add_argument("--applicant", required=True, help="申請人")
    create_parser.add_argument("--type", required=True, help="例外類型")
    create_parser.add_argument("--justification", required=True, help="申請理由")
    create_parser.add_argument(
        "--risk",
        required=True,
        choices=["low", "medium", "high", "critical"],
        help="風險評估",
    )
    create_parser.add_argument("--expiry", required=True, help="到期日期 (YYYY-MM-DD)")
    create_parser.add_argument("--resources", nargs="+", help="受影響的資源")
    create_parser.add_argument("--mitigation", nargs="+", help="緩解措施")

    # 批准例外
    approve_parser = subparsers.add_parser("approve", help="批准例外申請")
    approve_parser.add_argument("--id", required=True, help="例外 ID")
    approve_parser.add_argument("--reviewer", required=True, help="審核人")
    approve_parser.add_argument("--notes", help="審核備註")

    # 拒絕例外
    reject_parser = subparsers.add_parser("reject", help="拒絕例外申請")
    reject_parser.add_argument("--id", required=True, help="例外 ID")
    reject_parser.add_argument("--reviewer", required=True, help="審核人")
    reject_parser.add_argument("--reason", required=True, help="拒絕原因")

    # 檢查到期例外
    subparsers.add_parser("check-expired", help="檢查已到期的例外")

    # 撤銷例外
    revoke_parser = subparsers.add_parser("revoke", help="撤銷例外")
    revoke_parser.add_argument("--id", required=True, help="例外 ID")
    revoke_parser.add_argument("--reason", required=True, help="撤銷原因")

    # 生成報告
    report_parser = subparsers.add_parser("report", help="生成例外報告")
    report_parser.add_argument("--status", help="按狀態過濾")
    report_parser.add_argument("--output", help="輸出文件路徑")
    report_parser.add_argument(
        "--format", choices=["yaml", "json"], default="yaml", help="輸出格式"
    )

    # 列出所有例外
    list_parser = subparsers.add_parser("list", help="列出所有例外")
    list_parser.add_argument("--status", help="按狀態過濾")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # 初始化例外管理器
    manager = ExceptionManager(args.spec, args.db)

    if args.command == "create":
        # 創建例外申請
        exception = ComplianceException(
            id=manager.generate_exception_id(),
            applicant=args.applicant,
            exception_type=args.type,
            justification=args.justification,
            risk_assessment=args.risk,
            expiry_date=args.expiry,
            status=ExceptionStatus.PENDING,
            resources_affected=args.resources or [],
            mitigation_measures=args.mitigation or [],
        )

        manager.create_exception(exception)

    elif args.command == "approve":
        # 批准例外
        manager.approve_exception(args.id, args.reviewer, args.notes)

    elif args.command == "reject":
        # 拒絕例外
        manager.reject_exception(args.id, args.reviewer, args.reason)

    elif args.command == "check-expired":
        # 檢查到期例外
        expired = manager.check_expired_exceptions()

        if expired:
            print(f"⚠️  發現 {len(expired)} 個已到期的例外:")
            for exc in expired:
                print(f"   - {exc['id']}: {exc['exception_type']}")
        else:
            print("✅ 沒有到期的例外")

    elif args.command == "revoke":
        # 撤銷例外
        manager.revoke_exception(args.id, args.reason)

    elif args.command == "report":
        # 生成報告
        report = manager.generate_exception_report(args.status)

        if args.format == "yaml":
            output = yaml.dump(report, allow_unicode=True, default_flow_style=False)
        else:
            output = json.dumps(report, indent=2, ensure_ascii=False)

        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(output)
            print(f"報告已生成至: {args.output}")
        else:
            print(output)

    elif args.command == "list":
        # 列出例外
        filtered = manager.exceptions
        if args.status:
            filtered = [exc for exc in filtered if exc["status"] == args.status]

        print(f"\n共 {len(filtered)} 個例外申請:\n")

        for exc in filtered:
            status_emoji = {
                "UnderReview": "⏳",
                "Approved": "✅",
                "Rejected": "❌",
                "Expired": "⏰",
                "Revoked": "🚫",
            }.get(exc["status"], "❓")

            print(f"{status_emoji} {exc['id']}")
            print(f"   類型: {exc['exception_type']}")
            print(f"   申請人: {exc['applicant']}")
            print(f"   狀態: {exc['status']}")
            print(f"   到期: {exc['expiry_date']}")
            print(f"   風險: {exc['risk_assessment']}")
            print()


if __name__ == "__main__":
    main()
