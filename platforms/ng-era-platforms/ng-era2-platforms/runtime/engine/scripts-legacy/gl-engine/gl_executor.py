#
# @ECO-governed
# @ECO-layer: gl-platform.gl-platform.governance
# @ECO-semantic: gl_executor
# @ECO-audit-trail: ../../engine/gl-platform.gl-platform.governance/GL_SEMANTIC_ANCHOR.json
#
#!/usr/bin/env python3
"""
GL Layer Executor - Governance Layer Execution Engine
MachineNativeOps GL Architecture Implementation
This module provides the core execution engine for GL (Governance Layers) operations,
enabling automated gl-platform.gl-platform.governance artifact management, validation, and orchestration.
"""
# MNGA-002: Import organization needs review
import sys
import yaml
import json
import logging
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod
# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('GLExecutor')
class GLLayer(Enum):
    """GL Layer enumeration with metadata."""
    GL00_09 = ("GL00-09", "Strategic Layer", "戰略層")
    GL10_29 = ("GL10-29", "Operational Layer", "運營層")
    GL30_49 = ("GL30-49", "Execution Layer", "執行層")
    GL50_59 = ("GL50-59", "Observability Layer", "觀測層")
    GL60_80 = ("GL60-80", "Advanced/Feedback Layer", "進階/回饋層")
    GL81_83 = ("GL81-83", "Extended Layer", "擴展層")
    GL90_99 = ("GL90-99", "Meta-Specification Layer", "元規範層")
    def __init__(self, layer_id: str, name_en: str, name_zh: str):
        self.layer_id = layer_id
        self.name_en = name_en
        self.name_zh = name_zh
    @classmethod
    def from_string(cls, layer_str: str) -> Optional['GLLayer']:
        """Get GLLayer from string identifier."""
        for layer in cls:
            if layer.layer_id == layer_str:
                return layer
        return None
