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
修復源代碼中的硬編時間線
將硬編的年份和日期替換為相對表達或配置化變量
"""

"""
Module docstring
================

This module is part of the GL governance framework.
Please add specific module documentation here.
"""
import os
import re
from pathlib import Path
from datetime import datetime
from collections import defaultdict

class TimelineFixer:
    """時間線修復器"""
    
    def __init__(self, repo_path="/workspace/machine-native-ops"):
        self.repo_path = Path(repo_path)
        self.fixes_applied = defaultdict(list)
        self.files_modified = 0
        
        # 定義修復規則
        self.fix_rules = self._define_fix_rules()
    
    def _define_fix_rules(self):
        """定義修復規則"""
        return {
            # 修復路線圖年份 - 改為相對表達
            'roadmap_year': {
                'pattern': re.compile(r'(\s*)(timeline|schedule):\s*"(\d{4}-Q[1-4])"'),
                'replacement': r'\1\2: "{{TIMELINE_QUARTER}}"',
                'description': 'Replace hard-coded timeline with variable'
            },
            'roadmap_year_2025': {
                'pattern': re.compile(r'plan-2025'),
                'replacement': 'plan-{{CURRENT_YEAR}}',
                'description': 'Replace year-based plan with variable'
            },
            
            # 修復截止日期 - 改為里程碑
            'deadline_q1': {
                'pattern': re.compile(r'due_date:\s*"2025-03-31"'),
                'replacement': 'due_date: "{{MILESTONE_Q1}}"',
                'description': 'Replace Q1 deadline with milestone variable'
            },
            'deadline_q2': {
                'pattern': re.compile(r'due_date:\s*"2025-06-30"'),
                'replacement': 'due_date: "{{MILESTONE_Q2}}"',
                'description': 'Replace Q2 deadline with milestone variable'
            },
            'deadline_q3': {
                'pattern': re.compile(r'due_date:\s*"2025-09-30"'),
                'replacement': 'due_date: "{{MILESTONE_Q3}}"',
                'description': 'Replace Q3 deadline with milestone variable'
            },
            'deadline_q4': {
                'pattern': re.compile(r'due_date:\s*"2025-10-31"|due_date:\s*"2025-11-30"|due_date:\s*"2025-12-31"'),
                'replacement': 'due_date: "{{MILESTONE_Q4}}"',
                'description': 'Replace Q4 deadline with milestone variable'
            },
            'deadline_february': {
                'pattern': re.compile(r'(due_date|target_date):\s*"2025-02-(15|28|29)"'),
                'replacement': r'\1: "{{MILESTONE_FEBRUARY}}"',
                'description': 'Replace February deadline with milestone variable'
            },
            'deadline_march': {
                'pattern': re.compile(r'(due_date|target_date):\s*"2025-03-(15|31)"'),
                'replacement': r'\1: "{{MILESTONE_MARCH}}"',
                'description': 'Replace March deadline with milestone variable'
            },
            'deadline_april': {
                'pattern': re.compile(r'due_date:\s*"2025-04-30"'),
                'replacement': 'due_date: "{{MILESTONE_APRIL}}"',
                'description': 'Replace April deadline with milestone variable'
            },
            'deadline_may': {
                'pattern': re.compile(r'due_date:\s*"2025-05-31"'),
                'replacement': 'due_date: "{{MILESTONE_MAY}}"',
                'description': 'Replace May deadline with milestone variable'
            },
            'deadline_january': {
                'pattern': re.compile(r'(due_date|target_date):\s*"2025-01-(05|15|31)"'),
                'replacement': r'\1: "{{MILESTONE_JANUARY}}"',
                'description': 'Replace January deadline with milestone variable'
            },
            'deadline_2025_generic': {
                'pattern': re.compile(r'(due_date|target_date):\s*"2025-(\d{2}-\d{2})"'),
                'replacement': r'\1: "{{MILESTONE_DATE}}"',
                'description': 'Replace generic 2025 deadline with milestone variable'
            },
            'deadline_2024': {
                'pattern': re.compile(r'(completion_date|target_date):\s*"2024-12-(01|15)"'),
                'replacement': r'\1: "{{COMPLETION_MILESTONE}}"',
                'description': 'Replace 2024 completion date with milestone variable'
            },
            
            # 修復發布日期 - 改為版本號
            'release_date_2025': {
                'pattern': re.compile(r'(deployment_date|release_date):\s*"2025-01-18"'),
                'replacement': r'\1: "{{RELEASE_DATE}}"',
                'description': 'Replace release date with variable'
            },
            'release_date_in_content': {
                'pattern': re.compile(r'\*\*Deployment Date\*\*: \d{4}-\d{2}-\d{2}'),
                'replacement': '**Deployment Date**: {{DEPLOYMENT_DATE}}',
                'description': 'Replace deployment date in documentation with variable'
            },
            
            # 修復 in_year 表達
            'in_year_2024': {
                'pattern': re.compile(r'\b(in|In)\s+2024\b'),
                'replacement': r'\1 {{CURRENT_YEAR}}',
                'description': 'Replace "in 2024" with variable'
            },
            
            # 修復年份引用 - 保留歷史記錄但標記為變量
            'year_2025_in_plans': {
                'pattern': re.compile(r'deprecation-schedule:\s*"2025-01-01"'),
                'replacement': 'deprecation-schedule: "{{DEPRECATION_DATE}}"',
                'description': 'Replace deprecation schedule with variable'
            },
            'year_2026_timestamp': {
                'pattern': re.compile(r'  Timestamp: \d{4}'),
                'replacement': '  Timestamp: {{TIMESTAMP}}',
                'description': 'Replace timestamp with variable'
            },
            'year_2026_created_at': {
                'pattern': re.compile(r'created_at:\s*"\d{4}'),
                'replacement': 'created_at: "{{CREATED_AT_YEAR}}',
                'description': 'Replace created_at year with variable'
            },
            'year_2026_last_updated': {
                'pattern': re.compile(r'last_updated:\s*"\d{4}'),
                'replacement': 'last_updated: "{{LAST_UPDATED_YEAR}}',
                'description': 'Replace last_updated year with variable'
            },
            'version_date': {
                'pattern': re.compile(r'### v[0-9.]+ \((\d{4}-\d{2}-\d{2})\)'),
                'replacement': '### v\\1 ({{VERSION_DATE}})',
                'description': 'Replace version date with variable'
            },
        }
    
    def fix_file(self, file_path):
        """修復單個文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                original_content = f.read()
            
            content = original_content
            fixes_in_file = []
            
            # 應用所有修復規則
            for rule_name, rule in self.fix_rules.items():
                matches = list(rule['pattern'].finditer(content))
                if matches:
                    content = rule['pattern'].sub(rule['replacement'], content)
                    fixes_in_file.append({
                        'rule': rule_name,
                        'count': len(matches),
                        'description': rule['description']
                    })
            
            # 如果有修改，寫回文件
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                self.files_modified += 1
                self.fixes_applied[str(file_path)] = fixes_in_file
                
                return True, fixes_in_file
            
            return False, []
            
        except Exception as e:
            print(f"Error fixing {file_path}: {e}")
            return False, []
    
    def fix_files(self, file_list):
        """修復文件列表"""
        print(f"開始修復 {len(file_list)} 個文件...\n")
        
        for i, file_path in enumerate(file_list, 1):
            print(f"[{i}/{len(file_list)}] 修復: {file_path.relative_to(self.repo_path)}")
            modified, fixes = self.fix_file(file_path)
            
            if modified:
                print(f"  ✓ 修復完成，應用了 {len(fixes)} 條規則")
                for fix in fixes:
                    print(f"    - {fix['description']}: {fix['count']} 處")
            else:
                print(f"  - 無需修復")
            print()
        
        print(f"修復完成！共修改 {self.files_modified} 個文件\n")
    
    def generate_fix_report(self):
        """生成修復報告"""
        report = {
            'fix_time': datetime.now().isoformat(),
            'total_files_modified': self.files_modified,
            'total_fixes_applied': sum(len(fixes) for fixes in self.fixes_applied.values()),
            'files_fixed': dict(self.fixes_applied)
        }
        
        return report
    
    def save_fix_report(self, output_path):
        """保存修復報告"""
        import json
        
        report = self.generate_fix_report()
        
        # 保存 JSON 報告
        json_path = Path(output_path) / 'timeline-fixes-applied.json'
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        # 保存 Markdown 報告
        md_path = Path(output_path) / 'timeline-fixes-applied.md'
        self._save_markdown_report(report, md_path)
        
        return json_path, md_path
    
    def _save_markdown_report(self, report, output_path):
        """保存 Markdown 報告"""
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("# 硬編時間線修復報告\n\n")
            f.write(f"**修復時間**: {report['fix_time']}\n\n")
            
            f.write("## 修復摘要\n\n")
            f.write(f"- **修改的文件數**: {report['total_files_modified']}\n")
            f.write(f"- **應用的修復數**: {report['total_fixes_applied']}\n\n")
            
            if report['total_files_modified'] > 0:
                f.write("## 修復詳情\n\n")
                
                for file_path, fixes in report['files_fixed'].items():
                    rel_path = Path(file_path).relative_to(self.repo_path)
                    f.write(f"### {rel_path}\n\n")
                    f.write(f"**應用的修復數**: {len(fixes)}\n\n")
                    f.write("| 規則 | 描述 | 數量 |\n")
                    f.write("|------|------|------|\n")
                    
                    for fix in fixes:
                        f.write(f"| {fix['rule']} | {fix['description']} | {fix['count']} |\n")
                    
                    f.write("\n")


