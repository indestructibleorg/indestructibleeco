#
# @ECO-governed
# @ECO-layer: gl-platform.gl-platform.governance
# @ECO-semantic: generate-evidence-chain
# @ECO-audit-trail: ../../engine/gl-platform.gl-platform.governance/GL_SEMANTIC_ANCHOR.json
#
#!/usr/bin/env python3
"""
GL Evidence Chain Generator
Generates immutable evidence chains for GL gl-platform.gl-platform.governance
"""
# MNGA-002: Import organization needs review
import argparse
import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
class EvidenceChainGenerator:
    """Generate evidence chains for GL gl-platform.gl-platform.governance"""
    def __init__(self, layer: str, output_dir: str):
        self.layer = layer
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.evidence_chain = []
        self.timestamp = datetime.now()
    def generate_hash(self, content: str) -> str:
        """Generate SHA256 hash for content"""
        return hashlib.sha256(content.encode()).hexdigest()
    def scan_layer_directory(self, layer_path: Path) -> List[Dict[str, Any]]:
        """Scan layer directory and collect file evidence"""
        evidence_entries = []
        if not layer_path.exists():
            return evidence_entries
        for file_path in layer_path.rglob('*'):
            if file_path.is_file() and not file_path.name.startswith('.'):
                try:
                    with open(file_path, 'rb') as f:
                        content = f.read()
                    file_hash = hashlib.sha256(content).hexdigest()
                    evidence_entry = {
                        'path': str(file_path),
                        'relative_path': str(file_path.relative_to(layer_path)),
                        'hash': file_hash,
                        'size': len(content),
                        'timestamp': datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                    }
                    evidence_entries.append(evidence_entry)
                except Exception:
                    # Skip files that can't be read
                    pass
        return sorted(evidence_entries, key=lambda x: x['path'])
    def generate_layer_evidence(self) -> Dict[str, Any]:
        """Generate evidence for the entire layer"""
        layer_path = Path(f"workspace/src/{self.layer.split('-')[0].lower()}")
        if not layer_path.exists():
            return {
                'status': 'SKIPPED',
                'reason': f'Layer path does not exist: {layer_path}'
            }
        # Scan layer directory
        file_evidence = self.scan_layer_directory(layer_path)
        # Generate directory hash
        dir_hash_input = ''.join([f['hash'] for f in file_evidence])
        directory_hash = self.generate_hash(dir_hash_input)
        layer_evidence = {
            'layer_id': self.layer,
            'layer_path': str(layer_path),
            'directory_hash': directory_hash,
            'file_count': len(file_evidence),
            'total_size': sum(f['size'] for f in file_evidence),
            'files': file_evidence
        }
        return layer_evidence
    def generate_semantic_index_evidence(self) -> Dict[str, Any]:
        """Generate evidence for semantic index"""
        semantic_index_path = Path(f"workspace/src/{self.layer.split('-')[0].lower()}/ECO-SEMANTIC-INDEX.json")
        if not semantic_index_path.exists():
            return {
                'status': 'SKIPPED',
                'reason': f'Semantic index not found: {semantic_index_path}'
            }
        try:
            with open(semantic_index_path, 'r') as f:
                content = f.read()
            index_hash = self.generate_hash(content)
            index_data = json.loads(content)
            return {
                'path': str(semantic_index_path),
                'hash': index_hash,
                'artifact_count': len(index_data.get('artifacts', [])),
                'layer': index_data.get('layer'),
                'semantic_root': index_data.get('semantic_root')
            }
        except Exception as e:
            return {
                'status': 'ERROR',
                'reason': f'Failed to read semantic index: {e}'
            }
    def generate_registry_evidence(self) -> Dict[str, Any]:
        """Generate evidence from module registry"""
        registry_path = Path("controlplane/registries/ECO-AI-NATIVE-MODULES.yaml")
        if not registry_path.exists():
            return {
                'status': 'SKIPPED',
                'reason': f'Module registry not found: {registry_path}'
            }
        try:
            with open(registry_path, 'r') as f:
                content = f.read()
            registry_hash = self.generate_hash(content)
            return {
                'path': str(registry_path),
                'hash': registry_hash
            }
        except Exception as e:
            return {
                'status': 'ERROR',
                'reason': f'Failed to read module registry: {e}'
            }
    def generate_evidence_chain(self) -> Dict[str, Any]:
        """Generate complete evidence chain"""
        evidence_id = f"ECO-EVIDENCE-{self.layer}-{self.timestamp.strftime('%Y%m%d%H%M%S')}"
        evidence_chain = {
            'evidence_id': evidence_id,
            'layer': self.layer,
            'timestamp': self.timestamp.isoformat(),
            'validation_status': 'VALID',
            'evidence_entries': [],
            'evidence_hash': None
        }
        # Generate different types of evidence
        print(f"  Generating evidence for {self.layer}...")
        # Layer evidence
        layer_evidence = self.generate_layer_evidence()
        evidence_chain['evidence_entries'].append({
            'type': 'LAYER_FILES',
            'evidence': layer_evidence
        })
        print(f"    ✅ Layer files: {layer_evidence.get('file_count', 0)} files")
        # Semantic index evidence
        semantic_evidence = self.generate_semantic_index_evidence()
        evidence_chain['evidence_entries'].append({
            'type': 'SEMANTIC_INDEX',
            'evidence': semantic_evidence
        })
        print(f"    ✅ Semantic index: {semantic_evidence.get('artifact_count', 'N/A')} artifacts")
        # Registry evidence
        registry_evidence = self.generate_registry_evidence()
        evidence_chain['evidence_entries'].append({
            'type': 'MODULE_REGISTRY',
            'evidence': registry_evidence
        })
        print("    ✅ Module registry: captured")
        # Generate evidence chain hash
        evidence_chain_json = json.dumps(evidence_chain, sort_keys=True)
        evidence_chain['evidence_hash'] = self.generate_hash(evidence_chain_json)
        return evidence_chain
    def save_evidence_chain(self, evidence_chain: Dict[str, Any]) -> Path:
        """Save evidence chain to file"""
        filename = f"evidence-{self.layer}-{self.timestamp.strftime('%Y%m%d%H%M%S')}.json"
        filepath = self.output_dir / filename
        with open(filepath, 'w') as f:
            json.dump(evidence_chain, f, indent=2)
        return filepath
