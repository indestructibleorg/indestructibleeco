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
掃描源代碼中的硬編時間線
專注於真正需要修正的時間線，排除生成的文件和元數據
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

class SourceCodeTimelineScanner:
    """源代碼時間線掃描器"""
    
    def __init__(self, repo_path="/workspace/machine-native-ops"):
        self.repo_path = repo_path
        self.results = defaultdict(list)
        self.skip_dirs = self._define_skip_dirs()
        self.skip_patterns = self._define_skip_patterns()
        self.metadata_patterns = self._define_metadata_patterns()
        
    def _define_skip_dirs(self):
        """定義跳過的目錄"""
        return {
            # Git 相關
            '.git',
            
            # 備份和歷史
            '.axiom-refactor-backup-repo',
            'backup',
            'backups',
            '.backup',
            'archive',
            'archived',
            '.archive',
            
            # 依賴和構建
            '__pycache__',
            'node_modules',
            '.venv',
            'venv',
            'dist',
            'build',
            '.next',
            'coverage',
            '.pytest_cache',
            
            # 生成的文件和日誌
            'logs',
            'outputs',
            'audit-reports',
            'audit-results',
            '.gl-platform.governance/audit-reports',
            '.gl-platform.governance/audit-results',
            '.gl-platform.governance/per-file-audits',
            '.gl-platform.governance/outputs',
            '.gl-platform.governance/supply-chain-evidence',
            
            # 暫時文件
            'tmp',
            'temp',
            '.tmp',
        }
    
    def _define_skip_patterns(self):
        """定義跳過的文件模式"""
        return [
            # 備份文件
            r'.*\.bak$',
            r'.*\.backup$',
            r'.*\.old$',
            r'.*\.legacy$',
            
            # 測試數據和示例
            r'.*test.*data.*',
            r'.*fixture.*',
            r'.*example.*',
            r'.*sample.*',
            
            # 生成的文件
            r'.*generated.*',
            r'.*auto.*generated.*',
        ]
    
    def _define_metadata_patterns(self):
        """定義元數據模式（這些時間戳記不需要修正）"""
        return {
            'timestamp': re.compile(r'timestamp["\']?\s*:\s*["\']?\d{4}-\d{2}-\d{2}'),
            'created_at': re.compile(r'created_at["\']?\s*:\s*["\']?\d{4}-\d{2}-\d{2}'),
            'updated_at': re.compile(r'updated_at["\']?\s*:\s*["\']?\d{4}-\d{2}-\d{2}'),
            'generated_at': re.compile(r'generated_at["\']?\s*:\s*["\']?\d{4}-\d{2}-\d{2}'),
            'creation_date': re.compile(r'(creation|created).*date["\']?\s*:\s*["\']?\d{4}-\d{2}-\d{2}', re.IGNORECASE),
            'version_date': re.compile(r'version.*date["\']?\s*:\s*["\']?\d{4}-\d{2}-\d{2}', re.IGNORECASE),
            'migration_date': re.compile(r'migration.*date["\']?\s*:\s*["\']?\d{4}-\d{2}-\d{2}', re.IGNORECASE),
            'integration_date': re.compile(r'integration.*date["\']?\s*:\s*["\']?\d{4}-\d{2}-\d{2}', re.IGNORECASE),
            'effective_date': re.compile(r'effective.*date["\']?\s*:\s*["\']?\d{4}-\d{2}-\d{2}', re.IGNORECASE),
            'valid_date': re.compile(r'valid.*date["\']?\s*:\s*["\']?\d{4}-\d{2}-\d{2}', re.IGNORECASE),
            'meta_date': re.compile(r'meta.*date["\']?\s*:\s*["\']?\d{4}-\d{2}-\d{2}', re.IGNORECASE),
        }
    
    def _define_timeline_patterns(self):
        """定義需要修正的時間線模式"""
        return {
            # 路線圖和計劃
            'roadmap_year': re.compile(
                r'(roadmap|timeline|schedule|plan).*?(202[4-9]|203[0-9])',
                re.IGNORECASE
            ),
            'phase_timeline': re.compile(
                r'(Phase|Stage|Milestone|Sprint|Iteration)\s+\d+.*?(by|in|until|before|after)\s+(202[4-9]|203[0-9])',
                re.IGNORECASE
            ),
            'deadline': re.compile(
                r'(deadline|due.*date|target.*date|completion.*date)\s*[:=]\s*["\']?\d{4}-\d{2}-\d{2}',
                re.IGNORECASE
            ),
            'release_date': re.compile(
                r'(release|launch|deploy|deploy.*date|rollout).*?(202[4-9]|203[0-9])',
                re.IGNORECASE
            ),
            
            # 季度和週計劃
            'quarter_plan': re.compile(
                r'(Q[1-4]\s*202[4-9]|quarter\s*\d).*?(plan|timeline|schedule|roadmap)',
                re.IGNORECASE
            ),
            'week_plan': re.compile(
                r'Week\s*\d{1,2}.*?(202[4-9]|plan|schedule|roadmap)',
                re.IGNORECASE
            ),
            
            # 月份計劃
            'month_plan': re.compile(
                r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+202[4-9].*?(plan|timeline|schedule|roadmap)',
                re.IGNORECASE
            ),
            
            # 時間表達關鍵字
            'by_year': re.compile(
                r'\bby\s+(202[4-9]|203[0-9])\b',
                re.IGNORECASE
            ),
            'in_year': re.compile(
                r'\bin\s+(202[4-9]|203[0-9])\b',
                re.IGNORECASE
            ),
            'until_year': re.compile(
                r'\buntil\s+(202[4-9]|203[0-9])\b',
                re.IGNORECASE
            ),
            'before_year': re.compile(
                r'\bbefore\s+(202[4-9]|203[0-9])\b',
                re.IGNORECASE
            ),
            'after_year': re.compile(
                r'\bafter\s+(202[4-9]|203[0-9])\b',
                re.IGNORECASE
            ),
            
            # 具體的計劃日期
            'planned_date': re.compile(
                r'(planned|scheduled|targeted|expected).*?(date|completion|delivery)\s*[:=]\s*["\']?\d{4}-\d{2}-\d{2}',
                re.IGNORECASE
            ),
        }
    
    def should_skip_file(self, file_path):
        """判斷是否應該跳過該文件"""
        path_str = str(file_path)
        
        # 跳過目錄
        if any(skip_dir in path_str for skip_dir in self.skip_dirs):
            return True
        
        # 跳過文件模式
        for pattern in self.skip_patterns:
            if re.match(pattern, file_path.name, re.IGNORECASE):
                return True
        
        return False
    
    def is_metadata_line(self, line):
        """判斷是否為元數據行"""
        for pattern_name, pattern in self.metadata_patterns.items():
            if pattern.search(line):
                return True
        return False
    
    def scan_file(self, file_path):
        """掃描單個文件"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                lines = content.split('\n')
                
                patterns = self._define_timeline_patterns()
                file_matches = []
                
                for line_num, line in enumerate(lines, 1):
                    # 跳過元數據行
                    if self.is_metadata_line(line):
                        continue
                    
                    # 檢查時間線模式
                    for pattern_name, pattern in patterns.items():
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
            
        for root, dirs, files in os.walk(directory):
            # 移除跳過的目錄
            dirs[:] = [d for d in dirs if d not in self.skip_dirs]
            
            for file in files:
                file_path = Path(root) / file
                
                # 跳過文件
                if self.should_skip_file(file_path):
                    continue
                
                # 只掃描源代碼文件
                source_extensions = {
                    '.py', '.js', '.ts', '.java', '.go', '.rs', '.cpp', '.c', '.h',
                    '.yml', '.yaml', '.json', '.xml', '.md', '.txt', '.rst',
                    '.sh', '.bash', '.zsh', '.fish', '.ps1',
                    '.rego', '.tf', '.hcl', '.toml', '.ini', '.cfg', '.conf',
                    '.sql', '.graphql', '.gql',
                }
                
                if file_path.suffix.lower() in source_extensions:
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
        
        # 按目錄統計
        dir_stats = defaultdict(int)
        for file_path in self.results.keys():
            dir_path = str(Path(file_path).parent.relative_to(self.repo_path))
            dir_stats[dir_path] += 1
        
        report = {
            'scan_time': datetime.now().isoformat(),
            'summary': {
                'total_files_with_timelines': total_files,
                'total_timeline_matches': total_matches,
                'pattern_distribution': dict(pattern_stats),
                'file_type_distribution': dict(ext_stats),
                'directory_distribution': dict(dir_stats)
            },
            'detailed_results': dict(self.results)
        }
        
        return report
    
    def save_report(self, output_path):
        """保存報告"""
        report = self.generate_report()
        
        # 保存 JSON 報告
        json_path = Path(output_path) / 'timeline-scan-source-code.json'
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        # 保存 Markdown 報告
        md_path = Path(output_path) / 'timeline-scan-source-code.md'
        self._save_markdown_report(report, md_path)
        
        return json_path, md_path
    
    def _save_markdown_report(self, report, output_path):
        """保存 Markdown 報告"""
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("# 源代碼硬編時間線掃描報告\n\n")
            f.write(f"**掃描時間**: {report['scan_time']}\n")
            f.write("**過濾條件**: \n")
            f.write("- 排除備份目錄、歷史檔案、暫時文件\n")
            f.write("- 排除審計報告、日誌、生成的文件\n")
            f.write("- 排除元數據（timestamp、created_at、updated_at 等）\n")
            f.write("- 專注於需要修正的計劃、路線圖、截止日期等\n\n")
            
            # 摘要
            f.write("## 掃描摘要\n\n")
            summary = report['summary']
            f.write(f"- **包含時間線的文件數**: {summary['total_files_with_timelines']}\n")
            f.write(f"- **總時間線匹配數**: {summary['total_timeline_matches']}\n\n")
            
            if summary['total_timeline_matches'] == 0:
                f.write("✅ **沒有發現需要修正的硬編時間線！**\n\n")
                return
            
            # 模式分佈
            f.write("### 時間線類型分佈\n\n")
            f.write("| 類型 | 數量 | 百分比 |\n")
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
            
            # 目錄分佈
            f.write("### 目錄分佈\n\n")
            f.write("| 目錄 | 文件數 |\n")
            f.write("|------|--------|\n")
            for dir_path, count in sorted(summary['directory_distribution'].items(), 
                                         key=lambda x: x[1], reverse=True):
                f.write(f"| {dir_path} | {count} |\n")
            f.write("\n")
            
            # 詳細結果
            f.write("## 詳細結果\n\n")
            f.write("以下是包含需要修正的硬編時間線的所有文件：\n\n")
            
            for file_path, matches in sorted(report['detailed_results'].items()):
                # 顯示相對路徑
                rel_path = Path(file_path).relative_to(self.repo_path)
                f.write(f"### {rel_path}\n\n")
                f.write(f"**匹配數**: {len(matches)}\n\n")
                
                f.write("| 行號 | 類型 | 匹配內容 | 上下文 |\n")
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
    print("開始掃描源代碼中的硬編時間線...")
    print("=" * 60)
    
    scanner = SourceCodeTimelineScanner()
    print(f"掃描目錄: {scanner.repo_path}")
    print("過濾條件:")
    print("  - 排除備份目錄、歷史檔案、暫時文件")
    print("  - 排除審計報告、日誌、生成的文件")
    print("  - 排除元數據（timestamp、created_at、updated_at 等）")
    print("  - 專注於需要修正的計劃、路線圖、截止日期等")
    
    # 執行掃描
    scanner.scan_directory()
    
    print(f"\n掃描完成！找到 {len(scanner.results)} 個包含時間線的文件")
    
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
    
    if report['summary']['total_timeline_matches'] > 0:
        print("\n前 10 個最常見的類型:")
        for pattern, count in sorted(report['summary']['pattern_distribution'].items(), 
                                   key=lambda x: x[1], reverse=True)[:10]:
            print(f"  - {pattern}: {count}")
    else:
        print("\n✅ 沒有發現需要修正的硬編時間線！")


if __name__ == "__main__":
    main()