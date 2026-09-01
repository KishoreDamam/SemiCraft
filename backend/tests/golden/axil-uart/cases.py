"""Golden case matrix for the ``axil-uart`` IP (Phase-4 P4-05b).

The second composed IP, and the first with real sequential protocol logic, so
these goldens pin the framing as well as the splice.

Axes:

- ``default_divisor`` — clocks per bit, which sets every bit boundary in the
  generated testbench. ``2`` is the smallest usable value (the receiver waits
  half a divisor to reach mid-bit); ``13`` is deliberately odd, so the
  half-period truncates.
- ``input_sync_stages`` — flops between the asynchronous rx pin and the
  receiver.
- ``reset_style`` — the always_ff skeleton for both the register block and the
  UART logic.

No reset-polarity axis: AXI4-Lite fixes it active-low.

A ``styled_names`` case pins the naming axis. Nothing covered it until P4-11,
and three separate restyling bugs shipped behind that gap: assertion specs
naming canonical resets (P3-05a), a hardcoded testbench clock net (P4-07), and
datasheet port tables that never applied the name map at all. Every generated
artifact resolves identifiers through ``build_name_map``; a case that changes
every identifier is what makes a generator that forgot to visible.
"""

from __future__ import annotations

CASES: dict[str, dict] = {
    # --- naming style (the axis no golden case covered until P4-11) ---------
    "styled_names": {
        "language": "sv",
        "naming": {"convention": "camel", "prefix": "p_"},
    },
    "defaults": {},
    # --- line rate -----------------------------------------------------------
    "divisor_2": {"default_divisor": 2},
    "divisor_13_odd": {"default_divisor": 13},
    "divisor_434": {"default_divisor": 434},
    # --- synchroniser depth --------------------------------------------------
    "sync_4_stages": {"input_sync_stages": 4},
    # --- reset skeleton ------------------------------------------------------
    "async_reset": {"reset_style": "async"},
    # --- verilog-pinned ------------------------------------------------------
    "verilog_slow_deep_sync": {
        "language": "verilog",
        "default_divisor": 16,
        "input_sync_stages": 3,
    },
}

__all__ = ["CASES"]