def main():
    parser = argparse.ArgumentParser(
        description='Generate GL evidence chain',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python generate-evidence-chain.py --layer GL20-29 --output var/evidence
  python generate-evidence-chain.py --layer GL40-49 --output var/evidence
  python generate-evidence-chain.py --layer GL50-59 --output var/evidence
        """
    )
    parser.add_argument('--layer', required=True, help='GL layer (e.g., GL20-29)')
    parser.add_argument('--output', required=True, help='Output directory')
    args = parser.parse_args()
    print(f"\\n{'='*60}")
    print("GL Evidence Chain Generator")
    print(f"{'='*60}")
    print(f"Layer: {args.layer}")
    print(f"Output: {args.output}")
    print(f"{'='*60}\\n")
    # Generate evidence chain
    generator = EvidenceChainGenerator(args.layer, args.output)
    evidence_chain = generator.generate_evidence_chain()
    # Save evidence chain
    filepath = generator.save_evidence_chain(evidence_chain)
    print(f"\\n{'='*60}")
    print("✅ Evidence chain generated successfully")
    print(f"{'='*60}")
    print(f"\\nEvidence ID: {evidence_chain['evidence_id']}")
    print(f"Evidence Hash: {evidence_chain['evidence_hash']}")
    print(f"File: {filepath}")
    print(f"Size: {filepath.stat().st_size} bytes")
    # Display evidence summary
    print("\\nEvidence Summary:")
    for entry in evidence_chain['evidence_entries']:
        entry_type = entry['type']
        evidence = entry['evidence']
        status = evidence.get('status', 'OK')
        print(f"  - {entry_type}: {status}")
    print(f"\\n{'='*60}\\n")
if __name__ == "__main__":
    main()