# SemiCraft v0.4.0
# cocotb testbench for axil_timer (config hash: 0cd916fa1b61)
# BETA: the SystemVerilog testbench is the supported default backend.
#
# Generated code is provided as-is, without warranty of any kind. Free for
# commercial and non-commercial use at the user's own risk.

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, RisingEdge, Timer


@cocotb.test(timeout_time=7680, timeout_unit="ns")
async def smoke(dut):
    """Directed smoke test for axil_timer (generated).

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
    assert dut.p_irq.value == 0, (
        f"SMOKE FAIL: p_irq at cycle 0 expected 0, "
        f"got {int(dut.p_irq.value)}"
    )
    await FallingEdge(dut.p_aclk)
    dut.p_awaddr.value = 12
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
        f"SMOKE FAIL: p_bvalid at cycle 3 expected 1, "
        f"got {int(dut.p_bvalid.value)}"
    )
    assert dut.p_bresp.value == 0, (
        f"SMOKE FAIL: p_bresp at cycle 3 expected 0, "
        f"got {int(dut.p_bresp.value)}"
    )
    assert dut.p_irq.value == 0, (
        f"SMOKE FAIL: p_irq at cycle 3 expected 0, "
        f"got {int(dut.p_irq.value)}"
    )
    await FallingEdge(dut.p_aclk)
    dut.p_awaddr.value = 4
    dut.p_awvalid.value = 1
    dut.p_bready.value = 1
    dut.p_wdata.value = 3
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
    assert dut.p_irq.value == 0, (
        f"SMOKE FAIL: p_irq at cycle 6 expected 0, "
        f"got {int(dut.p_irq.value)}"
    )
    await FallingEdge(dut.p_aclk)
    dut.p_araddr.value = 8
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
    assert dut.p_rdata.value == 3, (
        f"SMOKE FAIL: p_rdata at cycle 8 expected 3, "
        f"got {int(dut.p_rdata.value)}"
    )
    assert dut.p_rresp.value == 0, (
        f"SMOKE FAIL: p_rresp at cycle 8 expected 0, "
        f"got {int(dut.p_rresp.value)}"
    )
    await FallingEdge(dut.p_aclk)
    dut.p_awaddr.value = 0
    dut.p_awvalid.value = 1
    dut.p_bready.value = 1
    dut.p_wdata.value = 7
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
    assert dut.p_irq.value == 0, (
        f"SMOKE FAIL: p_irq at cycle 11 expected 0, "
        f"got {int(dut.p_irq.value)}"
    )
    await FallingEdge(dut.p_aclk)
    await Timer(1, units="ns")
    assert dut.p_bvalid.value == 0, (
        f"SMOKE FAIL: p_bvalid at cycle 12 expected 0, "
        f"got {int(dut.p_bvalid.value)}"
    )
    for _ in range(7):
        await FallingEdge(dut.p_aclk)
    await Timer(1, units="ns")
    assert dut.p_irq.value == 0, (
        f"SMOKE FAIL: p_irq at cycle 19 expected 0, "
        f"got {int(dut.p_irq.value)}"
    )
    await FallingEdge(dut.p_aclk)
    await Timer(1, units="ns")
    assert dut.p_irq.value == 1, (
        f"SMOKE FAIL: p_irq at cycle 20 expected 1, "
        f"got {int(dut.p_irq.value)}"
    )
    await FallingEdge(dut.p_aclk)
    dut.p_araddr.value = 16
    dut.p_arvalid.value = 1
    dut.p_rready.value = 1
    await FallingEdge(dut.p_aclk)
    dut.p_arvalid.value = 0
    await Timer(1, units="ns")
    assert dut.p_rvalid.value == 1, (
        f"SMOKE FAIL: p_rvalid at cycle 22 expected 1, "
        f"got {int(dut.p_rvalid.value)}"
    )
    assert dut.p_rdata.value == 1, (
        f"SMOKE FAIL: p_rdata at cycle 22 expected 1, "
        f"got {int(dut.p_rdata.value)}"
    )
    assert dut.p_rresp.value == 0, (
        f"SMOKE FAIL: p_rresp at cycle 22 expected 0, "
        f"got {int(dut.p_rresp.value)}"
    )
    await FallingEdge(dut.p_aclk)
    dut.p_awaddr.value = 0
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
        f"SMOKE FAIL: p_bvalid at cycle 25 expected 1, "
        f"got {int(dut.p_bvalid.value)}"
    )
    assert dut.p_bresp.value == 0, (
        f"SMOKE FAIL: p_bresp at cycle 25 expected 0, "
        f"got {int(dut.p_bresp.value)}"
    )
    assert dut.p_irq.value == 0, (
        f"SMOKE FAIL: p_irq at cycle 25 expected 0, "
        f"got {int(dut.p_irq.value)}"
    )
    await FallingEdge(dut.p_aclk)
    dut.p_awaddr.value = 16
    dut.p_awvalid.value = 1
    dut.p_bready.value = 1
    dut.p_wdata.value = 1
    dut.p_wstrb.value = 15
    dut.p_wvalid.value = 1
    await Timer(1, units="ns")
    assert dut.p_bvalid.value == 0, (
        f"SMOKE FAIL: p_bvalid at cycle 26 expected 0, "
        f"got {int(dut.p_bvalid.value)}"
    )
    await FallingEdge(dut.p_aclk)
    dut.p_awvalid.value = 0
    dut.p_wvalid.value = 0
    await FallingEdge(dut.p_aclk)
    await Timer(1, units="ns")
    assert dut.p_bvalid.value == 1, (
        f"SMOKE FAIL: p_bvalid at cycle 28 expected 1, "
        f"got {int(dut.p_bvalid.value)}"
    )
    assert dut.p_bresp.value == 0, (
        f"SMOKE FAIL: p_bresp at cycle 28 expected 0, "
        f"got {int(dut.p_bresp.value)}"
    )
    assert dut.p_irq.value == 0, (
        f"SMOKE FAIL: p_irq at cycle 28 expected 0, "
        f"got {int(dut.p_irq.value)}"
    )
    await FallingEdge(dut.p_aclk)
    dut.p_araddr.value = 16
    dut.p_arvalid.value = 1
    dut.p_rready.value = 1
    await Timer(1, units="ns")
    assert dut.p_bvalid.value == 0, (
        f"SMOKE FAIL: p_bvalid at cycle 29 expected 0, "
        f"got {int(dut.p_bvalid.value)}"
    )
    await FallingEdge(dut.p_aclk)
    dut.p_arvalid.value = 0
    await Timer(1, units="ns")
    assert dut.p_rvalid.value == 1, (
        f"SMOKE FAIL: p_rvalid at cycle 30 expected 1, "
        f"got {int(dut.p_rvalid.value)}"
    )
    assert dut.p_rdata.value == 0, (
        f"SMOKE FAIL: p_rdata at cycle 30 expected 0, "
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
    dut.p_wdata.value = 5
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
    assert dut.p_irq.value == 0, (
        f"SMOKE FAIL: p_irq at cycle 33 expected 0, "
        f"got {int(dut.p_irq.value)}"
    )
    await FallingEdge(dut.p_aclk)
    await Timer(1, units="ns")
    assert dut.p_bvalid.value == 0, (
        f"SMOKE FAIL: p_bvalid at cycle 34 expected 0, "
        f"got {int(dut.p_bvalid.value)}"
    )
    for _ in range(7):
        await FallingEdge(dut.p_aclk)
    await Timer(1, units="ns")
    assert dut.p_irq.value == 0, (
        f"SMOKE FAIL: p_irq at cycle 41 expected 0, "
        f"got {int(dut.p_irq.value)}"
    )
    await FallingEdge(dut.p_aclk)
    await Timer(1, units="ns")
    assert dut.p_irq.value == 1, (
        f"SMOKE FAIL: p_irq at cycle 42 expected 1, "
        f"got {int(dut.p_irq.value)}"
    )
    await FallingEdge(dut.p_aclk)
    dut.p_awaddr.value = 16
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
        f"SMOKE FAIL: p_bvalid at cycle 45 expected 1, "
        f"got {int(dut.p_bvalid.value)}"
    )
    assert dut.p_bresp.value == 0, (
        f"SMOKE FAIL: p_bresp at cycle 45 expected 0, "
        f"got {int(dut.p_bresp.value)}"
    )
    assert dut.p_irq.value == 0, (
        f"SMOKE FAIL: p_irq at cycle 45 expected 0, "
        f"got {int(dut.p_irq.value)}"
    )
    await FallingEdge(dut.p_aclk)
    await Timer(1, units="ns")
    assert dut.p_bvalid.value == 0, (
        f"SMOKE FAIL: p_bvalid at cycle 46 expected 0, "
        f"got {int(dut.p_bvalid.value)}"
    )
    for _ in range(24):
        await FallingEdge(dut.p_aclk)
    dut.p_araddr.value = 8
    dut.p_arvalid.value = 1
    dut.p_rready.value = 1
    await FallingEdge(dut.p_aclk)
    dut.p_arvalid.value = 0
    await Timer(1, units="ns")
    assert dut.p_rvalid.value == 1, (
        f"SMOKE FAIL: p_rvalid at cycle 71 expected 1, "
        f"got {int(dut.p_rvalid.value)}"
    )
    assert dut.p_rdata.value == 0, (
        f"SMOKE FAIL: p_rdata at cycle 71 expected 0, "
        f"got {int(dut.p_rdata.value)}"
    )
    assert dut.p_rresp.value == 0, (
        f"SMOKE FAIL: p_rresp at cycle 71 expected 0, "
        f"got {int(dut.p_rresp.value)}"
    )
    await FallingEdge(dut.p_aclk)
    dut.p_araddr.value = 16
    dut.p_arvalid.value = 1
    dut.p_rready.value = 1
    await FallingEdge(dut.p_aclk)
    dut.p_arvalid.value = 0
    await Timer(1, units="ns")
    assert dut.p_rvalid.value == 1, (
        f"SMOKE FAIL: p_rvalid at cycle 73 expected 1, "
        f"got {int(dut.p_rvalid.value)}"
    )
    assert dut.p_rdata.value == 0, (
        f"SMOKE FAIL: p_rdata at cycle 73 expected 0, "
        f"got {int(dut.p_rdata.value)}"
    )
    assert dut.p_rresp.value == 0, (
        f"SMOKE FAIL: p_rresp at cycle 73 expected 0, "
        f"got {int(dut.p_rresp.value)}"
    )
    assert dut.p_irq.value == 0, (
        f"SMOKE FAIL: p_irq at cycle 73 expected 0, "
        f"got {int(dut.p_irq.value)}"
    )
    await FallingEdge(dut.p_aclk)
    dut.p_awaddr.value = 0
    dut.p_awvalid.value = 1
    dut.p_bready.value = 1
    dut.p_wdata.value = 8
    dut.p_wstrb.value = 15
    dut.p_wvalid.value = 1
    await FallingEdge(dut.p_aclk)
    dut.p_awvalid.value = 0
    dut.p_wvalid.value = 0
    await FallingEdge(dut.p_aclk)
    await Timer(1, units="ns")
    assert dut.p_bvalid.value == 1, (
        f"SMOKE FAIL: p_bvalid at cycle 76 expected 1, "
        f"got {int(dut.p_bvalid.value)}"
    )
    assert dut.p_bresp.value == 2, (
        f"SMOKE FAIL: p_bresp at cycle 76 expected 2, "
        f"got {int(dut.p_bresp.value)}"
    )
    assert dut.p_irq.value == 0, (
        f"SMOKE FAIL: p_irq at cycle 76 expected 0, "
        f"got {int(dut.p_irq.value)}"
    )
    await FallingEdge(dut.p_aclk)
    await Timer(1, units="ns")
    assert dut.p_bvalid.value == 0, (
        f"SMOKE FAIL: p_bvalid at cycle 77 expected 0, "
        f"got {int(dut.p_bvalid.value)}"
    )

    dut._log.info("SMOKE PASS: axil_timer")
