# SemiCraft v0.4.0
# cocotb testbench for sync_ram (config hash: 4ce06443ea46)
# BETA: the SystemVerilog testbench is the supported default backend.
#
# Generated code is provided as-is, without warranty of any kind. Free for
# commercial and non-commercial use at the user's own risk.

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, Timer


@cocotb.test(timeout_time=2080, timeout_unit="ns")
async def smoke(dut):
    """Directed smoke test for sync_ram (generated).

    Mirrors the SystemVerilog smoke testbench cycle for cycle.
    """
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())

    # Initialise inputs and assert reset
    dut.addr.value = 0
    dut.we.value = 0
    dut.din.value = 0
    dut.re.value = 0

    # Directed vectors; sample checks after a settle on the falling edge
    await FallingEdge(dut.clk)
    dut.addr.value = 0
    dut.din.value = 1
    dut.re.value = 0
    dut.we.value = 1
    await FallingEdge(dut.clk)
    dut.addr.value = 1
    dut.din.value = 0
    dut.re.value = 0
    dut.we.value = 1
    await FallingEdge(dut.clk)
    dut.addr.value = 0
    dut.re.value = 1
    dut.we.value = 0
    await FallingEdge(dut.clk)
    dut.addr.value = 1
    await Timer(1, units="ns")
    assert dut.dout.value == 1, (
        f"SMOKE FAIL: dout at cycle 3 expected 1, "
        f"got {int(dut.dout.value)}"
    )
    await FallingEdge(dut.clk)
    await Timer(1, units="ns")
    assert dut.dout.value == 0, (
        f"SMOKE FAIL: dout at cycle 4 expected 0, "
        f"got {int(dut.dout.value)}"
    )
    await FallingEdge(dut.clk)
    dut.addr.value = 0
    dut.din.value = 0
    dut.re.value = 1
    dut.we.value = 1
    await FallingEdge(dut.clk)
    dut.addr.value = 0
    dut.re.value = 1
    dut.we.value = 0
    await Timer(1, units="ns")
    assert dut.dout.value == 1, (
        f"SMOKE FAIL: dout at cycle 6 expected 1, "
        f"got {int(dut.dout.value)}"
    )
    await FallingEdge(dut.clk)
    dut.addr.value = 1
    dut.re.value = 0
    await Timer(1, units="ns")
    assert dut.dout.value == 0, (
        f"SMOKE FAIL: dout at cycle 7 expected 0, "
        f"got {int(dut.dout.value)}"
    )
    await FallingEdge(dut.clk)
    await Timer(1, units="ns")
    assert dut.dout.value == 0, (
        f"SMOKE FAIL: dout at cycle 8 expected 0, "
        f"got {int(dut.dout.value)}"
    )
    for _ in range(1):
        await FallingEdge(dut.clk)

    dut._log.info("SMOKE PASS: sync_ram")
