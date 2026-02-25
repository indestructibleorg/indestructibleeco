# @ECO-governed
# @ECO-layer: GL90-99
# @ECO-semantic: archive-tools
# @ECO-audit-trail: ../../engine/gl-platform.governance/GL_SEMANTIC_ANCHOR.json
#
# GL Unified Architecture Governance Framework Activated
#
# @ECO-governed
# @ECO-layer: gl-platform.governance
# @ECO-semantic: cognitive_engine
# @ECO-audit-trail: ../../engine/gl-platform.governance/GL_SEMANTIC_ANCHOR.json
#
#!/usr/bin/env python3
"""
Cognitive Engine - 認知推理引擎
提供高階認知能力，包括：
1. 理解層 (Understanding): 多維度全面理解用戶需求
2. 推理層 (Reasoning): 內部推理與邏輯分析
3. 搜尋層 (Search): 利用工具/API尋找最新解決方案
4. 整合層 (Integration): 整合推理結果生成決策
Version: 1.0.0
"""
# MNGA-002: Import organization needs review
import json
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional
import yaml
# ============================================================================
# 認知層級定義
# ============================================================================
class CognitiveLevel(Enum):
    """認知層級"""
    PERCEPTION = "perception"  # 感知層：接收原始輸入
    UNDERSTANDING = "understanding"  # 理解層：Spec解析
    REASONING = "reasoning"  # 推理層：邏輯分析
    SEARCH = "search"  # 搜尋層：外部資源
    INTEGRATION = "integration"  # 整合層：綜合決策
    DECISION = "decision"  # 決策層：最終輸出
class ConfidenceLevel(Enum):
    """信心水平"""
    HIGH = "high"  # >= 0.8
    MEDIUM = "medium"  # 0.5 - 0.8
    LOW = "low"  # 0.3 - 0.5
    INSUFFICIENT = "insufficient"  # < 0.3
# ============================================================================
# 資料結構
# ============================================================================
@dataclass
class CognitiveContext:
    """認知上下文"""
    session_id: str
    timestamp: str
    raw_input: Dict
    understanding: Optional[Dict] = None
    reasoning_trace: List[Dict] = field(default_factory=list)
    search_results: List[Dict] = field(default_factory=list)
    integration_result: Optional[Dict] = None
    final_decision: Optional[Dict] = None
    confidence: float = 0.0
    metadata: Dict = field(default_factory=dict)
@dataclass
class UnderstandingResult:
    """理解層結果"""
    intent: str  # 用戶意圖
    entities: List[Dict]  # 識別的實體
    constraints: List[str]  # 約束條件
    implicit_requirements: List[str]  # 隱含需求
    ambiguities: List[str]  # 歧義點
    completeness_score: float  # 完整度評分 0-1
    dimensions: Dict[str, Any]  # 多維度分析
@dataclass
class ReasoningStep:
    """推理步驟"""
    step_id: int
    hypothesis: str  # 假設
    evidence: List[str]  # 證據
    conclusion: str  # 結論
    confidence: float  # 信心度
    alternatives: List[str]  # 備選方案
@dataclass
class SearchQuery:
    """搜尋查詢"""
    query_type: str  # local, web, api, knowledge_base
    query_text: str
    filters: Dict
    max_results: int = 10
@dataclass
class IntegrationResult:
    """整合結果"""
    synthesized_understanding: Dict
    weighted_recommendations: List[Dict]
    risk_assessment: Dict
    confidence_breakdown: Dict
    final_score: float
