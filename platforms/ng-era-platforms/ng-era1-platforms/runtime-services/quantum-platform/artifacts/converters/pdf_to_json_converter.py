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
GL Quantum Artifact Converter - PDF to JSON
Converts PDF documents to structured JSON artifacts
"""

"""
Module docstring
================

This module is part of the GL governance framework.
Please add specific module documentation here.
"""
# MNGA-002: Import organization needs review
import os
import sys
import json
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime
import PyPDF2
from PyPDF2 import PdfReader

class PDFToJSONConverter:
    """Convert PDF documents to structured JSON artifacts"""
    
    def __init__(self, input_path: str, output_path: str = None):
        self.input_path = Path(input_path)
        self.output_path = Path(output_path) if output_path else self.input_path.with_suffix('.json')
        
    def extract_document_structure(self, reader: PdfReader) -> Dict[str, Any]:
        """Extract structured content from PDF"""
        
        structure = {
            'metadata': {
                'title': '',
                'author': '',
                'subject': '',
                'creator': '',
                'producer': '',
                'pages': len(reader.pages),
                'created': datetime.now().isoformat(),
                'version': '1.0.0',
                'type': 'artifact',
                'format': 'json',
                'source': str(self.input_path)
            },
            'content': {
                'pages': [],
                'text': '',
                'structure': []
            },
            'validation': {
                'required_fields': True,
                'structure_valid': True
            }
        }
        
        # Extract metadata
        metadata = reader.metadata
        if metadata:
            structure['metadata']['title'] = metadata.get('/Title', '')
            structure['metadata']['author'] = metadata.get('/Author', '')
            structure['metadata']['subject'] = metadata.get('/Subject', '')
            structure['metadata']['creator'] = metadata.get('/Creator', '')
            structure['metadata']['producer'] = metadata.get('/Producer', '')
            
        # Extract pages
        all_text = []
        for page_num, page in enumerate(reader.pages):
            text = page.extract_text()
            all_text.append(text)
            
            structure['content']['pages'].append({
                'page_number': page_num + 1,
                'text': text,
                'word_count': len(text.split())
            })
            
        structure['content']['text'] = '\n'.join(all_text)
        
        # Detect structure (headings, paragraphs)
        structure['content']['structure'] = self.detect_structure(all_text)
        
        return structure
        
    def detect_structure(self, pages: List[str]) -> List[Dict[str, Any]]:
        """Detect document structure from pages"""
        
        structure = []
        
        for page_num, page_text in enumerate(pages):
            lines = page_text.split('\n')
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                # Detect headings (uppercase, short lines)
                if len(line) < 100 and line.isupper():
                    structure.append({
                        'type': 'heading',
                        'page': page_num + 1,
                        'content': line,
                        'level': 1
                    })
                # Detect subheadings
                elif line.startswith(('Chapter', 'Section', 'Part')):
                    structure.append({
                        'type': 'heading',
                        'page': page_num + 1,
                        'content': line,
                        'level': 2
                    })
                # Regular paragraph
                elif len(line) > 50:
                    structure.append({
                        'type': 'paragraph',
                        'page': page_num + 1,
                        'content': line,
                        'word_count': len(line.split())
                    })
                    
        return structure
        
    def convert(self) -> Dict[str, Any]:
        """Convert PDF to JSON structure"""
        
        if not self.input_path.exists():
            raise FileNotFoundError(f"Input file not found: {self.input_path}")
            
        with open(self.input_path, 'rb') as f:
            reader = PdfReader(f)
            structure = self.extract_document_structure(reader)
            
        return structure
        
    def save_json(self, data: Dict[str, Any], output_path: Path = None):
        """Save JSON artifact"""
        
        output = output_path or self.output_path
        output.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            
        return output
        
    def validate_structure(self, data: Dict[str, Any]) -> bool:
        """Validate JSON structure"""
        
        required_keys = ['metadata', 'content', 'validation']
        for key in required_keys:
            if key not in data:
                return False
                
        return True

def main():
    """Main entry point"""
    
    if len(sys.argv) < 2:
        print("Usage: python pdf-to-json-converter.py <input.pdf> [output.json]")
        sys.exit(1)
        
    input_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None
    
    converter = PDFToJSONConverter(input_path, output_path)
    
    try:
        structure = converter.convert()
        
        if converter.validate_structure(structure):
            output_file = converter.save_json(structure)
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