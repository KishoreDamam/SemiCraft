# SemiCraft v0.4.0
# cocotb testbench for axil_intc (config hash: 75a8ad364387)
# BETA: the SystemVerilog testbench is the supported default backend.
#
# Generated code is provided as-is, without warranty of any kind. Free for
# commercial and non-commercial use at the user's own risk.

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, RisingEdge, Timer


@cocotb.test(timeout_time=6080, timeout_unit="ns")
async def smoke(dut):
    """Directed smoke test for axil_intc (generated).

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
    dut.p_irqIn.value = 0
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
    assert dut.p_irqOut.value == 0, (
        f"SMOKE FAIL: p_irqOut at cycle 0 expected 0, "
        f"got {int(dut.p_irqOut.value)}"
    )
    await FallingEdge(dut.p_aclk)
    dut.p_irqIn.value = 1
    for _ in range(2):
        await FallingEdge(dut.p_aclk)
    dut.p_araddr.value = 0
    dut.p_arvalid.value = 1
    dut.p_irqIn.value = 0
    dut.p_rready.value = 1
    await FallingEdge(dut.p_aclk)
    dut.p_arvalid.value = 0
    await Timer(1, units="ns")
    assert dut.p_rvalid.value == 1, (
        f"SMOKE FAIL: p_rvalid at cycle 4 expected 1, "
        f"got {int(dut.p_rvalid.value)}"
    )
    assert dut.p_rdata.value == 0, (
        f"SMOKE FAIL: p_rdata at cycle 4 expected 0, "
        f"got {int(dut.p_rdata.value)}"
    )
    assert dut.p_rresp.value == 0, (
        f"SMOKE FAIL: p_rresp at cycle 4 expected 0, "
        f"got {int(dut.p_rresp.value)}"
    )
    await FallingEdge(dut.p_aclk)
    dut.p_araddr.value = 0
    dut.p_arvalid.value = 1
    dut.p_rready.value = 1
    await FallingEdge(dut.p_aclk)
    dut.p_arvalid.value = 0
    await Timer(1, units="ns")
    assert dut.p_rvalid.value == 1, (
        f"SMOKE FAIL: p_rvalid at cycle 6 expected 1, "
        f"got {int(dut.p_rvalid.value)}"
    )
    assert dut.p_rdata.value == 1, (
        f"SMOKE FAIL: p_rdata at cycle 6 expected 1, "
        f"got {int(dut.p_rdata.value)}"
    )
    assert dut.p_rresp.value == 0, (
        f"SMOKE FAIL: p_rresp at cycle 6 expected 0, "
        f"got {int(dut.p_rresp.value)}"
    )
    await FallingEdge(dut.p_aclk)
    dut.p_araddr.value = 8
    dut.p_arvalid.value = 1
    dut.p_rready.value = 1
    await FallingEdge(dut.p_aclk)
    dut.p_arvalid.value = 0
    await Timer(1, units="ns")
    assert dut.p_rvalid.value == 1, (
        f"SMOKE FAIL: p_rvalid at cycle 8 expected 1, "
        f"got {int(dut.p_rvalid.value)}"
    )
    assert dut.p_rdata.value == 0, (
        f"SMOKE FAIL: p_rdata at cycle 8 expected 0, "
        f"got {int(dut.p_rdata.value)}"
    )
    assert dut.p_rresp.value == 0, (
        f"SMOKE FAIL: p_rresp at cycle 8 expected 0, "
        f"got {int(dut.p_rresp.value)}"
    )
    await FallingEdge(dut.p_aclk)
    dut.p_awaddr.value = 4
    dut.p_awvalid.value = 1
    dut.p_bready.value = 1
    dut.p_wdata.value = 1
    dut.p_wstrb.value = 15
    dut.p_wvalid.value = 1
    await FallingEdge(dut.p_aclk)
    dut.p_awvalid.value = 0
    dut.p_wvalid.value = 0
    await FallingEdge(dut.p_aclk)
    await Timer(1, units="ns")
    assert dut.p_bvalid.value == 1, (
        f"SMOKE FAIL: p_bvalid at cycle 11 expected 1, "
        f"got {int(dut.p_bvalid.value)}"
    )
    assert dut.p_bresp.value == 0, (
        f"SMOKE FAIL: p_bresp at cycle 11 expected 0, "
        f"got {int(dut.p_bresp.value)}"
    )
    assert dut.p_irqOut.value == 1, (
        f"SMOKE FAIL: p_irqOut at cycle 11 expected 1, "
        f"got {int(dut.p_irqOut.value)}"
    )
    await FallingEdge(dut.p_aclk)
    dut.p_araddr.value = 8
    dut.p_arvalid.value = 1
    dut.p_rready.value = 1
    await Timer(1, units="ns")
    assert dut.p_bvalid.value == 0, (
        f"SMOKE FAIL: p_bvalid at cycle 12 expected 0, "
        f"got {int(dut.p_bvalid.value)}"
    )
    await FallingEdge(dut.p_aclk)
    dut.p_arvalid.value = 0
    await Timer(1, units="ns")
    assert dut.p_rvalid.value == 1, (
        f"SMOKE FAIL: p_rvalid at cycle 13 expected 1, "
        f"got {int(dut.p_rvalid.value)}"
    )
    assert dut.p_rdata.value == 1, (
        f"SMOKE FAIL: p_rdata at cycle 13 expected 1, "
        f"got {int(dut.p_rdata.value)}"
    )
    assert dut.p_rresp.value == 0, (
        f"SMOKE FAIL: p_rresp at cycle 13 expected 0, "
        f"got {int(dut.p_rresp.value)}"
    )
    await FallingEdge(dut.p_aclk)
    dut.p_irqIn.value = 2
    for _ in range(2):
        await FallingEdge(dut.p_aclk)
    dut.p_irqIn.value = 0
    for _ in range(4):
        await FallingEdge(dut.p_aclk)
    dut.p_araddr.value = 0
    dut.p_arvalid.value = 1
    dut.p_rready.value = 1
    await FallingEdge(dut.p_aclk)
    dut.p_arvalid.value = 0
    await Timer(1, units="ns")
    assert dut.p_rvalid.value == 1, (
        f"SMOKE FAIL: p_rvalid at cycle 21 expected 1, "
        f"got {int(dut.p_rvalid.value)}"
    )
    assert dut.p_rdata.value == 3, (
        f"SMOKE FAIL: p_rdata at cycle 21 expected 3, "
        f"got {int(dut.p_rdata.value)}"
    )
    assert dut.p_rresp.value == 0, (
        f"SMOKE FAIL: p_rresp at cycle 21 expected 0, "
        f"got {int(dut.p_rresp.value)}"
    )
    await FallingEdge(dut.p_aclk)
    dut.p_araddr.value = 8
    dut.p_arvalid.value = 1
    dut.p_rready.value = 1
    await FallingEdge(dut.p_aclk)
    dut.p_arvalid.value = 0
    await Timer(1, units="ns")
    assert dut.p_rvalid.value == 1, (
        f"SMOKE FAIL: p_rvalid at cycle 23 expected 1, "
        f"got {int(dut.p_rvalid.value)}"
    )
    assert dut.p_rdata.value == 1, (
        f"SMOKE FAIL: p_rdata at cycle 23 expected 1, "
        f"got {int(dut.p_rdata.value)}"
    )
    assert dut.p_rresp.value == 0, (
        f"SMOKE FAIL: p_rresp at cycle 23 expected 0, "
        f"got {int(dut.p_rresp.value)}"
    )
    await FallingEdge(dut.p_aclk)
    dut.p_awaddr.value = 0
    dut.p_awvalid.value = 1
    dut.p_bready.value = 1
    dut.p_wdata.value = 1
    dut.p_wstrb.value = 15
    dut.p_wvalid.value = 1
    await FallingEdge(dut.p_aclk)
    dut.p_awvalid.value = 0
    dut.p_wvalid.value = 0
    await FallingEdge(dut.p_aclk)
    await Timer(1, units="ns")
    assert dut.p_bvalid.value == 1, (
        f"SMOKE FAIL: p_bvalid at cycle 26 expected 1, "
        f"got {int(dut.p_bvalid.value)}"
    )
    assert dut.p_bresp.value == 0, (
        f"SMOKE FAIL: p_bresp at cycle 26 expected 0, "
        f"got {int(dut.p_bresp.value)}"
    )
    assert dut.p_irqOut.value == 0, (
        f"SMOKE FAIL: p_irqOut at cycle 26 expected 0, "
        f"got {int(dut.p_irqOut.value)}"
    )
    await FallingEdge(dut.p_aclk)
    dut.p_araddr.value = 8
    dut.p_arvalid.value = 1
    dut.p_rready.value = 1
    await Timer(1, units="ns")
    assert dut.p_bvalid.value == 0, (
        f"SMOKE FAIL: p_bvalid at cycle 27 expected 0, "
        f"got {int(dut.p_bvalid.value)}"
    )
    await FallingEdge(dut.p_aclk)
    dut.p_arvalid.value = 0
    await Timer(1, units="ns")
    assert dut.p_rvalid.value == 1, (
        f"SMOKE FAIL: p_rvalid at cycle 28 expected 1, "
        f"got {int(dut.p_rvalid.value)}"
    )
    assert dut.p_rdata.value == 0, (
        f"SMOKE FAIL: p_rdata at cycle 28 expected 0, "
        f"got {int(dut.p_rdata.value)}"
    )
    assert dut.p_rresp.value == 0, (
        f"SMOKE FAIL: p_rresp at cycle 28 expected 0, "
        f"got {int(dut.p_rresp.value)}"
    )
    await FallingEdge(dut.p_aclk)
    dut.p_araddr.value = 0
    dut.p_arvalid.value = 1
    dut.p_rready.value = 1
    await FallingEdge(dut.p_aclk)
    dut.p_arvalid.value = 0
    await Timer(1, units="ns")
    assert dut.p_rvalid.value == 1, (
        f"SMOKE FAIL: p_rvalid at cycle 30 expected 1, "
        f"got {int(dut.p_rvalid.value)}"
    )
    assert dut.p_rdata.value == 2, (
        f"SMOKE FAIL: p_rdata at cycle 30 expected 2, "
        f"got {int(dut.p_rdata.value)}"
    )
    assert dut.p_rresp.value == 0, (
        f"SMOKE FAIL: p_rresp at cycle 30 expected 0, "
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
        f"SMOKE FAIL: p_bvalid at cycle 33 expected 1, "
        f"got {int(dut.p_bvalid.value)}"
    )
    assert dut.p_bresp.value == 0, (
        f"SMOKE FAIL: p_bresp at cycle 33 expected 0, "
        f"got {int(dut.p_bresp.value)}"
    )
    assert dut.p_irqOut.value == 0, (
        f"SMOKE FAIL: p_irqOut at cycle 33 expected 0, "
        f"got {int(dut.p_irqOut.value)}"
    )
    await FallingEdge(dut.p_aclk)
    dut.p_araddr.value = 0
    dut.p_arvalid.value = 1
    dut.p_rready.value = 1
    await Timer(1, units="ns")
    assert dut.p_bvalid.value == 0, (
        f"SMOKE FAIL: p_bvalid at cycle 34 expected 0, "
        f"got {int(dut.p_bvalid.value)}"
    )
    await FallingEdge(dut.p_aclk)
    dut.p_arvalid.value = 0
    await Timer(1, units="ns")
    assert dut.p_rvalid.value == 1, (
        f"SMOKE FAIL: p_rvalid at cycle 35 expected 1, "
        f"got {int(dut.p_rvalid.value)}"
    )
    assert dut.p_rdata.value == 0, (
        f"SMOKE FAIL: p_rdata at cycle 35 expected 0, "
        f"got {int(dut.p_rdata.value)}"
    )
    assert dut.p_rresp.value == 0, (
        f"SMOKE FAIL: p_rresp at cycle 35 expected 0, "
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
        f"SMOKE FAIL: p_bvalid at cycle 38 expected 1, "
        f"got {int(dut.p_bvalid.value)}"
    )
    assert dut.p_bresp.value == 0, (
        f"SMOKE FAIL: p_bresp at cycle 38 expected 0, "
        f"got {int(dut.p_bresp.value)}"
    )
    assert dut.p_irqOut.value == 0, (
        f"SMOKE FAIL: p_irqOut at cycle 38 expected 0, "
        f"got {int(dut.p_irqOut.value)}"
    )
    await FallingEdge(dut.p_aclk)
    dut.p_irqIn.value = 1
    await Timer(1, units="ns")
    assert dut.p_bvalid.value == 0, (
        f"SMOKE FAIL: p_bvalid at cycle 39 expected 0, "
        f"got {int(dut.p_bvalid.value)}"
    )
    for _ in range(4):
        await FallingEdge(dut.p_aclk)
    dut.p_araddr.value = 0
    dut.p_arvalid.value = 1
    dut.p_rready.value = 1
    await FallingEdge(dut.p_aclk)
    dut.p_arvalid.value = 0
    await Timer(1, units="ns")
    assert dut.p_rvalid.value == 1, (
        f"SMOKE FAIL: p_rvalid at cycle 44 expected 1, "
        f"got {int(dut.p_rvalid.value)}"
    )
    assert dut.p_rdata.value == 1, (
        f"SMOKE FAIL: p_rdata at cycle 44 expected 1, "
        f"got {int(dut.p_rdata.value)}"
    )
    assert dut.p_rresp.value == 0, (
        f"SMOKE FAIL: p_rresp at cycle 44 expected 0, "
        f"got {int(dut.p_rresp.value)}"
    )
    await FallingEdge(dut.p_aclk)
    dut.p_awaddr.value = 0
    dut.p_awvalid.value = 1
    dut.p_bready.value = 1
    dut.p_wdata.value = 1
    dut.p_wstrb.value = 15
    dut.p_wvalid.value = 1
    await FallingEdge(dut.p_aclk)
    dut.p_awvalid.value = 0
    dut.p_wvalid.value = 0
    await FallingEdge(dut.p_aclk)
    await Timer(1, units="ns")
    assert dut.p_bvalid.value == 1, (
        f"SMOKE FAIL: p_bvalid at cycle 47 expected 1, "
        f"got {int(dut.p_bvalid.value)}"
    )
    assert dut.p_bresp.value == 0, (
        f"SMOKE FAIL: p_bresp at cycle 47 expected 0, "
        f"got {int(dut.p_bresp.value)}"
    )
    assert dut.p_irqOut.value == 0, (
        f"SMOKE FAIL: p_irqOut at cycle 47 expected 0, "
        f"got {int(dut.p_irqOut.value)}"
    )
    await FallingEdge(dut.p_aclk)
    await Timer(1, units="ns")
    assert dut.p_bvalid.value == 0, (
        f"SMOKE FAIL: p_bvalid at cycle 48 expected 0, "
        f"got {int(dut.p_bvalid.value)}"
    )
    for _ in range(4):
        await FallingEdge(dut.p_aclk)
    dut.p_araddr.value = 0
    dut.p_arvalid.value = 1
    dut.p_rready.value = 1
    await FallingEdge(dut.p_aclk)
    dut.p_arvalid.value = 0
    await Timer(1, units="ns")
    assert dut.p_rvalid.value == 1, (
        f"SMOKE FAIL: p_rvalid at cycle 53 expected 1, "
        f"got {int(dut.p_rvalid.value)}"
    )
    assert dut.p_rdata.value == 0, (
        f"SMOKE FAIL: p_rdata at cycle 53 expected 0, "
        f"got {int(dut.p_rdata.value)}"
    )
    assert dut.p_rresp.value == 0, (
        f"SMOKE FAIL: p_rresp at cycle 53 expected 0, "
        f"got {int(dut.p_rresp.value)}"
    )
    await FallingEdge(dut.p_aclk)
    dut.p_awaddr.value = 4
    dut.p_awvalid.value = 1
    dut.p_bready.value = 1
    dut.p_irqIn.value = 0
    dut.p_wdata.value = 256
    dut.p_wstrb.value = 15
    dut.p_wvalid.value = 1
    await FallingEdge(dut.p_aclk)
    dut.p_awvalid.value = 0
    dut.p_wvalid.value = 0
    await FallingEdge(dut.p_aclk)
    await Timer(1, units="ns")
    assert dut.p_bvalid.value == 1, (
        f"SMOKE FAIL: p_bvalid at cycle 56 expected 1, "
        f"got {int(dut.p_bvalid.value)}"
    )
    assert dut.p_bresp.value == 2, (
        f"SMOKE FAIL: p_bresp at cycle 56 expected 2, "
        f"got {int(dut.p_bresp.value)}"
    )
    assert dut.p_irqOut.value == 0, (
        f"SMOKE FAIL: p_irqOut at cycle 56 expected 0, "
        f"got {int(dut.p_irqOut.value)}"
    )
    await FallingEdge(dut.p_aclk)
    await Timer(1, units="ns")
    assert dut.p_bvalid.value == 0, (
        f"SMOKE FAIL: p_bvalid at cycle 57 expected 0, "
        f"got {int(dut.p_bvalid.value)}"
    )

    dut._log.info("SMOKE PASS: axil_intc")