# ============================================================================
# 理解層 - Understanding Layer
# ============================================================================
class UnderstandingLayer:
    """
    理解層：多維度全面理解用戶需求
    功能：
    - 意圖識別
    - 實體抽取
    - 約束分析
    - 隱含需求推斷
    - 歧義檢測
    - 完整度評估
    """
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        # 意圖模式庫
        self.intent_patterns = {
            "refactor": ["重構", "refactor", "restructure", "reorganize", "整理"],
            "analyze": ["分析", "analyze", "examine", "inspect", "檢視"],
            "integrate": ["整合", "integrate", "merge", "combine", "集成"],
            "migrate": ["遷移", "migrate", "move", "transfer", "搬遷"],
            "cleanup": ["清理", "cleanup", "remove", "delete", "刪除"],
            "optimize": ["優化", "optimize", "improve", "enhance", "改進"],
        }
        # 實體類型
        self.entity_types = {
            "path": r"[\w\-./]+(?:\.(?:py|yaml|yml|md|json|ts|js))?",
            "module": r"(?:module|package|library|套件|模組)[\s:：]*[\w\-]+",
            "priority": r"(?:P[0-3]|優先[級度][\s:：]*[高中低])",
            "action": r"(?:create|update|delete|move|rename|建立|更新|刪除|移動|重命名)",
        }
    def understand(self, raw_input: Dict) -> UnderstandingResult:
        """執行多維度理解"""
        text = self._extract_text(raw_input)
        intent = self._identify_intent(text)
        entities = self._extract_entities(text, raw_input)
        constraints = self._extract_constraints(text, raw_input)
        implicit_reqs = self._infer_implicit_requirements(intent, entities, constraints)
        ambiguities = self._detect_ambiguities(text, entities)
        completeness = self._assess_completeness(intent, entities, constraints)
        dimensions = self._multi_dimensional_analysis(raw_input)
        return UnderstandingResult(
            intent=intent,
            entities=entities,
            constraints=constraints,
            implicit_requirements=implicit_reqs,
            ambiguities=ambiguities,
            completeness_score=completeness,
            dimensions=dimensions,
        )
    def _extract_text(self, raw_input: Dict) -> str:
        """從原始輸入提取文本"""
        if isinstance(raw_input, str):
            return raw_input
        if "text" in raw_input:
            return raw_input["text"]
        if "description" in raw_input:
            return raw_input["description"]
        if "query" in raw_input:
            return raw_input["query"]
        return str(raw_input)
    def _identify_intent(self, text: str) -> str:
        """識別用戶意圖"""
        text_lower = text.lower()
        intent_scores = {}
        for intent, patterns in self.intent_patterns.items():
            score = sum(1 for p in patterns if p.lower() in text_lower)
            if score > 0:
                intent_scores[intent] = score
        if not intent_scores:
            return "unknown"
        return max(intent_scores, key=intent_scores.get)
    def _extract_entities(self, text: str, raw_input: Dict) -> List[Dict]:
        """抽取實體"""
        entities = []
        for entity_type, pattern in self.entity_types.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                entities.append(
                    {
                        "type": entity_type,
                        "value": match,
                        "confidence": 0.8,
                    }
                )
        # 從結構化輸入提取
        if isinstance(raw_input, dict):
            if "target" in raw_input:
                entities.append(
                    {"type": "path", "value": raw_input["target"], "confidence": 1.0}
                )
            if "files" in raw_input:
                for f in raw_input["files"]:
                    entities.append({"type": "path", "value": f, "confidence": 1.0})
        return entities
    def _extract_constraints(self, text: str, raw_input: Dict) -> List[str]:
        """提取約束條件"""
        constraints = []
        # 時間約束
        time_patterns = [
            r"(?:before|by|until|在[\s]*之前)[\s]*([^,。]+)",
            r"(?:within|在[\s]*)(\d+[\s]*(?:天|小時|分鐘|days?|hours?))",
        ]
        for pattern in time_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            constraints.extend([f"time_constraint: {m}" for m in matches])
        # 範圍約束
        if "only" in text.lower() or "僅" in text or "只" in text:
            constraints.append("scope_limited")
        # 明確的約束
        if isinstance(raw_input, dict):
            if "constraints" in raw_input:
                constraints.extend(raw_input["constraints"])
            if "exclude" in raw_input:
                constraints.append(f"exclude: {raw_input['exclude']}")
        return constraints
    def _infer_implicit_requirements(
        self, intent: str, entities: List[Dict], constraints: List[str]
    ) -> List[str]:
        """推斷隱含需求"""
        implicit = []
        # 根據意圖推斷
        if intent == "refactor":
            implicit.append("需要保持向後兼容")
            implicit.append("需要更新相關引用")
            implicit.append("需要維護目錄結構一致性")
        if intent == "integrate":
            implicit.append("需要解決潛在衝突")
            implicit.append("需要驗證依賴關係")
        if intent == "cleanup":
            implicit.append("需要備份待刪除內容")
            implicit.append("需要確認無活躍引用")
        # 根據實體推斷
        paths = [e["value"] for e in entities if e["type"] == "path"]
        if any("legacy" in p.lower() for p in paths):
            implicit.append("涉及遺留代碼處理")
        if any("config" in p.lower() for p in paths):
            implicit.append("需要小心處理配置變更")
        return implicit
    def _detect_ambiguities(self, text: str, entities: List[Dict]) -> List[str]:
        """檢測歧義"""
        ambiguities = []
        # 模糊詞檢測
        vague_terms = ["相關", "類似", "等等", "之類", "some", "etc", "related"]
        for term in vague_terms:
            if term in text.lower():
                ambiguities.append(f"模糊術語: '{term}'")
        # 實體歧義
        path_entities = [e for e in entities if e["type"] == "path"]
        for entity in path_entities:
            if "*" in entity["value"] or "?" in entity["value"]:
                ambiguities.append(f"路徑通配符需要確認: {entity['value']}")
        # 缺失關鍵信息
        if len(entities) == 0:
            ambiguities.append("未識別到具體操作目標")
        return ambiguities
    def _assess_completeness(
        self, intent: str, entities: List[Dict], constraints: List[str]
    ) -> float:
        """評估信息完整度"""
        score = 0.0
        max_score = 5.0
        # 有明確意圖
        if intent != "unknown":
            score += 1.0
        # 有目標實體
        if len(entities) > 0:
            score += 1.0
            if len(entities) >= 3:
                score += 0.5
        # 有約束條件
        if len(constraints) > 0:
            score += 0.5
        # 有路徑實體
        if any(e["type"] == "path" for e in entities):
            score += 1.0
        # 有優先級指定
        if any(e["type"] == "priority" for e in entities):
            score += 0.5
        # 有動作指定
        if any(e["type"] == "action" for e in entities):
            score += 0.5
        return min(score / max_score, 1.0)
    def _multi_dimensional_analysis(self, raw_input: Dict) -> Dict[str, Any]:
        """多維度分析"""
        return {
            "scope_dimension": self._analyze_scope(raw_input),
            "complexity_dimension": self._analyze_complexity(raw_input),
            "risk_dimension": self._analyze_risk(raw_input),
            "temporal_dimension": self._analyze_temporal(raw_input),
            "dependency_dimension": self._analyze_dependencies(raw_input),
        }
    def _analyze_scope(self, raw_input: Dict) -> Dict:
        """分析範圍維度"""
        return {
            "breadth": "narrow",  # narrow, moderate, wide
            "depth": "surface",  # surface, moderate, deep
            "coverage": 0.5,
        }
    def _analyze_complexity(self, raw_input: Dict) -> Dict:
        """分析複雜度維度"""
        return {
            "structural": "low",
            "logical": "medium",
            "integration": "low",
        }
    def _analyze_risk(self, raw_input: Dict) -> Dict:
        """分析風險維度"""
        return {
            "breaking_changes": "low",
            "data_loss": "low",
            "rollback_difficulty": "easy",
        }
    def _analyze_temporal(self, raw_input: Dict) -> Dict:
        """分析時間維度"""
        return {
            "urgency": "normal",
            "estimated_duration": "unknown",
        }
    def _analyze_dependencies(self, raw_input: Dict) -> Dict:
        """分析依賴維度"""
        return {
            "internal_deps": [],
            "external_deps": [],
            "blocking_tasks": [],
        }
