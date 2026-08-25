# SemiCraft v0.3.0
# cocotb testbench for debouncer (config hash: ca39af83da6d)
# BETA: the SystemVerilog testbench is the supported default backend.
#
# Generated code is provided as-is, without warranty of any kind. Free for
# commercial and non-commercial use at the user's own risk.

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, RisingEdge, Timer


@cocotb.test(timeout_time=2080, timeout_unit="ns")
async def smoke(dut):
    """Directed smoke test for debouncer (generated).

    Mirrors the SystemVerilog smoke testbench cycle for cycle.
    """
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())

    # Initialise inputs and assert reset
    dut.d_in.value = 0
    dut.rst.value = 1
    for _ in range(2):
        await RisingEdge(dut.clk)
    await Timer(1, units="ns")
    dut.rst.value = 0

    # Directed vectors; sample checks after a settle on the falling edge
    await FallingEdge(dut.clk)
    dut.d_in.value = 1
    await FallingEdge(dut.clk)
    dut.d_in.value = 0
    await FallingEdge(dut.clk)
    dut.d_in.value = 1
    await FallingEdge(dut.clk)
    dut.d_in.value = 0
    await FallingEdge(dut.clk)
    dut.d_in.value = 1
    await Timer(1, units="ns")
    assert dut.q.value == 1, (
        f"SMOKE FAIL: q at cycle 4 expected 1, "
        f"got {int(dut.q.value)}"
    )
    await FallingEdge(dut.clk)
    dut.d_in.value = 0
    await FallingEdge(dut.clk)
    dut.d_in.value = 0
    await FallingEdge(dut.clk)
    dut.d_in.value = 0
    await Timer(1, units="ns")
    assert dut.q.value == 1, (
        f"SMOKE FAIL: q at cycle 7 expected 1, "
        f"got {int(dut.q.value)}"
    )

    dut._log.info("SMOKE PASS: debouncer")
