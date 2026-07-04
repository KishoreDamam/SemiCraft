"""SemiCraft core generation engine (IR, rendering, snippets, lint).

This package has zero web dependencies — importing it must not pull in
FastAPI or any web framework.

Public entry point (IMPLEMENTATION_PLAN §3 task 4)::

    from semicraft_core import generate
    result = generate("counter", {"width": 16, "direction": "up"})
    result.code, result.filename, result.explanation, result.config_hash

``semicraft_core.generate`` is the end-to-end function; it is re-exported here
so ``semicraft_core.generate(...)`` works directly (the name shadows the
``semicraft_core.generate`` submodule for attribute access, which is
intentional — the function is the public surface).
"""

from __future__ import annotations

from .generate import GenerateResult, config_hash, generate
from .version import VERSION

__all__ = ["generate", "GenerateResult", "config_hash", "VERSION"]
