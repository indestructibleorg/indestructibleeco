"""Integration test: Validate platform isolation — no cross-platform dependencies."""

import os
import subprocess


PLATFORM_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC_DIR = os.path.join(PLATFORM_ROOT, "src")

# Patterns that indicate cross-platform coupling
FORBIDDEN_PATTERNS = [
    "from superai",
    "import superai",
    "from govops",
    "import govops",
    "from machinenativeops",
    "import machinenativeops",
]


def test_no_cross_platform_imports():
    """Ensure no source file imports from sibling platforms."""
    violations = []
    for root, _dirs, files in os.walk(SRC_DIR):
        for fname in files:
            if not fname.endswith(".py"):
                continue
            filepath = os.path.join(root, fname)
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                for lineno, line in enumerate(f, 1):
                    for pattern in FORBIDDEN_PATTERNS:
                        if pattern in line and not line.strip().startswith("#"):
                            violations.append(f"{filepath}:{lineno}: {line.strip()}")
    assert violations == [], f"Cross-platform imports found:\n" + "\n".join(violations)


def test_platform_manifest_exists():
    """Ensure .platform/manifest.yaml exists."""
    manifest = os.path.join(PLATFORM_ROOT, ".platform", "manifest.yaml")
    assert os.path.isfile(manifest), f"Missing: {manifest}"


def test_extraction_manifest_exists():
    """Ensure .platform/extraction.yaml exists."""
    extraction = os.path.join(PLATFORM_ROOT, ".platform", "extraction.yaml")
    assert os.path.isfile(extraction), f"Missing: {extraction}"


def test_dependencies_manifest_exists():
    """Ensure .platform/dependencies.yaml exists."""
    deps = os.path.join(PLATFORM_ROOT, ".platform", "dependencies.yaml")
    assert os.path.isfile(deps), f"Missing: {deps}"
