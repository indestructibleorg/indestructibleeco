# 
# @ECO-governed
# @ECO-layer: data
# @ECO-semantic: instant_archiver_v1
# @ECO-audit-trail: ../../engine/gov-platform.governance/GL_SEMANTIC_ANCHOR.json
#
# GL Unified Architecture Governance Framework Activated

#!/usr/bin/env python3
"""
INSTANT Archive System v1.0.0
Autonomous archival with <5s execution time
"""
# MNGA-002: Import organization needs review
import os
import json
import hashlib
import tarfile
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict
import logging
# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
class InstantArchiver:
    """INSTANT Archive System - Autonomous archival with validation"""
    def __init__(self, source_dir: str, archive_dir: str):
        self.source_dir = Path(source_dir)
        self.archive_dir = Path(archive_dir)
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        # Validate paths
        if not self.source_dir.exists():
            raise ValueError(f"Source directory does not exist: {source_dir}")
        # Create archive directory if needed
        self.archive_dir.mkdir(parents=True, exist_ok=True)
    def _preflight_checks(self):
        """Pre-execution validation"""
        # 1. Check disk space
        stat = shutil.disk_usage(self.archive_dir)
        required_space = sum(f.stat().st_size for f in self.source_dir.rglob('*') if f.is_file()) * 2
        if stat.free < required_space:
            raise Exception(f"Insufficient disk space: need {required_space/1024/1024:.2f}MB, have {stat.free/1024/1024:.2f}MB")
        # 2. Check write permissions
        if not os.access(self.archive_dir, os.W_OK):
            raise Exception(f"No write permission: {self.archive_dir}")
        # 3. Check source exists and readable
        if not os.access(self.source_dir, os.R_OK):
            raise Exception(f"No read permission: {self.source_dir}")
        logger.info("✅ Pre-flight checks passed")
    def execute_instant_archive(self) -> Dict:
        """
        Execute INSTANT archive pipeline
        Returns: Execution results with metrics
        """
        start_time = datetime.now()
        logger.info("🚀 Starting INSTANT archive execution")
        try:
            # Pre-flight checks
            self._preflight_checks()
            # Stage 1: Instant Analysis (target: 0.3s)
            logger.info("📊 Stage 1: Instant Analysis")
            analysis = self._instant_analysis()
            stage1_time = (datetime.now() - start_time).total_seconds()
            logger.info(f"✅ Analysis complete: {stage1_time:.2f}s")
            # Stage 2: Smart Archive (target: 1.2s)
            logger.info("🗜️ Stage 2: Smart Archive")
            stage2_start = datetime.now()
            archive_path = self._smart_archive(analysis)
            stage2_time = (datetime.now() - stage2_start).total_seconds()
            logger.info(f"✅ Archive complete: {stage2_time:.2f}s")
            # Stage 3: Instant Validation (target: 0.8s)
            logger.info("🔍 Stage 3: Instant Validation")
            stage3_start = datetime.now()
            validation = self._instant_validation(archive_path, analysis)
            stage3_time = (datetime.now() - stage3_start).total_seconds()
            logger.info(f"✅ Validation complete: {stage3_time:.2f}s")
            total_time = (datetime.now() - start_time).total_seconds()
            result = {
                "status": "REALIZED",
                "execution_time": total_time,
                "stages": {
                    "analysis": stage1_time,
                    "archive": stage2_time,
                    "validation": stage3_time
                },
                "analysis": analysis,
                "archive_path": str(archive_path),
                "validation": validation,
                "timestamp": self.timestamp
            }
            logger.info(f"🎉 INSTANT archive complete: {total_time:.2f}s")
            return result
        except Exception as e:
            logger.error(f"❌ Archive failed: {str(e)}")
            raise
    def _instant_analysis(self) -> Dict:
        """
        Stage 1: Instant Analysis
        Analyze source directory and determine archival strategy
        """
        analysis = {
            "file_count": 0,
            "total_size": 0,
            "file_types": {},
            "directory_structure": [],
            "largest_files": []
        }
        files_info = []
        # Walk directory tree
        for root, dirs, files in os.walk(self.source_dir):
            rel_root = Path(root).relative_to(self.source_dir)
            analysis["directory_structure"].append(str(rel_root))
            for file in files:
                file_path = Path(root) / file
                try:
                    file_size = file_path.stat().st_size
                    file_ext = file_path.suffix.lower()
                    analysis["file_count"] += 1
                    analysis["total_size"] += file_size
                    # Track file types
                    if file_ext:
                        analysis["file_types"][file_ext] = \
                            analysis["file_types"].get(file_ext, 0) + 1
                    # Track file info for largest files
                    files_info.append({
                        "path": str(file_path.relative_to(self.source_dir)),
                        "size": file_size,
                        "ext": file_ext
                    })
                except Exception as e:
                    logger.warning(f"Skipping file {file_path}: {str(e)}")
        # Get top 10 largest files
        files_info.sort(key=lambda x: x["size"], reverse=True)
        analysis["largest_files"] = files_info[:10]
        # Calculate compression estimate
        analysis["estimated_compression_ratio"] = self._estimate_compression(
            analysis["file_types"]
        )
        return analysis
    def _estimate_compression(self, file_types: Dict) -> float:
        """Estimate compression ratio based on file types"""
        # Compression ratios by file type (empirical)
        compression_map = {
            ".md": 0.3,    # Text compresses well
            ".yaml": 0.35,
            ".yml": 0.35,
            ".json": 0.4,
            ".txt": 0.3,
            ".py": 0.35,
            ".js": 0.35,
            ".html": 0.4,
            ".css": 0.4,
            ".docx": 0.7,  # Already compressed
            ".pdf": 0.9,   # Already compressed
            ".png": 0.95,  # Already compressed
            ".jpg": 0.98,  # Already compressed
        }
        if not file_types:
            return 0.5  # Default estimate
        # Weighted average
        total_files = sum(file_types.values())
        weighted_ratio = sum(
            compression_map.get(ext, 0.5) * count 
            for ext, count in file_types.items()
        ) / total_files
        return round(weighted_ratio, 2)
    def _smart_archive(self, analysis: Dict) -> Path:
        """
        Stage 2: Smart Archive
        Create compressed tar archive with metadata
        """
        # Archive filename
        archive_name = f"refactor_playbooks_{self.timestamp}.tar.gz"
        archive_path = self.archive_dir / archive_name
        # Create metadata file
        metadata = {
            "archive_name": archive_name,
            "source_directory": str(self.source_dir),
            "timestamp": self.timestamp,
            "analysis": analysis,
            "compression": "gzip",
            "format": "tar.gz"
        }
        metadata_path = self.archive_dir / f"metadata_{self.timestamp}.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        # Create tar.gz archive
        logger.info(f"Creating archive: {archive_path}")
        with tarfile.open(archive_path, "w:gz") as tar:
            tar.add(self.source_dir, arcname=self.source_dir.name)
        # Calculate actual compression ratio
        archive_size = archive_path.stat().st_size
        original_size = analysis["total_size"]
        actual_ratio = archive_size / original_size if original_size > 0 else 1.0
        logger.info(f"Archive created: {archive_size / 1024 / 1024:.2f} MB")
        logger.info(f"Compression ratio: {actual_ratio:.2%}")
        # Update metadata with actual compression
        metadata["actual_compression_ratio"] = round(actual_ratio, 3)
        metadata["archive_size"] = archive_size
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        return archive_path
    def _instant_validation(self, archive_path: Path, analysis: Dict) -> Dict:
        """
        Stage 3: Instant Validation
        Verify archive integrity and accessibility
        """
        validation = {
            "integrity_check": False,
            "file_count_match": False,
            "accessibility_check": False,
            "checksum": None,
            "errors": []
        }
        try:
            # 1. Integrity Check - verify tar can be opened
            with tarfile.open(archive_path, "r:gz") as tar:
                members = tar.getmembers()
                archive_file_count = len([m for m in members if m.isfile()])
                validation["integrity_check"] = True
                validation["archive_file_count"] = archive_file_count
                # 2. File Count Match
                if archive_file_count == analysis["file_count"]:
                    validation["file_count_match"] = True
                else:
                    validation["errors"].append(
                        f"File count mismatch: expected {analysis['file_count']}, "
                        f"got {archive_file_count}"
                    )
            # 3. Accessibility Check - verify file permissions
            if os.access(archive_path, os.R_OK):
                validation["accessibility_check"] = True
            else:
                validation["errors"].append("Archive not readable")
            # 4. Calculate checksum
            validation["checksum"] = self._calculate_checksum(archive_path)
            # Overall validation status
            validation["status"] = "VERIFIED" if (
                validation["integrity_check"] and
                validation["file_count_match"] and
                validation["accessibility_check"]
            ) else "FAILED"
        except Exception as e:
            validation["errors"].append(f"Validation error: {str(e)}")
            validation["status"] = "FAILED"
        return validation
    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate SHA-256 checksum of file"""
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                sha256.update(chunk)
        return sha256.hexdigest()
def main():
    """Main execution function"""
    # Configuration
    source_dir = "machine-native-ops/workspace/docs/refactor_playbooks"
    archive_dir = "machine-native-ops/ns-root/namespaces-mcp/refactor_playbooks/_archive"
    # Execute INSTANT archive
    archiver = InstantArchiver(source_dir, archive_dir)
    result = archiver.execute_instant_archive()
    # Save result
    result_path = Path(archive_dir) / f"archive_result_{result['timestamp']}.json"
    with open(result_path, 'w') as f:
        json.dump(result, f, indent=2)
    # Print summary
    print("\n" + "="*70)
    print("⚡ INSTANT ARCHIVE COMPLETE")
    print("="*70)
    print(f"Status: {result['status']}")
    print(f"Execution Time: {result['execution_time']:.2f}s")
    print(f"Files Archived: {result['analysis']['file_count']}")
    print(f"Original Size: {result['analysis']['total_size'] / 1024 / 1024:.2f} MB")
    print(f"Archive Path: {result['archive_path']}")
    print(f"Validation: {result['validation']['status']}")
    print("="*70)
    return result
if __name__ == "__main__":
    main()