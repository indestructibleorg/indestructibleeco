# @ECO-governed
# @ECO-layer: GL00-09
# @ECO-semantic: execution-script
# @ECO-audit-trail: gl-enterprise-architecture/governance/audit-trails/GL00_09-audit.json
#
# GL Unified Architecture Governance Framework Activated
# GL Root Semantic Anchor: gl-enterprise-architecture/governance/ECO-ROOT-SEMANTIC-ANCHOR.yaml
# GL Unified Naming Charter: gl-enterprise-architecture/governance/ECO-UNIFIED-NAMING-CHARTER.yaml


#!/usr/bin/env python3
"""
文件版本核對腳本
系統性核對所有關鍵文件的版本信息
"""

"""
Module docstring
================

This module is part of the GL governance framework.
Please add specific module documentation here.
"""
# MNGA-002: Import organization needs review
import os
import json
import yaml
import re
from pathlib import Path
from datetime import datetime

class VersionAuditor:
    def __init__(self, repo_path):
        self.repo_path = Path(repo_path)
        self.results = {
            'audit_timestamp': datetime.now().isoformat(),
            'issues': [],
            'warnings': [],
            'version_conflicts': [],
            'missing_files': [],
            'successes': []
        }
    
    def audit_package_json(self):
        """核對 package.json 版本"""
        pkg_json_path = self.repo_path / 'package.json'
        if not pkg_json_path.exists():
            self.results['missing_files'].append('package.json')
            return
        
        try:
            with open(pkg_json_path, 'r') as f:
                pkg = json.load(f)
            
            version = pkg.get('version', 'unknown')
            gl_layer = pkg.get('gl_layer', 'unknown')
            gl_purpose = pkg.get('gl_purpose', 'unknown')
            
            self.results['package_json'] = {
                'version': version,
                'gl_layer': gl_layer,
                'gl_purpose': gl_purpose,
                'status': 'ok' if version else 'missing_version'
            }
            
            print(f"✅ package.json: v{version}, Layer: {gl_layer}")
            
        except Exception as e:
            self.results['issues'].append(f"package.json 讀取失敗: {e}")
            print(f"❌ package.json: 讀取失敗 - {e}")
    
    def audit_agent_orchestration(self):
        """核對 agent-orchestration.yml 版本"""
        agent_yml_path = self.repo_path / '.github' / 'agents' / 'agent-orchestration.yml'
        if not agent_yml_path.exists():
            self.results['missing_files'].append('.github/agents/agent-orchestration.yml')
            return
        
        try:
            with open(agent_yml_path, 'r') as f:
                agent_config = yaml.safe_load(f)
            
            metadata_version = agent_config.get('metadata', {}).get('version', 'unknown')
            comment_version = None
            
            # 從註釋中提取版本
            with open(agent_yml_path, 'r') as f:
                first_lines = [f.readline() for _ in range(10)]
                for line in first_lines:
                    if 'v' in line and '.0.0' in line:
                        match = re.search(r'v(\d+\.\d+\.\d+)', line)
                        if match:
                            comment_version = match.group(1)
                            break
            
            self.results['agent_orchestration'] = {
                'metadata_version': metadata_version,
                'comment_version': comment_version,
                'version_match': metadata_version == comment_version,
                'status': 'conflict' if metadata_version != comment_version else 'ok'
            }
            
            if metadata_version != comment_version:
                conflict_msg = f"agent-orchestration.yml 版本不一致: metadata={metadata_version}, comment={comment_version}"
                self.results['version_conflicts'].append(conflict_msg)
                self.results['warnings'].append(conflict_msg)
                print(f"⚠️  agent-orchestration.yml: 版本不一致 - metadata={metadata_version}, comment={comment_version}")
            else:
                print(f"✅ agent-orchestration.yml: v{metadata_version}")
            
        except Exception as e:
            self.results['issues'].append(f"agent-orchestration.yml 讀取失敗: {e}")
            print(f"❌ agent-orchestration.yml: 讀取失敗 - {e}")
    
    def audit_governance_files(self):
        """核對治理相關文件"""
        governance_dirs = [
            'gl-execution-runtime/governance-root-layer',
            'gl-execution-runtime/meta-governance-layer',
            'gl-execution-runtime/reality-falsification-layer'
        ]
        
        for gov_dir in governance_dirs:
            gov_path = self.repo_path / gov_dir
            if not gov_path.exists():
                self.results['warnings'].append(f"治理目錄不存在: {gov_dir}")
                print(f"⚠️  治理目錄不存在: {gov_dir}")
                continue
            
            # 查找 YAML 文件
            yaml_files = list(gov_path.glob('**/*.yaml'))
            yaml_files.extend(list(gov_path.glob('**/*.yml')))
            
            print(f"📁 {gov_dir}: 找到 {len(yaml_files)} 個 YAML 文件")
            self.results[f'{gov_dir.replace("/", "_")}_file_count'] = len(yaml_files)
    
    def audit_quantum_platform(self):
        """核對量子平台文件"""
        quantum_dirs = [
            'governance-quantum',
            'infrastructure-quantum', 
            'monitoring-quantum',
            'artifacts-quantum'
        ]
        
        for q_dir in quantum_dirs:
            q_path = self.repo_path / q_dir
            if not q_path.exists():
                self.results['warnings'].append(f"量子平台目錄不存在: {q_dir}")
                print(f"⚠️  量子平台目錄不存在: {q_dir}")
                continue
            
            yaml_files = list(q_path.glob('**/*.yaml'))
            yaml_files.extend(list(q_path.glob('**/*.yml')))
            
            print(f"📁 {q_dir}: 找到 {len(yaml_files)} 個 YAML 文件")
            self.results[f'{q_dir.replace("/", "_")}_file_count'] = len(yaml_files)
    
    def audit_completion_docs(self):
        """核對完成文檔"""
        completion_files = list(self.repo_path.glob('*COMPLETION*.md'))
        summary_files = list(self.repo_path.glob('*SUMMARY*.md'))
        
        print(f"📄 COMPLETION 文檔: {len(completion_files)} 個")
        print(f"📄 SUMMARY 文檔: {len(summary_files)} 個")
        
        self.results['completion_docs_count'] = len(completion_files)
        self.results['summary_docs_count'] = len(summary_files)
    
    def generate_report(self):
        """生成核對報告"""
        report = {
            **self.results,
            'summary': {
                'total_issues': len(self.results['issues']),
                'total_warnings': len(self.results['warnings']),
                'total_version_conflicts': len(self.results['version_conflicts']),
                'total_missing_files': len(self.results['missing_files'])
            }
        }
        return report
    
    def run_full_audit(self):
        """執行完整核對"""
        print("=" * 60)
        print("開始文件版本核對")
        print("=" * 60)
        
        self.audit_package_json()
        self.audit_agent_orchestration()
        self.audit_governance_files()
        self.audit_quantum_platform()
        self.audit_completion_docs()
        
        print("=" * 60)
        print("核對完成")
        print("=" * 60)
        
        return self.generate_report()

if __name__ == '__main__':
    repo_path = '/workspace/gl-repo'
    auditor = VersionAuditor(repo_path)
    report = auditor.run_full_audit()
    
    # 保存報告
    report_path = Path(repo_path) / 'VERSION_AUDIT_REPORT.json'
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n📊 報告已保存: {report_path}")
    print(f"總問題: {report['summary']['total_issues']}")
    print(f"總警告: {report['summary']['total_warnings']}")
    print(f"版本衝突: {report['summary']['total_version_conflicts']}")
    print(f"缺失文件: {report['summary']['total_missing_files']}")