"""Golden case matrix for the ``axil-gpio`` IP (Phase-4 P4-05a).

The first *composed* IP: an AXI4-Lite register block spliced into a peripheral
rather than instantiated, so these goldens also pin the splice itself.

Axes:

- ``num_pins`` — the field widths, and whether any bits are reserved at all.
  ``32`` fills the data word, which removes the reserved-bit error path from
  both the RTL and the testbench; ``13`` is a deliberately awkward width.
- ``input_sync_stages`` — how many flops sit between the pin and the IN
  register, and therefore the latency the testbench waits out.
- ``reset_style`` — the always_ff skeleton for the block and the synchroniser.

There is no reset-polarity axis: AXI4-Lite fixes it active-low.
"""

from __future__ import annotations

CASES: dict[str, dict] = {
    "defaults": {},
    # --- pin count -----------------------------------------------------------
    "one_pin": {"num_pins": 1},
    "full_width": {"num_pins": 32},
    "odd_width": {"num_pins": 13},
    # --- synchroniser depth --------------------------------------------------
    "deep_synchroniser": {"input_sync_stages": 4},
    # --- reset skeleton ------------------------------------------------------
    "async_reset": {"reset_style": "async"},
    # --- verilog-pinned ------------------------------------------------------
    "verilog_wide_deep_sync": {
        "language": "verilog",
        "num_pins": 24,
        "input_sync_stages": 3,
    },
}

__all__ = ["CASES"]