def main():
    """主函數"""
    print("=" * 60)
    print("開始修復硬編時間線...")
    print("=" * 60)
    print()
    
    repo_path = Path("/workspace/machine-native-ops")
    fixer = TimelineFixer(repo_path)
    
    # 定義需要修復的文件列表（高優先級）
    files_to_fix = [
        # 高優先級 - 截止日期
        repo_path / "engine/gl-platform.governance/gl-artifacts/operational/artifacts/operational-plan.yaml",
        repo_path / "engine/gl-platform.governance/gl-artifacts/strategic/artifacts/strategic-objectives.yaml",
        repo_path / "documentation-manifest.yaml",
        
        # 中優先級
        repo_path / "engine/gl-platform.governance/gl-artifacts/strategic/artifacts/cross-domain-integration.yaml",
        repo_path / "engine/gl-platform.governance/gl-artifacts/feedback/artifacts/innovation-registry.yaml",
        
        # 配置文件
        repo_path / "engine/etl-pipeline/controlplane/baseline/pipeline-baseline.yaml",
        
        # 元數據文件
        repo_path / "engine/gl-platform.governance/gl-artifacts/meta/spec/ECO-ARCHITECTURE-SPEC.yaml",
        repo_path / "engine/gl-platform.governance/gl-artifacts/meta/spec/ECO-ARTIFACTS-TEMPLATES.yaml",
        repo_path / "engine/gl-platform.governance/gl-artifacts/meta/spec/ECO-DEPENDENCY-GRAPH.yaml",
        repo_path / "engine/gl-platform.governance/gl-artifacts/execution/artifacts/deployment-record.yaml",
    ]
    
    # 過濾存在的文件
    existing_files = [f for f in files_to_fix if f.exists()]
    
    if len(existing_files) < len(files_to_fix):
        print(f"警告: {len(files_to_fix) - len(existing_files)} 個文件不存在\n")
    
    # 執行修復
    fixer.fix_files(existing_files)
    
    # 生成報告
    output_dir = repo_path / "logs"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    json_path, md_path = fixer.save_fix_report(output_dir)
    
    print(f"修復報告已生成:")
    print(f"  - JSON: {json_path}")
    print(f"  - Markdown: {md_path}")
    print()
    print("=" * 60)


if __name__ == "__main__":
    main()