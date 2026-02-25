# 
# @ECO-governed
# @ECO-layer: data
# @ECO-semantic: validate-instant-execution
# @ECO-audit-trail: ../../engine/governance/GL_SEMANTIC_ANCHOR.json
#
# GL Unified Architecture Governance Framework Activated

#!/usr/bin/env python3
"""
Instant Execution Manifest Validator
即時執行清單驗證器
驗證專案是否符合 INSTANT-EXECUTION-MANIFEST.yaml 定義的標準
"""
# MNGA-002: Import organization needs review
import json
import sys
import time
from datetime import datetime
from pathlib import Path
import yaml
# 顏色輸出
class Colors:
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BLUE = "\033[94m"
    BOLD = "\033[1m"
    END = "\033[0m"
def print_success(msg: str):
    print(f"{Colors.GREEN}✅ {msg}{Colors.END}")
def print_warning(msg: str):
    print(f"{Colors.YELLOW}⚠️  {msg}{Colors.END}")
def print_error(msg: str):
    print(f"{Colors.RED}❌ {msg}{Colors.END}")
def print_info(msg: str):
    print(f"{Colors.BLUE}ℹ️  {msg}{Colors.END}")
def print_header(msg: str):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{msg}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}\n")
class InstantExecutionValidator:
    def __init__(self, manifest_path: str):
        self.manifest_path = Path(manifest_path)
        self.manifest = None
        self.results = {
            "total_checks": 0,
            "passed": 0,
            "failed": 0,
            "warnings": 0,
            "start_time": datetime.now().isoformat(),
            "end_time": None,
            "checks": [],
        }
    def load_manifest(self) -> bool:
        """載入 INSTANT-EXECUTION-MANIFEST.yaml"""
        print_info(f"載入執行清單: {self.manifest_path}")
        if not self.manifest_path.exists():
            print_error(f"執行清單不存在: {self.manifest_path}")
            return False
        try:
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                self.manifest = yaml.safe_load(f)
            print_success("執行清單載入成功")
            return True
        except Exception as e:
            print_error(f"載入執行清單失敗: {e}")
            return False
    def validate_structure(self) -> bool:
        """驗證清單結構"""
        print_header("驗證清單結構")
        required_sections = ["apiVersion", "kind", "metadata", "spec", "status"]
        all_passed = True
        for section in required_sections:
            if section in self.manifest:
                self.results["passed"] += 1
                print_success(f"必備區段存在: {section}")
            else:
                self.results["failed"] += 1
                print_error(f"必備區段缺失: {section}")
                all_passed = False
        # 驗證 kind
        if self.manifest.get("kind") == "InstantExecutionManifest":
            self.results["passed"] += 1
            print_success("正確的 kind: InstantExecutionManifest")
        else:
            self.results["failed"] += 1
            print_error(f"錯誤的 kind: {self.manifest.get('kind')}")
            all_passed = False
        self.results["total_checks"] += len(required_sections) + 1
        return all_passed
    def validate_latency_thresholds(self) -> bool:
        """驗證延遲閾值"""
        print_header("驗證延遲閾值")
        thresholds = (
            self.manifest.get("spec", {})
            .get("execution_standards", {})
            .get("latency_thresholds", {})
        )
        all_passed = True
        for task, threshold in thresholds.items():
            self.results["total_checks"] += 1
            # 驗證格式
            if not threshold.startswith("<="):
                self.results["failed"] += 1
                print_error(f"延遲閾值格式錯誤: {task} = {threshold}")
                all_passed = False
                continue
            # 驗證數值
            try:
                value_str = threshold[2:].replace("s", "").replace("m", "")
                value = float(value_str)
                # 檢查是否符合 INSTANT 標準
                if "m" in threshold and value > 3:
                    self.results["warnings"] += 1
                    print_warning(f"延遲閾值超過 3 分鐘: {task} = {threshold}")
                else:
                    self.results["passed"] += 1
                    print_success(f"延遲閾值符合標準: {task} = {threshold}")
            except ValueError:
                self.results["failed"] += 1
                print_error(f"延遲閾值數值無效: {task} = {threshold}")
                all_passed = False
        return all_passed
    def validate_parallelism(self) -> bool:
        """驗證並行度配置"""
        print_header("驗證並行度配置")
        parallelism = (
            self.manifest.get("spec", {})
            .get("execution_standards", {})
            .get("parallelism", {})
        )
        all_passed = True
        # 驗證最小代理數
        min_agents = parallelism.get("min_agents", 0)
        self.results["total_checks"] += 1
        if min_agents >= 64:
            self.results["passed"] += 1
            print_success(f"最小代理數符合標準: {min_agents} >= 64")
        else:
            self.results["failed"] += 1
            print_error(f"最小代理數低於標準: {min_agents} < 64")
            all_passed = False
        # 驗證推薦代理數
        recommended = parallelism.get("recommended_agents", 0)
        self.results["total_checks"] += 1
        if recommended >= 128:
            self.results["passed"] += 1
            print_success(f"推薦代理數符合標準: {recommended} >= 128")
        else:
            self.results["warnings"] += 1
            print_warning(f"推薦代理數低於最佳: {recommended} < 128")
        return all_passed
    def validate_autonomy(self) -> bool:
        """驗證自治度配置"""
        print_header("驗證自治度配置")
        autonomy = (
            self.manifest.get("spec", {})
            .get("execution_standards", {})
            .get("autonomy", {})
        )
        all_passed = True
        # 驗證自治層級
        level = autonomy.get("level")
        self.results["total_checks"] += 1
        if level == "full":
            self.results["passed"] += 1
            print_success(f"自治層級: {level}")
        else:
            self.results["failed"] += 1
            print_error(f"自治層級應為 'full': {level}")
            all_passed = False
        # 驗證人工介入閾值
        intervention = autonomy.get("human_intervention_threshold", 1)
        self.results["total_checks"] += 1
        if intervention == 0:
            self.results["passed"] += 1
            print_success(f"人工介入閾值: {intervention}")
        else:
            self.results["warnings"] += 1
            print_warning(f"人工介入閾值應為 0: {intervention}")
        # 驗證自動修復
        auto_rollback = autonomy.get("auto_rollback")
        self.results["total_checks"] += 1
        if auto_rollback:
            self.results["passed"] += 1
            print_success(f"自動回滾: {auto_rollback}")
        else:
            self.results["failed"] += 1
            print_error("應啟用自動回滾")
            all_passed = False
        return all_passed
    def validate_event_driven(self) -> bool:
        """驗證事件驅動架構"""
        print_header("驗證事件驅動架構")
        event_arch = self.manifest.get("spec", {}).get("event_driven_architecture", {})
        all_passed = True
        # 驗證觸發類型
        trigger_type = event_arch.get("trigger_type")
        self.results["total_checks"] += 1
        if trigger_type == "event-based":
            self.results["passed"] += 1
            print_success(f"觸發類型: {trigger_type}")
        else:
            self.results["failed"] += 1
            print_error(f"觸發類型應為 'event-based': {trigger_type}")
            all_passed = False
        # 驗證時間線獨立
        timeline_independence = event_arch.get("timeline_independence")
        self.results["total_checks"] += 1
        if timeline_independence:
            self.results["passed"] += 1
            print_success(f"時間線獨立: {timeline_independence}")
        else:
            self.results["failed"] += 1
            print_error("應啟用時間線獨立")
            all_passed = False
        # 驗證觸發器存在
        triggers = event_arch.get("triggers", [])
        self.results["total_checks"] += 1
        if len(triggers) > 0:
            self.results["passed"] += 1
            print_success(f"定義的觸發器數量: {len(triggers)}")
        else:
            self.results["failed"] += 1
            print_error("沒有定義任何觸發器")
            all_passed = False
        return all_passed
    def validate_responsible_agents(self) -> bool:
        """驗證責任代理人"""
        print_header("驗證責任代理人")
        agents = self.manifest.get("spec", {}).get("responsible_agents", [])
        all_passed = True
        if len(agents) == 0:
            self.results["total_checks"] += 1
            self.results["failed"] += 1
            print_error("沒有定義任何責任代理人")
            return False
        print_success(f"責任代理人數量: {len(agents)}")
        required_tasks = ["code-generation", "deployment", "monitoring"]
        self.results["total_checks"] += len(required_tasks)
        for task in required_tasks:
            task_found = any(agent.get("task") == task for agent in agents)
            if task_found:
                self.results["passed"] += 1
                print_success(f"必要任務的代理存在: {task}")
            else:
                self.results["warnings"] += 1
                print_warning(f"缺少任務代理: {task}")
        return all_passed
    def validate_pipelines(self) -> bool:
        """驗證即時執行流水線"""
        print_header("驗證即時執行流水線")
        pipelines = self.manifest.get("spec", {}).get("instant_pipelines", [])
        all_passed = True
        if len(pipelines) == 0:
            self.results["total_checks"] += 1
            self.results["failed"] += 1
            print_error("沒有定義任何流水線")
            return False
        print_success(f"定義的流水線數量: {len(pipelines)}")
        for pipeline in pipelines:
            name = pipeline.get("name", "unknown")
            stages = pipeline.get("stages", [])
            # 驗證階段數量
            if len(stages) > 0:
                self.results["passed"] += 1
                print_success(f"流水線 '{name}' 有 {len(stages)} 個階段")
            else:
                self.results["failed"] += 1
                print_error(f"流水線 '{name}' 沒有定義任何階段")
                all_passed = False
            # 驗證人工介入
            human_intervention = pipeline.get("human_intervention", True)
            if not human_intervention:
                self.results["passed"] += 1
                print_success(f"流水線 '{name}' 無需人工介入")
            else:
                self.results["warnings"] += 1
                print_warning(f"流水線 '{name}' 需要人工介入")
            # 驗證總延遲
            total_latency = pipeline.get("total_latency", "")
            if total_latency and "<=3m" in total_latency:
                self.results["passed"] += 1
                print_success(f"流水線 '{name}' 延遲符合標準: {total_latency}")
            else:
                self.results["warnings"] += 1
                print_warning(f"流水線 '{name}' 延遲超過標準: {total_latency}")
        return all_passed
    def validate_governance(self) -> bool:
        """驗證治理驗證配置"""
        print_header("驗證治理驗證配置")
        validators = self.manifest.get("spec", {}).get("governance_validation", [])
        all_passed = True
        required_validators = [
            "INSTANT_EXECUTION",
            "AUTONOMY_LEVEL",
            "LATENCY_COMPLIANCE",
        ]
        self.results["total_checks"] += len(required_validators)
        for validator_name in required_validators:
            validator_found = any(
                v.get("standard") == validator_name for v in validators
            )
            if validator_found:
                self.results["passed"] += 1
                print_success(f"必要驗證器存在: {validator_name}")
            else:
                self.results["failed"] += 1
                print_error(f"缺少驗證器: {validator_name}")
                all_passed = False
        return all_passed
    def validate_status(self) -> bool:
        """驗證狀態配置"""
        print_header("驗證狀態配置")
        status = self.manifest.get("status", {})
        all_passed = True
        # 驗證合規等級
        compliance = status.get("compliance_level")
        self.results["total_checks"] += 1
        if compliance == "FULLY_COMPLIANT":
            self.results["passed"] += 1
            print_success(f"合規等級: {compliance}")
        else:
            self.results["warnings"] += 1
            print_warning(f"合規等級: {compliance}")
        # 驗證即時模式
        execution = status.get("execution", {})
        instant_mode = execution.get("instant_mode")
        self.results["total_checks"] += 1
        if instant_mode:
            self.results["passed"] += 1
            print_success(f"即時模式: {instant_mode}")
        else:
            self.results["failed"] += 1
            print_error("應啟用即時模式")
            all_passed = False
        return all_passed
    def run_all_validations(self) -> bool:
        """執行所有驗證"""
        print_header("開始驗證 INSTANT-EXECUTION-MANIFEST.yaml")
        # 記錄開始時間
        start_time = time.time()
        # 載入清單
        if not self.load_manifest():
            return False
        # 執行各類驗證
        self.validate_structure()
        self.validate_latency_thresholds()
        self.validate_parallelism()
        self.validate_autonomy()
        self.validate_event_driven()
        self.validate_responsible_agents()
        self.validate_pipelines()
        self.validate_governance()
        self.validate_status()
        # 記錄結束時間
        self.results["end_time"] = datetime.now().isoformat()
        self.results["duration_seconds"] = time.time() - start_time
        # 輸出摘要
        self.print_summary()
        # 判斷是否通過
        return self.results["failed"] == 0
    def print_summary(self):
        """輸出驗證摘要"""
        print_header("驗證摘要")
        print(f"總檢查數: {self.results['total_checks']}")
        print(f"{Colors.GREEN}通過: {self.results['passed']}{Colors.END}")
        print(f"{Colors.YELLOW}警告: {self.results['warnings']}{Colors.END}")
        print(f"{Colors.RED}失敗: {self.results['failed']}{Colors.END}")
        print(f"執行時間: {self.results['duration_seconds']:.2f} 秒")
        # 計算通過率
        if self.results["total_checks"] > 0:
            pass_rate = (self.results["passed"] / self.results["total_checks"]) * 100
            print(f"通過率: {pass_rate:.1f}%")
        # 輸出結論
        if self.results["failed"] == 0:
            print(f"\n{Colors.GREEN}{Colors.BOLD}✅ 所有檢查通過！{Colors.END}")
            print(f"{Colors.GREEN}專案符合 INSTANT 執行標準{Colors.END}")
        else:
            print(
                f"\n{Colors.RED}{Colors.BOLD}❌ 有 {self.results['failed']} 項檢查失敗！{Colors.END}"
            )
            print(f"{Colors.RED}專案不符合 INSTANT 執行標準{Colors.END}")
    def generate_report(self, output_path: str = None):
        """生成驗證報告"""
        report = {
            "manifest_path": str(
                self.manifest_path),
            "validation_timestamp": datetime.now().isoformat(),
            "results": self.results,
            "summary": {
                "status": "PASSED" if self.results["failed"] == 0 else "FAILED",
                "pass_rate": f"{(self.results['passed'] / self.results['total_checks'] * 100):.1f}%",
            },
        }
        if output_path:
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            print_success(f"驗證報告已保存: {output_path}")
        return report
def main():
    import argparse
    parser = argparse.ArgumentParser(description="Instant Execution Manifest Validator")
    parser.add_argument(
        "--manifest",
        default="contracts/INSTANT-EXECUTION-MANIFEST.yaml",
        help="Path to the instant execution manifest file",
    )
    parser.add_argument(
        "--report", help="Path to save the validation report (JSON format)"
    )
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    args = parser.parse_args()
    # 創建驗證器
    validator = InstantExecutionValidator(args.manifest)
    # 執行驗證
    passed = validator.run_all_validations()
    # 生成報告
    if args.report:
        validator.generate_report(args.report)
    # 返回退出代碼
    sys.exit(0 if passed else 1)
if __name__ == "__main__":
    main()
