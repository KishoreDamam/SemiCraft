# SemiCraft v0.3.0
# cocotb testbench for rr_arbiter (config hash: 9f9d319602a8)
# BETA: the SystemVerilog testbench is the supported default backend.
#
# Generated code is provided as-is, without warranty of any kind. Free for
# commercial and non-commercial use at the user's own risk.

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, RisingEdge, Timer


@cocotb.test(timeout_time=2240, timeout_unit="ns")
async def smoke(dut):
    """Directed smoke test for rr_arbiter (generated).

    Mirrors the SystemVerilog smoke testbench cycle for cycle.
    """
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())

    # Initialise inputs and assert reset
    dut.req.value = 0
    dut.rst.value = 1
    for _ in range(2):
        await RisingEdge(dut.clk)
    await Timer(1, units="ns")
    dut.rst.value = 0

    # Directed vectors; sample checks after a settle on the falling edge
    await FallingEdge(dut.clk)
    dut.req.value = 0
    await FallingEdge(dut.clk)
    dut.req.value = 1
    await FallingEdge(dut.clk)
    dut.req.value = 1
    await Timer(1, units="ns")
    assert dut.grant_valid.value == 1, (
        f"SMOKE FAIL: grant_valid at cycle 2 expected 1, got {int(dut.grant_valid.value)}"
    )
    assert dut.grant.value == 1, (
        f"SMOKE FAIL: grant at cycle 2 expected 1, got {int(dut.grant.value)}"
    )
    await FallingEdge(dut.clk)
    dut.req.value = 65535
    await FallingEdge(dut.clk)
    dut.req.value = 65535
    await FallingEdge(dut.clk)
    dut.req.value = 65535
    await FallingEdge(dut.clk)
    dut.req.value = 65535
    await FallingEdge(dut.clk)
    dut.req.value = 0
    await FallingEdge(dut.clk)
    dut.req.value = 32768
    await Timer(1, units="ns")
    assert dut.grant_valid.value == 0, (
        f"SMOKE FAIL: grant_valid at cycle 8 expected 0, got {int(dut.grant_valid.value)}"
    )
    await FallingEdge(dut.clk)
    dut.req.value = 32768

    dut._log.info("SMOKE PASS: rr_arbiter")
