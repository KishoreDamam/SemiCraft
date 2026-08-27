"""Golden case matrix for the ``axil-timer`` IP (Phase-4 P4-08).

Axes:

- ``counter_width`` — the RELOAD/COUNT field widths, and therefore whether
  those registers have reserved bits at all. ``32`` fills the data word;
  ``4`` is the narrowest the option allows and still holds the test reload.
- ``prescale_width`` — ``1`` reduces the prescaler to a single bit, which is
  the smallest divider the RTL can express; ``32`` is the widest.
- ``reset_style`` — the always_ff skeleton for the block and the counter.

There is no reset-polarity axis: AXI4-Lite fixes it active-low. The testbench's
expiry cycles are derived from the reload and prescale *values*, which are
options-independent constants, so no case needs to pin them.
"""

from __future__ import annotations

CASES: dict[str, dict] = {
    "defaults": {},
    # --- counter width -------------------------------------------------------
    "narrow_counter": {"counter_width": 4},
    "odd_counter": {"counter_width": 20},
    # --- prescaler -----------------------------------------------------------
    "single_bit_prescaler": {"prescale_width": 1},
    "wide_prescaler": {"prescale_width": 32},
    # --- reset skeleton ------------------------------------------------------
    "async_reset": {"reset_style": "async"},
    # --- verilog-pinned ------------------------------------------------------
    "verilog_narrow": {
        "language": "verilog",
        "counter_width": 16,
        "prescale_width": 8,
    },
}

__all__ = ["CASES"]
