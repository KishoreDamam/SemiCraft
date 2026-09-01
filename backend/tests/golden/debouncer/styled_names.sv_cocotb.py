# SemiCraft v0.4.0
# cocotb testbench for debouncer (config hash: 25b930679f39)
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
    cocotb.start_soon(Clock(dut.p_clk, 10, units="ns").start())

    # Initialise inputs and assert reset
    dut.p_dIn.value = 0
    dut.p_rst_n.value = 0
    for _ in range(2):
        await RisingEdge(dut.p_clk)
    await Timer(1, units="ns")
    dut.p_rst_n.value = 1

    # Directed vectors; sample checks after a settle on the falling edge
    await FallingEdge(dut.p_clk)
    dut.p_dIn.value = 1
    await FallingEdge(dut.p_clk)
    dut.p_dIn.value = 0
    await FallingEdge(dut.p_clk)
    dut.p_dIn.value = 1
    await FallingEdge(dut.p_clk)
    dut.p_dIn.value = 0
    await FallingEdge(dut.p_clk)
    dut.p_dIn.value = 1
    await Timer(1, units="ns")
    assert dut.p_q.value == 1, (
        f"SMOKE FAIL: p_q at cycle 4 expected 1, "
        f"got {int(dut.p_q.value)}"
    )
    await FallingEdge(dut.p_clk)
    dut.p_dIn.value = 0
    await FallingEdge(dut.p_clk)
    dut.p_dIn.value = 0
    await FallingEdge(dut.p_clk)
    dut.p_dIn.value = 0
    await Timer(1, units="ns")
    assert dut.p_q.value == 1, (
        f"SMOKE FAIL: p_q at cycle 7 expected 1, "
        f"got {int(dut.p_q.value)}"
    )

    dut._log.info("SMOKE PASS: debouncer")
