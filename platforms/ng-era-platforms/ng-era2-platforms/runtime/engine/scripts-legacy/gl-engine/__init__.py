#
# @ECO-governed
# @ECO-layer: gl-platform.gl-platform.governance
# @ECO-semantic: __init__
# @ECO-audit-trail: ../../engine/gl-platform.gl-platform.governance/GL_SEMANTIC_ANCHOR.json
#
"""
GL Engine - Governance Layer Execution Engine
MachineNativeOps GL Architecture Implementation
This package provides the core components for GL gl-platform.gl-platform.governance operations:
- gl_executor: Main execution engine for GL commands
- gl_validator: Comprehensive artifact validation
- gl_reporter: Report generation and dashboards
"""
from pathlib import Path
__version__ = "2.0.0"
__author__ = "MachineNativeOps Team"
# Package metadata
PACKAGE_NAME = "gl-engine"
PACKAGE_DESCRIPTION = "Governance Layer Execution Engine for MachineNativeOps"
# GL Layer definitions
GL_LAYERS = {
    "GL00-09": {
        "name": "Strategic Layer",
        "name_zh": "戰略層",
        "description": "組織願景、長期目標、治理框架、核心政策與最高層級決策制定"
    },
    "GL10-29": {
        "name": "Operational Layer", 
        "name_zh": "運營層",
        "description": "治理政策落地、組織運作、資源調度、流程管理與日常監控"
    },
    "GL30-49": {
        "name": "Execution Layer",
        "name_zh": "執行層",
        "description": "具體任務、專案、產品開發、部署與交付"
    },
    "GL50-59": {
        "name": "Observability Layer",
        "name_zh": "觀測層",
        "description": "即時監控、數據收集、異常偵測、審計與合規追蹤"
    },
    "GL60-80": {
        "name": "Advanced/Feedback Layer",
        "name_zh": "進階/回饋層",
        "description": "高階分析、智能優化、回饋機制、A/B測試、模型再訓練"
    },
    "GL81-83": {
        "name": "Extended Layer",
        "name_zh": "擴展層",
        "description": "新興議題、跨域協作、臨時專案、外部合作、社群治理"
    },
    "GL90-99": {
        "name": "Meta-Specification Layer",
        "name_zh": "元規範層",
        "description": "治理體系的元規範、標準制定、規格管理、治理流程定義"
    }
}
# Default paths
DEFAULT_GOVERNANCE_PATH = "workspace/gl-platform.gl-platform.governance"
DEFAULT_REPORTS_PATH = "reports/gl-gl-platform.gl-platform.governance"
DEFAULT_TEMPLATES_PATH = "workspace/gl-platform.gl-platform.governance/meta-spec/ECO-ARTIFACTS-TEMPLATES.yaml"
def get_version() -> str:
    """Get package version."""
    return __version__
def get_layer_info(layer_id: str) -> dict:
    """Get information about a GL layer."""
    return GL_LAYERS.get(layer_id, {})
def list_layers() -> list:
    """List all GL layers."""
    return list(GL_LAYERS.keys())