# ============================================================================
# 推理層 - Reasoning Layer
# ============================================================================
class ReasoningLayer:
    """
    推理層：內部邏輯推理與分析
    功能：
    - 假設生成
    - 證據收集
    - 邏輯推導
    - 結論驗證
    - 備選方案生成
    """
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.reasoning_trace: List[ReasoningStep] = []
    def reason(
        self, understanding: UnderstandingResult, context: Optional[Dict] = None
    ) -> List[ReasoningStep]:
        """執行推理"""
        self.reasoning_trace = []
        # 步驟1: 信息充足性推理
        step1 = self._reason_completeness(understanding)
        self.reasoning_trace.append(step1)
        # 如果信息不足，進行補充推理
        if understanding.completeness_score < 0.6:
            step_infer = self._infer_missing_information(understanding)
            self.reasoning_trace.append(step_infer)
        # 步驟2: 意圖澄清推理
        step2 = self._reason_intent_clarification(understanding)
        self.reasoning_trace.append(step2)
        # 步驟3: 約束分析推理
        step3 = self._reason_constraints(understanding)
        self.reasoning_trace.append(step3)
        # 步驟4: 方案可行性推理
        step4 = self._reason_feasibility(understanding, context)
        self.reasoning_trace.append(step4)
        # 步驟5: 最佳路徑推理
        step5 = self._reason_optimal_path(understanding, context)
        self.reasoning_trace.append(step5)
        return self.reasoning_trace
    def _reason_completeness(self, understanding: UnderstandingResult) -> ReasoningStep:
        """推理信息完整性"""
        hypothesis = "當前輸入信息是否足以做出決策"
        evidence = []
        if understanding.intent != "unknown":
            evidence.append(f"已識別意圖: {understanding.intent}")
        if len(understanding.entities) > 0:
            evidence.append(f"已識別 {len(understanding.entities)} 個實體")
        if len(understanding.ambiguities) > 0:
            evidence.append(f"發現 {len(understanding.ambiguities)} 個歧義點")
        completeness = understanding.completeness_score
        if completeness >= 0.8:
            conclusion = "信息充足，可直接進行決策"
        elif completeness >= 0.5:
            conclusion = "信息基本充足，需要補充部分細節"
        else:
            conclusion = "信息不足，需要額外推理或用戶確認"
        return ReasoningStep(
            step_id=1,
            hypothesis=hypothesis,
            evidence=evidence,
            conclusion=conclusion,
            confidence=completeness,
            alternatives=[],
        )
    def _infer_missing_information(
        self, understanding: UnderstandingResult
    ) -> ReasoningStep:
        """推斷缺失信息"""
        hypothesis = "嘗試推斷缺失的關鍵信息"
        inferences = []
        evidence = []
        # 根據意圖推斷目標
        if understanding.intent == "refactor" and not any(
            e["type"] == "path" for e in understanding.entities
        ):
            inferences.append("基於上下文，目標可能是 docs/refactor_playbooks")
            evidence.append("重構意圖通常針對 playbooks 目錄")
        # 根據隱含需求推斷約束
        for implicit in understanding.implicit_requirements:
            if "兼容" in implicit:
                inferences.append("推斷需要生成遷移計畫")
                evidence.append("向後兼容暗示需要漸進式遷移")
        return ReasoningStep(
            step_id=len(self.reasoning_trace) + 1,
            hypothesis=hypothesis,
            evidence=evidence,
            conclusion=(
                "; ".join(inferences) if inferences else "無法有效推斷，需要更多信息"
            ),
            confidence=0.6 if inferences else 0.3,
            alternatives=["請求用戶提供更多細節"],
        )
    def _reason_intent_clarification(
        self, understanding: UnderstandingResult
    ) -> ReasoningStep:
        """推理意圖澄清"""
        hypothesis = f"用戶意圖 '{understanding.intent}' 的具體含義"
        evidence = [f"識別的意圖: {understanding.intent}"]
        for entity in understanding.entities:
            evidence.append(f"相關實體: {entity['type']}={entity['value']}")
        # 意圖細化
        if understanding.intent == "refactor":
            conclusion = "用戶希望重新組織目錄結構，提高可維護性"
            alternatives = ["可能是重命名", "可能是分割模組", "可能是合併檔案"]
        elif understanding.intent == "integrate":
            conclusion = "用戶希望將分散的資源整合到統一位置"
            alternatives = ["可能是合併內容", "可能是建立引用", "可能是嵌入式整合"]
        else:
            conclusion = f"執行 {understanding.intent} 操作"
            alternatives = []
        return ReasoningStep(
            step_id=len(self.reasoning_trace) + 1,
            hypothesis=hypothesis,
            evidence=evidence,
            conclusion=conclusion,
            confidence=0.75,
            alternatives=alternatives,
        )
    def _reason_constraints(self, understanding: UnderstandingResult) -> ReasoningStep:
        """推理約束條件"""
        hypothesis = "分析並整合所有約束條件"
        evidence = understanding.constraints.copy()
        evidence.extend([f"隱含約束: {r}" for r in understanding.implicit_requirements])
        # 識別衝突
        conflicts = []
        if (
            "scope_limited" in understanding.constraints
            and len(understanding.entities) == 0
        ):
            conflicts.append("範圍限制但未指定具體目標")
        if conflicts:
            conclusion = f"發現 {len(conflicts)} 個約束衝突需要解決"
        else:
            conclusion = f"共 {len(evidence)} 個約束條件，無明顯衝突"
        return ReasoningStep(
            step_id=len(self.reasoning_trace) + 1,
            hypothesis=hypothesis,
            evidence=evidence,
            conclusion=conclusion,
            confidence=0.8 if not conflicts else 0.5,
            alternatives=[f"衝突: {c}" for c in conflicts],
        )
    def _reason_feasibility(
        self, understanding: UnderstandingResult, context: Optional[Dict]
    ) -> ReasoningStep:
        """推理可行性"""
        hypothesis = "評估操作的技術可行性"
        evidence = []
        feasibility_score = 1.0
        # 檢查資源可用性
        if context and "available_resources" in context:
            evidence.append(f"可用資源: {context['available_resources']}")
        else:
            evidence.append("未提供資源上下文，假設資源充足")
        # 檢查風險等級
        risk = understanding.dimensions.get("risk_dimension", {})
        if risk.get("breaking_changes") == "high":
            feasibility_score -= 0.3
            evidence.append("高破壞性變更風險")
        if feasibility_score >= 0.7:
            conclusion = "技術可行，風險可控"
        elif feasibility_score >= 0.4:
            conclusion = "技術可行，但需要額外風險控制"
        else:
            conclusion = "存在重大技術障礙，需要重新評估"
        return ReasoningStep(
            step_id=len(self.reasoning_trace) + 1,
            hypothesis=hypothesis,
            evidence=evidence,
            conclusion=conclusion,
            confidence=feasibility_score,
            alternatives=["分階段執行", "簡化範圍", "尋求替代方案"],
        )
    def _reason_optimal_path(
        self, understanding: UnderstandingResult, context: Optional[Dict]
    ) -> ReasoningStep:
        """推理最佳執行路徑"""
        hypothesis = "確定最優執行策略"
        evidence = []
        paths = []
        # 根據意圖生成路徑
        if understanding.intent == "refactor":
            paths = [
                {"name": "漸進式重構", "phases": 9, "risk": "low"},
                {"name": "一次性重構", "phases": 3, "risk": "medium"},
                {"name": "並行重構", "phases": 6, "risk": "low"},
            ]
            evidence.append("重構操作支持多種策略")
        elif understanding.intent == "integrate":
            paths = [
                {"name": "完全整合", "phases": 3, "risk": "medium"},
                {"name": "嵌入式整合", "phases": 2, "risk": "low"},
                {"name": "引用式整合", "phases": 1, "risk": "low"},
            ]
            evidence.append("整合操作根據內容類型選擇策略")
        # 選擇最優路徑
        if paths:
            optimal = min(
                paths,
                key=lambda p: (
                    {"low": 0, "medium": 1, "high": 2}[p["risk"]],
                    p["phases"],
                ),
            )
            conclusion = f"推薦策略: {optimal['name']} ({optimal['phases']} 階段, {optimal['risk']} 風險)"
        else:
            conclusion = "使用默認執行策略"
            optimal = None
        return ReasoningStep(
            step_id=len(self.reasoning_trace) + 1,
            hypothesis=hypothesis,
            evidence=evidence,
            conclusion=conclusion,
            confidence=0.8 if optimal else 0.5,
            alternatives=[p["name"] for p in paths if p != optimal] if paths else [],
        )
    def get_confidence_level(self) -> ConfidenceLevel:
        """獲取整體信心水平"""
        if not self.reasoning_trace:
            return ConfidenceLevel.INSUFFICIENT
        avg_confidence = sum(s.confidence for s in self.reasoning_trace) / len(
            self.reasoning_trace
        )
        if avg_confidence >= 0.8:
            return ConfidenceLevel.HIGH
        elif avg_confidence >= 0.5:
            return ConfidenceLevel.MEDIUM
        elif avg_confidence >= 0.3:
            return ConfidenceLevel.LOW
        else:
            return ConfidenceLevel.INSUFFICIENT
    def needs_external_search(self) -> bool:
        """判斷是否需要外部搜尋"""
        if self.get_confidence_level() in [
            ConfidenceLevel.LOW,
            ConfidenceLevel.INSUFFICIENT,
        ]:
            return True
        # 檢查是否有未解決的歧義
        for step in self.reasoning_trace:
            if "需要更多信息" in step.conclusion or "無法有效推斷" in step.conclusion:
                return True
        return False
