# @ECO-governed
# @ECO-layer: GL00-09
# @ECO-semantic: general-component
# @ECO-audit-trail: gl-enterprise-architecture/gl-platform.governance/audit-trails/GL00_09-audit.json
#
# GL Unified Architecture Governance Framework Activated
# GL Root Semantic Anchor: gl-enterprise-architecture/gl-platform.governance/ECO-ROOT-SEMANTIC-ANCHOR.yaml
# GL Unified Naming Charter: gl-enterprise-architecture/gl-platform.governance/ECO-UNIFIED-NAMING-CHARTER.yaml


#!/usr/bin/env python3
"""
GL 语义折叠引擎基准测试脚本
"""

"""
Module docstring
================

This module is part of the GL governance framework.
Please add specific module documentation here.
"""
# MNGA-002: Import organization needs review
import asyncio
import time
import json
import numpy as np
from dataclasses import dataclass
from typing import Dict, List, Any
import argparse
from pathlib import Path
import sys

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from semantic_folding.engine import (
    SemanticFoldingEngine,
    FoldingConfig,
    FoldingStrategy
)


@dataclass
class BenchmarkResult:
    """基准测试结果"""
    strategy: FoldingStrategy
    dataset_size: int
    vector_dimensions: int
    folding_time_ms: float
    memory_usage_mb: float
    compression_ratio: float
    query_latency_ms: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "strategy": self.strategy.value,
            "dataset_size": self.dataset_size,
            "vector_dimensions": self.vector_dimensions,
            "folding_time_ms": round(self.folding_time_ms, 2),
            "memory_usage_mb": round(self.memory_usage_mb, 2),
            "compression_ratio": round(self.compression_ratio, 3),
            "query_latency_ms": round(self.query_latency_ms, 2)
        }


