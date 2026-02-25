# @ECO-governed
# @ECO-layer: GL00-09
# @ECO-semantic: test
# @ECO-audit-trail: gl-enterprise-architecture/gl-platform.governance/audit-trails/GL00_09-audit.json
#
# GL Unified Architecture Governance Framework Activated
# GL Root Semantic Anchor: gl-enterprise-architecture/gl-platform.governance/ECO-ROOT-SEMANTIC-ANCHOR.yaml
# GL Unified Naming Charter: gl-enterprise-architecture/gl-platform.governance/ECO-UNIFIED-NAMING-CHARTER.yaml


"""
GL 语义折叠引擎单元测试
"""

"""
Module docstring
================

This module is part of the GL governance framework.
Please add specific module documentation here.
"""
# MNGA-002: Import organization needs review
import pytest
import numpy as np
from unittest.mock import Mock, patch
from pathlib import Path
import tempfile
import json
import sys

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from semantic_folding.engine import (
    SemanticFoldingEngine,
    FoldingConfig,
    FoldingStrategy,
    SemanticNode,
    FoldedSemantics
)


class TestSemanticFoldingEngine:
    
    def setup_method(self):
        """测试设置"""
        self.config = FoldingConfig(
            strategy=FoldingStrategy.VECTOR_FOLDING,
            vector_dimensions=64,
            compression_enabled=False
        )
        self.engine = SemanticFoldingEngine(self.config)
        
        # 创建测试节点
        self.test_nodes = [
            SemanticNode(
                id="domain:runtime:capability:dag",
                domain="runtime",
                capability="dag",
                resource=None,
                semantic_key="domain_capability",
                semantic_value="runtime.dag",
                vector_embedding=None,
                graph_properties={"type": "domain_capability"},
                metadata={"description": "运行时DAG平台"}
            ),
            SemanticNode(
                id="domain:runtime:capability:dag:resource:executor",
                domain="runtime",
                capability="dag",
                resource="executor",
                semantic_key="resource",
                semantic_value="executor",
                vector_embedding=None,
                graph_properties={"type": "resource"},
                metadata={"description": "DAG执行器"}
            )
        ]
    
    def test_engine_initialization(self):
        """测试引擎初始化"""
        assert self.engine.config.strategy == FoldingStrategy.VECTOR_FOLDING
        assert self.engine.config.vector_dimensions == 64
        assert self.engine.config.compression_enabled == False
    
    def test_fold_vector_strategy(self):
        """测试向量折叠策略"""
        folded = self.engine._fold_vector_strategy(self.test_nodes)
        
        assert isinstance(folded, FoldedSemantics)
        assert folded.node_count == 2
        assert folded.vector_dimensions == 64
        assert folded.adjacency_matrix.shape == (2, 2)
        assert folded.metadata["folding_strategy"] == "vector"
    
    def test_fold_graph_strategy(self):
        """测试图折叠策略"""
        graph_config = FoldingConfig(strategy=FoldingStrategy.GRAPH_FOLDING)
        graph_engine = SemanticFoldingEngine(graph_config)
        
        folded = graph_engine._fold_graph_strategy(self.test_nodes)
        
        assert isinstance(folded, FoldedSemantics)
        assert folded.node_count == 2
        assert folded.metadata["folding_strategy"] == "graph"
    
    def test_fold_hybrid_strategy(self):
        """测试混合折叠策略"""
        hybrid_config = FoldingConfig(strategy=FoldingStrategy.HYBRID_FOLDING)
        hybrid_engine = SemanticFoldingEngine(hybrid_config)
        
        folded = hybrid_engine._fold_hybrid_strategy(self.test_nodes)
        
        assert isinstance(folded, FoldedSemantics)
        assert folded.node_count == 2
        assert folded.vector_dimensions == 128  # 64 + 64
        assert folded.metadata["folding_strategy"] == "hybrid"
    
    def test_fold_adaptive_strategy(self):
        """测试自适应折叠策略"""
        adaptive_config = FoldingConfig(strategy=FoldingStrategy.ADAPTIVE_FOLDING)
        adaptive_engine = SemanticFoldingEngine(adaptive_config)
        
        folded = adaptive_engine._fold_adaptive_strategy(self.test_nodes)
        
        assert isinstance(folded, FoldedSemantics)
        assert folded.node_count == 2
        assert folded.metadata["folding_strategy"] in ["vector", "graph", "hybrid"]
    
    def test_similar_nodes_search(self):
        """测试相似节点搜索"""
        nodes = self.test_nodes
        vector_space = np.array([
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
        ])
        
        folded = FoldedSemantics(
            nodes=nodes,
            adjacency_matrix=np.zeros((2, 2)),
            vector_space=vector_space,
            metadata={}
        )
        
        query_vector = np.array([1.0, 0.0, 0.0])
        results = folded.get_similar_nodes(query_vector, top_k=2)
        
        assert len(results) == 2
        assert results[0]["node"].id == "domain:runtime:capability:dag"
        assert results[0]["similarity"] == 1.0
        assert results[1]["similarity"] == 0.0
    
    def test_save_and_load_folded_semantics(self):
        """测试保存和加载折叠语义"""
        with tempfile.TemporaryDirectory() as tmpdir:
            folded = FoldedSemantics(
                nodes=self.test_nodes,
                adjacency_matrix=np.array([[0, 0.5], [0.5, 0]]),
                vector_space=np.random.randn(2, 64),
                metadata={"test": True}
            )
            
            output_path = Path(tmpdir) / "test_folded"
            self.engine.save_folded_semantics(folded, str(output_path))
            
            assert output_path.with_suffix(".json").exists()
            assert output_path.with_name("test_folded_vectors.npy").exists()
            assert output_path.with_name("test_folded_adjacency.npy").exists()
            
            loaded = self.engine.load_folded_semantics(str(output_path))
            
            assert loaded.node_count == folded.node_count
            assert loaded.vector_dimensions == folded.vector_dimensions
            assert loaded.metadata["test"] == True
    
    def test_parse_semantic_nodes(self):
        """测试解析语义节点"""
        spec_data = {
            "spec": {
                "semantic-taxonomy": {
                    "domains": [
                        {
                            "domain_id": "runtime",
                            "abbr": "rt",
                            "description": "运行时"
                        }
                    ],
                    "capabilities": [
                        {
                            "domain": "runtime",
                            "capability_id": "dag",
                            "abbr": "dag",
                            "description": "DAG引擎"
                        }
                    ]
                }
            }
        }
        
        nodes = self.engine._parse_semantic_nodes(spec_data)
        
        # 应该解析出 2 个节点：1 个 domain，1 个 capability
        assert len(nodes) == 2
        assert nodes[0].domain == "runtime"
        assert nodes[1].domain == "runtime"
        assert nodes[1].capability == "dag"
    
    def test_cosine_similarity_calculation(self):
        """测试余弦相似度计算"""
        # 测试相同向量
        vector1 = np.array([1.0, 0.0, 0.0])
        vector2 = np.array([1.0, 0.0, 0.0])
        similarity = self.engine._cosine_similarity_single(vector1, vector2)
        assert abs(similarity - 1.0) < 1e-6
        
        # 测试正交向量
        vector1 = np.array([1.0, 0.0, 0.0])
        vector2 = np.array([0.0, 1.0, 0.0])
        similarity = self.engine._cosine_similarity_single(vector1, vector2)
        assert abs(similarity - 0.0) < 1e-6