# ============================================================================
# 搜尋層 - Search Layer
# ============================================================================
class SearchLayer:
    """
    搜尋層：利用外部工具/API尋找最新解決方案
    功能：
    - 本地代碼庫搜尋
    - 知識庫查詢
    - 網路搜尋 (模擬)
    - API 調用 (模擬)
    """
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.search_results: List[Dict] = []
    def search(
        self, queries: List[SearchQuery], context: Optional[Dict] = None
    ) -> List[Dict]:
        """執行搜尋"""
        self.search_results = []
        for query in queries:
            if query.query_type == "local":
                results = self._search_local(query, context)
            elif query.query_type == "knowledge_base":
                results = self._search_knowledge_base(query)
            elif query.query_type == "web":
                results = self._search_web(query)
            elif query.query_type == "api":
                results = self._search_api(query)
            else:
                results = []
            self.search_results.extend(results)
        return self.search_results
    def _search_local(self, query: SearchQuery, context: Optional[Dict]) -> List[Dict]:
        """本地代碼庫搜尋"""
        results = []
        # 搜尋目標目錄
        target = context.get("target_path") if context else "."
        target_path = Path(target)
        if not target_path.exists():
            return results
        # 根據查詢文本搜尋檔案
        search_term = query.query_text.lower()
        for file in target_path.rglob("*"):
            if file.is_file():
                if search_term in file.name.lower():
                    results.append(
                        {
                            "source": "local",
                            "type": "file_match",
                            "path": str(file),
                            "relevance": 0.9,
                        }
                    )
                # 內容搜尋 (限制於小檔案)
                if (
                    file.suffix in [".md", ".yaml", ".yml", ".py"]
                    and file.stat().st_size < 100000
                ):
                    try:
                        content = file.read_text(encoding="utf-8")
                        if search_term in content.lower():
                            results.append(
                                {
                                    "source": "local",
                                    "type": "content_match",
                                    "path": str(file),
                                    "relevance": 0.7,
                                }
                            )
                    except BaseException:
                        pass
        return results[: query.max_results]
    def _search_knowledge_base(self, query: SearchQuery) -> List[Dict]:
        """知識庫查詢"""
        # 模擬知識庫查詢
        kb_entries = [
            {
                "topic": "refactor_best_practices",
                "content": "重構最佳實踐：漸進式變更、保持測試覆蓋、更新文檔",
                "relevance": 0.8,
            },
            {
                "topic": "directory_organization",
                "content": "目錄組織原則：功能分組、深度限制、命名一致性",
                "relevance": 0.85,
            },
            {
                "topic": "legacy_migration",
                "content": "遺留代碼遷移：暫存區處理、引用更新、驗證測試",
                "relevance": 0.75,
            },
        ]
        results = []
        search_term = query.query_text.lower()
        for entry in kb_entries:
            if any(term in entry["content"].lower() for term in search_term.split()):
                results.append(
                    {
                        "source": "knowledge_base",
                        "type": "kb_entry",
                        "topic": entry["topic"],
                        "content": entry["content"],
                        "relevance": entry["relevance"],
                    }
                )
        return results[: query.max_results]
    def _search_web(self, query: SearchQuery) -> List[Dict]:
        """網路搜尋 (模擬)"""
        # 在實際實現中，這裡會調用搜尋 API
        return [
            {
                "source": "web",
                "type": "web_result",
                "title": f"搜尋結果: {query.query_text}",
                "url": "https://example.com/result",
                "snippet": "模擬的網路搜尋結果...",
                "relevance": 0.6,
            }
        ]
    def _search_api(self, query: SearchQuery) -> List[Dict]:
        """API 調用 (模擬)"""
        # 在實際實現中，這裡會調用外部 API
        return [
            {
                "source": "api",
                "type": "api_response",
                "endpoint": query.query_text,
                "data": {"status": "simulated"},
                "relevance": 0.5,
            }
        ]
    def generate_queries(
        self, understanding: UnderstandingResult, reasoning: List[ReasoningStep]
    ) -> List[SearchQuery]:
        """根據理解和推理結果生成搜尋查詢"""
        queries = []
        # 根據意圖生成查詢
        if understanding.intent == "refactor":
            queries.append(
                SearchQuery(
                    query_type="knowledge_base",
                    query_text="refactor best practices",
                    filters={},
                )
            )
        # 根據實體生成本地搜尋
        for entity in understanding.entities:
            if entity["type"] == "path":
                queries.append(
                    SearchQuery(
                        query_type="local",
                        query_text=entity["value"],
                        filters={"type": "file"},
                    )
                )
        # 根據歧義生成澄清查詢
        for ambiguity in understanding.ambiguities:
            queries.append(
                SearchQuery(
                    query_type="knowledge_base",
                    query_text=ambiguity,
                    filters={},
                    max_results=3,
                )
            )
        return queries
