"""End-to-end test: Validate complete govops-platform structure."""

import os

PLATFORM_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


REQUIRED_DIRS = [
    "src/domain",
    "src/domain/entities",
    "src/domain/value_objects",
    "src/application",
    "src/engine",
    "src/infrastructure",
    "src/presentation",
    "src/shared",
    "tests/unit",
    "tests/integration",
    "tests/e2e",
    "k8s/base",
    "helm",
    "monitoring",
    ".platform",
    "scripts",
]

REQUIRED_FILES = [
    "pyproject.toml",
    "Dockerfile.prod",
    "docker-compose.yaml",
    ".platform/manifest.yaml",
    ".platform/extraction.yaml",
    ".platform/dependencies.yaml",
]


def test_required_directories_exist():
    """Verify all required directories are present."""
    missing = []
    for d in REQUIRED_DIRS:
        path = os.path.join(PLATFORM_ROOT, d)
        if not os.path.isdir(path):
            missing.append(d)
    assert missing == [], f"Missing directories:\n" + "\n".join(missing)


def test_required_files_exist():
    """Verify all required files are present."""
    missing = []
    for f in REQUIRED_FILES:
        path = os.path.join(PLATFORM_ROOT, f)
        if not os.path.isfile(path):
            missing.append(f)
    assert missing == [], f"Missing files:\n" + "\n".join(missing)


def test_domain_entities_present():
    """Verify core domain entity files exist."""
    entities_dir = os.path.join(PLATFORM_ROOT, "src", "domain", "entities")
    expected = ["evidence.py", "governance_module.py", "gate.py", "scan_report.py"]
    for name in expected:
        path = os.path.join(entities_dir, name)
        assert os.path.isfile(path), f"Missing entity: {name}"


def test_source_files_are_valid_python():
    """Verify all .py files in src/ can be parsed."""
    import ast

    errors = []
    src_dir = os.path.join(PLATFORM_ROOT, "src")
    for root, _dirs, files in os.walk(src_dir):
        for fname in files:
            if not fname.endswith(".py"):
                continue
            filepath = os.path.join(root, fname)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    ast.parse(f.read(), filename=filepath)
            except SyntaxError as exc:
                errors.append(f"{filepath}: {exc}")
    assert errors == [], f"Syntax errors found:\n" + "\n".join(errors)