class TestFoldedSemantics:
    
    def setup_method(self):
        """测试设置"""
        self.nodes = [
            SemanticNode(
                id="node1",
                domain="runtime",
                capability="dag",
                resource=None,
                semantic_key="domain_capability",
                semantic_value="runtime.dag",
                vector_embedding=np.array([1.0, 0.0, 0.0]),
                graph_properties={},
                metadata={}
            ),
            SemanticNode(
                id="node2",
                domain="api",
                capability="schema",
                resource=None,
                semantic_key="domain_capability",
                semantic_value="api.schema",
                vector_embedding=np.array([0.0, 1.0, 0.0]),
                graph_properties={},
                metadata={}
            )
        ]
        
        self.folded = FoldedSemantics(
            nodes=self.nodes,
            adjacency_matrix=np.array([[0, 0.5], [0.5, 0]]),
            vector_space=np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]]),
            metadata={"test": True}
        )
    
    def test_properties(self):
        """测试属性"""
        assert self.folded.node_count == 2
        assert self.folded.vector_dimensions == 3
    
    def test_get_node_by_id(self):
        """测试通过ID获取节点"""
        node = self.folded.get_node_by_id("node1")
        assert node is not None
        assert node.id == "node1"
        assert node.domain == "runtime"
        
        node = self.folded.get_node_by_id("nonexistent")
        assert node is None
    
    def test_get_similar_nodes(self):
        """测试获取相似节点"""
        query_vector = np.array([1.0, 0.0, 0.0])
        results = self.folded.get_similar_nodes(query_vector, top_k=2)
        
        assert len(results) == 2
        assert results[0]["node"].id == "node1"
        assert results[0]["similarity"] == 1.0
        assert results[0]["rank"] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])