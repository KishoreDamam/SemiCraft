"""Golden case matrix for the ``sync-fifo`` IP (Phase-4 P4-03a).

Same ``CASES`` contract as every other golden dir (tests/golden/conftest.py).

Axes chosen for what they change in the emitted RTL:

- ``depth`` — sets the pointer width and the memory declaration. ``2`` is the
  smallest legal FIFO (a single index bit plus the wrap bit) and ``1024``
  checks that a deep FIFO does not explode the testbench: the fill and drain
  phases hold their enable for one driven cycle and idle, which the TB
  generator coalesces into a ``repeat``.
- ``width`` — ``1`` is the degenerate payload where the ordered-readback
  phase has only one distinct non-zero value to work with.
- ``count_output`` — removes an output and its continuous assignment.
- reset style x polarity — the ``always_ff`` skeleton.
"""

from __future__ import annotations

CASES: dict[str, dict] = {
    "defaults": {},
    # --- geometry ------------------------------------------------------------
    "depth_2_width_1": {"depth": 2, "width": 1},
    "depth_4_width_16": {"depth": 4, "width": 16},
    "deep_1024": {"depth": 1024, "width": 16},
    "wide_64": {"depth": 16, "width": 64},
    # --- optional output -----------------------------------------------------
    "no_count_output": {"count_output": False},
    # --- reset matrix --------------------------------------------------------
    "reset_async_active_low": {"reset_style": "async", "reset_polarity": "active_low"},
    "reset_sync_active_high": {"reset_style": "sync", "reset_polarity": "active_high"},
    # --- verilog-pinned ------------------------------------------------------
    "verilog_deep_no_count": {
        "language": "verilog",
        "depth": 256,
        "count_output": False,
    },
}

__all__ = ["CASES"]
