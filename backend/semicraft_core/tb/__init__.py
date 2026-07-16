"""Testbench generation and its IR node family (P3-01).

Separate from the synthesizable IR by design (plan cross-cutting decision 2):
testbench constructs never appear in ``semicraft_core.ir``, and the
synthesizable validator never sees these nodes. The node family (``nodes.py``)
covers the P2 smoke set plus the Phase 3 additions (fork/join, tasks, timeout
watchdog, waveform dump, SVA-property stub); :func:`validate_tb` enforces the
TB_SPEC T-rules, including the TB/RTL separation invariant. See
``docs/TB_SPEC.md``.
"""

from .generate_tb import generate_tb
from .render_tb import render_tb
from .scripts import emit_makefile, emit_run_script
from .validate import TbValidationError, validate_tb

__all__ = [
    "generate_tb",
    "render_tb",
    "validate_tb",
    "TbValidationError",
    "emit_run_script",
    "emit_makefile",
]