# ============================================================================
# 整合層 - Integration Layer
# ============================================================================
class IntegrationLayer:
    """
    整合層：綜合所有信息生成最終決策
    功能：
    - 信息綜合
    - 權重計算
    - 風險評估
    - 最終決策生成
    """
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
    def integrate(
        self,
        understanding: UnderstandingResult,
        reasoning: List[ReasoningStep],
        search_results: List[Dict],
    ) -> IntegrationResult:
        """整合所有層的結果"""
        # 綜合理解
        synthesized = self._synthesize_understanding(understanding, search_results)
        # 生成加權建議
        recommendations = self._generate_weighted_recommendations(
            understanding, reasoning, search_results
        )
        # 風險評估
        risk_assessment = self._assess_risks(understanding, reasoning)
        # 信心分解
        confidence_breakdown = self._calculate_confidence_breakdown(
            understanding, reasoning, search_results
        )
        # 最終評分
        final_score = self._calculate_final_score(confidence_breakdown)
        return IntegrationResult(
            synthesized_understanding=synthesized,
            weighted_recommendations=recommendations,
            risk_assessment=risk_assessment,
            confidence_breakdown=confidence_breakdown,
            final_score=final_score,
        )
    def _synthesize_understanding(
        self, understanding: UnderstandingResult, search_results: List[Dict]
    ) -> Dict:
        """綜合理解"""
        return {
            "confirmed_intent": understanding.intent,
            "validated_entities": [
                e for e in understanding.entities if e["confidence"] > 0.7
            ],
            "resolved_ambiguities": self._resolve_ambiguities(
                understanding, search_results
            ),
            "enriched_context": self._enrich_context(understanding, search_results),
        }
    def _resolve_ambiguities(
        self, understanding: UnderstandingResult, search_results: List[Dict]
    ) -> List[Dict]:
        """解決歧義"""
        resolutions = []
        for ambiguity in understanding.ambiguities:
            # 嘗試從搜尋結果中找到解答
            relevant_results = [
                r for r in search_results if ambiguity.lower() in str(r).lower()
            ]
            if relevant_results:
                resolutions.append(
                    {
                        "ambiguity": ambiguity,
                        "resolution": relevant_results[0].get(
                            "content", "已找到相關信息"
                        ),
                        "confidence": 0.7,
                    }
                )
            else:
                resolutions.append(
                    {
                        "ambiguity": ambiguity,
                        "resolution": "未能自動解決，需要用戶確認",
                        "confidence": 0.3,
                    }
                )
        return resolutions
    def _enrich_context(
        self, understanding: UnderstandingResult, search_results: List[Dict]
    ) -> Dict:
        """豐富上下文"""
        enriched = {}
        # 從知識庫結果中提取最佳實踐
        kb_results = [r for r in search_results if r.get("source") == "knowledge_base"]
        if kb_results:
            enriched["best_practices"] = [r.get("content") for r in kb_results]
        # 從本地搜尋中識別相關檔案
        local_results = [r for r in search_results if r.get("source") == "local"]
        if local_results:
            enriched["related_files"] = [r.get("path") for r in local_results]
        return enriched
    def _generate_weighted_recommendations(
        self,
        understanding: UnderstandingResult,
        reasoning: List[ReasoningStep],
        search_results: List[Dict],
    ) -> List[Dict]:
        """生成加權建議"""
        recommendations = []
        # 從推理步驟中提取建議
        for step in reasoning:
            if step.conclusion and "推薦" in step.conclusion:
                recommendations.append(
                    {
                        "source": "reasoning",
                        "recommendation": step.conclusion,
                        "weight": step.confidence,
                        "alternatives": step.alternatives,
                    }
                )
        # 從搜尋結果中提取建議
        for result in search_results:
            if result.get("source") == "knowledge_base":
                recommendations.append(
                    {
                        "source": "knowledge_base",
                        "recommendation": result.get("content", ""),
                        "weight": result.get("relevance", 0.5),
                        "alternatives": [],
                    }
                )
        # 按權重排序
        recommendations.sort(key=lambda r: -r["weight"])
        return recommendations
    def _assess_risks(
        self, understanding: UnderstandingResult, reasoning: List[ReasoningStep]
    ) -> Dict:
        """評估風險"""
        risks = {
            "overall_level": "low",
            "factors": [],
            "mitigations": [],
        }
        # 從維度分析中提取風險
        risk_dim = understanding.dimensions.get("risk_dimension", {})
        if risk_dim.get("breaking_changes") == "high":
            risks["factors"].append("高破壞性變更")
            risks["mitigations"].append("建議分階段執行")
            risks["overall_level"] = "medium"
        if risk_dim.get("data_loss") in ["medium", "high"]:
            risks["factors"].append("潛在數據丟失")
            risks["mitigations"].append("執行前創建完整備份")
            risks["overall_level"] = (
                "medium" if risks["overall_level"] == "low" else "high"
            )
        # 從推理中識別風險
        for step in reasoning:
            if step.confidence < 0.5:
                risks["factors"].append(f"低信心度推理: {step.hypothesis}")
                risks["mitigations"].append("需要額外驗證")
        return risks
    def _calculate_confidence_breakdown(
        self,
        understanding: UnderstandingResult,
        reasoning: List[ReasoningStep],
        search_results: List[Dict],
    ) -> Dict:
        """計算信心度分解"""
        return {
            "understanding_confidence": understanding.completeness_score,
            "reasoning_confidence": (
                sum(s.confidence for s in reasoning) / len(reasoning)
                if reasoning
                else 0.0
            ),
            "search_confidence": (
                sum(r.get("relevance", 0) for r in search_results) / len(search_results)
                if search_results
                else 0.0
            ),
            "overall_weights": {
                "understanding": 0.3,
                "reasoning": 0.4,
                "search": 0.3,
            },
        }
    def _calculate_final_score(self, confidence_breakdown: Dict) -> float:
        """計算最終評分"""
        weights = confidence_breakdown["overall_weights"]
        score = (
            confidence_breakdown["understanding_confidence"] * weights["understanding"]
            + confidence_breakdown["reasoning_confidence"] * weights["reasoning"]
            + confidence_breakdown["search_confidence"] * weights["search"]
        )
        return round(score, 3)
