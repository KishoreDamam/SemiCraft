"""Golden case matrix for the ``shift-register`` snippet (WP-08 layout).

``CASES`` maps a case name to an options dict exactly as it would be POSTed to
``/api/v1/generate``. Per IMPLEMENTATION_PLAN §5 WP-08 task 2: defaults case +
one case per option flipping it from default + 2-3 pairwise combos; every
reset_style x reset_polarity combination must appear at least once (clocked
snippet); at least one language-pinned verilog case.

Shift-register options (semicraft_core/snippets/shift_register.py,
ShiftRegisterOptions): ``depth`` (default 8), ``direction`` (left/right,
default right), ``parallel_load`` (default False), ``serial_out_only``
(default False), ``enable`` (default True), plus the common clocked fields
``reset_style``/``reset_polarity``.
"""

from __future__ import annotations

CASES: dict[str, dict] = {
    "defaults": {},
    # --- single-option flips from default -----------------------------------
    "depth_16": {"depth": 16},
    "direction_left": {"direction": "left"},
    "parallel_load_on": {"parallel_load": True},
    "serial_out_only_on": {"serial_out_only": True},
    "enable_off": {"enable": False},
    # --- reset style x polarity matrix (all four must appear) ---------------
    "reset_sync_active_low": {"reset_style": "sync", "reset_polarity": "active_low"},
    "reset_sync_active_high": {"reset_style": "sync", "reset_polarity": "active_high"},
    "reset_async_active_low": {"reset_style": "async", "reset_polarity": "active_low"},
    "reset_async_active_high": {"reset_style": "async", "reset_polarity": "active_high"},
    # --- pairwise / small combos ---------------------------------------------
    "left_parallel_load": {"direction": "left", "parallel_load": True},
    "serial_out_only_no_enable": {"serial_out_only": True, "enable": False},
    "wide_left_parallel_load": {"depth": 32, "direction": "left", "parallel_load": True},
    # --- language-pinned case -------------------------------------------------
    "verilog_parallel_load": {"parallel_load": True, "language": "verilog"},
}

__all__ = ["CASES"]
