# SemiCraft v0.3.0
# cocotb testbench for edge_detector (config hash: e8450808767b)
# BETA: the SystemVerilog testbench is the supported default backend.
#
# Generated code is provided as-is, without warranty of any kind. Free for
# commercial and non-commercial use at the user's own risk.

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, RisingEdge, Timer


@cocotb.test(timeout_time=1920, timeout_unit="ns")
async def smoke(dut):
    """Directed smoke test for edge_detector (generated).

    Mirrors the SystemVerilog smoke testbench cycle for cycle.
    """
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())

    # Initialise inputs and assert reset
    dut.d.value = 0
    dut.rst_n.value = 0
    for _ in range(2):
        await RisingEdge(dut.clk)
    await Timer(1, units="ns")
    dut.rst_n.value = 1

    # Directed vectors; sample checks after a settle on the falling edge
    await FallingEdge(dut.clk)
    dut.d.value = 0
    await FallingEdge(dut.clk)
    dut.d.value = 1
    await FallingEdge(dut.clk)
    dut.d.value = 1
    await Timer(1, units="ns")
    assert dut.pulse.value == 1, (
        f"SMOKE FAIL: pulse at cycle 2 expected 1, got {int(dut.pulse.value)}"
    )
    await FallingEdge(dut.clk)
    dut.d.value = 0
    await Timer(1, units="ns")
    assert dut.pulse.value == 0, (
        f"SMOKE FAIL: pulse at cycle 3 expected 0, got {int(dut.pulse.value)}"
    )
    await FallingEdge(dut.clk)
    dut.d.value = 0
    await FallingEdge(dut.clk)
    dut.d.value = 1

    dut._log.info("SMOKE PASS: edge_detector")