# ============================================================================
# 認知引擎 - Cognitive Engine (主控制器)
# ============================================================================
class CognitiveEngine:
    """
    認知引擎：協調所有認知層的主控制器
    處理流程：
    1. 感知 → 接收原始輸入
    2. 理解 → 多維度解析
    3. 推理 → 邏輯分析
    4. 搜尋 → 外部資源 (如需要)
    5. 再推理 → 整合新信息
    6. 整合 → 生成決策
    7. 輸出 → 返回結果
    """
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.understanding_layer = UnderstandingLayer(config)
        self.reasoning_layer = ReasoningLayer(config)
        self.search_layer = SearchLayer(config)
        self.integration_layer = IntegrationLayer(config)
    def process(
        self, raw_input: Dict, context: Optional[Dict] = None
    ) -> CognitiveContext:
        """執行完整認知處理"""
        # 初始化上下文
        ctx = CognitiveContext(
            session_id=datetime.now().strftime("%Y%m%d_%H%M%S"),
            timestamp=datetime.now().isoformat(),
            raw_input=raw_input,
        )
        print(f"🧠 認知引擎啟動 (Session: {ctx.session_id})")
        # 階段1: 理解
        print("📖 階段1: 多維度理解...")
        understanding = self.understanding_layer.understand(raw_input)
        ctx.understanding = asdict(understanding)
        print(f"   意圖: {understanding.intent}")
        print(f"   完整度: {understanding.completeness_score:.2f}")
        print(f"   歧義: {len(understanding.ambiguities)} 個")
        # 階段2: 初步推理
        print("🔍 階段2: 內部推理...")
        reasoning = self.reasoning_layer.reason(understanding, context)
        ctx.reasoning_trace = [asdict(s) for s in reasoning]
        confidence = self.reasoning_layer.get_confidence_level()
        print(f"   推理步驟: {len(reasoning)}")
        print(f"   信心水平: {confidence.value}")
        # 階段3: 判斷是否需要外部搜尋
        if self.reasoning_layer.needs_external_search():
            print("🔎 階段3: 外部搜尋...")
            queries = self.search_layer.generate_queries(understanding, reasoning)
            search_results = self.search_layer.search(queries, context)
            ctx.search_results = search_results
            print(f"   查詢數: {len(queries)}")
            print(f"   結果數: {len(search_results)}")
            # 階段4: 再推理 (整合搜尋結果)
            print("🔄 階段4: 再推理...")
            # 更新理解
            for result in search_results:
                if (
                    result.get("source") == "local"
                    and result.get("type") == "file_match"
                ):
                    understanding.entities.append(
                        {
                            "type": "discovered_file",
                            "value": result.get("path"),
                            "confidence": result.get("relevance", 0.5),
                        }
                    )
            # 重新推理
            reasoning = self.reasoning_layer.reason(understanding, context)
            ctx.reasoning_trace.extend([asdict(s) for s in reasoning])
        else:
            print("✓ 跳過外部搜尋 (信息充足)")
            ctx.search_results = []
        # 階段5: 整合
        print("🔗 階段5: 信息整合...")
        integration_result = self.integration_layer.integrate(
            understanding, reasoning, ctx.search_results
        )
        ctx.integration_result = asdict(integration_result)
        print(f"   最終評分: {integration_result.final_score:.3f}")
        print(f"   風險等級: {integration_result.risk_assessment['overall_level']}")
        # 階段6: 生成最終決策
        print("📋 階段6: 生成決策...")
        ctx.final_decision = self._generate_final_decision(
            understanding, reasoning, integration_result
        )
        ctx.confidence = integration_result.final_score
        print(f"\n✅ 認知處理完成 (信心度: {ctx.confidence:.3f})")
        return ctx
    def _generate_final_decision(
        self,
        understanding: UnderstandingResult,
        reasoning: List[ReasoningStep],
        integration: IntegrationResult,
    ) -> Dict:
        """生成最終決策"""
        # 確定是否可以自動執行
        can_auto_execute = (
            integration.final_score >= 0.7
            and integration.risk_assessment["overall_level"] != "high"
            and understanding.completeness_score >= 0.6
        )
        # 提取關鍵建議
        top_recommendations = integration.weighted_recommendations[:3]
        # 生成行動計畫
        action_plan = []
        for i, rec in enumerate(top_recommendations, 1):
            action_plan.append(
                {
                    "priority": f"P{i}",
                    "action": rec["recommendation"],
                    "confidence": rec["weight"],
                }
            )
        return {
            "decision_type": "auto" if can_auto_execute else "manual_confirm",
            "primary_intent": understanding.intent,
            "action_plan": action_plan,
            "requires_confirmation": not can_auto_execute,
            "confirmation_points": (
                [amb for amb in understanding.ambiguities]
                if not can_auto_execute
                else []
            ),
            "risk_summary": integration.risk_assessment["overall_level"],
            "mitigations": integration.risk_assessment["mitigations"],
        }
