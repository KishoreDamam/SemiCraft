"""Golden case matrix for the ``pwm`` module (Phase-2 P2-08).

Same ``CASES`` contract as the snippet golden dirs (tests/golden/conftest.py):
each entry maps a case name to an options dict as POSTed to generate. The
golden runner (test_snapshots.py) calls ``semicraft_core.generate`` — which
works for modules too — and snapshots the RTL only. No snapshot files are
committed here; the orchestrator runs ``pytest --update-golden`` to
materialize them.

PwmOptions: ``resolution`` (4..16, default 8), ``duty_input`` (port/param,
default port), ``invert_output`` (default False), plus the common clocked
fields ``reset_style``/``reset_polarity``.
"""

from __future__ import annotations

CASES: dict[str, dict] = {
    "defaults": {},
    # --- single-option flips from default -----------------------------------
    "resolution_4": {"resolution": 4},
    "resolution_16": {"resolution": 16},
    "duty_param": {"duty_input": "param"},
    "inverted": {"invert_output": True},
    # --- reset style x polarity matrix (all four must appear) ---------------
    "reset_sync_active_low": {"reset_style": "sync", "reset_polarity": "active_low"},
    "reset_sync_active_high": {"reset_style": "sync", "reset_polarity": "active_high"},
    "reset_async_active_low": {"reset_style": "async", "reset_polarity": "active_low"},
    "reset_async_active_high": {"reset_style": "async", "reset_polarity": "active_high"},
    # --- verilog-pinned -----------------------------------------------------
    "verilog_param_inverted": {
        "language": "verilog",
        "duty_input": "param",
        "invert_output": True,
    },
    # --- pairwise / small combos --------------------------------------------
    "param_inverted_narrow": {
        "duty_input": "param",
        "invert_output": True,
        "resolution": 6,
    },
    "port_async_high_wide": {
        "duty_input": "port",
        "reset_style": "async",
        "reset_polarity": "active_high",
        "resolution": 12,
    },
}

__all__ = ["CASES"]
