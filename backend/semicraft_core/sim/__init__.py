"""Local subprocess sim runner (P3-03a — first slice of the P3-03 sim sandbox).

Public seam::

    from semicraft_core.sim import SimResult, run_smoke

See :mod:`semicraft_core.sim.runner` for the implementation and status
semantics.
"""

from __future__ import annotations

from .runner import SimResult, run_smoke

__all__ = ["SimResult", "run_smoke"]
