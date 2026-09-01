# SemiCraft v0.4.0
# cocotb testbench for sync_ram (config hash: 7db33e8203f5)
# BETA: the SystemVerilog testbench is the supported default backend.
#
# Generated code is provided as-is, without warranty of any kind. Free for
# commercial and non-commercial use at the user's own risk.

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, Timer


@cocotb.test(timeout_time=2240, timeout_unit="ns")
async def smoke(dut):
    """Directed smoke test for sync_ram (generated).

    Mirrors the SystemVerilog smoke testbench cycle for cycle.
    """
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())

    # Initialise inputs and assert reset
    dut.waddr.value = 0
    dut.we.value = 0
    dut.din.value = 0
    dut.raddr.value = 0
    dut.re.value = 0

    # Directed vectors; sample checks after a settle on the falling edge
    await FallingEdge(dut.clk)
    dut.din.value = 17
    dut.re.value = 0
    dut.waddr.value = 0
    dut.we.value = 1
    await FallingEdge(dut.clk)
    dut.din.value = 34
    dut.re.value = 0
    dut.waddr.value = 1
    dut.we.value = 1
    await FallingEdge(dut.clk)
    dut.din.value = 51
    dut.re.value = 0
    dut.waddr.value = 255
    dut.we.value = 1
    await FallingEdge(dut.clk)
    dut.raddr.value = 0
    dut.re.value = 1
    dut.we.value = 0
    await FallingEdge(dut.clk)
    dut.raddr.value = 1
    await Timer(1, units="ns")
    assert dut.dout.value == 17, (
        f"SMOKE FAIL: dout at cycle 4 expected 17, "
        f"got {int(dut.dout.value)}"
    )
    await FallingEdge(dut.clk)
    dut.raddr.value = 255
    await Timer(1, units="ns")
    assert dut.dout.value == 34, (
        f"SMOKE FAIL: dout at cycle 5 expected 34, "
        f"got {int(dut.dout.value)}"
    )
    await FallingEdge(dut.clk)
    await Timer(1, units="ns")
    assert dut.dout.value == 51, (
        f"SMOKE FAIL: dout at cycle 6 expected 51, "
        f"got {int(dut.dout.value)}"
    )
    await FallingEdge(dut.clk)
    dut.din.value = 238
    dut.raddr.value = 0
    dut.re.value = 1
    dut.waddr.value = 0
    dut.we.value = 1
    await FallingEdge(dut.clk)
    dut.raddr.value = 0
    dut.re.value = 1
    dut.we.value = 0
    await Timer(1, units="ns")
    assert dut.dout.value == 17, (
        f"SMOKE FAIL: dout at cycle 8 expected 17, "
        f"got {int(dut.dout.value)}"
    )
    await FallingEdge(dut.clk)
    dut.raddr.value = 255
    dut.re.value = 0
    await Timer(1, units="ns")
    assert dut.dout.value == 238, (
        f"SMOKE FAIL: dout at cycle 9 expected 238, "
        f"got {int(dut.dout.value)}"
    )
    await FallingEdge(dut.clk)
    await Timer(1, units="ns")
    assert dut.dout.value == 238, (
        f"SMOKE FAIL: dout at cycle 10 expected 238, "
        f"got {int(dut.dout.value)}"
    )
    for _ in range(1):
        await FallingEdge(dut.clk)

    dut._log.info("SMOKE PASS: sync_ram")
