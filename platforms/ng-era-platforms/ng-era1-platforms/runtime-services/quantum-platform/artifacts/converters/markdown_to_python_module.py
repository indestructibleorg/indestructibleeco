# @ECO-layer: GQS-L0
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
GL Quantum Artifact Converter - Markdown to Python Module
Converts Markdown documents to Python module artifacts
"""

"""
Module docstring
================

This module is part of the GL governance framework.
Please add specific module documentation here.
"""
import os
import sys
import re
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

class MarkdownToPythonConverter:
    """Convert Markdown documents to Python modules"""
    
    def __init__(self, input_path: str, output_path: str = None):
        self.input_path = Path(input_path)
        self.output_path = Path(output_path) if output_path else self.input_path.with_suffix('.py')
        self.module_name = self.output_path.stem
        
    def extract_code_blocks(self, content: str) -> List[Dict[str, Any]]:
        """Extract code blocks from markdown"""
        
        code_blocks = []
        pattern = r'```(\w+)?\n(.*?)```'
        
        matches = re.findall(pattern, content, re.DOTALL)
        
        for lang, code in matches:
            code_blocks.append({
                'language': lang or 'text',
                'code': code.strip(),
                'type': 'function' if 'def ' in code else 'class' if 'class ' in code else 'statement'
            })
            
        return code_blocks
        
    def extract_structure(self, content: str) -> Dict[str, Any]:
        """Extract document structure from markdown"""
        
        structure = {
            'metadata': {
                'title': '',
                'author': '',
                'created': datetime.now().isoformat(),
                'version': '1.0.0',
                'type': 'python-module',
                'module_name': self.module_name,
                'source': str(self.input_path)
            },
            'content': {
                'imports': [],
                'classes': [],
                'functions': [],
                'variables': [],
                'docstring': ''
            },
            'validation': {
                'required_fields': True,
                'structure_valid': True
            }
        }
        
        lines = content.split('\n')
        current_section = None
        
        for line in lines:
            # Extract title
            if line.startswith('# ') and not structure['metadata']['title']:
                structure['metadata']['title'] = line[2:].strip()
                
            # Extract imports
            elif line.startswith(('import ', 'from ')):
                structure['content']['imports'].append(line.strip())
                
            # Extract classes
            elif line.startswith('class '):
                class_name = line.split('(')[0].replace('class ', '').strip()
                structure['content']['classes'].append({
                    'name': class_name,
                    'line': line
                })
                
            # Extract functions
            elif line.startswith('def '):
                func_name = line.split('(')[0].replace('def ', '').strip()
                structure['content']['functions'].append({
                    'name': func_name,
                    'line': line
                })
                
            # Extract variables
            elif '=' in line and not line.strip().startswith('#'):
                var_name = line.split('=')[0].strip()
                if var_name and not var_name.startswith('#'):
                    structure['content']['variables'].append({
                        'name': var_name,
                        'line': line
                    })
                    
        # Extract code blocks
        code_blocks = self.extract_code_blocks(content)
        structure['content']['code_blocks'] = code_blocks
        
        return structure
        
    def generate_python_module(self, structure: Dict[str, Any]) -> str:
        """Generate Python module from structure"""
        
        module_code = f'''"""
{structure['metadata']['title']}
Auto-generated from Markdown artifact
Generated: {datetime.now().isoformat()}
"""

'''
        
        # Add imports
        if structure['content']['imports']:
            module_code += '\n# Imports\n'
            for imp in structure['content']['imports']:
                module_code += f'{imp}\n'
            module_code += '\n'
            
        # Add variables
        if structure['content']['variables']:
            module_code += '\n# Variables\n'
            for var in structure['content']['variables']:
                module_code += f'{var["line"]}\n'
            module_code += '\n'
            
        # Add classes
        if structure['content']['classes']:
            module_code += '\n# Classes\n'
            for cls in structure['content']['classes']:
                module_code += f'{cls["line"]}\n'
            module_code += '\n'
            
        # Add functions
        if structure['content']['functions']:
            module_code += '\n# Functions\n'
            for func in structure['content']['functions']:
                module_code += f'{func["line"]}\n'
            module_code += '\n'
            
        # Add code blocks
        if structure['content'].get('code_blocks'):
            module_code += '\n# Code Blocks\n'
            for block in structure['content']['code_blocks']:
                if block['type'] in ['function', 'class']:
                    module_code += f'\n{block["code"]}\n'
                    
        module_code += '\n'
        
        return module_code
        
    def convert(self) -> Dict[str, Any]:
        """Convert Markdown to Python module structure"""
        
        if not self.input_path.exists():
            raise FileNotFoundError(f"Input file not found: {self.input_path}")
            
        with open(self.input_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        structure = self.extract_structure(content)
        structure['content']['python_code'] = self.generate_python_module(structure)
        
        return structure
        
    def save_python_module(self, data: Dict[str, Any], output_path: Path = None):
        """Save Python module"""
        
        output = output_path or self.output_path
        output.parent.mkdir(parents=True, exist_ok=True)
        
        python_code = data['content']['python_code']
        
        with open(output, 'w', encoding='utf-8') as f:
            f.write(python_code)
            
        return output
        
    def validate_structure(self, data: Dict[str, Any]) -> bool:
        """Validate Python module structure"""
        
        required_keys = ['metadata', 'content', 'validation']
        for key in required_keys:
            if key not in data:
                return False
                
        return True

def main():
    """Main entry point"""
    
    if len(sys.argv) < 2:
        print("Usage: python markdown-to-python-module.py <input.md> [output.py]")
        sys.exit(1)
        
    input_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None
    
    converter = MarkdownToPythonConverter(input_path, output_path)
    
    try:
        structure = converter.convert()
        
        if converter.validate_structure(structure):
            output_file = converter.save_python_module(structure)
            print(f"✅ Successfully converted {input_path} to {output_file}")
            return 0
        else:
            print("❌ Validation failed: Invalid structure")
            return 1
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())