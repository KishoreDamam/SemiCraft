"""Golden case matrix for the ``lfsr`` module (Phase-2 P2-11).

Same ``CASES`` contract as the snippet golden dirs (tests/golden/conftest.py):
each entry maps a case name to an options dict as POSTed to generate. The
golden runner (test_snapshots.py) calls ``semicraft_core.generate`` — which
works for modules too — and snapshots the RTL only. No snapshot files are
committed here; the orchestrator runs ``pytest --update-golden`` to
materialize them.

LfsrOptions: ``width`` (Literal[4,8,16,24,32], default 8), ``init_value``
(default 1), ``enable`` (default True), ``output_style`` (parallel/serial,
default parallel), plus the common clocked fields ``reset_style``/
``reset_polarity``.
"""

from __future__ import annotations

CASES: dict[str, dict] = {
    "defaults": {},
    # --- single-option flips from default, one per required width -----------
    "width_4": {"width": 4},
    "width_8": {"width": 8},
    "width_16": {"width": 16},
    "width_24": {"width": 24},
    "width_32": {"width": 32},
    "init_value_custom": {"init_value": 0b101},
    "enable_off": {"enable": False},
    "output_style_serial": {"output_style": "serial"},
    # --- reset style x polarity matrix (all four must appear) ---------------
    "reset_sync_active_low": {"reset_style": "sync", "reset_polarity": "active_low"},
    "reset_sync_active_high": {"reset_style": "sync", "reset_polarity": "active_high"},
    "reset_async_active_low": {"reset_style": "async", "reset_polarity": "active_low"},
    "reset_async_active_high": {"reset_style": "async", "reset_polarity": "active_high"},
    # --- verilog-pinned -----------------------------------------------------
    "verilog_serial_width16": {
        "language": "verilog",
        "output_style": "serial",
        "width": 16,
    },
    # --- pairwise / small combos --------------------------------------------
    "serial_no_enable_width32": {
        "output_style": "serial",
        "enable": False,
        "width": 32,
    },
    "custom_seed_async_high_width24": {
        "init_value": 0xABCDE1,
        "reset_style": "async",
        "reset_polarity": "active_high",
        "width": 24,
    },
}

__all__ = ["CASES"]
