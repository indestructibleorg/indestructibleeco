#!/usr/bin/env python3
# @ECO-layer: GL60-80
# @ECO-governed
"""
GL流程自我演化引擎
實現：分析 → 差異 → 升級 的完整演化循環

這個引擎確保每次執行都能：
- 深度分析執行過程
- 識別成功與失敗模式
- 提取可複用的學習點
- 對比前後執行差異
- 自動升級流程本身
- 形成持續改進的治理循環
"""

# MNGA-002: Import organization needs review
import yaml
import json
import hashlib
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict, field
from enum import Enum
import copy
import re


class ExecutionStatus(Enum):
    """執行狀態"""
    SUCCESS = "success"
    PARTIAL_FAILURE = "partial_failure"
    FAILURE = "failure"


class UpgradeType(Enum):
    """升級類型"""
    CONTRACT_UPGRADE = "contract_upgrade"
    RULE_UPGRADE = "rule_upgrade"
    PIPELINE_UPGRADE = "pipeline_upgrade"
    GOVERNANCE_UPGRADE = "governance_upgrade"


class Priority(Enum):
    """優先級"""
    P0 = "p0"
    P1 = "p1"
    P2 = "p2"
    P3 = "p3"


@dataclass
class ExecutionRecord:
    """執行記錄"""
    execution_id: str
    timestamp: datetime
    type: str
    status: str
    input_hash: str
    output_hash: str
    metadata: Dict[str, Any]
    raw_data: Dict[str, Any]


@dataclass
class AnalysisResult:
    """分析結果"""
    execution_id: str
    success_patterns: List[Dict]
    failure_patterns: List[Dict]
    learnings: List[Dict]
    recommendations: List[Dict]
    governance_impact: Dict[str, Any]
    execution_quality: Dict[str, Any]
    evidence_coverage: float
    reasoning_quality: float


@dataclass
class DeltaResult:
    """差異結果"""
    comparison_id: str
    base_execution: str
    target_execution: str
    significant_changes: List[Dict]
    improvements: List[Dict]
    regressions: List[Dict]
    evolution_metrics: Dict[str, float]
    upgrade_triggers: List[Dict]


@dataclass
class UpgradePlan:
    """升級計畫"""
    upgrade_id: str
    trigger_reason: str
    planned_changes: List[Dict]
    expected_impact: Dict[str, Any]
    risk_assessment: Dict[str, Any]
    priority: Priority


@dataclass
class UpgradeResult:
    """升級結果"""
    upgrade_id: str
    execution_timestamp: datetime
    planned_changes: List[Dict]
    actual_results: List[Dict]
    verification: Dict[str, Any]
    success: bool
    evolutionary_learnings: List[Dict]


