# SemiCraft v0.4.0
# cocotb testbench for axil_gpio (config hash: 28458bc0a6db)
# BETA: the SystemVerilog testbench is the supported default backend.
#
# Generated code is provided as-is, without warranty of any kind. Free for
# commercial and non-commercial use at the user's own risk.

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, RisingEdge, Timer


@cocotb.test(timeout_time=3040, timeout_unit="ns")
async def smoke(dut):
    """Directed smoke test for axil_gpio (generated).

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
    dut.p_gpioIn.value = 0
    dut.p_areset_n.value = 0
    for _ in range(2):
        await RisingEdge(dut.p_aclk)
    await Timer(1, units="ns")
    dut.p_areset_n.value = 1

    # Directed vectors; sample checks after a settle on the falling edge
    await FallingEdge(dut.p_aclk)
    await Timer(1, units="ns")
    assert dut.p_bvalid.value == 0, (
        f"SMOKE FAIL: p_bvalid at cycle 0 expected 0, "
        f"got {int(dut.p_bvalid.value)}"
    )
    assert dut.p_rvalid.value == 0, (
        f"SMOKE FAIL: p_rvalid at cycle 0 expected 0, "
        f"got {int(dut.p_rvalid.value)}"
    )
    assert dut.p_awready.value == 1, (
        f"SMOKE FAIL: p_awready at cycle 0 expected 1, "
        f"got {int(dut.p_awready.value)}"
    )
    assert dut.p_gpioOe.value == 0, (
        f"SMOKE FAIL: p_gpioOe at cycle 0 expected 0, "
        f"got {int(dut.p_gpioOe.value)}"
    )
    assert dut.p_gpioOut.value == 0, (
        f"SMOKE FAIL: p_gpioOut at cycle 0 expected 0, "
        f"got {int(dut.p_gpioOut.value)}"
    )
    await FallingEdge(dut.p_aclk)
    dut.p_awaddr.value = 0
    dut.p_awvalid.value = 1
    dut.p_bready.value = 1
    dut.p_wdata.value = 255
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
    assert dut.p_gpioOe.value == 255, (
        f"SMOKE FAIL: p_gpioOe at cycle 3 expected 255, "
        f"got {int(dut.p_gpioOe.value)}"
    )
    await FallingEdge(dut.p_aclk)
    dut.p_awaddr.value = 4
    dut.p_awvalid.value = 1
    dut.p_bready.value = 1
    dut.p_wdata.value = 165
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
    assert dut.p_gpioOut.value == 165, (
        f"SMOKE FAIL: p_gpioOut at cycle 6 expected 165, "
        f"got {int(dut.p_gpioOut.value)}"
    )
    await FallingEdge(dut.p_aclk)
    dut.p_araddr.value = 0
    dut.p_arvalid.value = 1
    dut.p_rready.value = 1
    await Timer(1, units="ns")
    assert dut.p_bvalid.value == 0, (
        f"SMOKE FAIL: p_bvalid at cycle 7 expected 0, "
        f"got {int(dut.p_bvalid.value)}"
    )
    await FallingEdge(dut.p_aclk)
    dut.p_arvalid.value = 0
    await Timer(1, units="ns")
    assert dut.p_rvalid.value == 1, (
        f"SMOKE FAIL: p_rvalid at cycle 8 expected 1, "
        f"got {int(dut.p_rvalid.value)}"
    )
    assert dut.p_rdata.value == 255, (
        f"SMOKE FAIL: p_rdata at cycle 8 expected 255, "
        f"got {int(dut.p_rdata.value)}"
    )
    assert dut.p_rresp.value == 0, (
        f"SMOKE FAIL: p_rresp at cycle 8 expected 0, "
        f"got {int(dut.p_rresp.value)}"
    )
    await FallingEdge(dut.p_aclk)
    dut.p_gpioIn.value = 90
    await FallingEdge(dut.p_aclk)
    dut.p_araddr.value = 8
    dut.p_arvalid.value = 1
    dut.p_rready.value = 1
    await FallingEdge(dut.p_aclk)
    dut.p_arvalid.value = 0
    await Timer(1, units="ns")
    assert dut.p_rvalid.value == 1, (
        f"SMOKE FAIL: p_rvalid at cycle 11 expected 1, "
        f"got {int(dut.p_rvalid.value)}"
    )
    assert dut.p_rdata.value == 0, (
        f"SMOKE FAIL: p_rdata at cycle 11 expected 0, "
        f"got {int(dut.p_rdata.value)}"
    )
    assert dut.p_rresp.value == 0, (
        f"SMOKE FAIL: p_rresp at cycle 11 expected 0, "
        f"got {int(dut.p_rresp.value)}"
    )
    for _ in range(3):
        await FallingEdge(dut.p_aclk)
    dut.p_araddr.value = 8
    dut.p_arvalid.value = 1
    dut.p_rready.value = 1
    await FallingEdge(dut.p_aclk)
    dut.p_arvalid.value = 0
    await Timer(1, units="ns")
    assert dut.p_rvalid.value == 1, (
        f"SMOKE FAIL: p_rvalid at cycle 15 expected 1, "
        f"got {int(dut.p_rvalid.value)}"
    )
    assert dut.p_rdata.value == 90, (
        f"SMOKE FAIL: p_rdata at cycle 15 expected 90, "
        f"got {int(dut.p_rdata.value)}"
    )
    assert dut.p_rresp.value == 0, (
        f"SMOKE FAIL: p_rresp at cycle 15 expected 0, "
        f"got {int(dut.p_rresp.value)}"
    )
    await FallingEdge(dut.p_aclk)
    dut.p_awaddr.value = 0
    dut.p_awvalid.value = 1
    dut.p_bready.value = 1
    dut.p_wdata.value = 256
    dut.p_wstrb.value = 15
    dut.p_wvalid.value = 1
    await FallingEdge(dut.p_aclk)
    dut.p_awvalid.value = 0
    dut.p_wvalid.value = 0
    await FallingEdge(dut.p_aclk)
    await Timer(1, units="ns")
    assert dut.p_bvalid.value == 1, (
        f"SMOKE FAIL: p_bvalid at cycle 18 expected 1, "
        f"got {int(dut.p_bvalid.value)}"
    )
    assert dut.p_bresp.value == 2, (
        f"SMOKE FAIL: p_bresp at cycle 18 expected 2, "
        f"got {int(dut.p_bresp.value)}"
    )
    assert dut.p_gpioOe.value == 255, (
        f"SMOKE FAIL: p_gpioOe at cycle 18 expected 255, "
        f"got {int(dut.p_gpioOe.value)}"
    )
    await FallingEdge(dut.p_aclk)
    await Timer(1, units="ns")
    assert dut.p_bvalid.value == 0, (
        f"SMOKE FAIL: p_bvalid at cycle 19 expected 0, "
        f"got {int(dut.p_bvalid.value)}"
    )

    dut._log.info("SMOKE PASS: axil_gpio")
