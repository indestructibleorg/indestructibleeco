#
# @ECO-governed
# @ECO-layer: gl-platform.gl-platform.governance
# @ECO-semantic: gl-consolidation-plan
# @ECO-audit-trail: ../../engine/gl-platform.gl-platform.governance/GL_SEMANTIC_ANCHOR.json
#
#!/usr/bin/env python3
"""
GL Consolidation Plan Generator
生成 GL 架構集中化與清理計劃
This script analyzes the current GL structure and generates a consolidation plan
based on the GL Unified Naming Charter.
"""
# MNGA-002: Import organization needs review
import json
import yaml
from pathlib import Path
from typing import Dict, List, Tuple
from dataclasses import dataclass, field
from datetime import datetime
@dataclass
class FileInfo:
    """檔案資訊"""
    path: str
    name: str
    size: int
    is_duplicate: bool = False
    duplicate_of: str = ""
    naming_compliant: bool = True
    issues: List[str] = field(default_factory=list)
@dataclass
class ConsolidationAction:
    """整合動作"""
    action_type: str  # merge, rename, delete, move
    source: str
    target: str
    reason: str
    priority: int  # 1=high, 2=medium, 3=low
    risk_level: str  # low, medium, high
class GLConsolidationPlanner:
    """GL 架構整合計劃生成器"""
    # GL 命名規則
    NAMING_RULES = {
        'gl_config_file': r'^gl-[a-z]+(-[a-z]+)*\.(yaml|yml)$',
        'gl_layer_dir': r'^(0[0-9]|[1-8][0-9]|9[0-9])-[a-z]+(-[a-z]+)*$',
        'legacy_gl_file': r'^GL[-_][A-Z]',  # 舊式命名 (需要修正)
    }
    # 已知的重複目錄對
    DUPLICATE_DIRECTORIES = [
        ('gl-platform.gl-platform.governance/ECO-architecture', 'workspace/gl-platform.gl-platform.governance/ECO-architecture'),
        ('gl-platform.gl-platform.governance/layers', 'workspace/gl-platform.gl-platform.governance/layers'),
        ('gl-platform.gl-platform.governance/meta-spec', 'workspace/gl-platform.gl-platform.governance/meta-spec'),
        ('gl-platform.gl-platform.governance/sealed', 'workspace/gl-platform.gl-platform.governance/sealed'),
        ('gl-platform.gl-platform.governance/naming-gl-platform.gl-platform.governance-v1.0.0', 'workspace/gl-platform.gl-platform.governance/naming-gl-platform.gl-platform.governance-v1.0.0'),
        ('gl-platform.gl-platform.governance/naming-gl-platform.gl-platform.governance-v1.0.0-extended', 'workspace/gl-platform.gl-platform.governance/naming-gl-platform.gl-platform.governance-v1.0.0-extended'),
        ('gl-platform.gl-platform.governance/quantum-naming-v4.0.0', 'workspace/gl-platform.gl-platform.governance/quantum-naming-v4.0.0'),
    ]
    # 需要重命名的檔案 (舊名 -> 新名)
    RENAME_MAP = {
        'GL_LAYERS.yaml': 'gl-layers.yaml',
        'GL_FILESYSTEM_MAPPING.yaml': 'gl-filesystem-mapping.yaml',
        'GL_DIRECTORY_NAMING_SPEC.yaml': 'gl-directory-naming-spec.yaml',
        'GL_SEMANTIC_STABILIZATION.yaml': 'gl-semantic-stabilization.yaml',
        'GL_MAPPING.csv': 'gl-mapping.csv',
        'GL_REFACTORING_EXEC_PROMPTS.md': 'gl-refactoring-exec-prompts.md',
        'GL_QUICKREF.md': 'gl-quickref.md',
        'ECO-EXECUTION-MODE.yaml': 'gl-execution-mode.yaml',
        'ECO-MAINLINE-INTEGRATION.md': 'gl-mainline-integration.md',
    }
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)
        self.gl_files: List[FileInfo] = []
        self.actions: List[ConsolidationAction] = []
        self.analysis_results: Dict = {}
    def scan_gl_files(self) -> List[FileInfo]:
        """掃描所有 GL 相關檔案"""
        gl_files = []
        for pattern in ['**/GL*', '**/gl-*', '**/gl_*']:
            for file_path in self.repo_path.rglob(pattern):
                if '.git' in str(file_path) or 'node_modules' in str(file_path):
                    continue
                if file_path.is_file():
                    file_info = FileInfo(
                        path=str(file_path.relative_to(self.repo_path)),
                        name=file_path.name,
                        size=file_path.stat().st_size
                    )
                    # 檢查命名合規性
                    issues = self._check_naming_compliance(file_path.name)
                    if issues:
                        file_info.naming_compliant = False
                        file_info.issues = issues
                    gl_files.append(file_info)
        self.gl_files = gl_files
        return gl_files
    def _check_naming_compliance(self, filename: str) -> List[str]:
        """檢查檔案命名合規性"""
        issues = []
        # 檢查是否使用舊式命名 (底線分隔的大寫)
        if '_' in filename and any(c.isupper() for c in filename):
            issues.append(f"使用底線分隔的大寫命名，建議改為 kebab-case: {filename}")
        # 檢查是否混合使用連字號和底線
        if '-' in filename and '_' in filename:
            issues.append(f"混合使用連字號和底線: {filename}")
        # 檢查是否需要重命名
        if filename in self.RENAME_MAP:
            issues.append(f"建議重命名為: {self.RENAME_MAP[filename]}")
        return issues
    def find_duplicates(self) -> List[Tuple[str, str]]:
        """找出重複的檔案"""
        duplicates = []
        for source_dir, target_dir in self.DUPLICATE_DIRECTORIES:
            source_path = self.repo_path / source_dir
            target_path = self.repo_path / target_dir
            if source_path.exists() and target_path.exists():
                # 比較兩個目錄中的檔案
                source_files = set(f.name for f in source_path.rglob('*') if f.is_file())
                target_files = set(f.name for f in target_path.rglob('*') if f.is_file())
                common_files = source_files & target_files
                if common_files:
                    duplicates.append((source_dir, target_dir, list(common_files)))
        return duplicates
    def generate_consolidation_actions(self) -> List[ConsolidationAction]:
        """生成整合動作計劃"""
        actions = []
        # 1. 合併重複目錄
        for source_dir, target_dir in self.DUPLICATE_DIRECTORIES:
            self.repo_path / source_dir
            target_path = self.repo_path / target_dir
            if target_path.exists():
                actions.append(ConsolidationAction(
                    action_type="merge",
                    source=target_dir,
                    target=source_dir,
                    reason=f"合併重複目錄 {target_dir} 到 {source_dir}",
                    priority=1,
                    risk_level="medium"
                ))
                actions.append(ConsolidationAction(
                    action_type="delete",
                    source=target_dir,
                    target="",
                    reason=f"刪除已合併的重複目錄 {target_dir}",
                    priority=1,
                    risk_level="medium"
                ))
        # 2. 重命名不合規檔案
        for file_info in self.gl_files:
            if file_info.name in self.RENAME_MAP:
                new_name = self.RENAME_MAP[file_info.name]
                new_path = str(Path(file_info.path).parent / new_name)
                actions.append(ConsolidationAction(
                    action_type="rename",
                    source=file_info.path,
                    target=new_path,
                    reason=f"統一命名風格: {file_info.name} -> {new_name}",
                    priority=2,
                    risk_level="low"
                ))
        # 3. 移動根目錄的 GL 檔案到統一位置
        root_gl_files = [f for f in self.gl_files if '/' not in f.path or f.path.count('/') == 0]
        for file_info in root_gl_files:
            if file_info.name.startswith('ECO-') or file_info.name.startswith('gl-'):
                target_path = f"gl-platform.gl-platform.governance/ECO-architecture/{file_info.name}"
                actions.append(ConsolidationAction(
                    action_type="move",
                    source=file_info.path,
                    target=target_path,
                    reason="將根目錄 GL 檔案移至統一位置",
                    priority=3,
                    risk_level="low"
                ))
        self.actions = actions
        return actions
    def analyze(self) -> Dict:
        """執行完整分析"""
        self.scan_gl_files()
        duplicates = self.find_duplicates()
        self.generate_consolidation_actions()
        # 統計分析
        total_files = len(self.gl_files)
        compliant_files = sum(1 for f in self.gl_files if f.naming_compliant)
        non_compliant_files = total_files - compliant_files
        self.analysis_results = {
            "scan_date": datetime.now().isoformat(),
            "summary": {
                "total_gl_files": total_files,
                "compliant_files": compliant_files,
                "non_compliant_files": non_compliant_files,
                "compliance_rate": f"{(compliant_files/total_files*100):.1f}%" if total_files > 0 else "N/A",
                "duplicate_directories": len(duplicates),
                "total_actions": len(self.actions)
            },
            "duplicates": [
                {
                    "source": d[0],
                    "target": d[1],
                    "common_files": d[2] if len(d) > 2 else []
                }
                for d in duplicates
            ],
            "non_compliant_files": [
                {
                    "path": f.path,
                    "name": f.name,
                    "issues": f.issues
                }
                for f in self.gl_files if not f.naming_compliant
            ],
            "actions": [
                {
                    "type": a.action_type,
                    "source": a.source,
                    "target": a.target,
                    "reason": a.reason,
                    "priority": a.priority,
                    "risk_level": a.risk_level
                }
                for a in self.actions
            ]
        }
        return self.analysis_results
    def generate_report(self, output_format: str = "markdown") -> str:
        """生成分析報告"""
        if not self.analysis_results:
            self.analyze()
        if output_format == "markdown":
            return self._generate_markdown_report()
        elif output_format == "json":
            return json.dumps(self.analysis_results, indent=2, ensure_ascii=False)
        elif output_format == "yaml":
            return yaml.dump(self.analysis_results, allow_unicode=True, default_flow_style=False)
        else:
            raise ValueError(f"Unsupported output format: {output_format}")
    def _generate_markdown_report(self) -> str:
        """生成 Markdown 格式報告"""
        results = self.analysis_results
        report = []
        report.append("# GL 架構整合計劃報告")
        report.append("")
        report.append(f"**生成日期**: {results['scan_date']}")
        report.append("")
        # 摘要
        report.append("## 摘要")
        report.append("")
        report.append("| 指標 | 數值 |")
        report.append("|------|------|")
        for key, value in results['summary'].items():
            report.append(f"| {key} | {value} |")
        report.append("")
        # 重複目錄
        if results['duplicates']:
            report.append("## 重複目錄")
            report.append("")
            for dup in results['duplicates']:
                report.append(f"### {dup['source']} ↔ {dup['target']}")
                if dup['common_files']:
                    report.append(f"共同檔案數: {len(dup['common_files'])}")
                report.append("")
        # 不合規檔案
        if results['non_compliant_files']:
            report.append("## 不合規檔案")
            report.append("")
            report.append("| 檔案路徑 | 問題 |")
            report.append("|----------|------|")
            for f in results['non_compliant_files']:
                issues = "; ".join(f['issues'])
                report.append(f"| `{f['path']}` | {issues} |")
            report.append("")
        # 整合動作
        if results['actions']:
            report.append("## 整合動作計劃")
            report.append("")
            # 按優先級分組
            high_priority = [a for a in results['actions'] if a['priority'] == 1]
            medium_priority = [a for a in results['actions'] if a['priority'] == 2]
            low_priority = [a for a in results['actions'] if a['priority'] == 3]
            if high_priority:
                report.append("### 高優先級 (Priority 1)")
                report.append("")
                for action in high_priority:
                    report.append(f"- **{action['type'].upper()}**: `{action['source']}`")
                    if action['target']:
                        report.append(f"  - 目標: `{action['target']}`")
                    report.append(f"  - 原因: {action['reason']}")
                    report.append(f"  - 風險: {action['risk_level']}")
                report.append("")
            if medium_priority:
                report.append("### 中優先級 (Priority 2)")
                report.append("")
                for action in medium_priority:
                    report.append(f"- **{action['type'].upper()}**: `{action['source']}`")
                    if action['target']:
                        report.append(f"  - 目標: `{action['target']}`")
                    report.append(f"  - 原因: {action['reason']}")
                report.append("")
            if low_priority:
                report.append("### 低優先級 (Priority 3)")
                report.append("")
                for action in low_priority:
                    report.append(f"- **{action['type'].upper()}**: `{action['source']}`")
                    if action['target']:
                        report.append(f"  - 目標: `{action['target']}`")
                    report.append(f"  - 原因: {action['reason']}")
                report.append("")
        return "\n".join(report)
    def generate_migration_script(self) -> str:
        """生成遷移腳本"""
        if not self.actions:
            self.generate_consolidation_actions()
        script_lines = [
            "#!/bin/bash",
            "# GL Architecture Consolidation Script",
            "# Generated by GL Consolidation Planner",
            f"# Date: {datetime.now().isoformat()}",
            "",
            "set -e  # Exit on error",
            "",
            "# Backup current state",
            "echo 'Creating backup...'",
            "BACKUP_DIR=&quot;backups/gl-consolidation-$(date +%Y%m%d-%H%M%S)&quot;",
            "mkdir -p &quot;$BACKUP_DIR&quot;",
            "",
        ]
        # 按優先級排序動作
        sorted_actions = sorted(self.actions, key=lambda a: a.priority)
        for action in sorted_actions:
            script_lines.append(f"# {action.reason}")
            if action.action_type == "merge":
                script_lines.append(f"echo 'Merging {action.source} to {action.target}...'")
                script_lines.append(f"cp -rn &quot;{action.source}/&quot;* &quot;{action.target}/&quot; 2>/dev/null || true")
            elif action.action_type == "delete":
                script_lines.append(f"echo 'Backing up and removing {action.source}...'")
                script_lines.append(f"cp -r &quot;{action.source}&quot; &quot;$BACKUP_DIR/&quot; 2>/dev/null || true")
                script_lines.append(f"rm -rf &quot;{action.source}&quot;")
            elif action.action_type == "rename":
                script_lines.append(f"echo 'Renaming {action.source} to {action.target}...'")
                script_lines.append(f"git mv &quot;{action.source}&quot; &quot;{action.target}&quot; 2>/dev/null || mv &quot;{action.source}&quot; &quot;{action.target}&quot;")
            elif action.action_type == "move":
                script_lines.append(f"echo 'Moving {action.source} to {action.target}...'")
                script_lines.append(f"mkdir -p &quot;$(dirname &quot;{action.target}&quot;)&quot;")
                script_lines.append(f"git mv &quot;{action.source}&quot; &quot;{action.target}&quot; 2>/dev/null || mv &quot;{action.source}&quot; &quot;{action.target}&quot;")
            script_lines.append("")
        script_lines.extend([
            "echo 'Consolidation complete!'",
            "echo &quot;Backup saved to: $BACKUP_DIR&quot;",
        ])
        return "\n".join(script_lines)
def main():
    """主函數"""
    import argparse
    parser = argparse.ArgumentParser(description='GL Consolidation Plan Generator')
    parser.add_argument('--repo', default='.', help='Repository path')
    parser.add_argument('--output', default='gl-consolidation-report.md', help='Output file')
    parser.add_argument('--format', choices=['markdown', 'json', 'yaml'], default='markdown', help='Output format')
    parser.add_argument('--script', action='store_true', help='Generate migration script')
    args = parser.parse_args()
    planner = GLConsolidationPlanner(args.repo)
    planner.analyze()
    # 生成報告
    report = planner.generate_report(args.format)
    with open(args.output, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"Report generated: {args.output}")
    # 生成遷移腳本
    if args.script:
        script = planner.generate_migration_script()
        script_path = args.output.replace('.md', '-migration.sh').replace('.json', '-migration.sh').replace('.yaml', '-migration.sh')
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(script)
        print(f"Migration script generated: {script_path}")
    # 輸出摘要
    print("\n=== Summary ===")
    for key, value in planner.analysis_results['summary'].items():
        print(f"{key}: {value}")
if __name__ == '__main__':
    main()