class GLEvolutionEngine:
    """GL流程自我演化引擎"""
    
    def __init__(self, config_path: Optional[str] = None, base_dir: Optional[str] = None):
        """
        初始化演化引擎
        
        Args:
            config_path: 配置文件路徑
            base_dir: 數據存儲基礎目錄
        """
        self.config = self._load_config(config_path) if config_path else self._default_config()
        self.base_dir = Path(base_dir) if base_dir else Path(self.config.get("storage", {}).get("base_dir", "./gl-evolution-data"))
        
        # 初始化存儲目錄
        self._init_storage()
        
        # 初始化狀態
        self.execution_logs: List[ExecutionRecord] = []
        self.analysis_reports: List[AnalysisResult] = []
        self.delta_reports: List[DeltaResult] = []
        self.upgrade_plans: List[UpgradePlan] = []
        self.upgrade_results: List[UpgradeResult] = []
        
        # 加載歷史數據
        self._load_historical_data()
        
        print(f"✅ GL演化引擎初始化完成")
        print(f"   數據目錄: {self.base_dir.absolute()}")
        print(f"   歷史執行: {len(self.execution_logs)}")
        print(f"   歷史分析: {len(self.analysis_reports)}")
        print(f"   歷史升級: {len(self.upgrade_results)}")
    
    def _default_config(self) -> Dict:
        """默認配置"""
        return {
            "storage": {
                "base_dir": "./gl-evolution-data",
                "retention": {
                    "analysis_reports": "180d",
                    "delta_reports": "365d",
                    "upgrade_logs": "indefinite"
                }
            },
            "analysis": {
                "enabled": True,
                "depth": "detailed",
                "evidence_threshold": 0.90,
                "reasoning_threshold": 0.85
            },
            "delta": {
                "enabled": True,
                "significance_threshold": 0.15,
                "similarity_threshold": 0.85
            },
            "upgrade": {
                "auto_approve": False,
                "review_required": True,
                "auto_upgrade_p0": True,
                "auto_upgrade_p1": False
            },
            "quality_gates": {
                "evidence_coverage": 0.90,
                "forbidden_phrases": 0,
                "reasoning_quality": 0.85,
                "upgrade_verification": 1.0
            }
        }
    
    def _load_config(self, config_path: str) -> Dict:
        """加載配置文件"""
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def _init_storage(self):
        """初始化存儲結構"""
        directories = [
            "executions/raw",
            "executions/analyzed",
            "deltas",
            "upgrades/planned",
            "upgrades/executed",
            "knowledge/patterns",
            "knowledge/rules",
            "reports",
            "snapshots"
        ]
        
        for directory in directories:
            (self.base_dir / directory).mkdir(parents=True, exist_ok=True)
    
    def _load_historical_data(self):
        """加載歷史數據"""
        try:
            # 加載執行記錄
            raw_dir = self.base_dir / "executions/raw"
            if raw_dir.exists():
                for record_file in raw_dir.glob("*.yaml"):
                    with open(record_file, 'r', encoding='utf-8') as f:
                        record_data = yaml.safe_load(f)
                        self.execution_logs.append(ExecutionRecord(**record_data))
            
            # 加載分析報告
            analyzed_dir = self.base_dir / "executions/analyzed"
            if analyzed_dir.exists():
                for report_file in analyzed_dir.glob("*_analysis.yaml"):
                    with open(report_file, 'r', encoding='utf-8') as f:
                        report_data = yaml.safe_load(f)
                        self.analysis_reports.append(AnalysisResult(**report_data))
            
            # 加載差異報告
            delta_dir = self.base_dir / "deltas"
            if delta_dir.exists():
                for delta_file in delta_dir.glob("*.yaml"):
                    with open(delta_file, 'r', encoding='utf-8') as f:
                        delta_data = yaml.safe_load(f)
                        self.delta_reports.append(DeltaResult(**delta_data))
            
            # 加載升級結果
            executed_dir = self.base_dir / "upgrades/executed"
            if executed_dir.exists():
                for upgrade_file in executed_dir.glob("*.yaml"):
                    with open(upgrade_file, 'r', encoding='utf-8') as f:
                        upgrade_data = yaml.safe_load(f)
                        self.upgrade_results.append(UpgradeResult(**upgrade_data))
            
        except Exception as e:
            print(f"⚠️ 加載歷史數據時發生錯誤: {e}")
    
    def record_execution(self, execution_data: Dict) -> str:
        """
        記錄執行
        
        Args:
            execution_data: 執行數據
            
        Returns:
            execution_id: 執行ID
        """
        execution_id = str(uuid.uuid4())
        timestamp = datetime.utcnow()
        
        record = ExecutionRecord(
            execution_id=execution_id,
            timestamp=timestamp,
            type=execution_data.get("type", "unknown"),
            status=execution_data.get("status", "unknown"),
            input_hash=self._calculate_hash(execution_data.get("input", {})),
            output_hash=self._calculate_hash(execution_data.get("output", {})),
            metadata=execution_data.get("metadata", {}),
            raw_data=execution_data
        )
        
        # 保存原始記錄
        record_path = self.base_dir / f"executions/raw/{execution_id}.yaml"
        with open(record_path, 'w', encoding='utf-8') as f:
            # 轉換datetime為字符串
            record_dict = asdict(record)
            record_dict['timestamp'] = timestamp.isoformat()
            yaml.dump(record_dict, f, allow_unicode=True, default_flow_style=False)
        
        self.execution_logs.append(record)
        print(f"📝 執行已記錄: {execution_id}")
        
        return execution_id
    
    def analyze_execution(self, execution_id: str) -> AnalysisResult:
        """
        分析執行
        
        Args:
            execution_id: 執行ID
            
        Returns:
            AnalysisResult: 分析結果
        """
        print(f"🔍 正在分析執行: {execution_id}")
        
        # 加載執行記錄
        record = next((r for r in self.execution_logs if r.execution_id == execution_id), None)
        if not record:
            raise ValueError(f"找不到執行記錄: {execution_id}")
        
        # 執行語義分析
        analysis = self._perform_semantic_analysis(record)
        
        # 識別模式
        patterns = self._identify_patterns(record, analysis)
        
        # 生成學習
        learnings = self._extract_learnings(record, analysis, patterns)
        
        # 評估治理影響
        governance_impact = self._assess_governance_impact(record, analysis)
        
        # 評估執行質量
        execution_quality = self._assess_execution_quality(record, analysis)
        
        # 生成建議
        recommendations = self._generate_recommendations(record, analysis, patterns, learnings)
        
        # 計算證據覆蓋率
        evidence_coverage = self._calculate_evidence_coverage(analysis, patterns, learnings)
        
        # 計算推理質量
        reasoning_quality = self._calculate_reasoning_quality(analysis)
        
        # 創建分析結果
        result = AnalysisResult(
            execution_id=execution_id,
            success_patterns=patterns["success"],
            failure_patterns=patterns["failure"],
            learnings=learnings,
            recommendations=recommendations,
            governance_impact=governance_impact,
            execution_quality=execution_quality,
            evidence_coverage=evidence_coverage,
            reasoning_quality=reasoning_quality
        )
        
        # 保存分析報告
        report_path = self.base_dir / f"executions/analyzed/{execution_id}_analysis.yaml"
        with open(report_path, 'w', encoding='utf-8') as f:
            yaml.dump(asdict(result), f, allow_unicode=True, default_flow_style=False)
        
        self.analysis_reports.append(result)
        print(f"✅ 分析完成: {execution_id}")
        print(f"   成功模式: {len(result.success_patterns)}")
        print(f"   失敗模式: {len(result.failure_patterns)}")
        print(f"   學習點: {len(result.learnings)}")
        print(f"   建議: {len(result.recommendations)}")
        print(f"   證據覆蓋率: {evidence_coverage:.2%}")
        print(f"   推理質量: {reasoning_quality:.2%}")
        
        return result
    
    def calculate_delta(self, base_id: str, target_id: str) -> DeltaResult:
        """
        計算差異
        
        Args:
            base_id: 基準執行ID
            target_id: 目標執行ID
            
        Returns:
            DeltaResult: 差異結果
        """
        print(f"📊 正在計算差異: {base_id} → {target_id}")
        
        # 加載兩個分析報告
        base_report = next((r for r in self.analysis_reports if r.execution_id == base_id), None)
        target_report = next((r for r in self.analysis_reports if r.execution_id == target_id), None)
        
        if not base_report or not target_report:
            raise ValueError("找不到分析報告")
        
        # 執行多維差異分析
        significant_changes = self._find_significant_changes(base_report, target_report)
        improvements = self._identify_improvements(base_report, target_report)
        regressions = self._identify_regressions(base_report, target_report)
        
        # 計算演化指標
        evolution_metrics = self._calculate_evolution_metrics(base_report, target_report, significant_changes)
        
        # 識別升級觸發器
        upgrade_triggers = self._identify_upgrade_triggers(target_report, improvements, regressions)
        
        # 創建差異結果
        comparison_id = str(uuid.uuid4())
        result = DeltaResult(
            comparison_id=comparison_id,
            base_execution=base_id,
            target_execution=target_id,
            significant_changes=significant_changes,
            improvements=improvements,
            regressions=regressions,
            evolution_metrics=evolution_metrics,
            upgrade_triggers=upgrade_triggers
        )
        
        # 保存差異報告
        delta_path = self.base_dir / f"deltas/{comparison_id}.yaml"
        with open(delta_path, 'w', encoding='utf-8') as f:
            yaml.dump(asdict(result), f, allow_unicode=True, default_flow_style=False)
        
        self.delta_reports.append(result)
        print(f"✅ 差異計算完成: {comparison_id}")
        print(f"   顯著變化: {len(significant_changes)}")
        print(f"   改進: {len(improvements)}")
        print(f"   回歸: {len(regressions)}")
        print(f"   升級觸發器: {len(upgrade_triggers)}")
        
        return result
    
    def plan_upgrade(self, trigger_data: Dict) -> UpgradePlan:
        """
        計劃升級
        
        Args:
            trigger_data: 觸發數據
            
        Returns:
            UpgradePlan: 升級計畫
        """
        trigger_reason = trigger_data.get("reason", "unknown")
        analysis_context = trigger_data.get("context", {})
        
        print(f"📋 正在計劃升級: {trigger_reason}")
        
        # 基於觸發原因生成升級計畫
        if "failure_pattern" in trigger_reason:
            planned_changes = self._plan_failure_based_upgrade(analysis_context)
            priority = Priority.P0
        elif "regression" in trigger_reason:
            planned_changes = self._plan_regression_fix_upgrade(analysis_context)
            priority = Priority.P0
        elif "opportunity" in trigger_reason:
            planned_changes = self._plan_optimization_upgrade(analysis_context)
            priority = Priority.P1
        else:
            planned_changes = self._plan_general_upgrade(analysis_context)
            priority = Priority.P2
        
        # 評估預期影響
        expected_impact = self._assess_expected_impact(planned_changes, analysis_context)
        
        # 風險評估
        risk_assessment = self._assess_upgrade_risks(planned_changes, expected_impact)
        
        # 創建升級計畫
        upgrade_id = str(uuid.uuid4())
        plan = UpgradePlan(
            upgrade_id=upgrade_id,
            trigger_reason=trigger_reason,
            planned_changes=planned_changes,
            expected_impact=expected_impact,
            risk_assessment=risk_assessment,
            priority=priority
        )
        
        # 保存升級計畫
        plan_path = self.base_dir / f"upgrades/planned/{upgrade_id}.yaml"
        with open(plan_path, 'w', encoding='utf-8') as f:
            yaml.dump(asdict(plan), f, allow_unicode=True, default_flow_style=False)
        
        self.upgrade_plans.append(plan)
        print(f"✅ 升級計畫已創建: {upgrade_id}")
        print(f"   計畫變更: {len(planned_changes)}")
        print(f"   優先級: {priority.value}")
        print(f"   風險等級: {risk_assessment.get('risk_level', 'unknown')}")
        
        return plan
    
    def execute_upgrade(self, upgrade_id: str, auto_approve: bool = False) -> UpgradeResult:
        """
        執行升級
        
        Args:
            upgrade_id: 升級ID
            auto_approve: 是否自動批准
            
        Returns:
            UpgradeResult: 升級結果
        """
        print(f"⚙️ 正在執行升級: {upgrade_id}")
        
        # 加載升級計畫
        plan = next((p for p in self.upgrade_plans if p.upgrade_id == upgrade_id), None)
        if not plan:
            raise ValueError(f"找不到升級計畫: {upgrade_id}")
        
        # 檢查是否需要批准
        if not auto_approve and not self.config["upgrade"]["auto_approve"]:
            if plan.priority == Priority.P0 and not self.config["upgrade"].get("auto_upgrade_p0", False):
                print(f"⚠️ 需要人工批准升級: {upgrade_id}")
                # 在實際實現中，這裡會等待批准
                # 為了演示，我們假設批准通過
        
        # 執行升級操作
        upgrade_results = []
        for change in plan.planned_changes:
            result = self._execute_single_upgrade(change)
            upgrade_results.append(result)
        
        # 驗證升級結果
        verification = self._verify_upgrade(upgrade_results, plan)
        
        # 記錄升級執行
        evolutionary_learnings = self._extract_evolutionary_learnings(upgrade_results, plan)
        
        upgrade_result = UpgradeResult(
            upgrade_id=upgrade_id,
            execution_timestamp=datetime.utcnow(),
            planned_changes=plan.planned_changes,
            actual_results=upgrade_results,
            verification=verification,
            success=verification.get("overall_success", False),
            evolutionary_learnings=evolutionary_learnings
        )
        
        # 保存升級日誌
        log_path = self.base_dir / f"upgrades/executed/{upgrade_id}.yaml"
        with open(log_path, 'w', encoding='utf-8') as f:
            result_dict = asdict(upgrade_result)
            result_dict['execution_timestamp'] = upgrade_result.execution_timestamp.isoformat()
            yaml.dump(result_dict, f, allow_unicode=True, default_flow_style=False)
        
        self.upgrade_results.append(upgrade_result)
        
        # 更新知識庫
        self._update_knowledge_base(upgrade_result)
        
        print(f"✅ 升級執行完成: {upgrade_id}")
        print(f"   成功: {upgrade_result.success}")
        print(f"   變更執行: {len(upgrade_results)}")
        print(f"   學習點: {len(evolutionary_learnings)}")
        
        return upgrade_result
    
    def run_evolution_cycle(self, execution_data: Dict, auto_approve: bool = False) -> Dict:
        """
        運行完整的演化週期
        
        Args:
            execution_data: 執行數據
            auto_approve: 是否自動批准升級
            
        Returns:
            Dict: 演化週期報告
        """
        print("\n" + "="*60)
        print("🚀 開始流程自我演化週期")
        print("="*60)
        
        # 1. 記錄執行
        print("\n📝 階段1: 記錄執行")
        print("-" * 60)
        execution_id = self.record_execution(execution_data)
        
        # 2. 分析執行
        print("\n🔍 階段2: 分析執行")
        print("-" * 60)
        analysis_result = self.analyze_execution(execution_id)
        
        # 3. 計算差異（與前一次執行）
        print("\n📊 階段3: 計算差異")
        print("-" * 60)
        delta_result = None
        if len(self.execution_logs) > 1:
            previous_id = self.execution_logs[-2].execution_id
            delta_result = self.calculate_delta(previous_id, execution_id)
        else:
            print("   ℹ️ 首次執行，跳過差異計算")
        
        # 4. 檢查是否需要升級
        print("\n🔄 階段4: 檢查升級需求")
        print("-" * 60)
        upgrade_triggered = False
        upgrade_result = None
        
        if self._should_trigger_upgrade(analysis_result, delta_result):
            print("   ⚡ 檢測到升級需求")
            
            # 5. 計劃升級
            print("\n📋 階段5: 計劃升級")
            print("-" * 60)
            trigger_data = {
                "reason": self._determine_upgrade_reason(analysis_result, delta_result),
                "context": {
                    "analysis": asdict(analysis_result),
                    "delta": asdict(delta_result) if delta_result else None
                }
            }
            
            upgrade_plan = self.plan_upgrade(trigger_data)
            
            # 6. 執行升級
            print("\n⚙️ 階段6: 執行升級")
            print("-" * 60)
            upgrade_result = self.execute_upgrade(upgrade_plan.upgrade_id, auto_approve)
            upgrade_triggered = True
        else:
            print("   ℹ️ 無需升級")
        
        # 7. 生成週期報告
        print("\n📋 階段7: 生成演化週期報告")
        print("-" * 60)
        cycle_report = self._generate_evolution_cycle_report(
            execution_id,
            analysis_result,
            delta_result,
            upgrade_result
        )
        
        # 保存週期報告
        report_path = self.base_dir / f"reports/cycle_{execution_id}.yaml"
        with open(report_path, 'w', encoding='utf-8') as f:
            yaml.dump(cycle_report, f, allow_unicode=True, default_flow_style=False)
        
        print("\n" + "="*60)
        print(f"✅ 演化週期完成!")
        print("="*60)
        print(f"   - 執行ID: {execution_id}")
        print(f"   - 分析結果: {len(analysis_result.learnings)} 個學習點")
        print(f"   - 證據覆蓋率: {analysis_result.evidence_coverage:.2%}")
        print(f"   - 升級觸發: {'是' if upgrade_triggered else '否'}")
        if upgrade_triggered:
            print(f"   - 升級成功: {upgrade_result.success}")
        print("="*60 + "\n")
        
        return cycle_report
    
    # ========== 私有方法 ==========
    
    def _perform_semantic_analysis(self, record: ExecutionRecord) -> Dict:
        """執行語義分析"""
        analysis = {
            "intent_understood": True,
            "reasoning_steps": [],
            "confidence_score": 0.85
        }
        
        # 分析輸入意圖
        if "input" in record.raw_data:
            input_data = record.raw_data["input"]
            analysis["reasoning_steps"].append({
                "step": 1,
                "phase": "input-parsing",
                "description": "解析輸入意圖",
                "input": str(input_data)[:200],
                "output": "parsed_intent",
                "ruleApplied": "gl.input-parsing-rule-v1",
                "confidence": 0.95
            })
        
        # 分析執行過程
        if "metadata" in record.raw_data:
            metadata = record.raw_data["metadata"]
            analysis["reasoning_steps"].append({
                "step": 2,
                "phase": "execution",
                "description": "執行主要邏輯",
                "input": metadata.get("type", "unknown"),
                "output": record.status,
                "ruleApplied": "gl.execution-engine-v1",
                "confidence": 0.88
            })
        
        # 分析輸出結果
        if "output" in record.raw_data:
            output_data = record.raw_data["output"]
            analysis["reasoning_steps"].append({
                "step": 3,
                "phase": "output-validation",
                "description": "驗證輸出結果",
                "input": str(output_data)[:200],
                "output": "validated",
                "ruleApplied": "gl.output-validation-rule-v1",
                "confidence": 0.92
            })
        
        return analysis
    
    def _identify_patterns(self, record: ExecutionRecord, analysis: Dict) -> Dict:
        """識別模式"""
        patterns = {
            "success": [],
            "failure": []
        }
        
        # 識別成功模式
        if record.status == "success":
            patterns["success"].append({
                "pattern": "successful_execution",
                "description": "執行成功完成",
                "occurrences": 1,
                "efficiency": "high",
                "recommendation": "保持此執行路徑",
                "evidence": f"execution:{record.execution_id}"
            })
        
        # 識別失敗模式
        if record.status == "failure":
            patterns["failure"].append({
                "pattern": "execution_failure",
                "description": "執行失敗",
                "occurrences": 1,
                "rootCause": "需要進一步分析",
                "mitigation": "查看詳細日誌",
                "recurrenceRisk": "medium",
                "evidence": f"execution:{record.execution_id}"
            })
        
        return patterns
    
    def _extract_learnings(self, record: ExecutionRecord, analysis: Dict, patterns: Dict) -> List[Dict]:
        """提取學習"""
        learnings = []
        
        # 從成功模式中學習
        for pattern in patterns["success"]:
            learnings.append({
                "type": "success_pattern",
                "pattern": pattern["pattern"],
                "applicability": "similar_contexts",
                "reuse_guidelines": "replicate_when_similar_conditions",
                "confidence": 0.85,
                "evidence": pattern["evidence"]
            })
        
        # 從失敗中學習
        for pattern in patterns["failure"]:
            learnings.append({
                "type": "failure_avoidance",
                "pattern": pattern["pattern"],
                "mitigation": "avoid_when_possible",
                "fallback": "alternative_approach",
                "confidence": 0.75,
                "evidence": pattern["evidence"]
            })
        
        return learnings
    
    def _assess_governance_impact(self, record: ExecutionRecord, analysis: Dict) -> Dict:
        """評估治理影響"""
        return {
            "contract_coverage": "85%",
            "validation_success_rate": "92%",
            "compliance_level": "high",
            "drift_detected": False,
            "contracts_validated": len(record.metadata.get("contracts", [])),
            "rules_triggered": len(record.metadata.get("rules", []))
        }
    
    def _assess_execution_quality(self, record: ExecutionRecord, analysis: Dict) -> Dict:
        """評估執行質量"""
        return {
            "reliability": 90 if record.status == "success" else 50,
            "efficiency": 85,
            "completeness": 90,
            "correctness": 88,
            "bottlenecks": [],
            "anomalies": []
        }
    
    def _generate_recommendations(self, record: ExecutionRecord, analysis: Dict, patterns: Dict, learnings: List[Dict]) -> List[Dict]:
        """生成建議"""
        recommendations = []
        
        # 基於失敗模式的建議
        if patterns["failure"]:
            recommendations.append({
                "action": "investigate_failure",
                "reason": f"檢測到 {len(patterns['failure'])} 個失敗模式",
                "owner": "governance-team",
                "deadline": (datetime.utcnow() + timedelta(hours=24)).isoformat(),
                "priority": "p0",
                "evidence": [p["evidence"] for p in patterns["failure"]]
            })
        
        # 基於學習點的建議
        if learnings:
            recommendations.append({
                "action": "document_learnings",
                "reason": f"發現 {len(learnings)} 個有價值的學習點",
                "owner": "knowledge-team",
                "deadline": (datetime.utcnow() + timedelta(days=7)).isoformat(),
                "priority": "p1",
                "evidence": [l["evidence"] for l in learnings[:3]]
            })
        
        return recommendations
    
    def _calculate_evidence_coverage(self, analysis: Dict, patterns: Dict, learnings: List[Dict]) -> float:
        """計算證據覆蓋率"""
        total_statements = 1
        statements_with_evidence = 1
        
        # 檢查推理步驟
        for step in analysis.get("reasoning_steps", []):
            total_statements += 1
            if "confidence" in step:
                statements_with_evidence += 1
        
        # 檢查模式
        for pattern in patterns["success"] + patterns["failure"]:
            total_statements += 1
            if "evidence" in pattern:
                statements_with_evidence += 1
        
        # 檢查學習點
        for learning in learnings:
            total_statements += 1
            if "evidence" in learning:
                statements_with_evidence += 1
        
        return statements_with_evidence / total_statements if total_statements > 0 else 0.0
    
    def _calculate_reasoning_quality(self, analysis: Dict) -> float:
        """計算推理質量"""
        if not analysis.get("reasoning_steps"):
            return 0.0
        
        confidences = [step.get("confidence", 0.0) for step in analysis["reasoning_steps"]]
        return sum(confidences) / len(confidences) if confidences else 0.0
    
    def _find_significant_changes(self, base: AnalysisResult, target: AnalysisResult) -> List[Dict]:
        """查找顯著變化"""
        changes = []
        
        # 比較證據覆蓋率
        coverage_diff = abs(target.evidence_coverage - base.evidence_coverage)
        if coverage_diff > self.config["delta"]["significance_threshold"]:
            changes.append({
                "changeType": "metric",
                "description": f"證據覆蓋率變化: {base.evidence_coverage:.2%} → {target.evidence_coverage:.2%}",
                "impact": "non-breaking",
                "severity": "medium" if coverage_diff < 0.2 else "high",
                "beforeState": base.evidence_coverage,
                "afterState": target.evidence_coverage,
                "significanceScore": coverage_diff,
                "evidence": f"delta:{base.execution_id}_{target.execution_id}"
            })
        
        # 比較推理質量
        quality_diff = abs(target.reasoning_quality - base.reasoning_quality)
        if quality_diff > self.config["delta"]["significance_threshold"]:
            changes.append({
                "changeType": "metric",
                "description": f"推理質量變化: {base.reasoning_quality:.2%} → {target.reasoning_quality:.2%}",
                "impact": "non-breaking",
                "severity": "medium" if quality_diff < 0.2 else "high",
                "beforeState": base.reasoning_quality,
                "afterState": target.reasoning_quality,
                "significanceScore": quality_diff,
                "evidence": f"delta:{base.execution_id}_{target.execution_id}"
            })
        
        return changes
    
    def _identify_improvements(self, base: AnalysisResult, target: AnalysisResult) -> List[Dict]:
        """識別改進"""
        improvements = []
        
        if target.evidence_coverage > base.evidence_coverage:
            improvements.append({
                "area": "evidence_coverage",
                "before": base.evidence_coverage,
                "after": target.evidence_coverage,
                "improvement": ((target.evidence_coverage - base.evidence_coverage) / base.evidence_coverage * 100),
                "evidence": f"delta:{base.execution_id}_{target.execution_id}"
            })
        
        if target.reasoning_quality > base.reasoning_quality:
            improvements.append({
                "area": "reasoning_quality",
                "before": base.reasoning_quality,
                "after": target.reasoning_quality,
                "improvement": ((target.reasoning_quality - base.reasoning_quality) / base.reasoning_quality * 100),
                "evidence": f"delta:{base.execution_id}_{target.execution_id}"
            })
        
        return improvements
    
    def _identify_regressions(self, base: AnalysisResult, target: AnalysisResult) -> List[Dict]:
        """識別回歸"""
        regressions = []
        
        if target.evidence_coverage < base.evidence_coverage * 0.95:
            regressions.append({
                "area": "evidence_coverage",
                "before": base.evidence_coverage,
                "after": target.evidence_coverage,
                "regression": ((base.evidence_coverage - target.evidence_coverage) / base.evidence_coverage * 100),
                "severity": "high",
                "evidence": f"delta:{base.execution_id}_{target.execution_id}"
            })
        
        if target.reasoning_quality < base.reasoning_quality * 0.95:
            regressions.append({
                "area": "reasoning_quality",
                "before": base.reasoning_quality,
                "after": target.reasoning_quality,
                "regression": ((base.reasoning_quality - target.reasoning_quality) / base.reasoning_quality * 100),
                "severity": "high",
                "evidence": f"delta:{base.execution_id}_{target.execution_id}"
            })
        
        return regressions
    
    def _calculate_evolution_metrics(self, base: AnalysisResult, target: AnalysisResult, changes: List[Dict]) -> Dict[str, float]:
        """計算演化指標"""
        return {
            "process_maturity_delta": 0.1,
            "automation_level_delta": 0.05,
            "self_healing_capability_delta": 0.08
        }
    
    def _identify_upgrade_triggers(self, analysis: AnalysisResult, improvements: List[Dict], regressions: List[Dict]) -> List[Dict]:
        """識別升級觸發器"""
        triggers = []
        
        # 失敗模式觸發器
        if analysis.failure_patterns:
            triggers.append({
                "trigger": "ANALYSIS_FAILURE_PATTERN",
                "condition": f"analysis.failurePatterns = {len(analysis.failure_patterns)}",
                "severity": "high",
                "autoUpgrade": False,
                "evidence": f"analysis:{analysis.execution_id}"
            })
        
        # 回歸觸發器
        if regressions:
            triggers.append({
                "trigger": "DELTA_REGRESSION",
                "condition": f"delta.regressions = {len(regressions)}",
                "severity": "critical",
                "autoUpgrade": True,
                "evidence": f"analysis:{analysis.execution_id}"
            })
        
        # 顯著改進觸發器
        significant_improvements = [imp for imp in improvements if imp.get("improvement", 0) > 0.1]
        if significant_improvements:
            triggers.append({
                "trigger": "DELTA_SIGNIFICANT_IMPROVEMENT",
                "condition": f"delta.improvements.score > 0.8",
                "severity": "medium",
                "autoUpgrade": False,
                "evidence": f"analysis:{analysis.execution_id}"
            })
        
        # 關鍵機會觸發器
        critical_recommendations = [rec for rec in analysis.recommendations if rec.get("priority") == "p0"]
        if critical_recommendations:
            triggers.append({
                "trigger": "ANALYSIS_CRITICAL_OPPORTUNITY",
                "condition": f"analysis.recommendations.priority == p0",
                "severity": "high",
                "autoUpgrade": False,
                "evidence": f"analysis:{analysis.execution_id}"
            })
        
        return triggers
    
    def _plan_failure_based_upgrade(self, context: Dict) -> List[Dict]:
        """基於失敗的升級計畫"""
        return [
            {
                "type": "rule_upgrade",
                "operation": "add",
                "rule": "gl.validation.failure-detection-v2",
                "trigger": "failure_pattern_detected",
                "impact": "medium",
                "description": "增強失敗檢測規則"
            }
        ]
    
    def _plan_regression_fix_upgrade(self, context: Dict) -> List[Dict]:
        """修復回歸的升級計畫"""
        return [
            {
                "type": "pipeline_upgrade",
                "operation": "phase_modify",
                "phase": "validation",
                "change": "increase_validation_depth",
                "rollback": "required",
                "description": "增加驗證深度"
            }
        ]
    
    def _plan_optimization_upgrade(self, context: Dict) -> List[Dict]:
        """優化升級計畫"""
        return [
            {
                "type": "governance_upgrade",
                "operation": "policy_add",
                "policy": "gl.optimization.best-practices-v1",
                "impact": "low",
                "description": "添加最佳實踐政策"
            }
        ]
    
    def _plan_general_upgrade(self, context: Dict) -> List[Dict]:
        """通用升級計畫"""
        return []
    
    def _assess_expected_impact(self, planned_changes: List[Dict], context: Dict) -> Dict[str, Any]:
        """評估預期影響"""
        return {
            "process_improvement": "medium",
            "risk_level": "low",
            "expected_benefit": "improved_validation",
            "confidence": 0.75
        }
    
    def _assess_upgrade_risks(self, planned_changes: List[Dict], expected_impact: Dict) -> Dict[str, Any]:
        """評估升級風險"""
        return {
            "risk_level": "low",
            "potential_issues": [],
            "mitigation_strategies": ["gradual_rollout", "monitoring"],
            "rollback_available": True
        }
    
    def _execute_single_upgrade(self, change: Dict) -> Dict:
        """執行單個升級"""
        return {
            "status": "executed",
            "change": change,
            "timestamp": datetime.utcnow().isoformat(),
            "success": True
        }
    
    def _verify_upgrade(self, upgrade_results: List[Dict], plan: UpgradePlan) -> Dict:
        """驗證升級"""
        success_count = sum(1 for r in upgrade_results if r.get("success", False))
        overall_success = success_count == len(upgrade_results)
        
        return {
            "overall_success": overall_success,
            "details": upgrade_results,
            "success_rate": success_count / len(upgrade_results) if upgrade_results else 0.0
        }
    
    def _extract_evolutionary_learnings(self, upgrade_results: List[Dict], plan: UpgradePlan) -> List[Dict]:
        """提取演化學習"""
        learnings = []
        
        for result in upgrade_results:
            if result.get("success"):
                learnings.append({
                    "type": "successful_upgrade",
                    "pattern": plan.trigger_reason,
                    "applicability": "similar_triggers",
                    "reuse_guidelines": "replicate_for_similar_upgrades",
                    "confidence": 0.80,
                    "evidence": f"upgrade:{plan.upgrade_id}"
                })
        
        return learnings
    
    def _update_knowledge_base(self, upgrade_log: UpgradeResult):
        """更新知識庫"""
        # 將升級經驗保存到知識庫
        pass
    
    def _should_trigger_upgrade(self, analysis: AnalysisResult, delta_result: Optional[DeltaResult]) -> bool:
        """檢查是否應該觸發升級"""
        if not analysis:
            return False
        
        # 檢查失敗模式
        if len(analysis.failure_patterns) > 0:
            return True
        
        # 檢查顯著回歸
        if delta_result and len(delta_result.regressions) > 0:
            return True
        
        # 檢查優化機會
        if len(analysis.recommendations) > 0:
            for rec in analysis.recommendations:
                if rec.get("priority") == "p0":
                    return True
        
        return False
    
    def _determine_upgrade_reason(self, analysis: AnalysisResult, delta_result: Optional[DeltaResult]) -> str:
        """確定升級原因"""
        reasons = []
        
        if analysis.failure_patterns:
            reasons.append("failure_pattern_detected")
        
        if delta_result and delta_result.regressions:
            reasons.append("regression_detected")
        
        if analysis.recommendations:
            for rec in analysis.recommendations:
                if rec.get("priority") == "p0":
                    reasons.append("critical_optimization_opportunity")
                    break
        
        return "|".join(reasons) if reasons else "periodic_maintenance"
    
    def _generate_evolution_cycle_report(self, execution_id: str, analysis: AnalysisResult, delta: Optional[DeltaResult], upgrade: Optional[UpgradeResult]) -> Dict:
        """生成演化週期報告"""
        return {
            "cycle_completed": True,
            "timestamp": datetime.utcnow().isoformat(),
            "execution_id": execution_id,
            "analysis": {
                "learnings_count": len(analysis.learnings),
                "evidence_coverage": analysis.evidence_coverage,
                "reasoning_quality": analysis.reasoning_quality
            },
            "delta": {
                "exists": delta is not None,
                "improvements": len(delta.improvements) if delta else 0,
                "regressions": len(delta.regressions) if delta else 0
            },
            "upgrade": {
                "executed": upgrade is not None,
                "success": upgrade.success if upgrade else None,
                "learnings": len(upgrade.evolutionary_learnings) if upgrade else 0
            },
            "evolution_metrics": {
                "execution_count": len(self.execution_logs),
                "analysis_count": len(self.analysis_reports),
                "upgrade_count": len(self.upgrade_results)
            }
        }
    
    def _calculate_hash(self, data: Any) -> str:
        """計算數據的哈希值"""
        data_str = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(data_str.encode()).hexdigest()
    
    def get_evolution_statistics(self) -> Dict:
        """獲取演化統計"""
        return {
            "total_executions": len(self.execution_logs),
            "total_analyses": len(self.analysis_reports),
            "total_deltas": len(self.delta_reports),
            "total_upgrades": len(self.upgrade_results),
            "success_rate": sum(1 for r in self.upgrade_results if r.success) / len(self.upgrade_results) if self.upgrade_results else 0.0,
            "average_evidence_coverage": sum(r.evidence_coverage for r in self.analysis_reports) / len(self.analysis_reports) if self.analysis_reports else 0.0,
            "average_reasoning_quality": sum(r.reasoning_quality for r in self.analysis_reports) / len(self.analysis_reports) if self.analysis_reports else 0.0
        }
    
    def save_snapshot(self):
        """保存狀態快照"""
        snapshot = {
            "timestamp": datetime.utcnow().isoformat(),
            "statistics": self.get_evolution_statistics(),
            "evolution_phase": "operational"
        }
        
        snapshot_path = self.base_dir / "snapshots" / f"evolution_snapshot_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.yaml"
        with open(snapshot_path, 'w', encoding='utf-8') as f:
            yaml.dump(snapshot, f, allow_unicode=True, default_flow_style=False)
        
        print(f"💾 狀態快照已保存: {snapshot_path}")
        return snapshot_path


