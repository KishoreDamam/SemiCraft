"""Golden case matrix for the ``edge-detector`` module (Phase-2 P2-04).

Same ``CASES`` contract as the snippet golden dirs (tests/golden/conftest.py):
each entry maps a case name to an options dict as POSTed to generate. The
golden runner (test_snapshots.py) calls ``semicraft_core.generate`` — which
works for modules too (it drives ``generate``/``explain`` and reads
language/include_wrapper via getattr) — and snapshots the RTL only.

Coverage (mirrors the snippet golden layout): defaults + one flip per option +
all four reset_style x reset_polarity combos + one verilog-pinned case + two
pairwise combos. No snapshot files are committed here; the orchestrator runs
``pytest --update-golden`` to materialize them.

EdgeDetectorOptions: ``detect`` (rising/falling/both, default rising),
``width`` (default 1), ``registered_output`` (default True), plus the common
clocked fields ``reset_style``/``reset_polarity``.
"""

from __future__ import annotations

CASES: dict[str, dict] = {
    "defaults": {},
    # --- single-option flips from default -----------------------------------
    "detect_falling": {"detect": "falling"},
    "detect_both": {"detect": "both"},
    "width_8": {"width": 8},
    "combinational": {"registered_output": False},
    # --- reset style x polarity matrix (all four must appear) ---------------
    "reset_sync_active_low": {"reset_style": "sync", "reset_polarity": "active_low"},
    "reset_sync_active_high": {"reset_style": "sync", "reset_polarity": "active_high"},
    "reset_async_active_low": {"reset_style": "async", "reset_polarity": "active_low"},
    "reset_async_active_high": {"reset_style": "async", "reset_polarity": "active_high"},
    # --- verilog-pinned -----------------------------------------------------
    "verilog_both_wide": {"language": "verilog", "detect": "both", "width": 4},
    # --- pairwise / small combos --------------------------------------------
    "falling_combinational_wide": {
        "detect": "falling",
        "registered_output": False,
        "width": 16,
    },
    "both_async_high_reg": {
        "detect": "both",
        "reset_style": "async",
        "reset_polarity": "active_high",
    },
}

__all__ = ["CASES"]
