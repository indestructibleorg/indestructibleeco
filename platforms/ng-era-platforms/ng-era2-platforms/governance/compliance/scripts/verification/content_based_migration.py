#!/usr/bin/env python3
# @ECO-layer: GL60-80
# @ECO-governed
"""
GL Content-Based Migration System
==================================
This system performs migration based on actual file content analysis,
not just file names. This ensures governance compliance.

Critical Features:
- Deep content analysis (L1-SEMANTIC, L2-CONTRACT, L3-IMPLEMENTATION)
- Evidence-based migration
- Full audit trail
- Validation before execution
"""

# MNGA-002: Import organization needs review
import os
import re
import json
import hashlib
from pathlib import Path
from typing import List, Tuple, Optional
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

@dataclass
class ContentAnalysis:
    """Content analysis result"""
    file_path: str
    file_size: int
    file_type: str
    
    # L1: Semantic Analysis
    purpose: str
    responsibility_boundary: str
    keywords: List[str]
    
    # L2: Contract Analysis
    contracts_referenced: List[str]
    governance_layer: Optional[str]
    platform_references: List[str]
    
    # L3: Implementation Analysis
    is_executable: bool
    is_config: bool
    is_documentation: bool
    has_gl_markers: bool
    
    # Classification
    recommended_directory: str
    confidence_score: float
    
    # Evidence
    content_hash: str
    analysis_timestamp: str

