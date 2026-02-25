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
GL Quantum Artifact CLI
Command-line interface for artifact conversion and management
"""

"""
Module docstring
================

This module is part of the GL governance framework.
Please add specific module documentation here.
"""
# MNGA-002: Import organization needs review
import argparse
import sys
import json
from pathlib import Path
from typing import Dict, Any

# Import converters
sys.path.insert(0, str(Path(__file__).parent / 'converters'))
from docx_to_yaml_converter import DOCXToYAMLConverter
from pdf_to_json_converter import PDFToJSONConverter
from markdown_to_python_module import MarkdownToPythonConverter

class ArtifactCLI:
    """CLI for artifact operations"""
    
    def __init__(self):
        self.converters = {
            'docx': DOCXToYAMLConverter,
            'pdf': PDFToJSONConverter,
            'markdown': MarkdownToPythonConverter
        }
        
    def convert(self, input_path: str, output_path: str = None, format: str = None) -> int:
        """Convert artifact to specified format"""
        
        input_file = Path(input_path)
        
        if not input_file.exists():
            print(f"❌ Error: Input file not found: {input_path}")
            return 1
            
        # Detect format from extension
        if not format:
            format = input_file.suffix.lower().lstrip('.')
            
        if format not in self.converters:
            print(f"❌ Error: Unsupported format: {format}")
            print(f"Supported formats: {', '.join(self.converters.keys())}")
            return 1
            
        converter_class = self.converters[format]
        converter = converter_class(input_path, output_path)
        
        try:
            structure = converter.convert()
            
            if converter.validate_structure(structure):
                if format == 'docx':
                    output_file = converter.save_yaml(structure)
                elif format == 'pdf':
                    output_file = converter.save_json(structure)
                elif format == 'markdown':
                    output_file = converter.save_python_module(structure)
                    
                print(f"✅ Successfully converted {input_path} to {output_file}")
                return 0
            else:
                print("❌ Validation failed: Invalid structure")
                return 1
                
        except Exception as e:
            print(f"❌ Error: {e}")
            return 1
            
    def batch_convert(self, input_dir: str, output_dir: str, format: str = None) -> int:
        """Batch convert all artifacts in directory"""
        
        input_path = Path(input_dir)
        output_path = Path(output_dir)
        
        if not input_path.exists():
            print(f"❌ Error: Input directory not found: {input_dir}")
            return 1
            
        output_path.mkdir(parents=True, exist_ok=True)
        
        success_count = 0
        failure_count = 0
        
        for file_path in input_path.rglob('*'):
            if file_path.is_file():
                file_format = file_path.suffix.lower().lstrip('.')
                
                if file_format in self.converters:
                    relative_path = file_path.relative_to(input_path)
                    output_file = output_path / relative_path.with_suffix(
                        '.yaml' if file_format == 'docx' else 
                        '.json' if file_format == 'pdf' else '.py'
                    )
                    output_file.parent.mkdir(parents=True, exist_ok=True)
                    
                    result = self.convert(str(file_path), str(output_file), file_format)
                    
                    if result == 0:
                        success_count += 1
                    else:
                        failure_count += 1
                        
        print(f"\n📊 Batch Conversion Summary:")
        print(f"  ✅ Successful: {success_count}")
        print(f"  ❌ Failed: {failure_count}")
        
        return 0 if failure_count == 0 else 1
        
    def validate(self, artifact_path: str) -> int:
        """Validate artifact structure"""
        
        artifact_file = Path(artifact_path)
        
        if not artifact_file.exists():
            print(f"❌ Error: Artifact file not found: {artifact_path}")
            return 1
            
        try:
            with open(artifact_file, 'r') as f:
                if artifact_file.suffix == '.json':
                    data = json.load(f)
                elif artifact_file.suffix in ['.yaml', '.yml']:
                    import yaml
                    data = yaml.safe_load(f)
                else:
                    print(f"❌ Error: Unsupported artifact format: {artifact_file.suffix}")
                    return 1
                    
            # Validate structure
            required_keys = ['metadata', 'content', 'validation']
            missing_keys = [key for key in required_keys if key not in data]
            
            if missing_keys:
                print(f"❌ Validation failed: Missing required keys: {', '.join(missing_keys)}")
                return 1
                
            print(f"✅ Artifact validation passed: {artifact_path}")
            return 0
            
        except Exception as e:
            print(f"❌ Error: {e}")
            return 1

def main():
    """Main entry point"""
    
    parser = argparse.ArgumentParser(
        description='GL Quantum Artifact CLI - Convert and manage artifacts',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Convert DOCX to YAML
  python artifact-cli.py convert document.docx -o artifact.yaml
  
  # Batch convert directory
  python artifact-cli.py batch ./docs ./artifacts
  
  # Validate artifact
  python artifact-cli.py validate artifact.yaml
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Convert command
    convert_parser = subparsers.add_parser('convert', help='Convert artifact to structured format')
    convert_parser.add_argument('input', help='Input file path')
    convert_parser.add_argument('-o', '--output', help='Output file path')
    convert_parser.add_argument('-f', '--format', help='Input format (docx, pdf, markdown)')
    
    # Batch convert command
    batch_parser = subparsers.add_parser('batch', help='Batch convert directory')
    batch_parser.add_argument('input_dir', help='Input directory')
    batch_parser.add_argument('output_dir', help='Output directory')
    batch_parser.add_argument('-f', '--format', help='Input format')
    
    # Validate command
    validate_parser = subparsers.add_parser('validate', help='Validate artifact structure')
    validate_parser.add_argument('artifact', help='Artifact file path')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
        
    cli = ArtifactCLI()
    
    if args.command == 'convert':
        return cli.convert(args.input, args.output, args.format)
    elif args.command == 'batch':
        return cli.batch_convert(args.input_dir, args.output_dir, args.format)
    elif args.command == 'validate':
        return cli.validate(args.artifact)
    else:
        parser.print_help()
        return 1

if __name__ == '__main__':
    sys.exit(main())