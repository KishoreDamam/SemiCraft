# SemiCraft v0.4.0
# cocotb testbench for axil_spi (config hash: bea2ab0054b1)
# BETA: the SystemVerilog testbench is the supported default backend.
#
# Generated code is provided as-is, without warranty of any kind. Free for
# commercial and non-commercial use at the user's own risk.

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, RisingEdge, Timer


@cocotb.test(timeout_time=5680, timeout_unit="ns")
async def smoke(dut):
    """Directed smoke test for axil_spi (generated).

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
    dut.p_miso.value = 0
    dut.p_areset_n.value = 0
    for _ in range(2):
        await RisingEdge(dut.p_aclk)
    await Timer(1, units="ns")
    dut.p_areset_n.value = 1

    # Directed vectors; sample checks after a settle on the falling edge
    await FallingEdge(dut.p_aclk)
    dut.p_awaddr.value = 4
    dut.p_awvalid.value = 1
    dut.p_bready.value = 1
    dut.p_wdata.value = 1
    dut.p_wstrb.value = 15
    dut.p_wvalid.value = 1
    await Timer(1, units="ns")
    assert dut.p_sclk.value == 0, (
        f"SMOKE FAIL: p_sclk at cycle 0 expected 0, "
        f"got {int(dut.p_sclk.value)}"
    )
    assert dut.p_csN.value == 1, (
        f"SMOKE FAIL: p_csN at cycle 0 expected 1, "
        f"got {int(dut.p_csN.value)}"
    )
    assert dut.p_bvalid.value == 0, (
        f"SMOKE FAIL: p_bvalid at cycle 0 expected 0, "
        f"got {int(dut.p_bvalid.value)}"
    )
    await FallingEdge(dut.p_aclk)
    dut.p_awvalid.value = 0
    dut.p_wvalid.value = 0
    await FallingEdge(dut.p_aclk)
    await Timer(1, units="ns")
    assert dut.p_bvalid.value == 1, (
        f"SMOKE FAIL: p_bvalid at cycle 2 expected 1, "
        f"got {int(dut.p_bvalid.value)}"
    )
    assert dut.p_bresp.value == 0, (
        f"SMOKE FAIL: p_bresp at cycle 2 expected 0, "
        f"got {int(dut.p_bresp.value)}"
    )
    assert dut.p_csN.value == 0, (
        f"SMOKE FAIL: p_csN at cycle 2 expected 0, "
        f"got {int(dut.p_csN.value)}"
    )
    await FallingEdge(dut.p_aclk)
    dut.p_miso.value = 0
    await Timer(1, units="ns")
    assert dut.p_bvalid.value == 0, (
        f"SMOKE FAIL: p_bvalid at cycle 3 expected 0, "
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
    dut.p_miso.value = 0
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
    await FallingEdge(dut.p_aclk)
    await Timer(1, units="ns")
    assert dut.p_mosi.value == 0, (
        f"SMOKE FAIL: p_mosi at cycle 8 expected 0, "
        f"got {int(dut.p_mosi.value)}"
    )
    await FallingEdge(dut.p_aclk)
    await Timer(1, units="ns")
    assert dut.p_sclk.value == 1, (
        f"SMOKE FAIL: p_sclk at cycle 9 expected 1, "
        f"got {int(dut.p_sclk.value)}"
    )
    await FallingEdge(dut.p_aclk)
    dut.p_miso.value = 0
    await FallingEdge(dut.p_aclk)
    await Timer(1, units="ns")
    assert dut.p_sclk.value == 0, (
        f"SMOKE FAIL: p_sclk at cycle 11 expected 0, "
        f"got {int(dut.p_sclk.value)}"
    )
    await FallingEdge(dut.p_aclk)
    await Timer(1, units="ns")
    assert dut.p_mosi.value == 1, (
        f"SMOKE FAIL: p_mosi at cycle 12 expected 1, "
        f"got {int(dut.p_mosi.value)}"
    )
    for _ in range(2):
        await FallingEdge(dut.p_aclk)
    dut.p_miso.value = 1
    for _ in range(2):
        await FallingEdge(dut.p_aclk)
    await Timer(1, units="ns")
    assert dut.p_mosi.value == 0, (
        f"SMOKE FAIL: p_mosi at cycle 16 expected 0, "
        f"got {int(dut.p_mosi.value)}"
    )
    for _ in range(2):
        await FallingEdge(dut.p_aclk)
    dut.p_miso.value = 0
    for _ in range(2):
        await FallingEdge(dut.p_aclk)
    await Timer(1, units="ns")
    assert dut.p_mosi.value == 0, (
        f"SMOKE FAIL: p_mosi at cycle 20 expected 0, "
        f"got {int(dut.p_mosi.value)}"
    )
    for _ in range(2):
        await FallingEdge(dut.p_aclk)
    dut.p_miso.value = 1
    for _ in range(2):
        await FallingEdge(dut.p_aclk)
    await Timer(1, units="ns")
    assert dut.p_mosi.value == 1, (
        f"SMOKE FAIL: p_mosi at cycle 24 expected 1, "
        f"got {int(dut.p_mosi.value)}"
    )
    for _ in range(2):
        await FallingEdge(dut.p_aclk)
    dut.p_miso.value = 1
    for _ in range(2):
        await FallingEdge(dut.p_aclk)
    await Timer(1, units="ns")
    assert dut.p_mosi.value == 0, (
        f"SMOKE FAIL: p_mosi at cycle 28 expected 0, "
        f"got {int(dut.p_mosi.value)}"
    )
    for _ in range(2):
        await FallingEdge(dut.p_aclk)
    dut.p_miso.value = 0
    for _ in range(2):
        await FallingEdge(dut.p_aclk)
    await Timer(1, units="ns")
    assert dut.p_mosi.value == 1, (
        f"SMOKE FAIL: p_mosi at cycle 32 expected 1, "
        f"got {int(dut.p_mosi.value)}"
    )
    for _ in range(2):
        await FallingEdge(dut.p_aclk)
    dut.p_miso.value = 1
    for _ in range(2):
        await FallingEdge(dut.p_aclk)
    await Timer(1, units="ns")
    assert dut.p_mosi.value == 1, (
        f"SMOKE FAIL: p_mosi at cycle 36 expected 1, "
        f"got {int(dut.p_mosi.value)}"
    )
    for _ in range(3):
        await FallingEdge(dut.p_aclk)
    await Timer(1, units="ns")
    assert dut.p_sclk.value == 0, (
        f"SMOKE FAIL: p_sclk at cycle 39 expected 0, "
        f"got {int(dut.p_sclk.value)}"
    )
    await FallingEdge(dut.p_aclk)
    dut.p_araddr.value = 0
    dut.p_arvalid.value = 1
    dut.p_rready.value = 1
    await FallingEdge(dut.p_aclk)
    dut.p_arvalid.value = 0
    await Timer(1, units="ns")
    assert dut.p_rvalid.value == 1, (
        f"SMOKE FAIL: p_rvalid at cycle 41 expected 1, "
        f"got {int(dut.p_rvalid.value)}"
    )
    assert dut.p_rdata.value == 2, (
        f"SMOKE FAIL: p_rdata at cycle 41 expected 2, "
        f"got {int(dut.p_rdata.value)}"
    )
    assert dut.p_rresp.value == 0, (
        f"SMOKE FAIL: p_rresp at cycle 41 expected 0, "
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
        f"SMOKE FAIL: p_rvalid at cycle 43 expected 1, "
        f"got {int(dut.p_rvalid.value)}"
    )
    assert dut.p_rdata.value == 45, (
        f"SMOKE FAIL: p_rdata at cycle 43 expected 45, "
        f"got {int(dut.p_rdata.value)}"
    )
    assert dut.p_rresp.value == 0, (
        f"SMOKE FAIL: p_rresp at cycle 43 expected 0, "
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
        f"SMOKE FAIL: p_bvalid at cycle 46 expected 1, "
        f"got {int(dut.p_bvalid.value)}"
    )
    assert dut.p_bresp.value == 0, (
        f"SMOKE FAIL: p_bresp at cycle 46 expected 0, "
        f"got {int(dut.p_bresp.value)}"
    )
    await FallingEdge(dut.p_aclk)
    dut.p_araddr.value = 0
    dut.p_arvalid.value = 1
    dut.p_rready.value = 1
    await Timer(1, units="ns")
    assert dut.p_bvalid.value == 0, (
        f"SMOKE FAIL: p_bvalid at cycle 47 expected 0, "
        f"got {int(dut.p_bvalid.value)}"
    )
    await FallingEdge(dut.p_aclk)
    dut.p_arvalid.value = 0
    await Timer(1, units="ns")
    assert dut.p_rvalid.value == 1, (
        f"SMOKE FAIL: p_rvalid at cycle 48 expected 1, "
        f"got {int(dut.p_rvalid.value)}"
    )
    assert dut.p_rdata.value == 0, (
        f"SMOKE FAIL: p_rdata at cycle 48 expected 0, "
        f"got {int(dut.p_rdata.value)}"
    )
    assert dut.p_rresp.value == 0, (
        f"SMOKE FAIL: p_rresp at cycle 48 expected 0, "
        f"got {int(dut.p_rresp.value)}"
    )
    await FallingEdge(dut.p_aclk)
    dut.p_awaddr.value = 4
    dut.p_awvalid.value = 1
    dut.p_bready.value = 1
    dut.p_wdata.value = 0
    dut.p_wstrb.value = 15
    dut.p_wvalid.value = 1
    await FallingEdge(dut.p_aclk)
    dut.p_awvalid.value = 0
    dut.p_wvalid.value = 0
    await FallingEdge(dut.p_aclk)
    await Timer(1, units="ns")
    assert dut.p_bvalid.value == 1, (
        f"SMOKE FAIL: p_bvalid at cycle 51 expected 1, "
        f"got {int(dut.p_bvalid.value)}"
    )
    assert dut.p_bresp.value == 0, (
        f"SMOKE FAIL: p_bresp at cycle 51 expected 0, "
        f"got {int(dut.p_bresp.value)}"
    )
    assert dut.p_csN.value == 1, (
        f"SMOKE FAIL: p_csN at cycle 51 expected 1, "
        f"got {int(dut.p_csN.value)}"
    )
    await FallingEdge(dut.p_aclk)
    await Timer(1, units="ns")
    assert dut.p_bvalid.value == 0, (
        f"SMOKE FAIL: p_bvalid at cycle 52 expected 0, "
        f"got {int(dut.p_bvalid.value)}"
    )

    dut._log.info("SMOKE PASS: axil_spi")
