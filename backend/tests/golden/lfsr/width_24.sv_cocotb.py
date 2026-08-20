# SemiCraft v0.3.0
# cocotb testbench for lfsr (config hash: f684639f0d65)
# BETA: the SystemVerilog testbench is the supported default backend.
#
# Generated code is provided as-is, without warranty of any kind. Free for
# commercial and non-commercial use at the user's own risk.

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, RisingEdge, Timer


@cocotb.test(timeout_time=1920, timeout_unit="ns")
async def smoke(dut):
    """Directed smoke test for lfsr (generated).

    Mirrors the SystemVerilog smoke testbench cycle for cycle.
    """
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())

    # Initialise inputs and assert reset
    dut.en.value = 0
    dut.rst_n.value = 0
    for _ in range(2):
        await RisingEdge(dut.clk)
    await Timer(1, units="ns")
    dut.rst_n.value = 1

    # Directed vectors; sample checks after a settle on the falling edge
    await FallingEdge(dut.clk)
    dut.en.value = 1
    await Timer(1, units="ns")
    assert dut.q.value == 1, (
        f"SMOKE FAIL: q at cycle 0 expected 1, got {int(dut.q.value)}"
    )
    await FallingEdge(dut.clk)
    dut.en.value = 1
    await FallingEdge(dut.clk)
    dut.en.value = 1
    await FallingEdge(dut.clk)
    dut.en.value = 0
    await FallingEdge(dut.clk)
    dut.en.value = 1
    await Timer(1, units="ns")
    assert dut.q.value == 0, (
        f"SMOKE FAIL: q at cycle 4 expected 0, got {int(dut.q.value)}"
    )
    await FallingEdge(dut.clk)
    dut.en.value = 1

    dut._log.info("SMOKE PASS: lfsr")
