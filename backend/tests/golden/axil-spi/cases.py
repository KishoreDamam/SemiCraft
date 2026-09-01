"""Golden case matrix for the ``axil-spi`` IP (Phase-4 P4-06).

All four clock modes are pinned, because CPOL and CPHA change the emitted
hardware in different ways: CPOL is a single inversion on the way out, while
CPHA moves which edge samples *and* changes the width of the receive shift
register (with CPHA=1 the last sample goes straight to RXDATA, so only seven
bits of history are kept).

Other axes:

- ``default_divisor`` — ``1`` is the fastest clock, where an sclk half period
  is a single aclk cycle and the testbench falls back to holding miso at a
  constant because a per-bit pattern cannot settle through the synchroniser.
- ``input_sync_stages`` — same trade-off from the other direction.

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
    # --- clock modes ---------------------------------------------------------
    "mode_01": {"cpha": 1},
    "mode_10": {"cpol": 1},
    "mode_11": {"cpol": 1, "cpha": 1},
    # --- clock rate ----------------------------------------------------------
    "divisor_1_fastest": {"default_divisor": 1},
    "divisor_7": {"default_divisor": 7},
    # --- synchroniser --------------------------------------------------------
    "sync_4_stages": {"input_sync_stages": 4},
    # --- verilog-pinned ------------------------------------------------------
    "verilog_mode_11_slow": {
        "language": "verilog",
        "cpol": 1,
        "cpha": 1,
        "default_divisor": 10,
    },
}

__all__ = ["CASES"]