# ============================================================================
# 便捷函數
# ============================================================================
def quick_understand(text: str) -> UnderstandingResult:
    """快速理解文本"""
    layer = UnderstandingLayer()
    return layer.understand({"text": text})
def quick_reason(understanding: UnderstandingResult) -> List[ReasoningStep]:
    """快速推理"""
    layer = ReasoningLayer()
    return layer.reason(understanding)
def full_cognitive_process(
    raw_input: Dict, context: Optional[Dict] = None
) -> CognitiveContext:
    """完整認知處理"""
    engine = CognitiveEngine()
    return engine.process(raw_input, context)
# ============================================================================
# 主程序入口
# ============================================================================
def main():
    """測試認知引擎"""
    import argparse
    parser = argparse.ArgumentParser(description="認知推理引擎")
    parser.add_argument("--input", "-i", required=True, help="輸入文本或 JSON 檔案")
    parser.add_argument("--output", "-o", help="輸出檔案")
    parser.add_argument("--verbose", "-v", action="store_true", help="詳細輸出")
    args = parser.parse_args()
    # 解析輸入
    if args.input.endswith(".json"):
        with open(args.input, "r", encoding="utf-8") as f:
            raw_input = json.load(f)
    elif args.input.endswith(".yaml") or args.input.endswith(".yml"):
        with open(args.input, "r", encoding="utf-8") as f:
            raw_input = yaml.safe_load(f)
    else:
        raw_input = {"text": args.input}
    # 執行認知處理
    engine = CognitiveEngine()
    result = engine.process(raw_input)
    # 輸出結果
    output = {
        "session_id": result.session_id,
        "timestamp": result.timestamp,
        "confidence": result.confidence,
        "understanding": result.understanding,
        "reasoning_steps": len(result.reasoning_trace),
        "search_results": len(result.search_results),
        "final_decision": result.final_decision,
    }
    if args.verbose:
        output["full_reasoning_trace"] = result.reasoning_trace
        output["integration_result"] = result.integration_result
    output_str = yaml.dump(
        output, allow_unicode=True, default_flow_style=False, sort_keys=False
    )
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output_str)
        print(f"\n結果已儲存: {args.output}")
    else:
        print("\n" + "=" * 50)
        print("認知處理結果:")
        print("=" * 50)
        print(output_str)
if __name__ == "__main__":
    main()
