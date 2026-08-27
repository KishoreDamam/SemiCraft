"""Golden case matrix for the ``axil-intc`` IP (Phase-4 P4-08).

Axes:

- ``num_irq`` — the field widths, and whether any bits are reserved at all.
  ``32`` fills the data word, which removes the reserved-bit error path from
  both the RTL and the testbench; ``13`` is a deliberately awkward width.
- ``trigger`` — the one option that changes the *testbench* as well as the
  RTL: a level build declares no history flop, and the final section of the
  sequence expects the opposite answer.
- ``input_sync_stages`` — how many flops sit between the pin and the trigger
  logic, and therefore the latency the testbench reads against.
- ``reset_style`` — the always_ff skeleton for the block and the synchroniser.

There is no reset-polarity axis: AXI4-Lite fixes it active-low.
"""

from __future__ import annotations

CASES: dict[str, dict] = {
    "defaults": {},
    # --- source count --------------------------------------------------------
    "one_source": {"num_irq": 1},
    "full_width": {"num_irq": 32},
    "odd_width": {"num_irq": 13},
    # --- trigger mode --------------------------------------------------------
    "level_triggered": {"trigger": "level"},
    "level_one_source": {"trigger": "level", "num_irq": 1},
    # --- synchroniser depth --------------------------------------------------
    "deep_synchroniser": {"input_sync_stages": 4},
    # --- reset skeleton ------------------------------------------------------
    "async_reset": {"reset_style": "async"},
    # --- verilog-pinned ------------------------------------------------------
    "verilog_level_deep_sync": {
        "language": "verilog",
        "trigger": "level",
        "num_irq": 24,
        "input_sync_stages": 3,
    },
}

__all__ = ["CASES"]