@dataclass
class GLArtifact:
    """Represents a GL gl-platform.gl-platform.governance artifact."""
    api_version: str
    kind: str
    metadata: Dict[str, Any]
    spec: Dict[str, Any]
    status: Dict[str, Any] = field(default_factory=dict)
    file_path: Optional[str] = None
    @property
    def name(self) -> str:
        return self.metadata.get('name', 'unknown')
    @property
    def layer(self) -> Optional[GLLayer]:
        layer_str = self.metadata.get('layer', '')
        return GLLayer.from_string(layer_str)
    @property
    def version(self) -> str:
        return self.metadata.get('version', '0.0.0')
    @property
    def owner(self) -> str:
        return self.metadata.get('owner', 'unknown')
    @classmethod
    def from_dict(cls, data: Dict[str, Any], file_path: Optional[str] = None) -> 'GLArtifact':
        """Create GLArtifact from dictionary."""
        return cls(
            api_version=data.get('apiVersion', ''),
            kind=data.get('kind', ''),
            metadata=data.get('metadata', {}),
            spec=data.get('spec', {}),
            status=data.get('status', {}),
            file_path=file_path
        )
    @classmethod
    def from_file(cls, file_path: Path) -> 'GLArtifact':
        """Load GLArtifact from YAML file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        return cls.from_dict(data, str(file_path))
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'apiVersion': self.api_version,
            'kind': self.kind,
            'metadata': self.metadata,
            'spec': self.spec,
            'status': self.status
        }
    def save(self, file_path: Optional[Path] = None):
        """Save artifact to YAML file."""
        path = file_path or Path(self.file_path) if self.file_path else None
        if not path:
            raise ValueError("No file path specified")
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            yaml.dump(self.to_dict(), f, default_flow_style=False, allow_unicode=True, sort_keys=False)
@dataclass
class ExecutionContext:
    """Context for GL execution operations."""
    workspace_path: Path
    layer: Optional[GLLayer] = None
    dry_run: bool = False
    verbose: bool = False
    config: Dict[str, Any] = field(default_factory=dict)
    def __post_init__(self):
        self.workspace_path = Path(self.workspace_path)
@dataclass
class ExecutionResult:
    """Result of a GL execution operation."""
    success: bool
    message: str
    data: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    artifacts_processed: int = 0
    execution_time: float = 0.0
class GLCommand(ABC):
    """Abstract base class for GL commands."""
    @property
    @abstractmethod
    def name(self) -> str:
        """Command name."""
        pass
    @property
    @abstractmethod
    def description(self) -> str:
        """Command description."""
        pass
    @abstractmethod
    def execute(self, context: ExecutionContext, **kwargs) -> ExecutionResult:
        """Execute the command."""
        pass
class ListArtifactsCommand(GLCommand):
    """List all GL artifacts."""
    @property
    def name(self) -> str:
        return "list"
    @property
    def description(self) -> str:
        return "List all GL artifacts in the workspace"
    def execute(self, context: ExecutionContext, **kwargs) -> ExecutionResult:
        """List artifacts."""
        import time
        start_time = time.time()
        artifacts = []
        gl-platform.gl-platform.governance_path = context.workspace_path / 'workspace' / 'gl-platform.gl-platform.governance'
        if not gl-platform.gl-platform.governance_path.exists():
            return ExecutionResult(
                success=False,
                message=f"Governance path not found: {gl-platform.gl-platform.governance_path}",
                errors=[f"Path does not exist: {gl-platform.gl-platform.governance_path}"]
            )
        yaml_files = list(gl-platform.gl-platform.governance_path.rglob('*.yaml')) + list(gl-platform.gl-platform.governance_path.rglob('*.yml'))
        for file_path in yaml_files:
            try:
                artifact = GLArtifact.from_file(file_path)
                if artifact.api_version:  # Valid GL artifact
                    artifact_info = {
                        'name': artifact.name,
                        'kind': artifact.kind,
                        'layer': artifact.layer.layer_id if artifact.layer else 'unknown',
                        'version': artifact.version,
                        'owner': artifact.owner,
                        'file': str(file_path.relative_to(context.workspace_path))
                    }
                    # Filter by layer if specified
                    if context.layer:
                        if artifact.layer == context.layer:
                            artifacts.append(artifact_info)
                    else:
                        artifacts.append(artifact_info)
            except Exception as e:
                logger.debug(f"Skipping {file_path}: {e}")
        execution_time = time.time() - start_time
        return ExecutionResult(
            success=True,
            message=f"Found {len(artifacts)} artifacts",
            data={'artifacts': artifacts},
            artifacts_processed=len(artifacts),
            execution_time=execution_time
        )
class ValidateCommand(GLCommand):
    """Validate GL artifacts."""
    @property
    def name(self) -> str:
        return "validate"
    @property
    def description(self) -> str:
        return "Validate GL artifacts against specifications"
    def execute(self, context: ExecutionContext, **kwargs) -> ExecutionResult:
        """Validate artifacts."""
        import time
        start_time = time.time()
        errors = []
        warnings = []
        validated = 0
        gl-platform.gl-platform.governance_path = context.workspace_path / 'workspace' / 'gl-platform.gl-platform.governance'
        yaml_files = list(gl-platform.gl-platform.governance_path.rglob('*.yaml')) + list(gl-platform.gl-platform.governance_path.rglob('*.yml'))
        for file_path in yaml_files:
            try:
                artifact = GLArtifact.from_file(file_path)
                if not artifact.api_version:
                    continue
                validated += 1
                file_errors, file_warnings = self._validate_artifact(artifact)
                for err in file_errors:
                    errors.append(f"{file_path}: {err}")
                for warn in file_warnings:
                    warnings.append(f"{file_path}: {warn}")
            except Exception as e:
                errors.append(f"{file_path}: Parse error - {e}")
        execution_time = time.time() - start_time
        return ExecutionResult(
            success=len(errors) == 0,
            message=f"Validated {validated} artifacts, {len(errors)} errors, {len(warnings)} warnings",
            data={
                'validated': validated,
                'error_count': len(errors),
                'warning_count': len(warnings)
            },
            errors=errors,
            warnings=warnings,
            artifacts_processed=validated,
            execution_time=execution_time
        )
    def _validate_artifact(self, artifact: GLArtifact) -> Tuple[List[str], List[str]]:
        """Validate a single artifact."""
        errors = []
        warnings = []
        # Required fields
        if not artifact.api_version:
            errors.append("Missing apiVersion")
        if not artifact.kind:
            errors.append("Missing kind")
        if not artifact.metadata:
            errors.append("Missing metadata")
        else:
            required_metadata = ['name', 'version', 'created_at', 'owner', 'layer']
            for field in required_metadata:
                if field not in artifact.metadata:
                    errors.append(f"Missing metadata.{field}")
        if not artifact.spec:
            errors.append("Missing spec")
        # Layer validation
        if artifact.layer is None and artifact.metadata.get('layer'):
            warnings.append(f"Unknown layer: {artifact.metadata.get('layer')}")
        # Version format
        version = artifact.version
        if version and not self._is_valid_semver(version):
            warnings.append(f"Version '{version}' is not valid semver")
        return errors, warnings
    def _is_valid_semver(self, version: str) -> bool:
        """Check if version follows semver format."""
        import re
        pattern = r'^(\d+)\.(\d+)\.(\d+)(-[a-zA-Z0-9]+)?(\+[a-zA-Z0-9]+)?$'
        return bool(re.match(pattern, version))
class GenerateCommand(GLCommand):
    """Generate GL artifacts from templates."""
    @property
    def name(self) -> str:
        return "generate"
    @property
    def description(self) -> str:
        return "Generate GL artifacts from templates"
    def execute(self, context: ExecutionContext, **kwargs) -> ExecutionResult:
        """Generate artifact."""
        import time
        start_time = time.time()
        artifact_type = kwargs.get('artifact_type', '')
        artifact_name = kwargs.get('artifact_name', '')
        owner = kwargs.get('owner', 'gl-platform.gl-platform.governance-team')
        if not context.layer:
            return ExecutionResult(
                success=False,
                message="Layer must be specified for generation",
                errors=["Missing --layer parameter"]
            )
        if not artifact_type or not artifact_name:
            return ExecutionResult(
                success=False,
                message="Artifact type and name must be specified",
                errors=["Missing --type or --name parameter"]
            )
        # Generate artifact
        now = datetime.utcnow().isoformat() + 'Z'
        artifact_data = {
            'apiVersion': 'gl-platform.gl-platform.governance.machinenativeops.io/v2',
            'kind': self._get_kind(artifact_type),
            'metadata': {
                'name': artifact_name,
                'version': '1.0.0',
                'created_at': now,
                'updated_at': now,
                'owner': owner,
                'layer': context.layer.layer_id,
                'tags': [context.layer.layer_id.lower(), artifact_type],
                'annotations': {
                    'generator': 'gl-executor',
                    'generated_at': now
                }
            },
            'spec': self._get_default_spec(artifact_type),
            'status': {
                'phase': 'draft',
                'conditions': []
            }
        }
        artifact = GLArtifact.from_dict(artifact_data)
        # Determine output path
        layer_dirs = {
            GLLayer.GL00_09: 'strategic',
            GLLayer.GL10_29: 'operational',
            GLLayer.GL30_49: 'execution',
            GLLayer.GL50_59: 'observability',
            GLLayer.GL60_80: 'feedback',
            GLLayer.GL81_83: 'extended',
            GLLayer.GL90_99: 'meta-spec',
        }
        output_dir = context.workspace_path / 'workspace' / 'gl-platform.gl-platform.governance' / layer_dirs.get(context.layer, 'other')
        output_file = output_dir / f"{artifact_name.lower().replace(' ', '-')}.yaml"
        if not context.dry_run:
            artifact.save(output_file)
            message = f"Generated artifact: {output_file}"
        else:
            message = f"[DRY RUN] Would generate artifact: {output_file}"
        execution_time = time.time() - start_time
        return ExecutionResult(
            success=True,
            message=message,
            data={
                'artifact': artifact.to_dict(),
                'output_path': str(output_file)
            },
            artifacts_processed=1,
            execution_time=execution_time
        )
    def _get_kind(self, artifact_type: str) -> str:
        """Get kind from artifact type."""
        kind_map = {
            'vision_statement': 'VisionStatement',
            'strategic_objectives': 'StrategicObjectives',
            'gl-platform.gl-platform.governance_charter': 'GovernanceCharter',
            'risk_register': 'RiskRegister',
            'operational_plan': 'OperationalPlan',
            'sop': 'StandardOperatingProcedure',
            'resource_allocation': 'ResourceAllocation',
            'project_plan': 'ProjectPlan',
            'test_report': 'TestReport',
            'deployment_record': 'DeploymentRecord',
            'metrics_definition': 'MetricsDefinition',
            'alert_rules': 'AlertRules',
            'slo_report': 'SLOReport',
            'ab_test_design': 'ABTestDesign',
            'model_retraining_log': 'ModelRetrainingLog',
            'innovation_experiment': 'InnovationExperiment',
            'meta_specification': 'MetaSpecification',
            'validation_report': 'ValidationReport',
        }
        return kind_map.get(artifact_type, artifact_type.title().replace('_', ''))
    def _get_default_spec(self, artifact_type: str) -> Dict[str, Any]:
        """Get default spec for artifact type."""
        default_specs = {
            'vision_statement': {
                'vision': {'statement': '# TODO: Define vision', 'horizon': '5 years'},
                'mission': {'statement': '# TODO: Define mission'},
                'values': [],
                'strategic_pillars': []
            },
            'strategic_objectives': {
                'objectives': [],
                'dependencies': [],
                'resources': {'budget': 0, 'headcount': 0}
            },
            'operational_plan': {
                'alignment': {'strategic_objectives': []},
                'initiatives': [],
                'resource_allocation': {},
                'gl-platform.gl-platform.governance': {'review_cadence': 'monthly'}
            },
            'metrics_definition': {
                'metrics': [],
                'dashboards': []
            },
            'alert_rules': {
                'rules': []
            },
            'project_plan': {
                'overview': {'title': '# TODO', 'description': '# TODO'},
                'team': {},
                'timeline': {},
                'work_breakdown': [],
                'risks': []
            }
        }
        return default_specs.get(artifact_type, {'description': '# TODO: Define specification'})
class ReportCommand(GLCommand):
    """Generate GL reports."""
    @property
    def name(self) -> str:
        return "report"
    @property
    def description(self) -> str:
        return "Generate GL gl-platform.gl-platform.governance reports"
    def execute(self, context: ExecutionContext, **kwargs) -> ExecutionResult:
        """Generate report."""
        import time
        start_time = time.time()
        report_type = kwargs.get('report_type', 'summary')
        kwargs.get('output_format', 'markdown')
        # Collect data
        list_cmd = ListArtifactsCommand()
        list_result = list_cmd.execute(context)
        validate_cmd = ValidateCommand()
        validate_result = validate_cmd.execute(context)
        # Generate report
        if report_type == 'summary':
            report = self._generate_summary_report(list_result, validate_result)
        elif report_type == 'detailed':
            report = self._generate_detailed_report(list_result, validate_result)
        elif report_type == 'layer':
            report = self._generate_layer_report(list_result, validate_result, context.layer)
        else:
            report = self._generate_summary_report(list_result, validate_result)
        # Save report
        reports_dir = context.workspace_path / 'reports' / 'gl-gl-platform.gl-platform.governance'
        reports_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        report_file = reports_dir / f"gl-report-{report_type}-{timestamp}.md"
        if not context.dry_run:
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(report)
        execution_time = time.time() - start_time
        return ExecutionResult(
            success=True,
            message=f"Generated {report_type} report: {report_file}",
            data={
                'report_path': str(report_file),
                'report_type': report_type,
                'artifacts_count': list_result.artifacts_processed,
                'validation_errors': len(validate_result.errors)
            },
            execution_time=execution_time
        )
    def _generate_summary_report(self, list_result: ExecutionResult, validate_result: ExecutionResult) -> str:
        """Generate summary report."""
        artifacts = list_result.data.get('artifacts', [])
        # Count by layer
        by_layer = {}
        for artifact in artifacts:
            layer = artifact.get('layer', 'unknown')
            by_layer[layer] = by_layer.get(layer, 0) + 1
        # Count by kind
        by_kind = {}
        for artifact in artifacts:
            kind = artifact.get('kind', 'unknown')
            by_kind[kind] = by_kind.get(kind, 0) + 1
        report = []
        report.append("# GL Governance Summary Report\n")
        report.append(f"**Generated**: {datetime.utcnow().isoformat()}Z\n")
        report.append("## Overview\n")
        report.append(f"- **Total Artifacts**: {len(artifacts)}")
        report.append(f"- **Validation Errors**: {len(validate_result.errors)}")
        report.append(f"- **Validation Warnings**: {len(validate_result.warnings)}")
        report.append("")
        report.append("## Artifacts by Layer\n")
        report.append("| Layer | Count |")
        report.append("|-------|-------|")
        for layer in sorted(by_layer.keys()):
            report.append(f"| {layer} | {by_layer[layer]} |")
        report.append("")
        report.append("## Artifacts by Kind\n")
        report.append("| Kind | Count |")
        report.append("|------|-------|")
        for kind in sorted(by_kind.keys()):
            report.append(f"| {kind} | {by_kind[kind]} |")
        report.append("")
        if validate_result.errors:
            report.append("## Validation Errors\n")
            for error in validate_result.errors[:10]:
                report.append(f"- {error}")
            if len(validate_result.errors) > 10:
                report.append(f"\n*... and {len(validate_result.errors) - 10} more errors*")
        return '\n'.join(report)
    def _generate_detailed_report(self, list_result: ExecutionResult, validate_result: ExecutionResult) -> str:
        """Generate detailed report."""
        artifacts = list_result.data.get('artifacts', [])
        report = []
        report.append("# GL Governance Detailed Report\n")
        report.append(f"**Generated**: {datetime.utcnow().isoformat()}Z\n")
        # Group by layer
        by_layer = {}
        for artifact in artifacts:
            layer = artifact.get('layer', 'unknown')
            if layer not in by_layer:
                by_layer[layer] = []
            by_layer[layer].append(artifact)
        for layer in sorted(by_layer.keys()):
            layer_artifacts = by_layer[layer]
            report.append(f"## {layer}\n")
            report.append(f"**Artifact Count**: {len(layer_artifacts)}\n")
            report.append("| Name | Kind | Version | Owner |")
            report.append("|------|------|---------|-------|")
            for artifact in layer_artifacts:
                report.append(f"| {artifact['name']} | {artifact['kind']} | {artifact['version']} | {artifact['owner']} |")
            report.append("")
        return '\n'.join(report)
    def _generate_layer_report(self, list_result: ExecutionResult, validate_result: ExecutionResult, layer: Optional[GLLayer]) -> str:
        """Generate layer-specific report."""
        if not layer:
            return self._generate_summary_report(list_result, validate_result)
        artifacts = [a for a in list_result.data.get('artifacts', []) if a.get('layer') == layer.layer_id]
        report = []
        report.append(f"# {layer.layer_id}: {layer.name_en} ({layer.name_zh}) Report\n")
        report.append(f"**Generated**: {datetime.utcnow().isoformat()}Z\n")
        report.append("## Overview\n")
        report.append(f"- **Layer**: {layer.layer_id}")
        report.append(f"- **Name (EN)**: {layer.name_en}")
        report.append(f"- **Name (ZH)**: {layer.name_zh}")
        report.append(f"- **Artifact Count**: {len(artifacts)}")
        report.append("")
        report.append("## Artifacts\n")
        if artifacts:
            report.append("| Name | Kind | Version | Owner | File |")
            report.append("|------|------|---------|-------|------|")
            for artifact in artifacts:
                report.append(f"| {artifact['name']} | {artifact['kind']} | {artifact['version']} | {artifact['owner']} | {artifact['file']} |")
        else:
            report.append("*No artifacts found for this layer*")
        return '\n'.join(report)
class GLExecutor:
    """Main GL Execution Engine."""
    def __init__(self, workspace_path: str = '.'):
        self.workspace_path = Path(workspace_path).resolve()
        self.commands: Dict[str, GLCommand] = {}
        self._register_default_commands()
    def _register_default_commands(self):
        """Register default commands."""
        commands = [
            ListArtifactsCommand(),
            ValidateCommand(),
            GenerateCommand(),
            ReportCommand(),
        ]
        for cmd in commands:
            self.register_command(cmd)
    def register_command(self, command: GLCommand):
        """Register a command."""
        self.commands[command.name] = command
    def execute(self, command_name: str, context: ExecutionContext, **kwargs) -> ExecutionResult:
        """Execute a command."""
        if command_name not in self.commands:
            return ExecutionResult(
                success=False,
                message=f"Unknown command: {command_name}",
                errors=[f"Available commands: {', '.join(self.commands.keys())}"]
            )
        command = self.commands[command_name]
        logger.info(f"Executing command: {command_name}")
        if context.verbose:
            logger.info(f"Context: layer={context.layer}, dry_run={context.dry_run}")
        try:
            result = command.execute(context, **kwargs)
            if result.success:
                logger.info(f"Command completed: {result.message}")
            else:
                logger.error(f"Command failed: {result.message}")
                for error in result.errors:
                    logger.error(f"  - {error}")
            return result
        except Exception as e:
            logger.exception(f"Command execution failed: {e}")
            return ExecutionResult(
                success=False,
                message=f"Execution error: {str(e)}",
                errors=[str(e)]
            )
def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='GL Layer Executor - Governance Layer Execution Engine',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List all artifacts
  python gl_executor.py list
  # List artifacts for a specific layer
  python gl_executor.py list --layer GL00-09
  # Validate all artifacts
  python gl_executor.py validate
  # Generate a new artifact
  python gl_executor.py generate --layer GL00-09 --type vision_statement --name my-vision
  # Generate a report
  python gl_executor.py report --type summary
        """
    )
    parser.add_argument('command', choices=['list', 'validate', 'generate', 'report'],
                        help='Command to execute')
    parser.add_argument('--workspace', '-w', default='.',
                        help='Workspace path (default: current directory)')
    parser.add_argument('--layer', '-l', choices=[l.layer_id for l in GLLayer],
                        help='Target GL layer')
    parser.add_argument('--type', '-t', dest='artifact_type',
                        help='Artifact type (for generate command)')
    parser.add_argument('--name', '-n', dest='artifact_name',
                        help='Artifact name (for generate command)')
    parser.add_argument('--owner', '-o', default='gl-platform.gl-platform.governance-team',
                        help='Artifact owner (for generate command)')
    parser.add_argument('--report-type', '-r', dest='report_type',
                        choices=['summary', 'detailed', 'layer'], default='summary',
                        help='Report type (for report command)')
    parser.add_argument('--output-format', '-f', dest='output_format',
                        choices=['markdown', 'json', 'yaml'], default='markdown',
                        help='Output format')
    parser.add_argument('--dry-run', '-d', action='store_true',
                        help='Dry run mode (no changes)')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Verbose output')
    parser.add_argument('--json', action='store_true',
                        help='Output results as JSON')
    args = parser.parse_args()
    # Create context
    layer = GLLayer.from_string(args.layer) if args.layer else None
    context = ExecutionContext(
        workspace_path=Path(args.workspace),
        layer=layer,
        dry_run=args.dry_run,
        verbose=args.verbose
    )
    # Create executor and run
    executor = GLExecutor(args.workspace)
    kwargs = {
        'artifact_type': args.artifact_type,
        'artifact_name': args.artifact_name,
        'owner': args.owner,
        'report_type': args.report_type,
        'output_format': args.output_format,
    }
    result = executor.execute(args.command, context, **kwargs)
    # Output results
    if args.json:
        output = {
            'success': result.success,
            'message': result.message,
            'data': result.data,
            'errors': result.errors,
            'warnings': result.warnings,
            'artifacts_processed': result.artifacts_processed,
            'execution_time': result.execution_time
        }
        print(json.dumps(output, indent=2, default=str))
    else:
        print(f"\n{'='*60}")
        print(f"GL Executor - {args.command.upper()}")
        print(f"{'='*60}")
        print(f"Status: {'✅ SUCCESS' if result.success else '❌ FAILED'}")
        print(f"Message: {result.message}")
        print(f"Artifacts Processed: {result.artifacts_processed}")
        print(f"Execution Time: {result.execution_time:.2f}s")
        if result.errors:
            print(f"\nErrors ({len(result.errors)}):")
            for error in result.errors[:10]:
                print(f"  - {error}")
            if len(result.errors) > 10:
                print(f"  ... and {len(result.errors) - 10} more")
        if result.warnings:
            print(f"\nWarnings ({len(result.warnings)}):")
            for warning in result.warnings[:5]:
                print(f"  - {warning}")
            if len(result.warnings) > 5:
                print(f"  ... and {len(result.warnings) - 5} more")
        if args.verbose and result.data:
            print("\nData:")
            print(json.dumps(result.data, indent=2, default=str))
    sys.exit(0 if result.success else 1)
if __name__ == '__main__':
    main()