class SemanticFoldingBenchmark:
    """语义折叠基准测试套件"""
    
    def __init__(self, output_dir: str = "./benchmark_results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.results: List[BenchmarkResult] = []
    
    def generate_test_dataset(self, size: int) -> List[Dict[str, Any]]:
        """生成测试数据集"""
        dataset = []
        
        for i in range(size):
            domain = f"domain_{i % 10}"
            capability = f"capability_{i % 5}"
            resource = f"resource_{i % 20}" if i % 3 == 0 else None
            
            node_data = {
                "id": f"{domain}:{capability}:{resource or ''}",
                "domain": domain,
                "capability": capability,
                "resource": resource,
                "semantic_key": f"key_{i % 15}",
                "semantic_value": f"value_{i % 25}",
                "metadata": {
                    "description": f"测试节点 {i}",
                    "type": ["domain", "capability", "resource"][i % 3],
                    "complexity": i % 10
                }
            }
            dataset.append(node_data)
        
        return dataset
    
    def run_benchmark(self, strategy: FoldingStrategy, 
                     dataset_size: int, 
                     vector_dimensions: int) -> BenchmarkResult:
        """运行基准测试"""
        print(f"运行基准测试: strategy={strategy.value}, size={dataset_size}, dim={vector_dimensions}")
        
        # 生成测试数据
        spec_data = {
            "spec": {
                "semantic-taxonomy": {
                    "domains": [
                        {"domain_id": f"domain_{i}", "abbr": f"d{i}", "description": f"Domain {i}"}
                        for i in range(min(10, dataset_size))
                    ],
                    "capabilities": [
                        {"domain": "domain_0", "capability_id": f"capability_{i}", "abbr": f"c{i}", "description": f"Capability {i}"}
                        for i in range(min(5, dataset_size))
                    ]
                }
            }
        }
        
        # 创建配置
        config = FoldingConfig(
            strategy=strategy,
            vector_dimensions=vector_dimensions,
            compression_enabled=True,
            batch_size=min(1000, dataset_size)
        )
        
        # 创建引擎
        engine = SemanticFoldingEngine(config)
        
        # 执行折叠并计时
        start_time = time.perf_counter()
        folded = engine.fold_specification(spec_data)
        end_time = time.perf_counter()
        
        folding_time_ms = (end_time - start_time) * 1000
        
        # 计算压缩比
        original_size = len(json.dumps(spec_data, ensure_ascii=False).encode('utf-8'))
        compressed_size = folded.vector_space.nbytes + folded.adjacency_matrix.nbytes
        compression_ratio = original_size / compressed_size if compressed_size > 0 else 0
        
        # 测量查询性能
        query_latency_ms = self.measure_query_performance(folded)
        
        result = BenchmarkResult(
            strategy=strategy,
            dataset_size=dataset_size,
            vector_dimensions=vector_dimensions,
            folding_time_ms=folding_time_ms,
            memory_usage_mb=folded.vector_space.nbytes / 1024 / 1024,
            compression_ratio=compression_ratio,
            query_latency_ms=query_latency_ms
        )
        
        return result
    
    def measure_query_performance(self, folded, num_queries: int = 100) -> float:
        """测量查询性能"""
        query_times = []
        
        query_vectors = [
            np.random.randn(folded.vector_dimensions)
            for _ in range(num_queries)
        ]
        
        for query_vector in query_vectors:
            start_time = time.perf_counter()
            _ = folded.get_similar_nodes(query_vector, top_k=10)
            end_time = time.perf_counter()
            
            query_time_ms = (end_time - start_time) * 1000
            query_times.append(query_time_ms)
        
        return np.mean(query_times)
    
    def run_all_benchmarks(self):
        """运行所有基准测试"""
        dataset_sizes = [10, 50, 100, 500]
        vector_dimensions = [64, 128, 256]
        strategies = [
            FoldingStrategy.VECTOR_FOLDING,
            FoldingStrategy.GRAPH_FOLDING,
            FoldingStrategy.HYBRID_FOLDING
        ]
        
        for strategy in strategies:
            for size in dataset_sizes:
                for dim in vector_dimensions:
                    result = self.run_benchmark(strategy, size, dim)
                    self.results.append(result)
    
    def save_results(self):
        """保存基准测试结果"""
        results_dict = [r.to_dict() for r in self.results]
        
        output_file = self.output_dir / "benchmark_results.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results_dict, f, ensure_ascii=False, indent=2)
        
        print(f"结果已保存到: {output_file}")
        return output_file
    
    def generate_report(self):
        """生成基准测试报告"""
        if not self.results:
            print("没有可用的结果数据")
            return
        
        results_dict = [r.to_dict() for r in self.results]
        
        report_lines = []
        report_lines.append("# GL 语义折叠引擎基准测试报告")
        report_lines.append("")
        report_lines.append(f"生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append(f"总测试数量: {len(self.results)}")
        report_lines.append("")
        
        # 最佳性能统计
        report_lines.append("## 最佳性能统计")
        report_lines.append("")
        
        best_folding = min(self.results, key=lambda x: x.folding_time_ms)
        report_lines.append(f"**最佳折叠时间**: {best_folding.strategy.value} "
                          f"(数据集大小={best_folding.dataset_size}, "
                          f"维度={best_folding.vector_dimensions}): "
                          f"{best_folding.folding_time_ms:.2f} ms")
        
        best_compression = max(self.results, key=lambda x: x.compression_ratio)
        report_lines.append(f"**最佳压缩比**: {best_compression.strategy.value} "
                          f"(数据集大小={best_compression.dataset_size}, "
                          f"维度={best_compression.vector_dimensions}): "
                          f"{best_compression.compression_ratio:.2f}:1")
        
        best_query = min(self.results, key=lambda x: x.query_latency_ms)
        report_lines.append(f"**最佳查询延迟**: {best_query.strategy.value} "
                          f"(数据集大小={best_query.dataset_size}, "
                          f"维度={best_query.vector_dimensions}): "
                          f"{best_query.query_latency_ms:.2f} ms")
        
        report_lines.append("")
        
        # 保存报告
        report_file = self.output_dir / "benchmark_report.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(report_lines))
        
        print(f"报告已保存到: {report_file}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='GL 语义折叠引擎基准测试')
    parser.add_argument('--output-dir', default='./benchmark_results',
                       help='输出目录路径')
    
    args = parser.parse_args()
    
    # 创建基准测试器
    benchmark = SemanticFoldingBenchmark(output_dir=args.output_dir)
    
    print("开始 GL 语义折叠引擎基准测试...")
    print()
    
    # 运行基准测试
    start_time = time.perf_counter()
    benchmark.run_all_benchmarks()
    end_time = time.perf_counter()
    
    print(f"基准测试完成，总耗时: {end_time - start_time:.2f} 秒")
    
    # 保存结果
    benchmark.save_results()
    
    # 生成报告
    benchmark.generate_report()
    
    print("基准测试全部完成！")


if __name__ == "__main__":
    main()