# SemiCraft v0.4.0
# cocotb testbench for axil_i2c (config hash: 0023434d01dd)
# BETA: the SystemVerilog testbench is the supported default backend.
#
# Generated code is provided as-is, without warranty of any kind. Free for
# commercial and non-commercial use at the user's own risk.

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, RisingEdge, Timer


@cocotb.test(timeout_time=17840, timeout_unit="ns")
async def smoke(dut):
    """Directed smoke test for axil_i2c (generated).

    Mirrors the SystemVerilog smoke testbench cycle for cycle.
    """
    cocotb.start_soon(Clock(dut.p_aclk, 10, units="ns").start())

    # Initialise inputs and assert reset
    dut.p_awaddr.value = 0
    dut.p_awvalid.value = 0
    dut.p_wdata.value = 0
    dut.p_wstrb.value = 0
    dut.p_wvalid.value = 0
    dut.p_bready.value = 0
    dut.p_araddr.value = 0
    dut.p_arvalid.value = 0
    dut.p_rready.value = 0
    dut.p_sclIn.value = 0
    dut.p_sdaIn.value = 0
    dut.p_areset_n.value = 0
    for _ in range(2):
        await RisingEdge(dut.p_aclk)
    await Timer(1, units="ns")
    dut.p_areset_n.value = 1

    # Directed vectors; sample checks after a settle on the falling edge
    await FallingEdge(dut.p_aclk)
    dut.p_sclIn.value = 1
    dut.p_sdaIn.value = 1
    await Timer(1, units="ns")
    assert dut.p_sclOe.value == 0, (
        f"SMOKE FAIL: p_sclOe at cycle 0 expected 0, "
        f"got {int(dut.p_sclOe.value)}"
    )
    assert dut.p_sdaOe.value == 0, (
        f"SMOKE FAIL: p_sdaOe at cycle 0 expected 0, "
        f"got {int(dut.p_sdaOe.value)}"
    )
    assert dut.p_bvalid.value == 0, (
        f"SMOKE FAIL: p_bvalid at cycle 0 expected 0, "
        f"got {int(dut.p_bvalid.value)}"
    )
    await FallingEdge(dut.p_aclk)
    dut.p_awaddr.value = 8
    dut.p_awvalid.value = 1
    dut.p_bready.value = 1
    dut.p_wdata.value = 75
    dut.p_wstrb.value = 15
    dut.p_wvalid.value = 1
    await FallingEdge(dut.p_aclk)
    dut.p_awvalid.value = 0
    dut.p_wvalid.value = 0
    await FallingEdge(dut.p_aclk)
    await Timer(1, units="ns")
    assert dut.p_bvalid.value == 1, (
        f"SMOKE FAIL: p_bvalid at cycle 3 expected 1, "
        f"got {int(dut.p_bvalid.value)}"
    )
    assert dut.p_bresp.value == 0, (
        f"SMOKE FAIL: p_bresp at cycle 3 expected 0, "
        f"got {int(dut.p_bresp.value)}"
    )
    await FallingEdge(dut.p_aclk)
    dut.p_awaddr.value = 4
    dut.p_awvalid.value = 1
    dut.p_bready.value = 1
    dut.p_wdata.value = 19
    dut.p_wstrb.value = 15
    dut.p_wvalid.value = 1
    await Timer(1, units="ns")
    assert dut.p_bvalid.value == 0, (
        f"SMOKE FAIL: p_bvalid at cycle 4 expected 0, "
        f"got {int(dut.p_bvalid.value)}"
    )
    await FallingEdge(dut.p_aclk)
    dut.p_awvalid.value = 0
    dut.p_wvalid.value = 0
    await FallingEdge(dut.p_aclk)
    await Timer(1, units="ns")
    assert dut.p_bvalid.value == 1, (
        f"SMOKE FAIL: p_bvalid at cycle 6 expected 1, "
        f"got {int(dut.p_bvalid.value)}"
    )
    assert dut.p_bresp.value == 0, (
        f"SMOKE FAIL: p_bresp at cycle 6 expected 0, "
        f"got {int(dut.p_bresp.value)}"
    )
    await FallingEdge(dut.p_aclk)
    await Timer(1, units="ns")
    assert dut.p_bvalid.value == 0, (
        f"SMOKE FAIL: p_bvalid at cycle 7 expected 0, "
        f"got {int(dut.p_bvalid.value)}"
    )
    assert dut.p_sclOe.value == 0, (
        f"SMOKE FAIL: p_sclOe at cycle 7 expected 0, "
        f"got {int(dut.p_sclOe.value)}"
    )
    assert dut.p_sdaOe.value == 0, (
        f"SMOKE FAIL: p_sdaOe at cycle 7 expected 0, "
        f"got {int(dut.p_sdaOe.value)}"
    )
    for _ in range(2):
        await FallingEdge(dut.p_aclk)
    await Timer(1, units="ns")
    assert dut.p_sclOe.value == 0, (
        f"SMOKE FAIL: p_sclOe at cycle 9 expected 0, "
        f"got {int(dut.p_sclOe.value)}"
    )
    assert dut.p_sdaOe.value == 0, (
        f"SMOKE FAIL: p_sdaOe at cycle 9 expected 0, "
        f"got {int(dut.p_sdaOe.value)}"
    )
    for _ in range(2):
        await FallingEdge(dut.p_aclk)
    await Timer(1, units="ns")
    assert dut.p_sclOe.value == 0, (
        f"SMOKE FAIL: p_sclOe at cycle 11 expected 0, "
        f"got {int(dut.p_sclOe.value)}"
    )
    assert dut.p_sdaOe.value == 1, (
        f"SMOKE FAIL: p_sdaOe at cycle 11 expected 1, "
        f"got {int(dut.p_sdaOe.value)}"
    )
    for _ in range(2):
        await FallingEdge(dut.p_aclk)
    await Timer(1, units="ns")
    assert dut.p_sclOe.value == 1, (
        f"SMOKE FAIL: p_sclOe at cycle 13 expected 1, "
        f"got {int(dut.p_sclOe.value)}"
    )
    assert dut.p_sdaOe.value == 1, (
        f"SMOKE FAIL: p_sdaOe at cycle 13 expected 1, "
        f"got {int(dut.p_sdaOe.value)}"
    )
    for _ in range(2):
        await FallingEdge(dut.p_aclk)
    await Timer(1, units="ns")
    assert dut.p_sclOe.value == 1, (
        f"SMOKE FAIL: p_sclOe at cycle 15 expected 1, "
        f"got {int(dut.p_sclOe.value)}"
    )
    assert dut.p_sdaOe.value == 1, (
        f"SMOKE FAIL: p_sdaOe at cycle 15 expected 1, "
        f"got {int(dut.p_sdaOe.value)}"
    )
    for _ in range(2):
        await FallingEdge(dut.p_aclk)
    dut.p_sclIn.value = 0
    await Timer(1, units="ns")
    assert dut.p_sclOe.value == 0, (
        f"SMOKE FAIL: p_sclOe at cycle 17 expected 0, "
        f"got {int(dut.p_sclOe.value)}"
    )
    assert dut.p_sdaOe.value == 1, (
        f"SMOKE FAIL: p_sdaOe at cycle 17 expected 1, "
        f"got {int(dut.p_sdaOe.value)}"
    )
    for _ in range(2):
        await FallingEdge(dut.p_aclk)
    await Timer(1, units="ns")
    assert dut.p_sclOe.value == 0, (
        f"SMOKE FAIL: p_sclOe at cycle 19 expected 0, "
        f"got {int(dut.p_sclOe.value)}"
    )
    assert dut.p_sdaOe.value == 1, (
        f"SMOKE FAIL: p_sdaOe at cycle 19 expected 1, "
        f"got {int(dut.p_sdaOe.value)}"
    )
    for _ in range(2):
        await FallingEdge(dut.p_aclk)
    dut.p_sclIn.value = 1
    for _ in range(4):
        await FallingEdge(dut.p_aclk)
    await Timer(1, units="ns")
    assert dut.p_sclOe.value == 1, (
        f"SMOKE FAIL: p_sclOe at cycle 25 expected 1, "
        f"got {int(dut.p_sclOe.value)}"
    )
    assert dut.p_sdaOe.value == 1, (
        f"SMOKE FAIL: p_sdaOe at cycle 25 expected 1, "
        f"got {int(dut.p_sdaOe.value)}"
    )
    for _ in range(2):
        await FallingEdge(dut.p_aclk)
    await Timer(1, units="ns")
    assert dut.p_sclOe.value == 1, (
        f"SMOKE FAIL: p_sclOe at cycle 27 expected 1, "
        f"got {int(dut.p_sclOe.value)}"
    )
    assert dut.p_sdaOe.value == 0, (
        f"SMOKE FAIL: p_sdaOe at cycle 27 expected 0, "
        f"got {int(dut.p_sdaOe.value)}"
    )
    for _ in range(2):
        await FallingEdge(dut.p_aclk)
    await Timer(1, units="ns")
    assert dut.p_sclOe.value == 0, (
        f"SMOKE FAIL: p_sclOe at cycle 29 expected 0, "
        f"got {int(dut.p_sclOe.value)}"
    )
    assert dut.p_sdaOe.value == 0, (
        f"SMOKE FAIL: p_sdaOe at cycle 29 expected 0, "
        f"got {int(dut.p_sdaOe.value)}"
    )
    for _ in range(2):
        await FallingEdge(dut.p_aclk)
    await Timer(1, units="ns")
    assert dut.p_sclOe.value == 0, (
        f"SMOKE FAIL: p_sclOe at cycle 31 expected 0, "
        f"got {int(dut.p_sclOe.value)}"
    )
    assert dut.p_sdaOe.value == 0, (
        f"SMOKE FAIL: p_sdaOe at cycle 31 expected 0, "
        f"got {int(dut.p_sdaOe.value)}"
    )
    for _ in range(2):
        await FallingEdge(dut.p_aclk)
    await Timer(1, units="ns")
    assert dut.p_sclOe.value == 1, (
        f"SMOKE FAIL: p_sclOe at cycle 33 expected 1, "
        f"got {int(dut.p_sclOe.value)}"
    )
    assert dut.p_sdaOe.value == 0, (
        f"SMOKE FAIL: p_sdaOe at cycle 33 expected 0, "
        f"got {int(dut.p_sdaOe.value)}"
    )
    for _ in range(2):
        await FallingEdge(dut.p_aclk)
    await Timer(1, units="ns")
    assert dut.p_sclOe.value == 1, (
        f"SMOKE FAIL: p_sclOe at cycle 35 expected 1, "
        f"got {int(dut.p_sclOe.value)}"
    )
    assert dut.p_sdaOe.value == 1, (
        f"SMOKE FAIL: p_sdaOe at cycle 35 expected 1, "
        f"got {int(dut.p_sdaOe.value)}"
    )
    for _ in range(2):
        await FallingEdge(dut.p_aclk)
    await Timer(1, units="ns")
    assert dut.p_sclOe.value == 0, (
        f"SMOKE FAIL: p_sclOe at cycle 37 expected 0, "
        f"got {int(dut.p_sclOe.value)}"
    )
    assert dut.p_sdaOe.value == 1, (
        f"SMOKE FAIL: p_sdaOe at cycle 37 expected 1, "
        f"got {int(dut.p_sdaOe.value)}"
    )
    for _ in range(2):
        await FallingEdge(dut.p_aclk)
    await Timer(1, units="ns")
    assert dut.p_sclOe.value == 0, (
        f"SMOKE FAIL: p_sclOe at cycle 39 expected 0, "
        f"got {int(dut.p_sclOe.value)}"
    )
    assert dut.p_sdaOe.value == 1, (
        f"SMOKE FAIL: p_sdaOe at cycle 39 expected 1, "
        f"got {int(dut.p_sdaOe.value)}"
    )
    for _ in range(2):
        await FallingEdge(dut.p_aclk)
    await Timer(1, units="ns")
    assert dut.p_sclOe.value == 1, (
        f"SMOKE FAIL: p_sclOe at cycle 41 expected 1, "
        f"got {int(dut.p_sclOe.value)}"
    )
    assert dut.p_sdaOe.value == 1, (
        f"SMOKE FAIL: p_sdaOe at cycle 41 expected 1, "
        f"got {int(dut.p_sdaOe.value)}"
    )
    for _ in range(2):
        await FallingEdge(dut.p_aclk)
    await Timer(1, units="ns")
    assert dut.p_sclOe.value == 1, (
        f"SMOKE FAIL: p_sclOe at cycle 43 expected 1, "
        f"got {int(dut.p_sclOe.value)}"
    )
    assert dut.p_sdaOe.value == 1, (
        f"SMOKE FAIL: p_sdaOe at cycle 43 expected 1, "
        f"got {int(dut.p_sdaOe.value)}"
    )
    for _ in range(2):
        await FallingEdge(dut.p_aclk)
    await Timer(1, units="ns")
    assert dut.p_sclOe.value == 0, (
        f"SMOKE FAIL: p_sclOe at cycle 45 expected 0, "
        f"got {int(dut.p_sclOe.value)}"
    )
    assert dut.p_sdaOe.value == 1, (
        f"SMOKE FAIL: p_sdaOe at cycle 45 expected 1, "
        f"got {int(dut.p_sdaOe.value)}"
    )
    for _ in range(2):
        await FallingEdge(dut.p_aclk)
    await Timer(1, units="ns")
    assert dut.p_sclOe.value == 0, (
        f"SMOKE FAIL: p_sclOe at cycle 47 expected 0, "
        f"got {int(dut.p_sclOe.value)}"
    )
    assert dut.p_sdaOe.value == 1, (
        f"SMOKE FAIL: p_sdaOe at cycle 47 expected 1, "
        f"got {int(dut.p_sdaOe.value)}"
    )
    for _ in range(2):
        await FallingEdge(dut.p_aclk)
    await Timer(1, units="ns")
    assert dut.p_sclOe.value == 1, (
        f"SMOKE FAIL: p_sclOe at cycle 49 expected 1, "
        f"got {int(dut.p_sclOe.value)}"
    )
    assert dut.p_sdaOe.value == 1, (
        f"SMOKE FAIL: p_sdaOe at cycle 49 expected 1, "
        f"got {int(dut.p_sdaOe.value)}"
    )
    for _ in range(2):
        await FallingEdge(dut.p_aclk)
    await Timer(1, units="ns")
    assert dut.p_sclOe.value == 1, (
        f"SMOKE FAIL: p_sclOe at cycle 51 expected 1, "
        f"got {int(dut.p_sclOe.value)}"
    )
    assert dut.p_sdaOe.value == 0, (
        f"SMOKE FAIL: p_sdaOe at cycle 51 expected 0, "
        f"got {int(dut.p_sdaOe.value)}"
    )
    for _ in range(2):
        await FallingEdge(dut.p_aclk)
    await Timer(1, units="ns")
    assert dut.p_sclOe.value == 0, (
        f"SMOKE FAIL: p_sclOe at cycle 53 expected 0, "
        f"got {int(dut.p_sclOe.value)}"
    )
    assert dut.p_sdaOe.value == 0, (
        f"SMOKE FAIL: p_sdaOe at cycle 53 expected 0, "
        f"got {int(dut.p_sdaOe.value)}"
    )
    for _ in range(2):
        await FallingEdge(dut.p_aclk)
    await Timer(1, units="ns")
    assert dut.p_sclOe.value == 0, (
        f"SMOKE FAIL: p_sclOe at cycle 55 expected 0, "
        f"got {int(dut.p_sclOe.value)}"
    )
    assert dut.p_sdaOe.value == 0, (
        f"SMOKE FAIL: p_sdaOe at cycle 55 expected 0, "
        f"got {int(dut.p_sdaOe.value)}"
    )
    for _ in range(2):
        await FallingEdge(dut.p_aclk)
    await Timer(1, units="ns")
    assert dut.p_sclOe.value == 1, (
        f"SMOKE FAIL: p_sclOe at cycle 57 expected 1, "
        f"got {int(dut.p_sclOe.value)}"
    )
    assert dut.p_sdaOe.value == 0, (
        f"SMOKE FAIL: p_sdaOe at cycle 57 expected 0, "
        f"got {int(dut.p_sdaOe.value)}"
    )
    for _ in range(2):
        await FallingEdge(dut.p_aclk)
    await Timer(1, units="ns")
    assert dut.p_sclOe.value == 1, (
        f"SMOKE FAIL: p_sclOe at cycle 59 expected 1, "
        f"got {int(dut.p_sclOe.value)}"
    )
    assert dut.p_sdaOe.value == 1, (
        f"SMOKE FAIL: p_sdaOe at cycle 59 expected 1, "
        f"got {int(dut.p_sdaOe.value)}"
    )
    for _ in range(2):
        await FallingEdge(dut.p_aclk)
    await Timer(1, units="ns")
    assert dut.p_sclOe.value == 0, (
        f"SMOKE FAIL: p_sclOe at cycle 61 expected 0, "
        f"got {int(dut.p_sclOe.value)}"
    )
    assert dut.p_sdaOe.value == 1, (
        f"SMOKE FAIL: p_sdaOe at cycle 61 expected 1, "
        f"got {int(dut.p_sdaOe.value)}"
    )
    for _ in range(2):
        await FallingEdge(dut.p_aclk)
    await Timer(1, units="ns")
    assert dut.p_sclOe.value == 0, (
        f"SMOKE FAIL: p_sclOe at cycle 63 expected 0, "
        f"got {int(dut.p_sclOe.value)}"
    )
    assert dut.p_sdaOe.value == 1, (
        f"SMOKE FAIL: p_sdaOe at cycle 63 expected 1, "
        f"got {int(dut.p_sdaOe.value)}"
    )
    for _ in range(2):
        await FallingEdge(dut.p_aclk)
    await Timer(1, units="ns")
    assert dut.p_sclOe.value == 1, (
        f"SMOKE FAIL: p_sclOe at cycle 65 expected 1, "
        f"got {int(dut.p_sclOe.value)}"
    )
    assert dut.p_sdaOe.value == 1, (
        f"SMOKE FAIL: p_sdaOe at cycle 65 expected 1, "
        f"got {int(dut.p_sdaOe.value)}"
    )
    for _ in range(2):
        await FallingEdge(dut.p_aclk)
    await Timer(1, units="ns")
    assert dut.p_sclOe.value == 1, (
        f"SMOKE FAIL: p_sclOe at cycle 67 expected 1, "
        f"got {int(dut.p_sclOe.value)}"
    )
    assert dut.p_sdaOe.value == 0, (
        f"SMOKE FAIL: p_sdaOe at cycle 67 expected 0, "
        f"got {int(dut.p_sdaOe.value)}"
    )
    for _ in range(2):
        await FallingEdge(dut.p_aclk)
    await Timer(1, units="ns")
    assert dut.p_sclOe.value == 0, (
        f"SMOKE FAIL: p_sclOe at cycle 69 expected 0, "
        f"got {int(dut.p_sclOe.value)}"
    )
    assert dut.p_sdaOe.value == 0, (
        f"SMOKE FAIL: p_sdaOe at cycle 69 expected 0, "
        f"got {int(dut.p_sdaOe.value)}"
    )
    for _ in range(2):
        await FallingEdge(dut.p_aclk)
    await Timer(1, units="ns")
    assert dut.p_sclOe.value == 0, (
        f"SMOKE FAIL: p_sclOe at cycle 71 expected 0, "
        f"got {int(dut.p_sclOe.value)}"
    )
    assert dut.p_sdaOe.value == 0, (
        f"SMOKE FAIL: p_sdaOe at cycle 71 expected 0, "
        f"got {int(dut.p_sdaOe.value)}"
    )
    for _ in range(2):
        await FallingEdge(dut.p_aclk)
    await Timer(1, units="ns")
    assert dut.p_sclOe.value == 1, (
        f"SMOKE FAIL: p_sclOe at cycle 73 expected 1, "
        f"got {int(dut.p_sclOe.value)}"
    )
    assert dut.p_sdaOe.value == 0, (
        f"SMOKE FAIL: p_sdaOe at cycle 73 expected 0, "
        f"got {int(dut.p_sdaOe.value)}"
    )
    for _ in range(2):
        await FallingEdge(dut.p_aclk)
    await Timer(1, units="ns")
    assert dut.p_sclOe.value == 1, (
        f"SMOKE FAIL: p_sclOe at cycle 75 expected 1, "
        f"got {int(dut.p_sclOe.value)}"
    )
    assert dut.p_sdaOe.value == 0, (
        f"SMOKE FAIL: p_sdaOe at cycle 75 expected 0, "
        f"got {int(dut.p_sdaOe.value)}"
    )
    for _ in range(2):
        await FallingEdge(dut.p_aclk)
    await Timer(1, units="ns")
    assert dut.p_sclOe.value == 0, (
        f"SMOKE FAIL: p_sclOe at cycle 77 expected 0, "
        f"got {int(dut.p_sclOe.value)}"
    )
    assert dut.p_sdaOe.value == 0, (
        f"SMOKE FAIL: p_sdaOe at cycle 77 expected 0, "
        f"got {int(dut.p_sdaOe.value)}"
    )
    for _ in range(2):
        await FallingEdge(dut.p_aclk)
    await Timer(1, units="ns")
    assert dut.p_sclOe.value == 0, (
        f"SMOKE FAIL: p_sclOe at cycle 79 expected 0, "
        f"got {int(dut.p_sclOe.value)}"
    )
    assert dut.p_sdaOe.value == 0, (
        f"SMOKE FAIL: p_sdaOe at cycle 79 expected 0, "
        f"got {int(dut.p_sdaOe.value)}"
    )
    for _ in range(2):
        await FallingEdge(dut.p_aclk)
    dut.p_sdaIn.value = 0
    await Timer(1, units="ns")
    assert dut.p_sclOe.value == 1, (
        f"SMOKE FAIL: p_sclOe at cycle 81 expected 1, "
        f"got {int(dut.p_sclOe.value)}"
    )
    assert dut.p_sdaOe.value == 0, (
        f"SMOKE FAIL: p_sdaOe at cycle 81 expected 0, "
        f"got {int(dut.p_sdaOe.value)}"
    )
    for _ in range(2):
        await FallingEdge(dut.p_aclk)
    await Timer(1, units="ns")
    assert dut.p_sclOe.value == 1, (
        f"SMOKE FAIL: p_sclOe at cycle 83 expected 1, "
        f"got {int(dut.p_sclOe.value)}"
    )
    assert dut.p_sdaOe.value == 0, (
        f"SMOKE FAIL: p_sdaOe at cycle 83 expected 0, "
        f"got {int(dut.p_sdaOe.value)}"
    )
    for _ in range(2):
        await FallingEdge(dut.p_aclk)
    await Timer(1, units="ns")
    assert dut.p_sclOe.value == 0, (
        f"SMOKE FAIL: p_sclOe at cycle 85 expected 0, "
        f"got {int(dut.p_sclOe.value)}"
    )
    assert dut.p_sdaOe.value == 0, (
        f"SMOKE FAIL: p_sdaOe at cycle 85 expected 0, "
        f"got {int(dut.p_sdaOe.value)}"
    )
    for _ in range(2):
        await FallingEdge(dut.p_aclk)
    await Timer(1, units="ns")
    assert dut.p_sclOe.value == 0, (
        f"SMOKE FAIL: p_sclOe at cycle 87 expected 0, "
        f"got {int(dut.p_sclOe.value)}"
    )
    assert dut.p_sdaOe.value == 0, (
        f"SMOKE FAIL: p_sdaOe at cycle 87 expected 0, "
        f"got {int(dut.p_sdaOe.value)}"
    )
    for _ in range(2):
        await FallingEdge(dut.p_aclk)
    await Timer(1, units="ns")
    assert dut.p_sclOe.value == 1, (
        f"SMOKE FAIL: p_sclOe at cycle 89 expected 1, "
        f"got {int(dut.p_sclOe.value)}"
    )
    assert dut.p_sdaOe.value == 0, (
        f"SMOKE FAIL: p_sdaOe at cycle 89 expected 0, "
        f"got {int(dut.p_sdaOe.value)}"
    )
    for _ in range(2):
        await FallingEdge(dut.p_aclk)
    dut.p_sdaIn.value = 1
    await Timer(1, units="ns")
    assert dut.p_sclOe.value == 1, (
        f"SMOKE FAIL: p_sclOe at cycle 91 expected 1, "
        f"got {int(dut.p_sclOe.value)}"
    )
    assert dut.p_sdaOe.value == 1, (
        f"SMOKE FAIL: p_sdaOe at cycle 91 expected 1, "
        f"got {int(dut.p_sdaOe.value)}"
    )
    for _ in range(2):
        await FallingEdge(dut.p_aclk)
    await Timer(1, units="ns")
    assert dut.p_sclOe.value == 0, (
        f"SMOKE FAIL: p_sclOe at cycle 93 expected 0, "
        f"got {int(dut.p_sclOe.value)}"
    )
    assert dut.p_sdaOe.value == 1, (
        f"SMOKE FAIL: p_sdaOe at cycle 93 expected 1, "
        f"got {int(dut.p_sdaOe.value)}"
    )
    for _ in range(2):
        await FallingEdge(dut.p_aclk)
    await Timer(1, units="ns")
    assert dut.p_sclOe.value == 0, (
        f"SMOKE FAIL: p_sclOe at cycle 95 expected 0, "
        f"got {int(dut.p_sclOe.value)}"
    )
    assert dut.p_sdaOe.value == 1, (
        f"SMOKE FAIL: p_sdaOe at cycle 95 expected 1, "
        f"got {int(dut.p_sdaOe.value)}"
    )
    for _ in range(2):
        await FallingEdge(dut.p_aclk)
    await Timer(1, units="ns")
    assert dut.p_sclOe.value == 0, (
        f"SMOKE FAIL: p_sclOe at cycle 97 expected 0, "
        f"got {int(dut.p_sclOe.value)}"
    )
    assert dut.p_sdaOe.value == 0, (
        f"SMOKE FAIL: p_sdaOe at cycle 97 expected 0, "
        f"got {int(dut.p_sdaOe.value)}"
    )
    for _ in range(5):
        await FallingEdge(dut.p_aclk)
    dut.p_araddr.value = 0
    dut.p_arvalid.value = 1
    dut.p_rready.value = 1
    await FallingEdge(dut.p_aclk)
    dut.p_arvalid.value = 0
    await Timer(1, units="ns")
    assert dut.p_rvalid.value == 1, (
        f"SMOKE FAIL: p_rvalid at cycle 103 expected 1, "
        f"got {int(dut.p_rvalid.value)}"
    )
    assert dut.p_rdata.value == 2, (
        f"SMOKE FAIL: p_rdata at cycle 103 expected 2, "
        f"got {int(dut.p_rdata.value)}"
    )
    assert dut.p_rresp.value == 0, (
        f"SMOKE FAIL: p_rresp at cycle 103 expected 0, "
        f"got {int(dut.p_rresp.value)}"
    )
    await FallingEdge(dut.p_aclk)
    dut.p_awaddr.value = 0
    dut.p_awvalid.value = 1
    dut.p_bready.value = 1
    dut.p_wdata.value = 2
    dut.p_wstrb.value = 15
    dut.p_wvalid.value = 1
    await FallingEdge(dut.p_aclk)
    dut.p_awvalid.value = 0
    dut.p_wvalid.value = 0
    await FallingEdge(dut.p_aclk)
    await Timer(1, units="ns")
    assert dut.p_bvalid.value == 1, (
        f"SMOKE FAIL: p_bvalid at cycle 106 expected 1, "
        f"got {int(dut.p_bvalid.value)}"
    )
    assert dut.p_bresp.value == 0, (
        f"SMOKE FAIL: p_bresp at cycle 106 expected 0, "
        f"got {int(dut.p_bresp.value)}"
    )
    await FallingEdge(dut.p_aclk)
    dut.p_awaddr.value = 4
    dut.p_awvalid.value = 1
    dut.p_bready.value = 1
    dut.p_wdata.value = 21
    dut.p_wstrb.value = 15
    dut.p_wvalid.value = 1
    await Timer(1, units="ns")
    assert dut.p_bvalid.value == 0, (
        f"SMOKE FAIL: p_bvalid at cycle 107 expected 0, "
        f"got {int(dut.p_bvalid.value)}"
    )
    await FallingEdge(dut.p_aclk)
    dut.p_awvalid.value = 0
    dut.p_wvalid.value = 0
    await FallingEdge(dut.p_aclk)
    await Timer(1, units="ns")
    assert dut.p_bvalid.value == 1, (
        f"SMOKE FAIL: p_bvalid at cycle 109 expected 1, "
        f"got {int(dut.p_bvalid.value)}"
    )
    assert dut.p_bresp.value == 0, (
        f"SMOKE FAIL: p_bresp at cycle 109 expected 0, "
        f"got {int(dut.p_bresp.value)}"
    )
    await FallingEdge(dut.p_aclk)
    await Timer(1, units="ns")
    assert dut.p_bvalid.value == 0, (
        f"SMOKE FAIL: p_bvalid at cycle 110 expected 0, "
        f"got {int(dut.p_bvalid.value)}"
    )
    for _ in range(6):
        await FallingEdge(dut.p_aclk)
    dut.p_sdaIn.value = 0
    for _ in range(8):
        await FallingEdge(dut.p_aclk)
    dut.p_sdaIn.value = 0
    for _ in range(8):
        await FallingEdge(dut.p_aclk)
    dut.p_sdaIn.value = 1
    for _ in range(8):
        await FallingEdge(dut.p_aclk)
    dut.p_sdaIn.value = 0
    for _ in range(8):
        await FallingEdge(dut.p_aclk)
    dut.p_sdaIn.value = 1
    for _ in range(8):
        await FallingEdge(dut.p_aclk)
    dut.p_sdaIn.value = 1
    for _ in range(8):
        await FallingEdge(dut.p_aclk)
    dut.p_sdaIn.value = 0
    for _ in range(8):
        await FallingEdge(dut.p_aclk)
    dut.p_sdaIn.value = 1
    for _ in range(8):
        await FallingEdge(dut.p_aclk)
    dut.p_sdaIn.value = 1
    for _ in range(2):
        await FallingEdge(dut.p_aclk)
    await Timer(1, units="ns")
    assert dut.p_sclOe.value == 1, (
        f"SMOKE FAIL: p_sclOe at cycle 182 expected 1, "
        f"got {int(dut.p_sclOe.value)}"
    )
    assert dut.p_sdaOe.value == 0, (
        f"SMOKE FAIL: p_sdaOe at cycle 182 expected 0, "
        f"got {int(dut.p_sdaOe.value)}"
    )
    for _ in range(2):
        await FallingEdge(dut.p_aclk)
    await Timer(1, units="ns")
    assert dut.p_sclOe.value == 0, (
        f"SMOKE FAIL: p_sclOe at cycle 184 expected 0, "
        f"got {int(dut.p_sclOe.value)}"
    )
    assert dut.p_sdaOe.value == 0, (
        f"SMOKE FAIL: p_sdaOe at cycle 184 expected 0, "
        f"got {int(dut.p_sdaOe.value)}"
    )
    for _ in range(2):
        await FallingEdge(dut.p_aclk)
    await Timer(1, units="ns")
    assert dut.p_sclOe.value == 0, (
        f"SMOKE FAIL: p_sclOe at cycle 186 expected 0, "
        f"got {int(dut.p_sclOe.value)}"
    )
    assert dut.p_sdaOe.value == 0, (
        f"SMOKE FAIL: p_sdaOe at cycle 186 expected 0, "
        f"got {int(dut.p_sdaOe.value)}"
    )
    for _ in range(2):
        await FallingEdge(dut.p_aclk)
    await Timer(1, units="ns")
    assert dut.p_sclOe.value == 1, (
        f"SMOKE FAIL: p_sclOe at cycle 188 expected 1, "
        f"got {int(dut.p_sclOe.value)}"
    )
    assert dut.p_sdaOe.value == 0, (
        f"SMOKE FAIL: p_sdaOe at cycle 188 expected 0, "
        f"got {int(dut.p_sdaOe.value)}"
    )
    for _ in range(13):
        await FallingEdge(dut.p_aclk)
    dut.p_araddr.value = 0
    dut.p_arvalid.value = 1
    dut.p_rready.value = 1
    await FallingEdge(dut.p_aclk)
    dut.p_arvalid.value = 0
    await Timer(1, units="ns")
    assert dut.p_rvalid.value == 1, (
        f"SMOKE FAIL: p_rvalid at cycle 202 expected 1, "
        f"got {int(dut.p_rvalid.value)}"
    )
    assert dut.p_rdata.value == 10, (
        f"SMOKE FAIL: p_rdata at cycle 202 expected 10, "
        f"got {int(dut.p_rdata.value)}"
    )
    assert dut.p_rresp.value == 0, (
        f"SMOKE FAIL: p_rresp at cycle 202 expected 0, "
        f"got {int(dut.p_rresp.value)}"
    )
    await FallingEdge(dut.p_aclk)
    dut.p_araddr.value = 12
    dut.p_arvalid.value = 1
    dut.p_rready.value = 1
    await FallingEdge(dut.p_aclk)
    dut.p_arvalid.value = 0
    await Timer(1, units="ns")
    assert dut.p_rvalid.value == 1, (
        f"SMOKE FAIL: p_rvalid at cycle 204 expected 1, "
        f"got {int(dut.p_rvalid.value)}"
    )
    assert dut.p_rdata.value == 45, (
        f"SMOKE FAIL: p_rdata at cycle 204 expected 45, "
        f"got {int(dut.p_rdata.value)}"
    )
    assert dut.p_rresp.value == 0, (
        f"SMOKE FAIL: p_rresp at cycle 204 expected 0, "
        f"got {int(dut.p_rresp.value)}"
    )

    dut._log.info("SMOKE PASS: axil_i2c")
