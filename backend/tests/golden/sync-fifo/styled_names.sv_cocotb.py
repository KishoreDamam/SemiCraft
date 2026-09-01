# SemiCraft v0.4.0
# cocotb testbench for sync_fifo (config hash: aa4576c29109)
# BETA: the SystemVerilog testbench is the supported default backend.
#
# Generated code is provided as-is, without warranty of any kind. Free for
# commercial and non-commercial use at the user's own risk.

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, RisingEdge, Timer


@cocotb.test(timeout_time=4080, timeout_unit="ns")
async def smoke(dut):
    """Directed smoke test for sync_fifo (generated).

    Mirrors the SystemVerilog smoke testbench cycle for cycle.
    """
    cocotb.start_soon(Clock(dut.p_clk, 10, units="ns").start())

    # Initialise inputs and assert reset
    dut.p_wrEn.value = 0
    dut.p_wrData.value = 0
    dut.p_rdEn.value = 0
    dut.p_rst_n.value = 0
    for _ in range(2):
        await RisingEdge(dut.p_clk)
    await Timer(1, units="ns")
    dut.p_rst_n.value = 1

    # Directed vectors; sample checks after a settle on the falling edge
    await FallingEdge(dut.p_clk)
    await Timer(1, units="ns")
    assert dut.p_empty.value == 1, (
        f"SMOKE FAIL: p_empty at cycle 0 expected 1, "
        f"got {int(dut.p_empty.value)}"
    )
    assert dut.p_full.value == 0, (
        f"SMOKE FAIL: p_full at cycle 0 expected 0, "
        f"got {int(dut.p_full.value)}"
    )
    assert dut.p_count.value == 0, (
        f"SMOKE FAIL: p_count at cycle 0 expected 0, "
        f"got {int(dut.p_count.value)}"
    )
    assert dut.p_rdData.value == 0, (
        f"SMOKE FAIL: p_rdData at cycle 0 expected 0, "
        f"got {int(dut.p_rdData.value)}"
    )
    await FallingEdge(dut.p_clk)
    dut.p_wrData.value = 1
    dut.p_wrEn.value = 1
    await FallingEdge(dut.p_clk)
    dut.p_wrData.value = 2
    dut.p_wrEn.value = 1
    await FallingEdge(dut.p_clk)
    dut.p_wrData.value = 3
    dut.p_wrEn.value = 1
    await FallingEdge(dut.p_clk)
    dut.p_wrData.value = 4
    dut.p_wrEn.value = 1
    await FallingEdge(dut.p_clk)
    dut.p_rdEn.value = 1
    dut.p_wrEn.value = 0
    await Timer(1, units="ns")
    assert dut.p_empty.value == 0, (
        f"SMOKE FAIL: p_empty at cycle 5 expected 0, "
        f"got {int(dut.p_empty.value)}"
    )
    assert dut.p_full.value == 0, (
        f"SMOKE FAIL: p_full at cycle 5 expected 0, "
        f"got {int(dut.p_full.value)}"
    )
    assert dut.p_count.value == 4, (
        f"SMOKE FAIL: p_count at cycle 5 expected 4, "
        f"got {int(dut.p_count.value)}"
    )
    await FallingEdge(dut.p_clk)
    await Timer(1, units="ns")
    assert dut.p_rdData.value == 1, (
        f"SMOKE FAIL: p_rdData at cycle 6 expected 1, "
        f"got {int(dut.p_rdData.value)}"
    )
    assert dut.p_empty.value == 0, (
        f"SMOKE FAIL: p_empty at cycle 6 expected 0, "
        f"got {int(dut.p_empty.value)}"
    )
    assert dut.p_full.value == 0, (
        f"SMOKE FAIL: p_full at cycle 6 expected 0, "
        f"got {int(dut.p_full.value)}"
    )
    assert dut.p_count.value == 3, (
        f"SMOKE FAIL: p_count at cycle 6 expected 3, "
        f"got {int(dut.p_count.value)}"
    )
    await FallingEdge(dut.p_clk)
    await Timer(1, units="ns")
    assert dut.p_rdData.value == 2, (
        f"SMOKE FAIL: p_rdData at cycle 7 expected 2, "
        f"got {int(dut.p_rdData.value)}"
    )
    assert dut.p_empty.value == 0, (
        f"SMOKE FAIL: p_empty at cycle 7 expected 0, "
        f"got {int(dut.p_empty.value)}"
    )
    assert dut.p_full.value == 0, (
        f"SMOKE FAIL: p_full at cycle 7 expected 0, "
        f"got {int(dut.p_full.value)}"
    )
    assert dut.p_count.value == 2, (
        f"SMOKE FAIL: p_count at cycle 7 expected 2, "
        f"got {int(dut.p_count.value)}"
    )
    await FallingEdge(dut.p_clk)
    await Timer(1, units="ns")
    assert dut.p_rdData.value == 3, (
        f"SMOKE FAIL: p_rdData at cycle 8 expected 3, "
        f"got {int(dut.p_rdData.value)}"
    )
    assert dut.p_empty.value == 0, (
        f"SMOKE FAIL: p_empty at cycle 8 expected 0, "
        f"got {int(dut.p_empty.value)}"
    )
    assert dut.p_full.value == 0, (
        f"SMOKE FAIL: p_full at cycle 8 expected 0, "
        f"got {int(dut.p_full.value)}"
    )
    assert dut.p_count.value == 1, (
        f"SMOKE FAIL: p_count at cycle 8 expected 1, "
        f"got {int(dut.p_count.value)}"
    )
    await FallingEdge(dut.p_clk)
    await Timer(1, units="ns")
    assert dut.p_rdData.value == 4, (
        f"SMOKE FAIL: p_rdData at cycle 9 expected 4, "
        f"got {int(dut.p_rdData.value)}"
    )
    assert dut.p_empty.value == 1, (
        f"SMOKE FAIL: p_empty at cycle 9 expected 1, "
        f"got {int(dut.p_empty.value)}"
    )
    assert dut.p_full.value == 0, (
        f"SMOKE FAIL: p_full at cycle 9 expected 0, "
        f"got {int(dut.p_full.value)}"
    )
    assert dut.p_count.value == 0, (
        f"SMOKE FAIL: p_count at cycle 9 expected 0, "
        f"got {int(dut.p_count.value)}"
    )
    await FallingEdge(dut.p_clk)
    dut.p_rdEn.value = 0
    dut.p_wrData.value = 255
    dut.p_wrEn.value = 1
    for _ in range(8):
        await FallingEdge(dut.p_clk)
    await Timer(1, units="ns")
    assert dut.p_empty.value == 0, (
        f"SMOKE FAIL: p_empty at cycle 18 expected 0, "
        f"got {int(dut.p_empty.value)}"
    )
    assert dut.p_full.value == 1, (
        f"SMOKE FAIL: p_full at cycle 18 expected 1, "
        f"got {int(dut.p_full.value)}"
    )
    assert dut.p_count.value == 8, (
        f"SMOKE FAIL: p_count at cycle 18 expected 8, "
        f"got {int(dut.p_count.value)}"
    )
    for _ in range(2):
        await FallingEdge(dut.p_clk)
    dut.p_wrEn.value = 0
    await Timer(1, units="ns")
    assert dut.p_empty.value == 0, (
        f"SMOKE FAIL: p_empty at cycle 20 expected 0, "
        f"got {int(dut.p_empty.value)}"
    )
    assert dut.p_full.value == 1, (
        f"SMOKE FAIL: p_full at cycle 20 expected 1, "
        f"got {int(dut.p_full.value)}"
    )
    assert dut.p_count.value == 8, (
        f"SMOKE FAIL: p_count at cycle 20 expected 8, "
        f"got {int(dut.p_count.value)}"
    )
    await FallingEdge(dut.p_clk)
    dut.p_rdEn.value = 1
    for _ in range(8):
        await FallingEdge(dut.p_clk)
    await Timer(1, units="ns")
    assert dut.p_empty.value == 1, (
        f"SMOKE FAIL: p_empty at cycle 29 expected 1, "
        f"got {int(dut.p_empty.value)}"
    )
    assert dut.p_full.value == 0, (
        f"SMOKE FAIL: p_full at cycle 29 expected 0, "
        f"got {int(dut.p_full.value)}"
    )
    assert dut.p_count.value == 0, (
        f"SMOKE FAIL: p_count at cycle 29 expected 0, "
        f"got {int(dut.p_count.value)}"
    )
    assert dut.p_rdData.value == 255, (
        f"SMOKE FAIL: p_rdData at cycle 29 expected 255, "
        f"got {int(dut.p_rdData.value)}"
    )
    for _ in range(2):
        await FallingEdge(dut.p_clk)
    dut.p_rdEn.value = 0
    await Timer(1, units="ns")
    assert dut.p_empty.value == 1, (
        f"SMOKE FAIL: p_empty at cycle 31 expected 1, "
        f"got {int(dut.p_empty.value)}"
    )
    assert dut.p_full.value == 0, (
        f"SMOKE FAIL: p_full at cycle 31 expected 0, "
        f"got {int(dut.p_full.value)}"
    )
    assert dut.p_count.value == 0, (
        f"SMOKE FAIL: p_count at cycle 31 expected 0, "
        f"got {int(dut.p_count.value)}"
    )
    assert dut.p_rdData.value == 255, (
        f"SMOKE FAIL: p_rdData at cycle 31 expected 255, "
        f"got {int(dut.p_rdData.value)}"
    )
    for _ in range(1):
        await FallingEdge(dut.p_clk)

    dut._log.info("SMOKE PASS: sync_fifo")