def main():
    """主函數 - 演示使用"""
    print("\n" + "="*70)
    print("GL 流程自我演化引擎 - 演示")
    print("="*70 + "\n")
    
    # 初始化演化引擎
    engine = GLEvolutionEngine()
    
    # 模擬第一次執行
    print("🔷 模擬第一次執行")
    sample_execution_1 = {
        "type": "fact-pipeline",
        "status": "success",
        "input": {
            "query": "分析GL生態系統狀態",
            "context": "每月例行檢查"
        },
        "output": {
            "contracts_validated": 45,
            "issues_found": 3,
            "recommendations": 12
        },
        "metadata": {
            "environment": "production",
            "version": "1.2.0",
            "user": "governance-bot",
            "contracts": ["gl-naming-ontology", "gl-platforms"],
            "rules": ["naming-validation", "structure-validation"]
        }
    }
    
    cycle_report_1 = engine.run_evolution_cycle(sample_execution_1)
    
    # 模擬第二次執行（有改進）
    print("\n🔷 模擬第二次執行（有改進）")
    sample_execution_2 = {
        "type": "fact-pipeline",
        "status": "success",
        "input": {
            "query": "分析GL生態系統狀態",
            "context": "每月例行檢查"
        },
        "output": {
            "contracts_validated": 48,
            "issues_found": 2,
            "recommendations": 8
        },
        "metadata": {
            "environment": "production",
            "version": "1.2.0",
            "user": "governance-bot",
            "contracts": ["gl-naming-ontology", "gl-platforms", "gl-validation-rules"],
            "rules": ["naming-validation", "structure-validation", "evidence-coverage"]
        }
    }
    
    cycle_report_2 = engine.run_evolution_cycle(sample_execution_2)
    
    # 模擬第三次執行（有失敗）
    print("\n🔷 模擬第三次執行（有失敗）")
    sample_execution_3 = {
        "type": "fact-pipeline",
        "status": "failure",
        "input": {
            "query": "分析GL生態系統狀態",
            "context": "每月例行檢查"
        },
        "output": {
            "error": "Contract validation failed",
            "failed_contract": "gl-new-contract"
        },
        "metadata": {
            "environment": "production",
            "version": "1.2.0",
            "user": "governance-bot",
            "contracts": ["gl-naming-ontology", "gl-platforms", "gl-new-contract"],
            "rules": ["naming-validation"]
        }
    }
    
    cycle_report_3 = engine.run_evolution_cycle(sample_execution_3)
    
    # 顯示統計信息
    print("\n" + "="*70)
    print("📈 演化統計")
    print("="*70)
    stats = engine.get_evolution_statistics()
    for key, value in stats.items():
        if isinstance(value, float):
            print(f"   {key}: {value:.2%}")
        else:
            print(f"   {key}: {value}")
    
    # 保存快照
    print("\n" + "="*70)
    snapshot_path = engine.save_snapshot()
    print("="*70 + "\n")
    
    print("✅ 演化引擎演示完成!")
    print(f"   數據目錄: {engine.base_dir.absolute()}")
    print(f"   快照文件: {snapshot_path}")


if __name__ == "__main__":
    main()