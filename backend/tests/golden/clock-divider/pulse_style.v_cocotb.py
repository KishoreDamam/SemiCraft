# SemiCraft v0.3.0
# cocotb testbench for clock_divider (config hash: 716c16a4e6be)
# BETA: the SystemVerilog testbench is the supported default backend.
#
# Generated code is provided as-is, without warranty of any kind. Free for
# commercial and non-commercial use at the user's own risk.

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, RisingEdge, Timer


@cocotb.test(timeout_time=1760, timeout_unit="ns")
async def smoke(dut):
    """Directed smoke test for clock_divider (generated).

    Mirrors the SystemVerilog smoke testbench cycle for cycle.
    """
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())

    # Initialise inputs and assert reset
    dut.rst_n.value = 0
    for _ in range(2):
        await RisingEdge(dut.clk)
    await Timer(1, units="ns")
    dut.rst_n.value = 1

    # Directed vectors; sample checks after a settle on the falling edge
    for _ in range(2):
        await FallingEdge(dut.clk)
    await Timer(1, units="ns")
    assert dut.clk_out.value == 0, (
        f"SMOKE FAIL: clk_out at cycle 1 expected 0, got {int(dut.clk_out.value)}"
    )
    await FallingEdge(dut.clk)
    await Timer(1, units="ns")
    assert dut.clk_out.value == 1, (
        f"SMOKE FAIL: clk_out at cycle 2 expected 1, got {int(dut.clk_out.value)}"
    )
    for _ in range(1):
        await FallingEdge(dut.clk)

    dut._log.info("SMOKE PASS: clock_divider")