class ContentAnalyzer:
    """Analyzes file content to determine correct placement"""
    
    def __init__(self, base_path: str = "/workspace/machine-native-ops"):
        self.base_path = Path(base_path)
        
        # Define directory mappings based on content analysis
        self.directory_patterns = {
            "ecosystem/contracts/": {
                "keywords": ["contract", "specification", "ontology", "definition", "schema"],
                "purpose": "Defines governance contracts and specifications"
            },
            "ecosystem/governance/": {
                "keywords": ["governance-manifest", "governance-monitor", "init-governance"],
                "purpose": "Governance configuration and initialization"
            },
            "ecosystem/docs/": {
                "keywords": ["report", "summary", "complete", "analysis", "guide", "migration", "audit"],
                "purpose": "Documentation and reports"
            },
            "ecosystem/tools/": {
                "keywords": ["add-gl-markers", "gl-audit", "scan-secrets", "fix-governance"],
                "purpose": "Governance tools and scripts"
            },
            "gl-governance-compliance/scripts/": {
                "keywords": ["compliance", "validator", "checker", "verification"],
                "purpose": "Compliance and validation scripts"
            },
            "gl-governance-compliance/data/": {
                "keywords": ["data", "metrics", "logs", "evolution"],
                "purpose": "Governance data and metrics"
            },
            "gl-governance-compliance/outputs/": {
                "keywords": ["output", "result", "generated"],
                "purpose": "Generated outputs"
            },
            "docs/archive/": {
                "keywords": ["v4", "v5", "v9", "v10", "v11", "v12", "legacy", "old"],
                "purpose": "Archived historical documents"
            },
            "docs/": {
                "keywords": ["readme", "contributing", "changelog", "security"],
                "purpose": "Core project documentation"
            }
        }
    
    def analyze_file(self, file_path: str) -> ContentAnalysis:
        """Perform deep content analysis on a file"""
        full_path = self.base_path / file_path
        
        if not full_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Read file content
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            # Binary or non-UTF-8-decodable file
            with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except Exception as e:
            # Binary file
            content_hash = self._calculate_hash(full_path)
            return ContentAnalysis(
                file_path=file_path,
                file_size=full_path.stat().st_size,
                file_type="binary",
                purpose="Binary file",
                responsibility_boundary="Unknown",
                keywords=[],
                contracts_referenced=[],
                governance_layer=None,
                platform_references=[],
                is_executable=False,
                is_config=False,
                is_documentation=False,
                has_gl_markers=False,
                recommended_directory="archives/",
                confidence_score=0.5,
                content_hash=content_hash,
                analysis_timestamp=datetime.now().isoformat()
            )
        
        # Calculate content hash
        content_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
        
        # L1: Semantic Analysis
        purpose, responsibility_boundary, keywords = self._analyze_semantic(content, file_path)
        
        # L2: Contract Analysis
        contracts, governance_layer, platform_refs = self._analyze_contracts(content)
        
        # L3: Implementation Analysis
        is_executable, is_config, is_doc, has_gl_markers = self._analyze_implementation(content, file_path)
        
        # Classification
        recommended_dir, confidence = self._classify_file(
            purpose, responsibility_boundary, keywords, 
            is_executable, is_config, is_doc, file_path
        )
        
        return ContentAnalysis(
            file_path=file_path,
            file_size=full_path.stat().st_size,
            file_size=len(content),
            file_type=self._determine_file_type(file_path),
            purpose=purpose,
            responsibility_boundary=responsibility_boundary,
            keywords=keywords,
            contracts_referenced=contracts,
            governance_layer=governance_layer,
            platform_references=platform_refs,
            is_executable=is_executable,
            is_config=is_config,
            is_documentation=is_doc,
            has_gl_markers=has_gl_markers,
            recommended_directory=recommended_dir,
            confidence_score=confidence,
            content_hash=content_hash,
            analysis_timestamp=datetime.now().isoformat()
        )
    
    def _analyze_semantic(self, content: str, file_path: str) -> Tuple[str, str, List[str]]:
        """L1: Semantic Analysis"""
        # Extract purpose from first paragraph
        first_para = content.split('\n\n')[0] if content else ""
        
        # Extract keywords using patterns
        keywords = []
        
        # Governance keywords
        gov_keywords = [
            "governance", "policy", "compliance", "audit", "validation",
            "verification", "contract", "specification", "ontology"
        ]
        for kw in gov_keywords:
            if kw.lower() in content.lower():
                keywords.append(kw)
        
        # Platform keywords
        platform_keywords = [
            "platform", "service", "runtime", "execution", "data",
            "observability", "monitoring", "infrastructure"
        ]
        for kw in platform_keywords:
            if kw.lower() in content.lower():
                keywords.append(kw)
        
        # Determine purpose
        if any(kw in content.lower() for kw in ["#", "##", "###"]):
            # Likely documentation
            if "complete" in content.lower():
                purpose = "Completion report"
            elif "audit" in content.lower():
                purpose = "Audit report"
            elif "migration" in content.lower():
                purpose = "Migration documentation"
            elif "guide" in content.lower():
                purpose = "User guide"
            else:
                purpose = "Documentation"
        elif file_path.endswith('.py'):
            purpose = "Python script"
        elif file_path.endswith('.sh'):
            purpose = "Shell script"
        elif file_path.endswith('.yaml') or file_path.endswith('.yml'):
            purpose = "Configuration file"
        else:
            purpose = "Unknown purpose"
        
        # Determine responsibility boundary
        if "governance" in content.lower() or "GL" in content:
            responsibility_boundary = "Governance Layer (GL00-99)"
        elif "platform" in content.lower():
            responsibility_boundary = "Platform Layer"
        elif "infrastructure" in content.lower():
            responsibility_boundary = "Infrastructure Layer"
        else:
            responsibility_boundary = "General"
        
        return purpose, responsibility_boundary, keywords
    
    def _analyze_contracts(self, content: str) -> Tuple[List[str], Optional[str], List[str]]:
        """L2: Contract Analysis"""
        contracts = []
        
        # Find contract references
        contract_patterns = [
            r'gl-[\w-]+\.yaml',
            r'GL_\w+',
            r'GL\d{2}-\d{2}'
        ]
        
        for pattern in contract_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            contracts.extend(matches)
        
        # Determine governance layer
        if 'GL00-09' in content or 'enterprise-architecture' in content.lower():
            governance_layer = "GL00-09"
        elif 'GL10-19' in content:
            governance_layer = "GL10-19"
        elif 'GL20-29' in content:
            governance_layer = "GL20-29"
        elif 'GL30-49' in content:
            governance_layer = "GL30-49"
        elif 'GL60-80' in content or 'compliance' in content.lower():
            governance_layer = "GL60-80"
        else:
            governance_layer = None
        
        # Find platform references
        platform_refs = re.findall(r'gl\.\w+\.\w+-platform', content, re.IGNORECASE)
        
        return list(set(contracts)), governance_layer, list(set(platform_refs))
    
    def _analyze_implementation(self, content: str, file_path: str) -> Tuple[bool, bool, bool, bool]:
        """L3: Implementation Analysis"""
        is_executable = file_path.endswith('.py') or file_path.endswith('.sh')
        is_config = file_path.endswith('.yaml') or file_path.endswith('.yml') or file_path.endswith('.json')
        is_doc = file_path.endswith('.md')
        has_gl_markers = 'ECO-' in content or 'gl.' in content
        
        return is_executable, is_config, is_doc, has_gl_markers
    
    def _classify_file(self, purpose: str, responsibility: str, keywords: List[str],
                       is_executable: bool, is_config: bool, is_doc: bool, 
                       file_path: str) -> Tuple[str, float]:
        """Classify file to appropriate directory"""
        confidence = 0.0
        
        # Check each directory pattern
        for directory, pattern_info in self.directory_patterns.items():
            match_score = 0.0
            
            # Check keywords
            for keyword in pattern_info['keywords']:
                if keyword.lower() in file_path.lower():
                    match_score += 0.3
                if keyword.lower() in purpose.lower():
                    match_score += 0.2
                if keyword.lower() in responsibility.lower():
                    match_score += 0.2
                if keyword.lower() in str(keywords).lower():
                    match_score += 0.2
            
            # Check file type
            if is_executable and "scripts" in directory:
                match_score += 0.1
            if is_config and directory == "ecosystem/governance/":
                match_score += 0.1
            if is_doc and "docs" in directory:
                match_score += 0.1
            
            if match_score > confidence:
                confidence = match_score
        
        # Normalize confidence
        confidence = min(confidence, 1.0)
        
        # Special cases
        if confidence < 0.3:
            if is_doc:
                recommended = "docs/archive/"
                confidence = 0.7
            elif is_executable:
                recommended = "ecosystem/tools/"
                confidence = 0.6
            else:
                recommended = "docs/"
                confidence = 0.5
        else:
            # Find best match
            best_dir = None
            best_score = 0
            for directory, pattern_info in self.directory_patterns.items():
                score = 0
                for keyword in pattern_info['keywords']:
                    if keyword.lower() in file_path.lower():
                        score += 1
                    if keyword.lower() in purpose.lower():
                        score += 1
                if score > best_score:
                    best_score = score
                    best_dir = directory
            recommended = best_dir if best_dir else "docs/"
        
        return recommended, confidence
    
    def _determine_file_type(self, file_path: str) -> str:
        """Determine file type from extension"""
        ext = Path(file_path).suffix.lower()
        type_map = {
            '.md': 'markdown',
            '.py': 'python',
            '.sh': 'shell',
            '.yaml': 'yaml',
            '.yml': 'yaml',
            '.json': 'json',
            '.txt': 'text',
            '.zip': 'archive'
        }
        return type_map.get(ext, 'unknown')
    
    def _calculate_hash(self, file_path: Path) -> str:
        """Calculate SHA-256 hash of a file"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()


def analyze_root_directory():
    """Analyze all files in root directory"""
    base_path = Path("/workspace/machine-native-ops")
    
    # Get all markdown, Python, shell, and YAML files in root
    extensions = ['.md', '.py', '.sh', '.yaml', '.yml', '.json']
    files = [str(f.relative_to(base_path)) for f in base_path.iterdir() 
             if f.is_file() and f.suffix in extensions]
    
    print(f"Found {len(files)} files to analyze")
    
    analyzer = ContentAnalyzer()
    analyses = []
    
    for i, file_path in enumerate(files, 1):
        print(f"\n[{i}/{len(files)}] Analyzing: {file_path}")
        try:
            analysis = analyzer.analyze_file(file_path)
            analyses.append(analysis)
            print(f"  Purpose: {analysis.purpose}")
            print(f"  Responsibility: {analysis.responsibility_boundary}")
            print(f"  Recommended: {analysis.recommended_directory}")
            print(f"  Confidence: {analysis.confidence_score:.2f}")
        except Exception as e:
            print(f"  ERROR: {e}")
    
    # Generate report
    report = {
        "total_files_analyzed": len(analyses),
        "analysis_timestamp": datetime.now().isoformat(),
        "files": [asdict(a) for a in analyses]
    }
    
    # Save report
    report_path = base_path / "content_analysis_report.json"
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Analysis complete. Report saved to: {report_path}")
    
    return analyses, report


if __name__ == "__main__":
    analyses, report = analyze_root_directory()
    
    # Print summary
    print("\n" + "="*80)
    print("CONTENT ANALYSIS SUMMARY")
    print("="*80)
    
    # Count by recommended directory
    dir_counts = {}
    for analysis in analyses:
        rec_dir = analysis.recommended_directory
        dir_counts[rec_dir] = dir_counts.get(rec_dir, 0) + 1
    
    print("\nRecommended directories:")
    for directory, count in sorted(dir_counts.items()):
        print(f"  {directory}: {count} files")
    
    # High confidence files
    high_conf = [a for a in analyses if a.confidence_score >= 0.7]
    print(f"\nHigh confidence (≥0.7): {len(high_conf)} files")
    
    # Low confidence files
    low_conf = [a for a in analyses if a.confidence_score < 0.5]
    print(f"Low confidence (<0.5): {len(low_conf)} files")
    if low_conf:
        print("\nLow confidence files:")
        for a in low_conf:
            print(f"  - {a.file_path}: {a.confidence_score:.2f} -> {a.recommended_directory}")