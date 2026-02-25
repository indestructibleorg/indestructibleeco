#!/usr/bin/env python3
# @ECO-layer: GL60-80
# @ECO-governed
"""
GL Naming Validator - GL 前綴使用原則驗證工具
"""

import re
import sys
from typing import Dict, List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass


class NamingType(Enum):
    """命名類型枚舉"""
    PLATFORM = "platform"           # gl-xxx
    SEMANTIC_KEY = "semantic_key"    # gl.key.xxx
    SEMANTIC_SHORT = "semantic_short"  # gl.xxx.yyy
    API_PATH = "api_path"           # /gl/xxx/yyy
    K8S_LABEL = "k8s_label"         # gl.xxx/yyy
    LANGUAGE_VAR = "language_var"   # glxxx 或 glXxx


@dataclass
class NamingRule:
    """命名規則"""
    type: NamingType
    pattern: str
    description: str
    example: str


class GLNamingValidator:
    """GL 命名驗證器"""
    
    # 定義各種命名類型的規則
    RULES = {
        NamingType.PLATFORM: {
            'pattern': r'^gl-[a-z0-9-]+$',
            'description': '平台級命名格式: gl-xxx',
            'example': 'gl-runtime-platform'
        },
        NamingType.SEMANTIC_KEY: {
            'pattern': r'^gl\.key\.[a-z0-9_]+(?:\.[a-z0-9_]+)*$',
            'description': '語意鍵命名格式: gl.key.xxx',
            'example': 'gl.key.api.schema'
        },
        NamingType.SEMANTIC_SHORT: {
            'pattern': r'^gl\.[a-z0-9_]+(?:\.[a-z0-9_]+)*$',
            'description': '語意短名格式: gl.xxx.yyy',
            'example': 'gl.api.schema'
        },
        NamingType.API_PATH: {
            'pattern': r'^/gl/[a-z0-9_]+(?:/[a-z0-9_]+)*$',
            'description': 'API 路徑格式: /gl/xxx/yyy',
            'example': '/gl/runtime/dag'
        },
        NamingType.K8S_LABEL: {
            'pattern': r'^gl\.[a-z0-9_]+(?:/[a-z0-9_]+)?$',
            'description': 'K8s/GitOps 標籤格式: gl.xxx/yyy',
            'example': 'gl.platform/runtime'
        },
        NamingType.LANGUAGE_VAR: {
            'pattern': r'^gl[a-zA-Z0-9_]*$',
            'description': '程式語言變量格式: glxxx 或 glXxx',
            'example': 'glruntime_dag, glRuntimeDag'
        }
    }
    
    def __init__(self):
        self.violations: List[Dict] = []
        self.warnings: List[Dict] = []
    
    def validate(self, name: str, naming_type: NamingType, context: str = "") -> bool:
        """
        驗證名稱是否符合指定類型的命名規則
        
        Args:
            name: 要驗證的名稱
            naming_type: 命名類型
            context: 上下文信息（用於錯誤報告）
        
        Returns:
            bool: 是否通過驗證
        """
        if naming_type not in self.RULES:
            self.warnings.append({
                'name': name,
                'message': f'未知的命名類型: {naming_type.value}',
                'context': context
            })
            return False
        
        rule = self.RULES[naming_type]
        pattern = rule['pattern']
        
        if not re.match(pattern, name):
            self.violations.append({
                'name': name,
                'type': naming_type.value,
                'message': f'命名格式錯誤: {name}',
                'expected': rule['description'],
                'example': rule['example'],
                'context': context
            })
            return False
        
        return True
    
    def validate_semantic_node(self, entity_type: str, entity_name: str) -> bool:
        """
        驗證語意節點命名
        
        Args:
            entity_type: 實體類型（如 entity, relation, attribute）
            entity_name: 實體名稱（如 user, order）
        
        Returns:
            bool: 是否通過驗證
        """
        # 檢查實體類型
        valid_types = ['entity', 'relation', 'attribute', 'event']
        if entity_type not in valid_types:
            self.violations.append({
                'name': entity_type,
                'message': f'無效的實體類型: {entity_type}',
                'expected': f'必須是以下之一: {", ".join(valid_types)}'
            })
            return False
        
        # 檢查實體名稱格式
        if not re.match(r'^[a-z]+(?:_[a-z]+)*$', entity_name):
            self.violations.append({
                'name': entity_name,
                'message': f'實體名稱格式錯誤: {entity_name}',
                'expected': '必須使用全小寫，用下劃線分隔多個單詞',
                'example': 'user, created_at, is_active'
            })
            return False
        
        # 構建完整的語意節點名稱
        full_name = f'gl.semantic_node.{entity_type}.{entity_name}'
        
        # 驗證完整名稱
        return self.validate(full_name, NamingType.SEMANTIC_SHORT, 
                          f'semantic_node.{entity_type}')
    
    def validate_semantic_key(self, category: str, key_name: str) -> bool:
        """
        驗證語意鍵命名
        
        Args:
            category: 鍵的類別（如 api, config, metadata）
            key_name: 具體的鍵名（如 schema, timeout）
        
        Returns:
            bool: 是否通過驗證
        """
        # 檢查類別格式
        if not re.match(r'^[a-z0-9_]+$', category):
            self.violations.append({
                'name': category,
                'message': f'鍵類別格式錯誤: {category}',
                'expected': '必須使用全小寫和數字'
            })
            return False
        
        # 檢查鍵名格式
        if not re.match(r'^[a-z0-9_]+$', key_name):
            self.violations.append({
                'name': key_name,
                'message': f'鍵名格式錯誤: {key_name}',
                'expected': '必須使用全小寫和數字'
            })
            return False
        
        # 構建完整的語意鍵名稱
        full_name = f'gl.key.{category}.{key_name}'
        
        # 驗證完整名稱
        return self.validate(full_name, NamingType.SEMANTIC_KEY, f'key.{category}')
    
    def validate_api_path(self, *path_parts: str) -> bool:
        """
        驗證 API 路徑命名
        
        Args:
            path_parts: 路徑部分（如 'runtime', 'dag'）
        
        Returns:
            bool: 是否通過驗證
        """
        if not path_parts:
            self.violations.append({
                'name': '',
                'message': 'API 路徑不能為空'
            })
            return False
        
        # 檢查每個路徑部分
        for part in path_parts:
            if not re.match(r'^[a-z0-9_]+$', part):
                self.violations.append({
                    'name': part,
                    'message': f'路徑部分格式錯誤: {part}',
                    'expected': '必須使用全小寫和數字',
                    'example': 'runtime, dag, jobs'
                })
                return False
        
        # 構建完整的 API 路徑（使用斜槓分隔）
        full_path = f'/gl/{"/".join(path_parts)}'
        
        # 驗證完整路徑
        return self.validate(full_path, NamingType.API_PATH)
    
    def validate_k8s_label(self, *label_parts: str) -> bool:
        """
        驗證 K8s 標籤命名
        
        Args:
            label_parts: 標籤部分（如 'platform', 'runtime'）
        
        Returns:
            bool: 是否通過驗證
        """
        if not label_parts:
            self.violations.append({
                'name': '',
                'message': 'K8s 標籤不能為空'
            })
            return False
        
        # 檢查每個標籤部分
        for part in label_parts:
            if not re.match(r'^[a-z0-9_]+$', part):
                self.violations.append({
                    'name': part,
                    'message': f'標籤部分格式錯誤: {part}',
                    'expected': '必須使用全小寫和數字',
                    'example': 'platform, runtime, service'
                })
                return False
        
        # 構建完整的 K8s 標籤
        full_label = f'gl.{"-".join(label_parts)}'
        
        # 驗證完整標籤
        return self.validate(full_label, NamingType.K8S_LABEL)
    
    def generate_report(self) -> str:
        """
        生成驗證報告
        
        Returns:
            str: 報告內容
        """
        report = []
        report.append("=" * 80)
        report.append("GL Naming Validation Report")
        report.append("=" * 80)
        report.append(f"")
        
        # 統計信息
        total_violations = len(self.violations)
        total_warnings = len(self.warnings)
        
        report.append(f"Total Violations: {total_violations}")
        report.append(f"Total Warnings: {total_warnings}")
        report.append("")
        
        # 違規報告
        if self.violations:
            report.append("VIOLATIONS:")
            report.append("-" * 80)
            for i, violation in enumerate(self.violations, 1):
                report.append(f"\n[{i}] Name: {violation.get('name', 'N/A')}")
                report.append(f"    Type: {violation.get('type', 'N/A')}")
                report.append(f"    Message: {violation.get('message')}")
                if 'expected' in violation:
                    report.append(f"    Expected: {violation['expected']}")
                if 'example' in violation:
                    report.append(f"    Example: {violation['example']}")
                if 'context' in violation:
                    report.append(f"    Context: {violation['context']}")
            report.append("")
        
        # 警告報告
        if self.warnings:
            report.append("WARNINGS:")
            report.append("-" * 80)
            for i, warning in enumerate(self.warnings, 1):
                report.append(f"\n[{i}] Name: {warning.get('name', 'N/A')}")
                report.append(f"    Message: {warning.get('message')}")
                if 'context' in warning:
                    report.append(f"    Context: {warning['context']}")
            report.append("")
        
        # 結論
        if total_violations == 0 and total_warnings == 0:
            report.append("✅ All naming conventions are valid!")
        elif total_violations == 0:
            report.append("⚠️  Naming is valid but there are warnings.")
        else:
            report.append("❌ Naming validation failed with violations.")
        
        return "\n".join(report)


