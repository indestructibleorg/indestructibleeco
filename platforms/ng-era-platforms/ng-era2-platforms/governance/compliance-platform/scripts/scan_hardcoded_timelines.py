# @ECO-governed
# @ECO-layer: GL00-09
# @ECO-semantic: execution-script
# @ECO-audit-trail: gl-enterprise-architecture/gl-platform.governance/audit-trails/GL00_09-audit.json
#
# GL Unified Architecture Governance Framework Activated
# GL Root Semantic Anchor: gl-enterprise-architecture/gl-platform.governance/ECO-ROOT-SEMANTIC-ANCHOR.yaml
# GL Unified Naming Charter: gl-enterprise-architecture/gl-platform.governance/ECO-UNIFIED-NAMING-CHARTER.yaml


#!/usr/bin/env python3
"""
掃描全儲存庫硬編時間線
找出所有包含硬編時間線的文件
"""

"""
Module docstring
================

This module is part of the GL governance framework.
Please add specific module documentation here.
"""
# MNGA-002: Import organization needs review
import os
import re
import json
from datetime import datetime
from pathlib import Path
from collections import defaultdict

class TimelineScanner:
    """時間線掃描器"""
    
    def __init__(self, repo_path="/workspace/machine-native-ops"):
        self.repo_path = repo_path
        self.results = defaultdict(list)
        self.patterns = self._define_patterns()
        
    def _define_patterns(self):
        """定義搜尋模式"""
        return {
            # 日期格式
            'date_iso': re.compile(r'\b\d{4}-\d{2}-\d{2}\b'),
            'date_us': re.compile(r'\b\d{2}/\d{2}/\d{4}\b'),
            'date_eu': re.compile(r'\b\d{2}-\d{2}-\d{4}\b'),
            
            # 年份
            'year_2024': re.compile(r'\b2024\b'),
            'year_2025': re.compile(r'\b2025\b'),
            'year_2026': re.compile(r'\b2026\b'),
            'year_2027': re.compile(r'\b2027\b'),
            'year_2028': re.compile(r'\b2028\b'),
            'year_2029': re.compile(r'\b2029\b'),
            'year_2030': re.compile(r'\b2030\b'),
            
            # 季度
            'quarter': re.compile(r'\bQ[1-4]\b'),
            
            # 週
            'week': re.compile(r'\bWeek\s*\d{1,2}\b', re.IGNORECASE),
            
            # 月份名稱
            'month_name': re.compile(
                r'\b(January|February|March|April|May|June|July|August|'
                r'September|October|November|December)\b',
                re.IGNORECASE
            ),
            
            # 月份縮寫
            'month_abbr': re.compile(
                r'\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\b',
                re.IGNORECASE
            ),
            
            # 里程碑
            'milestone': re.compile(
                r'\b(Milestone|Phase|Stage|Sprint|Iteration)\s+\d+\b',
                re.IGNORECASE
            ),
            
            # 時間表達
            'time_expression': re.compile(
                r'\b(by|in|until|before|after|during|from|to)\s+\d{4}\b',
                re.IGNORECASE
            ),
            
            # 具體日期引用
            'date_reference': re.compile(
                r'\b(early|mid|late)\s+(202[4-9]|203[0-9])\b',
                re.IGNORECASE
            ),
        }
    
    def scan_file(self, file_path):
        """掃描單個文件"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                lines = content.split('\n')
                
                file_matches = []
                for line_num, line in enumerate(lines, 1):
                    for pattern_name, pattern in self.patterns.items():
                        matches = pattern.finditer(line)
                        for match in matches:
                            file_matches.append({
                                'line': line_num,
                                'pattern': pattern_name,
                                'match': match.group(),
                                'context': line.strip()
                            })
                
                if file_matches:
                    self.results[str(file_path)] = file_matches
                    
        except Exception as e:
            # 跳過無法讀取的文件
            pass
    
    def scan_directory(self, directory=None):
        """掃描目錄"""
        if directory is None:
            directory = self.repo_path
            
        # 跳過的目錄
        skip_dirs = {'.git', '__pycache__', 'node_modules', '.venv', 'venv', 
                    'dist', 'build', '.next', 'coverage', '.pytest_cache'}
        
        for root, dirs, files in os.walk(directory):
            # 移除跳過的目錄
            dirs[:] = [d for d in dirs if d not in skip_dirs]
            
            for file in files:
                file_path = Path(root) / file
                
                # 只掃描文本文件
                text_extensions = {
                    '.py', '.js', '.ts', '.java', '.go', '.rs', '.cpp', '.c', '.h',
                    '.yml', '.yaml', '.json', '.xml', '.md', '.txt', '.rst',
                    '.sh', '.bash', '.zsh', '.fish', '.ps1',
                    '.rego', '.tf', '.hcl', '.toml', '.ini', '.cfg', '.conf',
                    '.sql', '.graphql', '.gql',
                }
                
                if file_path.suffix.lower() in text_extensions:
                    self.scan_file(file_path)
    
    def generate_report(self):
        """生成報告"""
        total_files = len(self.results)
        total_matches = sum(len(matches) for matches in self.results.values())
        
        # 按模式統計
        pattern_stats = defaultdict(int)
        for matches in self.results.values():
            for match in matches:
                pattern_stats[match['pattern']] += 1
        
        # 按文件類型統計
        ext_stats = defaultdict(int)
        for file_path in self.results.keys():
            ext = Path(file_path).suffix.lower()
            ext_stats[ext] += 1
        
        report = {
            'scan_time': datetime.now().isoformat(),
            'summary': {
                'total_files_with_timelines': total_files,
                'total_timeline_matches': total_matches,
                'pattern_distribution': dict(pattern_stats),
                'file_type_distribution': dict(ext_stats)
            },
            'detailed_results': dict(self.results)
        }
        
        return report
    
    def save_report(self, output_path):
        """保存報告"""
        report = self.generate_report()
        
        # 保存 JSON 報告
        json_path = Path(output_path) / 'timeline-scan-results.json'
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        # 保存 Markdown 報告
        md_path = Path(output_path) / 'timeline-scan-results.md'
        self._save_markdown_report(report, md_path)
        
        return json_path, md_path
    
    def _save_markdown_report(self, report, output_path):
        """保存 Markdown 報告"""
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("# 硬編時間線掃描報告\n\n")
            f.write(f"**掃描時間**: {report['scan_time']}\n\n")
            
            # 摘要
            f.write("## 掃描摘要\n\n")
            summary = report['summary']
            f.write(f"- **包含時間線的文件數**: {summary['total_files_with_timelines']}\n")
            f.write(f"- **總時間線匹配數**: {summary['total_timeline_matches']}\n\n")
            
            # 模式分佈
            f.write("### 模式分佈\n\n")
            f.write("| 模式 | 數量 | 百分比 |\n")
            f.write("|------|------|--------|\n")
            total = summary['total_timeline_matches']
            for pattern, count in sorted(summary['pattern_distribution'].items(), 
                                       key=lambda x: x[1], reverse=True):
                percentage = (count / total * 100) if total > 0 else 0
                f.write(f"| {pattern} | {count} | {percentage:.2f}% |\n")
            f.write("\n")
            
            # 文件類型分佈
            f.write("### 文件類型分佈\n\n")
            f.write("| 擴展名 | 文件數 |\n")
            f.write("|--------|--------|\n")
            for ext, count in sorted(summary['file_type_distribution'].items(), 
                                   key=lambda x: x[1], reverse=True):
                f.write(f"| {ext} | {count} |\n")
            f.write("\n")
            
            # 詳細結果
            f.write("## 詳細結果\n\n")
            f.write("以下是包含硬編時間線的所有文件及其匹配內容：\n\n")
            
            for file_path, matches in sorted(report['detailed_results'].items()):
                # 顯示相對路徑
                rel_path = Path(file_path).relative_to(self.repo_path)
                f.write(f"### {rel_path}\n\n")
                f.write(f"**匹配數**: {len(matches)}\n\n")
                
                f.write("| 行號 | 模式 | 匹配內容 | 上下文 |\n")
                f.write("|------|------|----------|--------|\n")
                
                for match in matches:
                    # 截斷過長的上下文
                    context = match['context'][:100]
                    if len(match['context']) > 100:
                        context += "..."
                    
                    # 轉義 Markdown
                    context = context.replace('|', '\\|')
                    
                    f.write(f"| {match['line']} | {match['pattern']} | {match['match']} | {context} |\n")
                
                f.write("\n")


def main():
    """主函數"""
    print("開始掃描儲存庫中的硬編時間線...")
    print("=" * 60)
    
    scanner = TimelineScanner()
    print(f"掃描目錄: {scanner.repo_path}")
    
    # 執行掃描
    scanner.scan_directory()
    
    print(f"掃描完成！找到 {len(scanner.results)} 個包含時間線的文件")
    
    # 生成報告
    output_dir = Path("/workspace/machine-native-ops/logs")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    json_path, md_path = scanner.save_report(output_dir)
    
    print(f"\n報告已生成:")
    print(f"  - JSON: {json_path}")
    print(f"  - Markdown: {md_path}")
    print("\n" + "=" * 60)
    
    # 顯示摘要
    report = scanner.generate_report()
    print("\n掃描摘要:")
    print(f"  總文件數: {report['summary']['total_files_with_timelines']}")
    print(f"  總匹配數: {report['summary']['total_timeline_matches']}")
    print("\n前 10 個最常見的模式:")
    for pattern, count in sorted(report['summary']['pattern_distribution'].items(), 
                               key=lambda x: x[1], reverse=True)[:10]:
        print(f"  - {pattern}: {count}")


if __name__ == "__main__":
    main()