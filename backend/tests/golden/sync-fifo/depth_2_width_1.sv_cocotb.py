# SemiCraft v0.3.0
# cocotb testbench for sync_fifo (config hash: e28447eb5885)
# BETA: the SystemVerilog testbench is the supported default backend.
#
# Generated code is provided as-is, without warranty of any kind. Free for
# commercial and non-commercial use at the user's own risk.

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, RisingEdge, Timer


@cocotb.test(timeout_time=2640, timeout_unit="ns")
async def smoke(dut):
    """Directed smoke test for sync_fifo (generated).

    Mirrors the SystemVerilog smoke testbench cycle for cycle.
    """
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())

    # Initialise inputs and assert reset
    dut.wr_en.value = 0
    dut.wr_data.value = 0
    dut.rd_en.value = 0
    dut.rst_n.value = 0
    for _ in range(2):
        await RisingEdge(dut.clk)
    await Timer(1, units="ns")
    dut.rst_n.value = 1

    # Directed vectors; sample checks after a settle on the falling edge
    await FallingEdge(dut.clk)
    await Timer(1, units="ns")
    assert dut.empty.value == 1, (
        f"SMOKE FAIL: empty at cycle 0 expected 1, "
        f"got {int(dut.empty.value)}"
    )
    assert dut.full.value == 0, (
        f"SMOKE FAIL: full at cycle 0 expected 0, "
        f"got {int(dut.full.value)}"
    )
    assert dut.count.value == 0, (
        f"SMOKE FAIL: count at cycle 0 expected 0, "
        f"got {int(dut.count.value)}"
    )
    assert dut.rd_data.value == 0, (
        f"SMOKE FAIL: rd_data at cycle 0 expected 0, "
        f"got {int(dut.rd_data.value)}"
    )
    await FallingEdge(dut.clk)
    dut.wr_data.value = 1
    dut.wr_en.value = 1
    await FallingEdge(dut.clk)
    dut.rd_en.value = 1
    dut.wr_en.value = 0
    await Timer(1, units="ns")
    assert dut.empty.value == 0, (
        f"SMOKE FAIL: empty at cycle 2 expected 0, "
        f"got {int(dut.empty.value)}"
    )
    assert dut.full.value == 0, (
        f"SMOKE FAIL: full at cycle 2 expected 0, "
        f"got {int(dut.full.value)}"
    )
    assert dut.count.value == 1, (
        f"SMOKE FAIL: count at cycle 2 expected 1, "
        f"got {int(dut.count.value)}"
    )
    await FallingEdge(dut.clk)
    await Timer(1, units="ns")
    assert dut.rd_data.value == 1, (
        f"SMOKE FAIL: rd_data at cycle 3 expected 1, "
        f"got {int(dut.rd_data.value)}"
    )
    assert dut.empty.value == 1, (
        f"SMOKE FAIL: empty at cycle 3 expected 1, "
        f"got {int(dut.empty.value)}"
    )
    assert dut.full.value == 0, (
        f"SMOKE FAIL: full at cycle 3 expected 0, "
        f"got {int(dut.full.value)}"
    )
    assert dut.count.value == 0, (
        f"SMOKE FAIL: count at cycle 3 expected 0, "
        f"got {int(dut.count.value)}"
    )
    await FallingEdge(dut.clk)
    dut.rd_en.value = 0
    dut.wr_data.value = 1
    dut.wr_en.value = 1
    for _ in range(2):
        await FallingEdge(dut.clk)
    await Timer(1, units="ns")
    assert dut.empty.value == 0, (
        f"SMOKE FAIL: empty at cycle 6 expected 0, "
        f"got {int(dut.empty.value)}"
    )
    assert dut.full.value == 1, (
        f"SMOKE FAIL: full at cycle 6 expected 1, "
        f"got {int(dut.full.value)}"
    )
    assert dut.count.value == 2, (
        f"SMOKE FAIL: count at cycle 6 expected 2, "
        f"got {int(dut.count.value)}"
    )
    for _ in range(2):
        await FallingEdge(dut.clk)
    dut.wr_en.value = 0
    await Timer(1, units="ns")
    assert dut.empty.value == 0, (
        f"SMOKE FAIL: empty at cycle 8 expected 0, "
        f"got {int(dut.empty.value)}"
    )
    assert dut.full.value == 1, (
        f"SMOKE FAIL: full at cycle 8 expected 1, "
        f"got {int(dut.full.value)}"
    )
    assert dut.count.value == 2, (
        f"SMOKE FAIL: count at cycle 8 expected 2, "
        f"got {int(dut.count.value)}"
    )
    await FallingEdge(dut.clk)
    dut.rd_en.value = 1
    for _ in range(2):
        await FallingEdge(dut.clk)
    await Timer(1, units="ns")
    assert dut.empty.value == 1, (
        f"SMOKE FAIL: empty at cycle 11 expected 1, "
        f"got {int(dut.empty.value)}"
    )
    assert dut.full.value == 0, (
        f"SMOKE FAIL: full at cycle 11 expected 0, "
        f"got {int(dut.full.value)}"
    )
    assert dut.count.value == 0, (
        f"SMOKE FAIL: count at cycle 11 expected 0, "
        f"got {int(dut.count.value)}"
    )
    assert dut.rd_data.value == 1, (
        f"SMOKE FAIL: rd_data at cycle 11 expected 1, "
        f"got {int(dut.rd_data.value)}"
    )
    for _ in range(2):
        await FallingEdge(dut.clk)
    dut.rd_en.value = 0
    await Timer(1, units="ns")
    assert dut.empty.value == 1, (
        f"SMOKE FAIL: empty at cycle 13 expected 1, "
        f"got {int(dut.empty.value)}"
    )
    assert dut.full.value == 0, (
        f"SMOKE FAIL: full at cycle 13 expected 0, "
        f"got {int(dut.full.value)}"
    )
    assert dut.count.value == 0, (
        f"SMOKE FAIL: count at cycle 13 expected 0, "
        f"got {int(dut.count.value)}"
    )
    assert dut.rd_data.value == 1, (
        f"SMOKE FAIL: rd_data at cycle 13 expected 1, "
        f"got {int(dut.rd_data.value)}"
    )
    for _ in range(1):
        await FallingEdge(dut.clk)

    dut._log.info("SMOKE PASS: sync_fifo")
