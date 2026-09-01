# SemiCraft v0.4.0
# cocotb testbench for gray_counter (config hash: b3c69989192d)
# BETA: the SystemVerilog testbench is the supported default backend.
#
# Generated code is provided as-is, without warranty of any kind. Free for
# commercial and non-commercial use at the user's own risk.

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, RisingEdge, Timer


@cocotb.test(timeout_time=1920, timeout_unit="ns")
async def smoke(dut):
    """Directed smoke test for gray_counter (generated).

    Mirrors the SystemVerilog smoke testbench cycle for cycle.
    """
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())

    # Initialise inputs and assert reset
    dut.en.value = 0
    dut.rst.value = 1
    for _ in range(2):
        await RisingEdge(dut.clk)
    await Timer(1, units="ns")
    dut.rst.value = 0

    # Directed vectors; sample checks after a settle on the falling edge
    await FallingEdge(dut.clk)
    dut.en.value = 1
    await Timer(1, units="ns")
    assert dut.gray.value == 0, (
        f"SMOKE FAIL: gray at cycle 0 expected 0, "
        f"got {int(dut.gray.value)}"
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
    assert dut.gray.value == 2, (
        f"SMOKE FAIL: gray at cycle 4 expected 2, "
        f"got {int(dut.gray.value)}"
    )
    await FallingEdge(dut.clk)
    dut.en.value = 1

    dut._log.info("SMOKE PASS: gray_counter")
