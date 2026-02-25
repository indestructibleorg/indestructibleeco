# @ECO-governed
# @ECO-layer: GL00-09
# @ECO-semantic: general-component
# @ECO-audit-trail: gl-enterprise-architecture/gl-platform.governance/audit-trails/GL00_09-audit.json
#
# GL Unified Architecture Governance Framework Activated
# GL Root Semantic Anchor: gl-enterprise-architecture/gl-platform.governance/ECO-ROOT-SEMANTIC-ANCHOR.yaml
# GL Unified Naming Charter: gl-enterprise-architecture/gl-platform.governance/ECO-UNIFIED-NAMING-CHARTER.yaml


"""
GL 语义折叠引擎核心实现
将语义规范折叠为可计算的多维表示
"""

"""
Module docstring
================

This module is part of the GL governance framework.
Please add specific module documentation here.
"""
# MNGA-002: Import organization needs review
from typing import Dict, List, Any, Optional
import numpy as np
from dataclasses import dataclass
from enum import Enum
import yaml
import json


class FoldingStrategy(Enum):
    """语义折叠策略"""
    VECTOR_FOLDING = "vector-folding"
    GRAPH_FOLDING = "graph-folding"
    HYBRID_FOLDING = "hybrid-folding"
    ADAPTIVE_FOLDING = "adaptive-folding"


class VectorEncodingMethod(Enum):
    """向量编码方法"""
    SEMANTIC_EMBEDDING = "semantic-embedding"
    TRANSFORMER_ENCODER = "transformer-encoder"
    GRAPH_EMBEDDING = "graph-embedding"
    MIXED_ENCODING = "mixed-encoding"


@dataclass
class FoldingConfig:
    """折叠引擎配置"""
    strategy: FoldingStrategy
    vector_dimensions: int = 768
    quantization_level: str = "int8"
    compression_enabled: bool = True
    batch_size: int = 1000
    chunk_size: int = 100
    parallelism: int = 8
    cache_size_gb: int = 10
    
    # 特征提取配置
    feature_extraction: Dict[str, bool] = None
    
    def __post_init__(self):
        if self.feature_extraction is None:
            self.feature_extraction = {
                "semantic_keywords": True,
                "context_window": True,
                "dependency_graph": True,
                "semantic_distance": True
            }


@dataclass
class SemanticNode:
    """语义节点表示"""
    id: str
    domain: str
    capability: str
    resource: Optional[str]
    semantic_key: str
    semantic_value: Optional[str]
    vector_embedding: Optional[np.ndarray]
    graph_properties: Dict[str, Any]
    metadata: Dict[str, Any]
    
    def __hash__(self):
        return hash(self.id)
    
    def to_vector(self) -> np.ndarray:
        """转换为向量表示"""
        if self.vector_embedding is not None:
            return self.vector_embedding
        # 生成语义哈希向量
        return self._generate_semantic_hash()
    
    def _generate_semantic_hash(self) -> np.ndarray:
        """生成语义哈希向量"""
        semantic_string = f"{self.domain}:{self.capability}:{self.resource or ''}:{self.semantic_key}"
        # 简化示例，实际使用语义编码模型
        hash_val = hash(semantic_string)
        return np.array([(hash_val >> i) & 1 for i in range(64)] * 12, dtype=np.float32)


@dataclass
class FoldedSemantics:
    """折叠后的语义表示"""
    nodes: List[SemanticNode]
    adjacency_matrix: np.ndarray
    vector_space: np.ndarray
    metadata: Dict[str, Any]
    
    @property
    def node_count(self) -> int:
        return len(self.nodes)
    
    @property
    def vector_dimensions(self) -> int:
        return self.vector_space.shape[1] if len(self.vector_space.shape) > 1 else 0
    
    def get_node_by_id(self, node_id: str) -> Optional[SemanticNode]:
        for node in self.nodes:
            if node.id == node_id:
                return node
        return None
    
    def get_similar_nodes(self, query_vector: np.ndarray, top_k: int = 10) -> List[Dict]:
        """查找相似节点"""
        if len(self.vector_space) == 0:
            return []
        
        # 计算余弦相似度
        similarities = self._cosine_similarity(query_vector, self.vector_space)
        top_indices = np.argsort(similarities)[-top_k:][::-1]
        
        results = []
        for idx in top_indices:
            results.append({
                "node": self.nodes[idx],
                "similarity": float(similarities[idx]),
                "rank": len(results) + 1
            })
        
        return results
    
    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> np.ndarray:
        """计算余弦相似度"""
        a_norm = np.linalg.norm(a)
        b_norm = np.linalg.norm(b, axis=1)
        dot_products = np.dot(b, a)
        return dot_products / (a_norm * b_norm + 1e-8)


