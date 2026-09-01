# SemiCraft v0.4.0
# cocotb testbench for sync_fifo (config hash: ac4b61ce8c0b)
# BETA: the SystemVerilog testbench is the supported default backend.
#
# Generated code is provided as-is, without warranty of any kind. Free for
# commercial and non-commercial use at the user's own risk.

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, RisingEdge, Timer


@cocotb.test(timeout_time=43760, timeout_unit="ns")
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
    assert dut.rd_data.value == 0, (
        f"SMOKE FAIL: rd_data at cycle 0 expected 0, "
        f"got {int(dut.rd_data.value)}"
    )
    await FallingEdge(dut.clk)
    dut.wr_data.value = 1
    dut.wr_en.value = 1
    await FallingEdge(dut.clk)
    dut.wr_data.value = 2
    dut.wr_en.value = 1
    await FallingEdge(dut.clk)
    dut.wr_data.value = 3
    dut.wr_en.value = 1
    await FallingEdge(dut.clk)
    dut.wr_data.value = 4
    dut.wr_en.value = 1
    await FallingEdge(dut.clk)
    dut.rd_en.value = 1
    dut.wr_en.value = 0
    await Timer(1, units="ns")
    assert dut.empty.value == 0, (
        f"SMOKE FAIL: empty at cycle 5 expected 0, "
        f"got {int(dut.empty.value)}"
    )
    assert dut.full.value == 0, (
        f"SMOKE FAIL: full at cycle 5 expected 0, "
        f"got {int(dut.full.value)}"
    )
    await FallingEdge(dut.clk)
    await Timer(1, units="ns")
    assert dut.rd_data.value == 1, (
        f"SMOKE FAIL: rd_data at cycle 6 expected 1, "
        f"got {int(dut.rd_data.value)}"
    )
    assert dut.empty.value == 0, (
        f"SMOKE FAIL: empty at cycle 6 expected 0, "
        f"got {int(dut.empty.value)}"
    )
    assert dut.full.value == 0, (
        f"SMOKE FAIL: full at cycle 6 expected 0, "
        f"got {int(dut.full.value)}"
    )
    await FallingEdge(dut.clk)
    await Timer(1, units="ns")
    assert dut.rd_data.value == 2, (
        f"SMOKE FAIL: rd_data at cycle 7 expected 2, "
        f"got {int(dut.rd_data.value)}"
    )
    assert dut.empty.value == 0, (
        f"SMOKE FAIL: empty at cycle 7 expected 0, "
        f"got {int(dut.empty.value)}"
    )
    assert dut.full.value == 0, (
        f"SMOKE FAIL: full at cycle 7 expected 0, "
        f"got {int(dut.full.value)}"
    )
    await FallingEdge(dut.clk)
    await Timer(1, units="ns")
    assert dut.rd_data.value == 3, (
        f"SMOKE FAIL: rd_data at cycle 8 expected 3, "
        f"got {int(dut.rd_data.value)}"
    )
    assert dut.empty.value == 0, (
        f"SMOKE FAIL: empty at cycle 8 expected 0, "
        f"got {int(dut.empty.value)}"
    )
    assert dut.full.value == 0, (
        f"SMOKE FAIL: full at cycle 8 expected 0, "
        f"got {int(dut.full.value)}"
    )
    await FallingEdge(dut.clk)
    await Timer(1, units="ns")
    assert dut.rd_data.value == 4, (
        f"SMOKE FAIL: rd_data at cycle 9 expected 4, "
        f"got {int(dut.rd_data.value)}"
    )
    assert dut.empty.value == 1, (
        f"SMOKE FAIL: empty at cycle 9 expected 1, "
        f"got {int(dut.empty.value)}"
    )
    assert dut.full.value == 0, (
        f"SMOKE FAIL: full at cycle 9 expected 0, "
        f"got {int(dut.full.value)}"
    )
    await FallingEdge(dut.clk)
    dut.rd_en.value = 0
    dut.wr_data.value = 255
    dut.wr_en.value = 1
    for _ in range(256):
        await FallingEdge(dut.clk)
    await Timer(1, units="ns")
    assert dut.empty.value == 0, (
        f"SMOKE FAIL: empty at cycle 266 expected 0, "
        f"got {int(dut.empty.value)}"
    )
    assert dut.full.value == 1, (
        f"SMOKE FAIL: full at cycle 266 expected 1, "
        f"got {int(dut.full.value)}"
    )
    for _ in range(2):
        await FallingEdge(dut.clk)
    dut.wr_en.value = 0
    await Timer(1, units="ns")
    assert dut.empty.value == 0, (
        f"SMOKE FAIL: empty at cycle 268 expected 0, "
        f"got {int(dut.empty.value)}"
    )
    assert dut.full.value == 1, (
        f"SMOKE FAIL: full at cycle 268 expected 1, "
        f"got {int(dut.full.value)}"
    )
    await FallingEdge(dut.clk)
    dut.rd_en.value = 1
    for _ in range(256):
        await FallingEdge(dut.clk)
    await Timer(1, units="ns")
    assert dut.empty.value == 1, (
        f"SMOKE FAIL: empty at cycle 525 expected 1, "
        f"got {int(dut.empty.value)}"
    )
    assert dut.full.value == 0, (
        f"SMOKE FAIL: full at cycle 525 expected 0, "
        f"got {int(dut.full.value)}"
    )
    assert dut.rd_data.value == 255, (
        f"SMOKE FAIL: rd_data at cycle 525 expected 255, "
        f"got {int(dut.rd_data.value)}"
    )
    for _ in range(2):
        await FallingEdge(dut.clk)
    dut.rd_en.value = 0
    await Timer(1, units="ns")
    assert dut.empty.value == 1, (
        f"SMOKE FAIL: empty at cycle 527 expected 1, "
        f"got {int(dut.empty.value)}"
    )
    assert dut.full.value == 0, (
        f"SMOKE FAIL: full at cycle 527 expected 0, "
        f"got {int(dut.full.value)}"
    )
    assert dut.rd_data.value == 255, (
        f"SMOKE FAIL: rd_data at cycle 527 expected 255, "
        f"got {int(dut.rd_data.value)}"
    )
    for _ in range(1):
        await FallingEdge(dut.clk)

    dut._log.info("SMOKE PASS: sync_fifo")
