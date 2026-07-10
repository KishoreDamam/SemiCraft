"""Smoke-testbench generation (P2-13 stub family).

Separate from the synthesizable IR by design (plan cross-cutting decision 2):
testbench constructs never appear in ``semicraft_core.ir``, and the
synthesizable validator never sees these nodes. The full TB node family lands
with Phase 3 (P3-01); this package covers only what module smoke tests need.
See ``docs/TB_SPEC.md``.
"""

from .generate_tb import generate_tb
from .render_tb import render_tb

__all__ = ["generate_tb", "render_tb"]
