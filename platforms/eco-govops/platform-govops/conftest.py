"""Root conftest — add src/ to sys.path so tests resolve platform imports."""
from __future__ import annotations

import sys
from pathlib import Path

# Insert the platform's src directory at the front of sys.path so that
# bare imports like ``from engine.orchestrator.closed_loop import …`` work.
_src = str(Path(__file__).resolve().parent / "src")
if _src not in sys.path:
    sys.path.insert(0, _src)
