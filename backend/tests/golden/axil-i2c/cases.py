"""Golden case matrix for the ``axil-i2c`` IP (Phase-4 P4-07).

The divisor axis matters more here than for the other serial IPs: an I2C bit
is four quarter-phases, so the divisor sets the SDA setup window as well as
the line rate, and ``1`` is the degenerate case where a quarter is a single
aclk cycle.

``input_sync_stages`` interacts with clock stretching — the stall the
testbench inserts has to outlast the synchroniser or the master would never
see SCL go low at all.

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
    # --- bit rate ------------------------------------------------------------
    "divisor_1_fastest": {"default_divisor": 1},
    "divisor_5": {"default_divisor": 5},
    "divisor_9": {"default_divisor": 9},
    # --- synchroniser --------------------------------------------------------
    "sync_4_stages": {"input_sync_stages": 4},
    # --- reset skeleton ------------------------------------------------------
    "async_reset": {"reset_style": "async"},
    # --- verilog-pinned ------------------------------------------------------
    "verilog_slow_deep_sync": {
        "language": "verilog",
        "default_divisor": 12,
        "input_sync_stages": 3,
    },
}

__all__ = ["CASES"]
