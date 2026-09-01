# SemiCraft v0.4.0
# cocotb testbench for sync_ram (config hash: 9e0ede76a0d6)
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
    cocotb.start_soon(Clock(dut.p_clk, 10, units="ns").start())

    # Initialise inputs and assert reset
    dut.p_addr.value = 0
    dut.p_we.value = 0
    dut.p_din.value = 0
    dut.p_re.value = 0

    # Directed vectors; sample checks after a settle on the falling edge
    await FallingEdge(dut.p_clk)
    dut.p_addr.value = 0
    dut.p_din.value = 17
    dut.p_re.value = 0
    dut.p_we.value = 1
    await FallingEdge(dut.p_clk)
    dut.p_addr.value = 1
    dut.p_din.value = 34
    dut.p_re.value = 0
    dut.p_we.value = 1
    await FallingEdge(dut.p_clk)
    dut.p_addr.value = 255
    dut.p_din.value = 51
    dut.p_re.value = 0
    dut.p_we.value = 1
    await FallingEdge(dut.p_clk)
    dut.p_addr.value = 0
    dut.p_re.value = 1
    dut.p_we.value = 0
    await FallingEdge(dut.p_clk)
    dut.p_addr.value = 1
    await Timer(1, units="ns")
    assert dut.p_dout.value == 17, (
        f"SMOKE FAIL: p_dout at cycle 4 expected 17, "
        f"got {int(dut.p_dout.value)}"
    )
    await FallingEdge(dut.p_clk)
    dut.p_addr.value = 255
    await Timer(1, units="ns")
    assert dut.p_dout.value == 34, (
        f"SMOKE FAIL: p_dout at cycle 5 expected 34, "
        f"got {int(dut.p_dout.value)}"
    )
    await FallingEdge(dut.p_clk)
    await Timer(1, units="ns")
    assert dut.p_dout.value == 51, (
        f"SMOKE FAIL: p_dout at cycle 6 expected 51, "
        f"got {int(dut.p_dout.value)}"
    )
    await FallingEdge(dut.p_clk)
    dut.p_addr.value = 0
    dut.p_din.value = 238
    dut.p_re.value = 1
    dut.p_we.value = 1
    await FallingEdge(dut.p_clk)
    dut.p_addr.value = 0
    dut.p_re.value = 1
    dut.p_we.value = 0
    await Timer(1, units="ns")
    assert dut.p_dout.value == 17, (
        f"SMOKE FAIL: p_dout at cycle 8 expected 17, "
        f"got {int(dut.p_dout.value)}"
    )
    await FallingEdge(dut.p_clk)
    dut.p_addr.value = 255
    dut.p_re.value = 0
    await Timer(1, units="ns")
    assert dut.p_dout.value == 238, (
        f"SMOKE FAIL: p_dout at cycle 9 expected 238, "
        f"got {int(dut.p_dout.value)}"
    )
    await FallingEdge(dut.p_clk)
    await Timer(1, units="ns")
    assert dut.p_dout.value == 238, (
        f"SMOKE FAIL: p_dout at cycle 10 expected 238, "
        f"got {int(dut.p_dout.value)}"
    )
    for _ in range(1):
        await FallingEdge(dut.p_clk)

    dut._log.info("SMOKE PASS: sync_ram")
