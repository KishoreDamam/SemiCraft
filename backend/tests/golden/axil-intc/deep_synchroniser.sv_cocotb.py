# SemiCraft v0.4.0
# cocotb testbench for axil_intc (config hash: 46f98a14ee2f)
# BETA: the SystemVerilog testbench is the supported default backend.
#
# Generated code is provided as-is, without warranty of any kind. Free for
# commercial and non-commercial use at the user's own risk.

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, RisingEdge, Timer


@cocotb.test(timeout_time=6720, timeout_unit="ns")
async def smoke(dut):
    """Directed smoke test for axil_intc (generated).

    Mirrors the SystemVerilog smoke testbench cycle for cycle.
    """
    cocotb.start_soon(Clock(dut.aclk, 10, units="ns").start())

    # Initialise inputs and assert reset
    dut.awaddr.value = 0
    dut.awvalid.value = 0
    dut.wdata.value = 0
    dut.wstrb.value = 0
    dut.wvalid.value = 0
    dut.bready.value = 0
    dut.araddr.value = 0
    dut.arvalid.value = 0
    dut.rready.value = 0
    dut.irq_in.value = 0
    dut.areset_n.value = 0
    for _ in range(2):
        await RisingEdge(dut.aclk)
    await Timer(1, units="ns")
    dut.areset_n.value = 1

    # Directed vectors; sample checks after a settle on the falling edge
    await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.bvalid.value == 0, (
        f"SMOKE FAIL: bvalid at cycle 0 expected 0, "
        f"got {int(dut.bvalid.value)}"
    )
    assert dut.rvalid.value == 0, (
        f"SMOKE FAIL: rvalid at cycle 0 expected 0, "
        f"got {int(dut.rvalid.value)}"
    )
    assert dut.irq_out.value == 0, (
        f"SMOKE FAIL: irq_out at cycle 0 expected 0, "
        f"got {int(dut.irq_out.value)}"
    )
    await FallingEdge(dut.aclk)
    dut.irq_in.value = 1
    for _ in range(2):
        await FallingEdge(dut.aclk)
    dut.irq_in.value = 0
    for _ in range(2):
        await FallingEdge(dut.aclk)
    dut.araddr.value = 0
    dut.arvalid.value = 1
    dut.rready.value = 1
    await FallingEdge(dut.aclk)
    dut.arvalid.value = 0
    await Timer(1, units="ns")
    assert dut.rvalid.value == 1, (
        f"SMOKE FAIL: rvalid at cycle 6 expected 1, "
        f"got {int(dut.rvalid.value)}"
    )
    assert dut.rdata.value == 0, (
        f"SMOKE FAIL: rdata at cycle 6 expected 0, "
        f"got {int(dut.rdata.value)}"
    )
    assert dut.rresp.value == 0, (
        f"SMOKE FAIL: rresp at cycle 6 expected 0, "
        f"got {int(dut.rresp.value)}"
    )
    await FallingEdge(dut.aclk)
    dut.araddr.value = 0
    dut.arvalid.value = 1
    dut.rready.value = 1
    await FallingEdge(dut.aclk)
    dut.arvalid.value = 0
    await Timer(1, units="ns")
    assert dut.rvalid.value == 1, (
        f"SMOKE FAIL: rvalid at cycle 8 expected 1, "
        f"got {int(dut.rvalid.value)}"
    )
    assert dut.rdata.value == 1, (
        f"SMOKE FAIL: rdata at cycle 8 expected 1, "
        f"got {int(dut.rdata.value)}"
    )
    assert dut.rresp.value == 0, (
        f"SMOKE FAIL: rresp at cycle 8 expected 0, "
        f"got {int(dut.rresp.value)}"
    )
    await FallingEdge(dut.aclk)
    dut.araddr.value = 8
    dut.arvalid.value = 1
    dut.rready.value = 1
    await FallingEdge(dut.aclk)
    dut.arvalid.value = 0
    await Timer(1, units="ns")
    assert dut.rvalid.value == 1, (
        f"SMOKE FAIL: rvalid at cycle 10 expected 1, "
        f"got {int(dut.rvalid.value)}"
    )
    assert dut.rdata.value == 0, (
        f"SMOKE FAIL: rdata at cycle 10 expected 0, "
        f"got {int(dut.rdata.value)}"
    )
    assert dut.rresp.value == 0, (
        f"SMOKE FAIL: rresp at cycle 10 expected 0, "
        f"got {int(dut.rresp.value)}"
    )
    await FallingEdge(dut.aclk)
    dut.awaddr.value = 4
    dut.awvalid.value = 1
    dut.bready.value = 1
    dut.wdata.value = 1
    dut.wstrb.value = 15
    dut.wvalid.value = 1
    await FallingEdge(dut.aclk)
    dut.awvalid.value = 0
    dut.wvalid.value = 0
    await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.bvalid.value == 1, (
        f"SMOKE FAIL: bvalid at cycle 13 expected 1, "
        f"got {int(dut.bvalid.value)}"
    )
    assert dut.bresp.value == 0, (
        f"SMOKE FAIL: bresp at cycle 13 expected 0, "
        f"got {int(dut.bresp.value)}"
    )
    assert dut.irq_out.value == 1, (
        f"SMOKE FAIL: irq_out at cycle 13 expected 1, "
        f"got {int(dut.irq_out.value)}"
    )
    await FallingEdge(dut.aclk)
    dut.araddr.value = 8
    dut.arvalid.value = 1
    dut.rready.value = 1
    await Timer(1, units="ns")
    assert dut.bvalid.value == 0, (
        f"SMOKE FAIL: bvalid at cycle 14 expected 0, "
        f"got {int(dut.bvalid.value)}"
    )
    await FallingEdge(dut.aclk)
    dut.arvalid.value = 0
    await Timer(1, units="ns")
    assert dut.rvalid.value == 1, (
        f"SMOKE FAIL: rvalid at cycle 15 expected 1, "
        f"got {int(dut.rvalid.value)}"
    )
    assert dut.rdata.value == 1, (
        f"SMOKE FAIL: rdata at cycle 15 expected 1, "
        f"got {int(dut.rdata.value)}"
    )
    assert dut.rresp.value == 0, (
        f"SMOKE FAIL: rresp at cycle 15 expected 0, "
        f"got {int(dut.rresp.value)}"
    )
    await FallingEdge(dut.aclk)
    dut.irq_in.value = 2
    for _ in range(2):
        await FallingEdge(dut.aclk)
    dut.irq_in.value = 0
    for _ in range(6):
        await FallingEdge(dut.aclk)
    dut.araddr.value = 0
    dut.arvalid.value = 1
    dut.rready.value = 1
    await FallingEdge(dut.aclk)
    dut.arvalid.value = 0
    await Timer(1, units="ns")
    assert dut.rvalid.value == 1, (
        f"SMOKE FAIL: rvalid at cycle 25 expected 1, "
        f"got {int(dut.rvalid.value)}"
    )
    assert dut.rdata.value == 3, (
        f"SMOKE FAIL: rdata at cycle 25 expected 3, "
        f"got {int(dut.rdata.value)}"
    )
    assert dut.rresp.value == 0, (
        f"SMOKE FAIL: rresp at cycle 25 expected 0, "
        f"got {int(dut.rresp.value)}"
    )
    await FallingEdge(dut.aclk)
    dut.araddr.value = 8
    dut.arvalid.value = 1
    dut.rready.value = 1
    await FallingEdge(dut.aclk)
    dut.arvalid.value = 0
    await Timer(1, units="ns")
    assert dut.rvalid.value == 1, (
        f"SMOKE FAIL: rvalid at cycle 27 expected 1, "
        f"got {int(dut.rvalid.value)}"
    )
    assert dut.rdata.value == 1, (
        f"SMOKE FAIL: rdata at cycle 27 expected 1, "
        f"got {int(dut.rdata.value)}"
    )
    assert dut.rresp.value == 0, (
        f"SMOKE FAIL: rresp at cycle 27 expected 0, "
        f"got {int(dut.rresp.value)}"
    )
    await FallingEdge(dut.aclk)
    dut.awaddr.value = 0
    dut.awvalid.value = 1
    dut.bready.value = 1
    dut.wdata.value = 1
    dut.wstrb.value = 15
    dut.wvalid.value = 1
    await FallingEdge(dut.aclk)
    dut.awvalid.value = 0
    dut.wvalid.value = 0
    await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.bvalid.value == 1, (
        f"SMOKE FAIL: bvalid at cycle 30 expected 1, "
        f"got {int(dut.bvalid.value)}"
    )
    assert dut.bresp.value == 0, (
        f"SMOKE FAIL: bresp at cycle 30 expected 0, "
        f"got {int(dut.bresp.value)}"
    )
    assert dut.irq_out.value == 0, (
        f"SMOKE FAIL: irq_out at cycle 30 expected 0, "
        f"got {int(dut.irq_out.value)}"
    )
    await FallingEdge(dut.aclk)
    dut.araddr.value = 8
    dut.arvalid.value = 1
    dut.rready.value = 1
    await Timer(1, units="ns")
    assert dut.bvalid.value == 0, (
        f"SMOKE FAIL: bvalid at cycle 31 expected 0, "
        f"got {int(dut.bvalid.value)}"
    )
    await FallingEdge(dut.aclk)
    dut.arvalid.value = 0
    await Timer(1, units="ns")
    assert dut.rvalid.value == 1, (
        f"SMOKE FAIL: rvalid at cycle 32 expected 1, "
        f"got {int(dut.rvalid.value)}"
    )
    assert dut.rdata.value == 0, (
        f"SMOKE FAIL: rdata at cycle 32 expected 0, "
        f"got {int(dut.rdata.value)}"
    )
    assert dut.rresp.value == 0, (
        f"SMOKE FAIL: rresp at cycle 32 expected 0, "
        f"got {int(dut.rresp.value)}"
    )
    await FallingEdge(dut.aclk)
    dut.araddr.value = 0
    dut.arvalid.value = 1
    dut.rready.value = 1
    await FallingEdge(dut.aclk)
    dut.arvalid.value = 0
    await Timer(1, units="ns")
    assert dut.rvalid.value == 1, (
        f"SMOKE FAIL: rvalid at cycle 34 expected 1, "
        f"got {int(dut.rvalid.value)}"
    )
    assert dut.rdata.value == 2, (
        f"SMOKE FAIL: rdata at cycle 34 expected 2, "
        f"got {int(dut.rdata.value)}"
    )
    assert dut.rresp.value == 0, (
        f"SMOKE FAIL: rresp at cycle 34 expected 0, "
        f"got {int(dut.rresp.value)}"
    )
    await FallingEdge(dut.aclk)
    dut.awaddr.value = 0
    dut.awvalid.value = 1
    dut.bready.value = 1
    dut.wdata.value = 2
    dut.wstrb.value = 15
    dut.wvalid.value = 1
    await FallingEdge(dut.aclk)
    dut.awvalid.value = 0
    dut.wvalid.value = 0
    await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.bvalid.value == 1, (
        f"SMOKE FAIL: bvalid at cycle 37 expected 1, "
        f"got {int(dut.bvalid.value)}"
    )
    assert dut.bresp.value == 0, (
        f"SMOKE FAIL: bresp at cycle 37 expected 0, "
        f"got {int(dut.bresp.value)}"
    )
    assert dut.irq_out.value == 0, (
        f"SMOKE FAIL: irq_out at cycle 37 expected 0, "
        f"got {int(dut.irq_out.value)}"
    )
    await FallingEdge(dut.aclk)
    dut.araddr.value = 0
    dut.arvalid.value = 1
    dut.rready.value = 1
    await Timer(1, units="ns")
    assert dut.bvalid.value == 0, (
        f"SMOKE FAIL: bvalid at cycle 38 expected 0, "
        f"got {int(dut.bvalid.value)}"
    )
    await FallingEdge(dut.aclk)
    dut.arvalid.value = 0
    await Timer(1, units="ns")
    assert dut.rvalid.value == 1, (
        f"SMOKE FAIL: rvalid at cycle 39 expected 1, "
        f"got {int(dut.rvalid.value)}"
    )
    assert dut.rdata.value == 0, (
        f"SMOKE FAIL: rdata at cycle 39 expected 0, "
        f"got {int(dut.rdata.value)}"
    )
    assert dut.rresp.value == 0, (
        f"SMOKE FAIL: rresp at cycle 39 expected 0, "
        f"got {int(dut.rresp.value)}"
    )
    await FallingEdge(dut.aclk)
    dut.awaddr.value = 4
    dut.awvalid.value = 1
    dut.bready.value = 1
    dut.wdata.value = 0
    dut.wstrb.value = 15
    dut.wvalid.value = 1
    await FallingEdge(dut.aclk)
    dut.awvalid.value = 0
    dut.wvalid.value = 0
    await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.bvalid.value == 1, (
        f"SMOKE FAIL: bvalid at cycle 42 expected 1, "
        f"got {int(dut.bvalid.value)}"
    )
    assert dut.bresp.value == 0, (
        f"SMOKE FAIL: bresp at cycle 42 expected 0, "
        f"got {int(dut.bresp.value)}"
    )
    assert dut.irq_out.value == 0, (
        f"SMOKE FAIL: irq_out at cycle 42 expected 0, "
        f"got {int(dut.irq_out.value)}"
    )
    await FallingEdge(dut.aclk)
    dut.irq_in.value = 1
    await Timer(1, units="ns")
    assert dut.bvalid.value == 0, (
        f"SMOKE FAIL: bvalid at cycle 43 expected 0, "
        f"got {int(dut.bvalid.value)}"
    )
    for _ in range(6):
        await FallingEdge(dut.aclk)
    dut.araddr.value = 0
    dut.arvalid.value = 1
    dut.rready.value = 1
    await FallingEdge(dut.aclk)
    dut.arvalid.value = 0
    await Timer(1, units="ns")
    assert dut.rvalid.value == 1, (
        f"SMOKE FAIL: rvalid at cycle 50 expected 1, "
        f"got {int(dut.rvalid.value)}"
    )
    assert dut.rdata.value == 1, (
        f"SMOKE FAIL: rdata at cycle 50 expected 1, "
        f"got {int(dut.rdata.value)}"
    )
    assert dut.rresp.value == 0, (
        f"SMOKE FAIL: rresp at cycle 50 expected 0, "
        f"got {int(dut.rresp.value)}"
    )
    await FallingEdge(dut.aclk)
    dut.awaddr.value = 0
    dut.awvalid.value = 1
    dut.bready.value = 1
    dut.wdata.value = 1
    dut.wstrb.value = 15
    dut.wvalid.value = 1
    await FallingEdge(dut.aclk)
    dut.awvalid.value = 0
    dut.wvalid.value = 0
    await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.bvalid.value == 1, (
        f"SMOKE FAIL: bvalid at cycle 53 expected 1, "
        f"got {int(dut.bvalid.value)}"
    )
    assert dut.bresp.value == 0, (
        f"SMOKE FAIL: bresp at cycle 53 expected 0, "
        f"got {int(dut.bresp.value)}"
    )
    assert dut.irq_out.value == 0, (
        f"SMOKE FAIL: irq_out at cycle 53 expected 0, "
        f"got {int(dut.irq_out.value)}"
    )
    await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.bvalid.value == 0, (
        f"SMOKE FAIL: bvalid at cycle 54 expected 0, "
        f"got {int(dut.bvalid.value)}"
    )
    for _ in range(6):
        await FallingEdge(dut.aclk)
    dut.araddr.value = 0
    dut.arvalid.value = 1
    dut.rready.value = 1
    await FallingEdge(dut.aclk)
    dut.arvalid.value = 0
    await Timer(1, units="ns")
    assert dut.rvalid.value == 1, (
        f"SMOKE FAIL: rvalid at cycle 61 expected 1, "
        f"got {int(dut.rvalid.value)}"
    )
    assert dut.rdata.value == 0, (
        f"SMOKE FAIL: rdata at cycle 61 expected 0, "
        f"got {int(dut.rdata.value)}"
    )
    assert dut.rresp.value == 0, (
        f"SMOKE FAIL: rresp at cycle 61 expected 0, "
        f"got {int(dut.rresp.value)}"
    )
    await FallingEdge(dut.aclk)
    dut.awaddr.value = 4
    dut.awvalid.value = 1
    dut.bready.value = 1
    dut.irq_in.value = 0
    dut.wdata.value = 256
    dut.wstrb.value = 15
    dut.wvalid.value = 1
    await FallingEdge(dut.aclk)
    dut.awvalid.value = 0
    dut.wvalid.value = 0
    await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.bvalid.value == 1, (
        f"SMOKE FAIL: bvalid at cycle 64 expected 1, "
        f"got {int(dut.bvalid.value)}"
    )
    assert dut.bresp.value == 2, (
        f"SMOKE FAIL: bresp at cycle 64 expected 2, "
        f"got {int(dut.bresp.value)}"
    )
    assert dut.irq_out.value == 0, (
        f"SMOKE FAIL: irq_out at cycle 64 expected 0, "
        f"got {int(dut.irq_out.value)}"
    )
    await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.bvalid.value == 0, (
        f"SMOKE FAIL: bvalid at cycle 65 expected 0, "
        f"got {int(dut.bvalid.value)}"
    )

    dut._log.info("SMOKE PASS: axil_intc")
