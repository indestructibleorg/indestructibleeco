"""Root conftest — ensure both this platform's src/ and _shared/src/ are importable."""

import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent

# This platform's source
_SRC = _HERE / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

# Shared kernel source
_SHARED_SRC = _HERE.parent / "_shared" / "src"
if str(_SHARED_SRC) not in sys.path:
    sys.path.insert(0, str(_SHARED_SRC))
