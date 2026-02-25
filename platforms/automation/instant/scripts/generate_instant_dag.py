# 
# @ECO-governed
# @ECO-layer: data
# @ECO-semantic: generate-instant-dag
# @ECO-audit-trail: ../../engine/gov-platform.governance/GL_SEMANTIC_ANCHOR.json
#
# GL Unified Architecture Governance Framework Activated

#!/usr/bin/env python3
"""
INSTANT Execution DAG Generator
根據 INSTANT-EXECUTION-MANIFEST.yaml 生成：
1. 事件驅動 DAG 圖
2. 依賴關係圖
3. 執行流程圖
4. Mermaid 格式圖表
"""
import sys
from pathlib import Path
import yaml
class InstantDAGGenerator:
    """INSTANT DAG 生成器"""
    def __init__(self, manifest_path: str):
        self.manifest_path = Path(manifest_path)
        self.manifest = None
    def load_manifest(self) -> bool:
        """載入 manifest"""
        try:
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                self.manifest = yaml.safe_load(f)
            return True
        except Exception as e:
            print(f"❌ 無法載入 manifest: {e}")
            return False
    def generate_event_dag(self) -> str:
        """生成事件驅動 DAG"""
        if "event_system" not in self.manifest:
            return "❌ 缺少 event_system"
        event_system = self.manifest["event_system"]
        event_types = event_system.get("event_types", {})
        mermaid = ["```mermaid", "graph TD"]
        mermaid.append("    %% 事件驅動 DAG")
        mermaid.append("")
        # 定義樣式
        mermaid.append("    classDef eventNode fill:#4CAF50,stroke:#2E7D32,color:#fff")
        mermaid.append("    classDef actionNode fill:#2196F3,stroke:#1565C0,color:#fff")
        mermaid.append(
            "    classDef decisionNode fill:#FF9800,stroke:#E65100,color:#fff"
        )
        mermaid.append("")
        # 生成事件節點
        for event_name, event_data in event_types.items():
            event_id = event_name.upper()
            event_data.get("description", "")
            latency = event_data.get("latency_tier", "")
            mermaid.append(f"    {event_id}[{event_name}<br/>{latency}]:::eventNode")
            # 生成動作節點
            actions = event_data.get("actions", [])
            for i, action in enumerate(actions):
                action_id = f"{event_id}_A{i+1}"
                mermaid.append(f"    {action_id}[{action}]:::actionNode")
                mermaid.append(f"    {event_id} --> {action_id}")
        mermaid.append("```")
        return "\n".join(mermaid)
    def generate_pipeline_dag(self) -> str:
        """生成流水線 DAG"""
        if "pipeline" not in self.manifest:
            return "❌ 缺少 pipeline"
        pipeline = self.manifest["pipeline"]
        stages = pipeline.get("stages", {})
        mermaid = ["```mermaid", "graph LR"]
        mermaid.append("    %% 閉環流水線 DAG")
        mermaid.append("")
        # 定義樣式
        mermaid.append("    classDef stage fill:#673AB7,stroke:#4527A0,color:#fff")
        mermaid.append("    classDef feedback fill:#F44336,stroke:#C62828,color:#fff")
        mermaid.append("")
        # 排序 stages
        sorted_stages = sorted(stages.items(), key=lambda x: x[0])
        # 生成 stage 節點
        prev_stage = None
        for stage_name, stage_data in sorted_stages:
            stage_id = stage_name.upper().replace("STAGE_", "S")
            name = stage_data.get("name", "")
            latency = stage_data.get("latency", "")
            mermaid.append(f"    {stage_id}[{name}<br/>{latency}]:::stage")
            if prev_stage:
                mermaid.append(f"    {prev_stage} --> {stage_id}")
            prev_stage = stage_id
        # 添加回饋循環
        if prev_stage:
            first_stage = sorted_stages[0][0].upper().replace("STAGE_", "S")
            mermaid.append(f"    {prev_stage} -.回饋.-> {first_stage}:::feedback")
        mermaid.append("```")
        return "\n".join(mermaid)
    def generate_agent_collaboration_dag(self) -> str:
        """生成代理協作 DAG"""
        if "agent_system" not in self.manifest:
            return "❌ 缺少 agent_system"
        agent_system = self.manifest["agent_system"]
        agent_types = agent_system.get("agent_types", {})
        mermaid = ["```mermaid", "graph TD"]
        mermaid.append("    %% 代理協作 DAG")
        mermaid.append("")
        # 定義樣式
        mermaid.append("    classDef architect fill:#9C27B0,stroke:#6A1B9A,color:#fff")
        mermaid.append("    classDef executor fill:#00BCD4,stroke:#00838F,color:#fff")
        mermaid.append("    classDef validator fill:#4CAF50,stroke:#2E7D32,color:#fff")
        mermaid.append("    classDef fixer fill:#FF9800,stroke:#E65100,color:#fff")
        mermaid.append("    classDef observer fill:#607D8B,stroke:#37474F,color:#fff")
        mermaid.append("")
        # 生成代理節點
        for agent_type, agent_data in agent_types.items():
            agent_id = agent_type.upper()
            count = agent_data.get("count", "")
            agent_data.get("responsibility", "")
            latency = agent_data.get("latency", "")
            # 確定樣式
            if "architect" in agent_type:
                style = "architect"
            elif "executor" in agent_type:
                style = "executor"
            elif "validator" in agent_type:
                style = "validator"
            elif "fixer" in agent_type:
                style = "fixer"
            else:
                style = "observer"
            mermaid.append(
                f"    {agent_id}[{agent_type}<br/>{count}<br/>{latency}]:::{style}"
            )
        # 生成協作關係
        mermaid.append("")
        mermaid.append("    ARCHITECT_AGENTS --> EXECUTOR_AGENTS")
        mermaid.append("    EXECUTOR_AGENTS --> VALIDATOR_AGENTS")
        mermaid.append("    VALIDATOR_AGENTS --> FIXER_AGENTS")
        mermaid.append("    FIXER_AGENTS --> EXECUTOR_AGENTS")
        mermaid.append("    OBSERVER_AGENTS --> ARCHITECT_AGENTS")
        mermaid.append("```")
        return "\n".join(mermaid)
    def generate_state_transition_dag(self) -> str:
        """生成狀態轉換 DAG"""
        if "state_system" not in self.manifest:
            return "❌ 缺少 state_system"
        state_system = self.manifest["state_system"]
        transitions = state_system.get("state_transitions", [])
        mermaid = ["```mermaid", "stateDiagram-v2"]
        mermaid.append("    %% 狀態轉換 DAG")
        mermaid.append("")
        # 生成狀態轉換
        for transition in transitions:
            from_state = transition.get("from", "").replace(".", "_")
            to_state = transition.get("to", "").replace(".", "_")
            trigger = transition.get("trigger", "")
            latency = transition.get("latency", "")
            mermaid.append(f"    {from_state} --> {to_state}: {trigger}<br/>{latency}")
        mermaid.append("```")
        return "\n".join(mermaid)
    def generate_full_report(self) -> str:
        """生成完整報告"""
        report = []
        report.append("# INSTANT Execution DAG 報告")
        report.append("")
        report.append("自動生成於 INSTANT-EXECUTION-MANIFEST.yaml")
        report.append("")
        report.append("## 1. 事件驅動 DAG")
        report.append("")
        report.append(self.generate_event_dag())
        report.append("")
        report.append("## 2. 閉環流水線 DAG")
        report.append("")
        report.append(self.generate_pipeline_dag())
        report.append("")
        report.append("## 3. 代理協作 DAG")
        report.append("")
        report.append(self.generate_agent_collaboration_dag())
        report.append("")
        report.append("## 4. 狀態轉換 DAG")
        report.append("")
        report.append(self.generate_state_transition_dag())
        report.append("")
        return "\n".join(report)
    def save_report(self, output_path: str):
        """儲存報告"""
        report = self.generate_full_report()
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"✅ DAG 報告已生成: {output_path}")
def main():
    """主程式"""
    if len(sys.argv) < 2:
        manifest_path = (
            "machine-native-ops/ns-root/docs/INSTANT-EXECUTION-MANIFEST.yaml"
        )
    else:
        manifest_path = sys.argv[1]
    if len(sys.argv) < 3:
        output_path = "machine-native-ops/ns-root/INSTANT-EXECUTION-DAG.md"
    else:
        output_path = sys.argv[2]
    generator = InstantDAGGenerator(manifest_path)
    if generator.load_manifest():
        generator.save_report(output_path)
    else:
        sys.exit(1)
if __name__ == "__main__":
    main()
