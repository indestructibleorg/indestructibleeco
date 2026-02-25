# 
# @ECO-governed
# @ECO-layer: data
# @ECO-semantic: validate-instant-manifest
# @ECO-audit-trail: ../../engine/gov-platform.governance/GL_SEMANTIC_ANCHOR.json
#
# GL Unified Architecture Governance Framework Activated

#!/usr/bin/env python3
"""
INSTANT Execution Manifest Validator
驗證 INSTANT-EXECUTION-MANIFEST.yaml 是否符合所有標準：
- 延遲閾值驗證
- 事件觸發驗證
- 並行度驗證
- 自治度驗證
- 二元狀態驗證
"""
import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import List
import yaml
class ValidationStatus(Enum):
    PASSED = "✅ PASSED"
    FAILED = "❌ FAILED"
    WARNING = "⚠️  WARNING"
@dataclass
class ValidationResult:
    status: ValidationStatus
    message: str
    details: List[str] = None
    def __post_init__(self):
        if self.details is None:
            self.details = []
class InstantManifestValidator:
    """INSTANT Manifest 驗證器"""
    def __init__(self, manifest_path: str):
        self.manifest_path = Path(manifest_path)
        self.manifest = None
        self.results: List[ValidationResult] = []
    def load_manifest(self) -> bool:
        """載入 manifest 檔案"""
        try:
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                self.manifest = yaml.safe_load(f)
            return True
        except Exception as e:
            self.results.append(
                ValidationResult(ValidationStatus.FAILED, f"無法載入 manifest: {e}")
            )
            return False
    def validate_latency_tiers(self) -> ValidationResult:
        """驗證延遲分層標準"""
        if "latency_tiers" not in self.manifest:
            return ValidationResult(ValidationStatus.FAILED, "缺少 latency_tiers 定義")
        tiers = self.manifest["latency_tiers"]
        required_tiers = {
            "tier_1_instant_decision": "<100ms",
            "tier_2_instant_execution": "<500ms",
            "tier_3_full_stack": "<5s",
        }
        details = []
        all_passed = True
        for tier_name, expected_threshold in required_tiers.items():
            if tier_name not in tiers:
                details.append(f"❌ 缺少 {tier_name}")
                all_passed = False
                continue
            tier = tiers[tier_name]
            actual_threshold = tier.get("threshold", "")
            if actual_threshold != expected_threshold:
                details.append(
                    f"❌ {tier_name}: 期望 {expected_threshold}, 實際 {actual_threshold}"
                )
                all_passed = False
            else:
                details.append(f"✅ {tier_name}: {actual_threshold}")
        return ValidationResult(
            ValidationStatus.PASSED if all_passed else ValidationStatus.FAILED,
            "延遲分層驗證",
            details,
        )
    def validate_event_system(self) -> ValidationResult:
        """驗證事件驅動系統"""
        if "event_system" not in self.manifest:
            return ValidationResult(ValidationStatus.FAILED, "缺少 event_system 定義")
        event_system = self.manifest["event_system"]
        details = []
        all_passed = True
        # 驗證事件類型
        if "event_types" not in event_system:
            details.append("❌ 缺少 event_types")
            all_passed = False
        else:
            event_types = event_system["event_types"]
            required_events = [
                "schema_change",
                "artifact_update",
                "dependency_shift",
                "gov-platform.governance_violation",
                "deployment_request",
            ]
            for event in required_events:
                if event in event_types:
                    details.append(f"✅ 事件類型: {event}")
                else:
                    details.append(f"❌ 缺少事件類型: {event}")
                    all_passed = False
        # 驗證事件閉環
        if "event_loop" not in event_system:
            details.append("❌ 缺少 event_loop")
            all_passed = False
        else:
            event_loop = event_system["event_loop"]
            if "steps" not in event_loop:
                details.append("❌ 缺少 event_loop.steps")
                all_passed = False
            else:
                steps = event_loop["steps"]
                if len(steps) < 9:
                    details.append(f"❌ event_loop.steps 數量不足: {len(steps)} < 9")
                    all_passed = False
                else:
                    details.append(f"✅ event_loop.steps: {len(steps)} 步驟")
            if "loop_type" not in event_loop or event_loop["loop_type"] != "CONTINUOUS":
                details.append("❌ loop_type 必須為 CONTINUOUS")
                all_passed = False
            else:
                details.append("✅ loop_type: CONTINUOUS")
        return ValidationResult(
            ValidationStatus.PASSED if all_passed else ValidationStatus.FAILED,
            "事件驅動系統驗證",
            details,
        )
    def validate_agent_parallelism(self) -> ValidationResult:
        """驗證代理並行度"""
        if "agent_system" not in self.manifest:
            return ValidationResult(ValidationStatus.FAILED, "缺少 agent_system 定義")
        agent_system = self.manifest["agent_system"]
        details = []
        all_passed = True
        if "parallelism" not in agent_system:
            details.append("❌ 缺少 parallelism 定義")
            all_passed = False
        else:
            parallelism = agent_system["parallelism"]
            min_agents = parallelism.get("min_agents", 0)
            max_agents = parallelism.get("max_agents", 0)
            if min_agents < 64:
                details.append(f"❌ min_agents 必須 >= 64, 實際: {min_agents}")
                all_passed = False
            else:
                details.append(f"✅ min_agents: {min_agents}")
            if max_agents > 256:
                details.append(f"❌ max_agents 必須 <= 256, 實際: {max_agents}")
                all_passed = False
            else:
                details.append(f"✅ max_agents: {max_agents}")
            if min_agents > max_agents:
                details.append(
                    f"❌ min_agents ({min_agents}) > max_agents ({max_agents})"
                )
                all_passed = False
        # 驗證代理類型
        if "agent_types" not in agent_system:
            details.append("❌ 缺少 agent_types 定義")
            all_passed = False
        else:
            agent_types = agent_system["agent_types"]
            required_types = [
                "architect_agents",
                "executor_agents",
                "validator_agents",
                "fixer_agents",
                "observer_agents",
            ]
            for agent_type in required_types:
                if agent_type in agent_types:
                    details.append(f"✅ 代理類型: {agent_type}")
                else:
                    details.append(f"❌ 缺少代理類型: {agent_type}")
                    all_passed = False
        return ValidationResult(
            ValidationStatus.PASSED if all_passed else ValidationStatus.FAILED,
            "代理並行度驗證",
            details,
        )
    def validate_autonomy(self) -> ValidationResult:
        """驗證自治度"""
        details = []
        all_passed = True
        # 驗證 metadata commitments
        if "metadata" in self.manifest and "commitments" in self.manifest["metadata"]:
            commitments = self.manifest["metadata"]["commitments"]
            human_intervention = commitments.get("human_intervention", -1)
            if human_intervention != 0:
                details.append(
                    f"❌ human_intervention 必須為 0, 實際: {human_intervention}"
                )
                all_passed = False
            else:
                details.append("✅ human_intervention: 0")
        else:
            details.append("❌ 缺少 metadata.commitments")
            all_passed = False
        # 驗證 gov-platform.governance
        if "gov-platform.governance" in self.manifest:
            gov-platform.governance = self.manifest["gov-platform.governance"]
            if "responsibility_matrix" in gov-platform.governance:
                matrix = gov-platform.governance["responsibility_matrix"]
                if "ai_100_percent" in matrix:
                    ai_scope = matrix["ai_100_percent"].get("scope", [])
                    expected_scope = [
                        "operational",
                        "automation",
                        "execution",
                        "monitoring",
                        "recovery",
                    ]
                    if set(expected_scope).issubset(set(ai_scope)):
                        details.append(f"✅ AI 100% 自治範圍: {', '.join(ai_scope)}")
                    else:
                        details.append("❌ AI 自治範圍不完整")
                        all_passed = False
                else:
                    details.append("❌ 缺少 ai_100_percent 定義")
                    all_passed = False
            else:
                details.append("❌ 缺少 responsibility_matrix")
                all_passed = False
        else:
            details.append("❌ 缺少 gov-platform.governance 定義")
            all_passed = False
        return ValidationResult(
            ValidationStatus.PASSED if all_passed else ValidationStatus.FAILED,
            "自治度驗證",
            details,
        )
    def validate_binary_state(self) -> ValidationResult:
        """驗證二元狀態系統"""
        if "state_system" not in self.manifest:
            return ValidationResult(ValidationStatus.FAILED, "缺少 state_system 定義")
        state_system = self.manifest["state_system"]
        details = []
        all_passed = True
        if "primary_states" not in state_system:
            details.append("❌ 缺少 primary_states")
            all_passed = False
        else:
            primary_states = state_system["primary_states"]
            # 驗證 realized 狀態
            if "realized" in primary_states:
                details.append("✅ realized 狀態已定義")
            else:
                details.append("❌ 缺少 realized 狀態")
                all_passed = False
            # 驗證 unrealized 狀態及子狀態
            if "unrealized" in primary_states:
                unrealized = primary_states["unrealized"]
                if "sub_states" in unrealized:
                    sub_states = unrealized["sub_states"]
                    required_sub_states = [
                        "blocked",
                        "invalid",
                        "failed",
                        "unrealizable",
                    ]
                    for sub_state in required_sub_states:
                        if sub_state in sub_states:
                            details.append(f"✅ unrealized.{sub_state} 已定義")
                        else:
                            details.append(f"❌ 缺少 unrealized.{sub_state}")
                            all_passed = False
                else:
                    details.append("❌ 缺少 unrealized.sub_states")
                    all_passed = False
            else:
                details.append("❌ 缺少 unrealized 狀態")
                all_passed = False
        # 驗證狀態轉換
        if "state_transitions" not in state_system:
            details.append("❌ 缺少 state_transitions")
            all_passed = False
        else:
            transitions = state_system["state_transitions"]
            if len(transitions) < 4:
                details.append(f"❌ state_transitions 數量不足: {len(transitions)} < 4")
                all_passed = False
            else:
                details.append(f"✅ state_transitions: {len(transitions)} 個轉換")
        return ValidationResult(
            ValidationStatus.PASSED if all_passed else ValidationStatus.FAILED,
            "二元狀態系統驗證",
            details,
        )
    def validate_execution_time(self) -> ValidationResult:
        """驗證執行時間承諾"""
        details = []
        all_passed = True
        if "metadata" in self.manifest and "commitments" in self.manifest["metadata"]:
            commitments = self.manifest["metadata"]["commitments"]
            stack_time = commitments.get("stack_completion_time", "")
            if stack_time != "<3min":
                details.append(
                    f"❌ stack_completion_time 必須為 <3min, 實際: {stack_time}"
                )
                all_passed = False
            else:
                details.append("✅ stack_completion_time: <3min")
        else:
            details.append("❌ 缺少執行時間承諾")
            all_passed = False
        # 驗證 pipeline 總時間
        if "pipeline" in self.manifest:
            pipeline = self.manifest["pipeline"]
            total_time = pipeline.get("total_pipeline_time", "")
            if not total_time.startswith("<") or not total_time.endswith("s"):
                details.append(f"❌ total_pipeline_time 格式錯誤: {total_time}")
                all_passed = False
            else:
                details.append(f"✅ total_pipeline_time: {total_time}")
        return ValidationResult(
            ValidationStatus.PASSED if all_passed else ValidationStatus.FAILED,
            "執行時間驗證",
            details,
        )
    def validate_closed_loop_pipeline(self) -> ValidationResult:
        """驗證閉環流水線"""
        if "pipeline" not in self.manifest:
            return ValidationResult(ValidationStatus.FAILED, "缺少 pipeline 定義")
        pipeline = self.manifest["pipeline"]
        details = []
        all_passed = True
        # 驗證 pipeline 類型
        if pipeline.get("type") != "CLOSED_LOOP":
            details.append("❌ pipeline.type 必須為 CLOSED_LOOP")
            all_passed = False
        else:
            details.append("✅ pipeline.type: CLOSED_LOOP")
        # 驗證 pipeline 模式
        if pipeline.get("mode") != "CONTINUOUS":
            details.append("❌ pipeline.mode 必須為 CONTINUOUS")
            all_passed = False
        else:
            details.append("✅ pipeline.mode: CONTINUOUS")
        # 驗證 stages
        if "stages" not in pipeline:
            details.append("❌ 缺少 pipeline.stages")
            all_passed = False
        else:
            stages = pipeline["stages"]
            required_stages = [
                "stage_1_trigger",
                "stage_2_classify",
                "stage_3_decide",
                "stage_4_parallel_execute",
                "stage_5_validate",
                "stage_6_auto_fix",
                "stage_7_deliver",
                "stage_8_observe",
                "stage_9_feedback",
            ]
            for stage_name in required_stages:
                if stage_name in stages:
                    details.append(f"✅ {stage_name}")
                else:
                    details.append(f"❌ 缺少 {stage_name}")
                    all_passed = False
        return ValidationResult(
            ValidationStatus.PASSED if all_passed else ValidationStatus.FAILED,
            "閉環流水線驗證",
            details,
        )
    def validate_commercial_value(self) -> ValidationResult:
        """驗證商業價值指標"""
        if "commercial_value" not in self.manifest:
            return ValidationResult(
                ValidationStatus.FAILED, "缺少 commercial_value 定義"
            )
        commercial_value = self.manifest["commercial_value"]
        details = []
        all_passed = True
        # 驗證競爭優勢
        if "competitive_advantage" in commercial_value:
            advantage = commercial_value["competitive_advantage"]
            required_advantages = [
                "instant_delivery",
                "zero_waiting",
                "full_automation",
            ]
            for adv in required_advantages:
                if adv in advantage:
                    status = advantage[adv].get("status", "UNKNOWN")
                    if status == "ACHIEVED":
                        details.append(f"✅ {adv}: ACHIEVED")
                    else:
                        details.append(f"⚠️  {adv}: {status}")
                else:
                    details.append(f"❌ 缺少 {adv}")
                    all_passed = False
        else:
            details.append("❌ 缺少 competitive_advantage")
            all_passed = False
        return ValidationResult(
            ValidationStatus.PASSED if all_passed else ValidationStatus.FAILED,
            "商業價值驗證",
            details,
        )
    def run_all_validations(self) -> bool:
        """執行所有驗證"""
        if not self.load_manifest():
            return False
        # 執行各項驗證
        validations = [
            self.validate_latency_tiers,
            self.validate_event_system,
            self.validate_agent_parallelism,
            self.validate_autonomy,
            self.validate_binary_state,
            self.validate_execution_time,
            self.validate_closed_loop_pipeline,
            self.validate_commercial_value,
        ]
        for validation in validations:
            result = validation()
            self.results.append(result)
        return all(r.status == ValidationStatus.PASSED for r in self.results)
    def print_report(self):
        """列印驗證報告"""
        print("\n" + "=" * 80)
        print("INSTANT EXECUTION MANIFEST 驗證報告")
        print("=" * 80 + "\n")
        passed = sum(1 for r in self.results if r.status == ValidationStatus.PASSED)
        failed = sum(1 for r in self.results if r.status == ValidationStatus.FAILED)
        warnings = sum(1 for r in self.results if r.status == ValidationStatus.WARNING)
        for result in self.results:
            print(f"\n{result.status.value} {result.message}")
            if result.details:
                for detail in result.details:
                    print(f"  {detail}")
        print("\n" + "=" * 80)
        print(f"總計: {len(self.results)} 項驗證")
        print(f"✅ 通過: {passed}")
        print(f"❌ 失敗: {failed}")
        print(f"⚠️  警告: {warnings}")
        print("=" * 80 + "\n")
        if failed == 0:
            print("🎉 所有驗證通過！INSTANT 標準已達成。\n")
            return True
        else:
            print("❌ 驗證失敗，請修正上述問題。\n")
            return False
def main():
    """主程式"""
    if len(sys.argv) < 2:
        manifest_path = (
            "machine-native-ops/ns-root/docs/INSTANT-EXECUTION-MANIFEST.yaml"
        )
    else:
        manifest_path = sys.argv[1]
    validator = InstantManifestValidator(manifest_path)
    success = validator.run_all_validations()
    validator.print_report()
    sys.exit(0 if success else 1)
if __name__ == "__main__":
    main()