class SemanticFoldingEngine:
    """语义折叠引擎"""
    
    def __init__(self, config: FoldingConfig):
        self.config = config
        self.vector_encoder = None
        self.graph_builder = None
        self.cache = {}
        
        # 初始化组件
        self._initialize_components()
    
    def _initialize_components(self):
        """初始化引擎组件"""
        if self.config.strategy in [FoldingStrategy.VECTOR_FOLDING, FoldingStrategy.HYBRID_FOLDING]:
            self.vector_encoder = self._create_vector_encoder()
        
        if self.config.strategy in [FoldingStrategy.GRAPH_FOLDING, FoldingStrategy.HYBRID_FOLDING]:
            self.graph_builder = self._create_graph_builder()
    
    def _create_vector_encoder(self):
        """创建向量编码器"""
        # 实际实现会加载预训练模型
        print(f"创建向量编码器: 维度={self.config.vector_dimensions}")
        return None  # 简化示例
    
    def _create_graph_builder(self):
        """创建图构建器"""
        print(f"创建图构建器: 压缩={self.config.compression_enabled}")
        return None  # 简化示例
    
    def fold_specification(self, spec_data: Dict[str, Any]) -> FoldedSemantics:
        """
        折叠语义规范
        
        Args:
            spec_data: 语义规范数据，来自 UnificationSpecification
            
        Returns:
            FoldedSemantics: 折叠后的语义表示
        """
        # 1. 解析语义节点
        nodes = self._parse_semantic_nodes(spec_data)
        
        # 2. 根据策略进行折叠
        if self.config.strategy == FoldingStrategy.VECTOR_FOLDING:
            return self._fold_vector_strategy(nodes)
        elif self.config.strategy == FoldingStrategy.GRAPH_FOLDING:
            return self._fold_graph_strategy(nodes)
        elif self.config.strategy == FoldingStrategy.HYBRID_FOLDING:
            return self._fold_hybrid_strategy(nodes)
        else:
            return self._fold_adaptive_strategy(nodes)
    
    def _parse_semantic_nodes(self, spec_data: Dict[str, Any]) -> List[SemanticNode]:
        """解析语义节点"""
        nodes = []
        
        # 从语义分类中解析
        semantic_taxonomy = spec_data.get("spec", {}).get("semantic-taxonomy", {})
        
        # 解析领域
        for domain_data in semantic_taxonomy.get("domains", []):
            domain_id = domain_data.get("domain_id")
            
            # 创建领域节点
            domain_node = SemanticNode(
                id=f"domain:{domain_id}",
                domain=domain_id,
                capability="",
                resource=None,
                semantic_key="domain",
                semantic_value=domain_id,
                vector_embedding=None,
                graph_properties={
                    "type": "domain",
                    "abbreviation": domain_data.get("abbr", ""),
                    "description": domain_data.get("description", "")
                },
                metadata=domain_data
            )
            nodes.append(domain_node)
            
            # 解析能力
            capability_data = semantic_taxonomy.get("capabilities", [])
            for cap in capability_data:
                if cap.get("domain") == domain_id:
                    cap_id = cap.get("capability_id")
                    
                    cap_node = SemanticNode(
                        id=f"domain:{domain_id}:capability:{cap_id}",
                        domain=domain_id,
                        capability=cap_id,
                        resource=None,
                        semantic_key="capability",
                        semantic_value=cap_id,
                        vector_embedding=None,
                        graph_properties={
                            "type": "capability",
                            "abbreviation": cap.get("abbr", ""),
                            "description": cap.get("description", "")
                        },
                        metadata=cap
                    )
                    nodes.append(cap_node)
        
        return nodes
    
    def _fold_vector_strategy(self, nodes: List[SemanticNode]) -> FoldedSemantics:
        """向量折叠策略"""
        print(f"执行向量折叠策略: {len(nodes)} 个节点")
        
        # 生成向量表示
        vector_space = []
        for node in nodes:
            vector = node.to_vector()
            vector_space.append(vector)
            node.vector_embedding = vector
        
        vector_space_np = np.array(vector_space, dtype=np.float32)
        
        # 构建邻接矩阵（基于语义相似度）
        adjacency_matrix = self._build_semantic_adjacency(vector_space_np)
        
        return FoldedSemantics(
            nodes=nodes,
            adjacency_matrix=adjacency_matrix,
            vector_space=vector_space_np,
            metadata={
                "folding_strategy": "vector",
                "node_count": len(nodes),
                "vector_dimensions": vector_space_np.shape[1],
                "compression_ratio": self._calculate_compression_ratio(nodes, vector_space_np)
            }
        )
    
    def _fold_graph_strategy(self, nodes: List[SemanticNode]) -> FoldedSemantics:
        """图折叠策略"""
        print(f"执行图折叠策略: {len(nodes)} 个节点")
        
        # 简化的图折叠实现
        vector_space = np.array([node.to_vector() for node in nodes], dtype=np.float32)
        adjacency_matrix = self._build_semantic_adjacency(vector_space)
        
        return FoldedSemantics(
            nodes=nodes,
            adjacency_matrix=adjacency_matrix,
            vector_space=vector_space,
            metadata={
                "folding_strategy": "graph",
                "node_count": len(nodes),
                "graph_edges": int(adjacency_matrix.sum() / 2)
            }
        )
    
    def _fold_hybrid_strategy(self, nodes: List[SemanticNode]) -> FoldedSemantics:
        """混合折叠策略"""
        print(f"执行混合折叠策略: {len(nodes)} 个节点")
        
        # 向量折叠
        vector_folded = self._fold_vector_strategy(nodes)
        
        # 图折叠
        graph_folded = self._fold_graph_strategy(nodes)
        
        # 融合两种表示
        fused_vector_space = self._fuse_representations(
            vector_folded.vector_space,
            graph_folded.vector_space
        )
        
        # 融合邻接矩阵
        fused_adjacency = self._fuse_adjacency_matrices(
            vector_folded.adjacency_matrix,
            graph_folded.adjacency_matrix
        )
        
        return FoldedSemantics(
            nodes=nodes,
            adjacency_matrix=fused_adjacency,
            vector_space=fused_vector_space,
            metadata={
                "folding_strategy": "hybrid",
                "node_count": len(nodes),
                "vector_dimensions": fused_vector_space.shape[1],
                "fusion_method": "concatenation"
            }
        )
    
    def _fold_adaptive_strategy(self, nodes: List[SemanticNode]) -> FoldedSemantics:
        """自适应折叠策略"""
        print(f"执行自适应折叠策略: {len(nodes)} 个节点")
        
        # 分析数据特征
        data_characteristics = self._analyze_data_characteristics(nodes)
        
        # 根据特征选择最佳策略
        if data_characteristics["semantic_density"] > 0.8:
            print("  选择图折叠策略（高语义密度）")
            return self._fold_graph_strategy(nodes)
        elif data_characteristics["feature_variety"] > 5:
            print("  选择混合折叠策略（高特征多样性）")
            return self._fold_hybrid_strategy(nodes)
        else:
            print("  选择向量折叠策略（标准场景）")
            return self._fold_vector_strategy(nodes)
    
    def _build_semantic_adjacency(self, vectors: np.ndarray, threshold: float = 0.7) -> np.ndarray:
        """基于语义相似度构建邻接矩阵"""
        n = len(vectors)
        adjacency = np.zeros((n, n), dtype=np.float32)
        
        for i in range(n):
            for j in range(i+1, n):
                similarity = self._cosine_similarity_single(vectors[i], vectors[j])
                if similarity >= threshold:
                    adjacency[i, j] = similarity
                    adjacency[j, i] = similarity
        
        return adjacency
    
    def _cosine_similarity_single(self, a: np.ndarray, b: np.ndarray) -> float:
        """计算单个向量对的余弦相似度"""
        dot_product = np.dot(a, b)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        return dot_product / (norm_a * norm_b + 1e-8)
    
    def _fuse_representations(self, vectors1: np.ndarray, vectors2: np.ndarray) -> np.ndarray:
        """融合两种向量表示"""
        # 简单的拼接融合
        return np.concatenate([vectors1, vectors2], axis=1)
    
    def _fuse_adjacency_matrices(self, adj1: np.ndarray, adj2: np.ndarray) -> np.ndarray:
        """融合邻接矩阵"""
        # 取最大值融合
        return np.maximum(adj1, adj2)
    
    def _analyze_data_characteristics(self, nodes: List[SemanticNode]) -> Dict[str, float]:
        """分析数据特征"""
        total_nodes = len(nodes)
        
        # 计算语义密度（简化）
        semantic_density = 0.5
        
        # 计算特征多样性
        feature_variety = len(set(
            node.semantic_key for node in nodes
        ))
        
        return {
            "semantic_density": semantic_density,
            "feature_variety": float(feature_variety),
            "average_node_complexity": 5.0
        }
    
    def _calculate_compression_ratio(self, nodes: List[SemanticNode], vectors: np.ndarray) -> float:
        """计算压缩比"""
        # 估算原始大小
        original_size = sum(
            len(json.dumps(node.metadata, ensure_ascii=False).encode('utf-8'))
            for node in nodes
        )
        
        # 估算压缩后大小
        compressed_size = vectors.nbytes
        
        return original_size / (compressed_size + 1e-8)
    
    def save_folded_semantics(self, folded: FoldedSemantics, output_path: str):
        """保存折叠后的语义表示"""
        # 序列化数据
        serializable_data = {
            "metadata": folded.metadata,
            "node_count": folded.node_count,
            "vector_dimensions": folded.vector_dimensions,
            "nodes": [
                {
                    "id": node.id,
                    "domain": node.domain,
                    "capability": node.capability,
                    "resource": node.resource,
                    "semantic_key": node.semantic_key,
                    "semantic_value": node.semantic_value,
                    "graph_properties": node.graph_properties,
                    "metadata": node.metadata
                }
                for node in folded.nodes
            ],
            "vector_space_shape": folded.vector_space.shape,
            "adjacency_matrix_shape": folded.adjacency_matrix.shape
        }
        
        # 保存为 JSON
        with open(f"{output_path}.json", 'w', encoding='utf-8') as f:
            json.dump(serializable_data, f, ensure_ascii=False, indent=2)
        
        # 保存向量空间和邻接矩阵为 NPY 文件
        np.save(f"{output_path}_vectors.npy", folded.vector_space)
        np.save(f"{output_path}_adjacency.npy", folded.adjacency_matrix)
        
        print(f"已保存折叠语义到: {output_path}")
    
    def load_folded_semantics(self, input_path: str) -> FoldedSemantics:
        """加载折叠后的语义表示"""
        # 加载元数据和节点
        with open(f"{input_path}.json", 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 加载向量空间和邻接矩阵
        vectors = np.load(f"{input_path}_vectors.npy")
        adjacency = np.load(f"{input_path}_adjacency.npy")
        
        # 重建节点对象
        nodes = []
        for node_data in data["nodes"]:
            node = SemanticNode(
                id=node_data["id"],
                domain=node_data["domain"],
                capability=node_data["capability"],
                resource=node_data["resource"],
                semantic_key=node_data["semantic_key"],
                semantic_value=node_data["semantic_value"],
                vector_embedding=None,
                graph_properties=node_data["graph_properties"],
                metadata=node_data["metadata"]
            )
            nodes.append(node)
        
        return FoldedSemantics(
            nodes=nodes,
            adjacency_matrix=adjacency,
            vector_space=vectors,
            metadata=data["metadata"]
        )


def main():
    """主函数 - 示例用法"""
    import sys
    
    # 创建配置
    config = FoldingConfig(
        strategy=FoldingStrategy.ADAPTIVE_FOLDING,
        vector_dimensions=768,
        compression_enabled=True
    )
    
    # 创建引擎
    engine = SemanticFoldingEngine(config)
    
    # 示例语义规范数据
    spec_data = {
        "spec": {
            "semantic-taxonomy": {
                "domains": [
                    {
                        "domain_id": "runtime",
                        "abbr": "rt",
                        "description": "运行时环境"
                    },
                    {
                        "domain_id": "api",
                        "abbr": "api",
                        "description": "API 接口"
                    }
                ],
                "capabilities": [
                    {
                        "domain": "runtime",
                        "capability_id": "dag",
                        "abbr": "dag",
                        "description": "DAG 执行引擎"
                    },
                    {
                        "domain": "api",
                        "capability_id": "schema",
                        "abbr": "sch",
                        "description": "Schema 定义"
                    }
                ]
            }
        }
    }
    
    # 执行语义折叠
    print("开始语义折叠...")
    folded = engine.fold_specification(spec_data)
    
    print(f"折叠完成:")
    print(f"  节点数: {folded.node_count}")
    print(f"  向量维度: {folded.vector_dimensions}")
    print(f"  压缩比: {folded.metadata.get('compression_ratio', 'N/A'):.2f}")
    
    # 保存结果
    output_path = "folded_semantics"
    engine.save_folded_semantics(folded, output_path)
    
    print("\n完成！")


if __name__ == "__main__":
    main()