def main():
    """主函數 - CLI 入口"""
    if len(sys.argv) < 3:
        print("Usage: gl_naming_validator.py <type> <name> [options]")
        print("")
        print("Types:")
        print("  semantic-node <entity_type> <entity_name>")
        print("  semantic-key <category> <key_name>")
        print("  api-path <path_parts...>")
        print("  k8s-label <label_parts...>")
        print("")
        print("Examples:")
        print("  gl_naming_validator.py semantic-node entity user")
        print("  gl_naming_validator.py semantic-key api schema")
        print("  gl_naming_validator.py api-path runtime dag")
        print("  gl_naming_validator.py k8s-label platform runtime")
        sys.exit(1)
    
    validator = GLNamingValidator()
    naming_type = sys.argv[1].lower()
    
    success = False
    
    if naming_type == "semantic-node":
        if len(sys.argv) < 4:
            print("Error: semantic-node requires <entity_type> and <entity_name>")
            sys.exit(1)
        success = validator.validate_semantic_node(sys.argv[2], sys.argv[3])
    
    elif naming_type == "semantic-key":
        if len(sys.argv) < 4:
            print("Error: semantic-key requires <category> and <key_name>")
            sys.exit(1)
        success = validator.validate_semantic_key(sys.argv[2], sys.argv[3])
    
    elif naming_type == "api-path":
        if len(sys.argv) < 3:
            print("Error: api-path requires at least one path part")
            sys.exit(1)
        success = validator.validate_api_path(*sys.argv[2:])
    
    elif naming_type == "k8s-label":
        if len(sys.argv) < 3:
            print("Error: k8s-label requires at least one label part")
            sys.exit(1)
        success = validator.validate_k8s_label(*sys.argv[2:])
    
    else:
        print(f"Error: Unknown naming type: {naming_type}")
        sys.exit(1)
    
    # 生成並打印報告
    print(validator.generate_report())
    
    # 根據驗證結果退出
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()