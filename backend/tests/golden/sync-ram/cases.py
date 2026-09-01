"""Golden case matrix for the ``sync-ram`` IP (Phase-4 P4-04).

Same ``CASES`` contract as every other golden dir (tests/golden/conftest.py).

Axes are the ones that change the emitted module's shape:

- ``port_mode`` — single-port shares one ``addr``; simple dual-port splits it
  into ``waddr``/``raddr``, which also changes the bundle layout (one bundle
  vs two, because a port may belong to at most one bundle).
- ``read_enable`` — removes the ``re`` port and the ``if`` around the read.
- ``width``/``depth`` — the storage declaration and the address width.

There is no reset axis: this IP has no reset (see the module docstring), so
reset style and polarity are not options.

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
    # --- port topology -------------------------------------------------------
    "simple_dual": {"port_mode": "simple_dual"},
    "no_read_enable": {"read_enable": False},
    "dual_without_read_enable": {
        "port_mode": "simple_dual",
        "read_enable": False,
    },
    # --- geometry ------------------------------------------------------------
    "depth_2_width_1": {"depth": 2, "width": 1},
    "wide_deep": {"depth": 1024, "width": 64},
    # --- verilog-pinned ------------------------------------------------------
    "verilog_dual_wide": {
        "language": "verilog",
        "port_mode": "simple_dual",
        "width": 32,
        "depth": 4096,
    },
}

__all__ = ["CASES"]
