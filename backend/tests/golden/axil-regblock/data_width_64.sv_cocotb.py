# SemiCraft v0.4.0
# cocotb testbench for axil_regblock (config hash: d9042ecb56c6)
# BETA: the SystemVerilog testbench is the supported default backend.
#
# Generated code is provided as-is, without warranty of any kind. Free for
# commercial and non-commercial use at the user's own risk.

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, RisingEdge, Timer


@cocotb.test(timeout_time=4080, timeout_unit="ns")
async def smoke(dut):
    """Directed smoke test for axil_regblock (generated).

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
    dut.status0_busy.value = 0
    dut.status0_code.value = 0
    dut.irq0_flags_set.value = 0
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
    assert dut.awready.value == 1, (
        f"SMOKE FAIL: awready at cycle 0 expected 1, "
        f"got {int(dut.awready.value)}"
    )
    assert dut.wready.value == 1, (
        f"SMOKE FAIL: wready at cycle 0 expected 1, "
        f"got {int(dut.wready.value)}"
    )
    assert dut.arready.value == 1, (
        f"SMOKE FAIL: arready at cycle 0 expected 1, "
        f"got {int(dut.arready.value)}"
    )
    assert dut.ctrl0_enable.value == 1, (
        f"SMOKE FAIL: ctrl0_enable at cycle 0 expected 1, "
        f"got {int(dut.ctrl0_enable.value)}"
    )
    assert dut.ctrl0_mode.value == 0, (
        f"SMOKE FAIL: ctrl0_mode at cycle 0 expected 0, "
        f"got {int(dut.ctrl0_mode.value)}"
    )
    assert dut.ctrl0_level.value == 0, (
        f"SMOKE FAIL: ctrl0_level at cycle 0 expected 0, "
        f"got {int(dut.ctrl0_level.value)}"
    )
    assert dut.irq0_flags.value == 0, (
        f"SMOKE FAIL: irq0_flags at cycle 0 expected 0, "
        f"got {int(dut.irq0_flags.value)}"
    )
    assert dut.cmd0_go.value == 0, (
        f"SMOKE FAIL: cmd0_go at cycle 0 expected 0, "
        f"got {int(dut.cmd0_go.value)}"
    )
    assert dut.cmd0_code.value == 0, (
        f"SMOKE FAIL: cmd0_code at cycle 0 expected 0, "
        f"got {int(dut.cmd0_code.value)}"
    )
    assert dut.scratch_value.value == 0, (
        f"SMOKE FAIL: scratch_value at cycle 0 expected 0, "
        f"got {int(dut.scratch_value.value)}"
    )
    await FallingEdge(dut.aclk)
    dut.awaddr.value = 0
    dut.awvalid.value = 1
    dut.bready.value = 1
    dut.wdata.value = 246
    dut.wstrb.value = 255
    dut.wvalid.value = 1
    await FallingEdge(dut.aclk)
    dut.awvalid.value = 0
    dut.wvalid.value = 0
    await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.bvalid.value == 1, (
        f"SMOKE FAIL: bvalid at cycle 3 expected 1, "
        f"got {int(dut.bvalid.value)}"
    )
    assert dut.bresp.value == 0, (
        f"SMOKE FAIL: bresp at cycle 3 expected 0, "
        f"got {int(dut.bresp.value)}"
    )
    assert dut.ctrl0_enable.value == 0, (
        f"SMOKE FAIL: ctrl0_enable at cycle 3 expected 0, "
        f"got {int(dut.ctrl0_enable.value)}"
    )
    assert dut.ctrl0_mode.value == 3, (
        f"SMOKE FAIL: ctrl0_mode at cycle 3 expected 3, "
        f"got {int(dut.ctrl0_mode.value)}"
    )
    assert dut.ctrl0_level.value == 15, (
        f"SMOKE FAIL: ctrl0_level at cycle 3 expected 15, "
        f"got {int(dut.ctrl0_level.value)}"
    )
    await FallingEdge(dut.aclk)
    dut.araddr.value = 0
    dut.arvalid.value = 1
    dut.rready.value = 1
    await Timer(1, units="ns")
    assert dut.bvalid.value == 0, (
        f"SMOKE FAIL: bvalid at cycle 4 expected 0, "
        f"got {int(dut.bvalid.value)}"
    )
    await FallingEdge(dut.aclk)
    dut.arvalid.value = 0
    await Timer(1, units="ns")
    assert dut.rvalid.value == 1, (
        f"SMOKE FAIL: rvalid at cycle 5 expected 1, "
        f"got {int(dut.rvalid.value)}"
    )
    assert dut.rdata.value == 246, (
        f"SMOKE FAIL: rdata at cycle 5 expected 246, "
        f"got {int(dut.rdata.value)}"
    )
    assert dut.rresp.value == 0, (
        f"SMOKE FAIL: rresp at cycle 5 expected 0, "
        f"got {int(dut.rresp.value)}"
    )
    await FallingEdge(dut.aclk)
    dut.araddr.value = 1
    dut.arvalid.value = 1
    dut.rready.value = 1
    await FallingEdge(dut.aclk)
    dut.arvalid.value = 0
    await Timer(1, units="ns")
    assert dut.rvalid.value == 1, (
        f"SMOKE FAIL: rvalid at cycle 7 expected 1, "
        f"got {int(dut.rvalid.value)}"
    )
    assert dut.rdata.value == 0, (
        f"SMOKE FAIL: rdata at cycle 7 expected 0, "
        f"got {int(dut.rdata.value)}"
    )
    assert dut.rresp.value == 2, (
        f"SMOKE FAIL: rresp at cycle 7 expected 2, "
        f"got {int(dut.rresp.value)}"
    )
    await FallingEdge(dut.aclk)
    dut.awaddr.value = 0
    dut.awvalid.value = 1
    dut.bready.value = 1
    dut.wdata.value = 8
    dut.wstrb.value = 255
    dut.wvalid.value = 1
    await FallingEdge(dut.aclk)
    dut.awvalid.value = 0
    dut.wvalid.value = 0
    await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.bvalid.value == 1, (
        f"SMOKE FAIL: bvalid at cycle 10 expected 1, "
        f"got {int(dut.bvalid.value)}"
    )
    assert dut.bresp.value == 2, (
        f"SMOKE FAIL: bresp at cycle 10 expected 2, "
        f"got {int(dut.bresp.value)}"
    )
    assert dut.ctrl0_enable.value == 0, (
        f"SMOKE FAIL: ctrl0_enable at cycle 10 expected 0, "
        f"got {int(dut.ctrl0_enable.value)}"
    )
    assert dut.ctrl0_mode.value == 3, (
        f"SMOKE FAIL: ctrl0_mode at cycle 10 expected 3, "
        f"got {int(dut.ctrl0_mode.value)}"
    )
    assert dut.ctrl0_level.value == 15, (
        f"SMOKE FAIL: ctrl0_level at cycle 10 expected 15, "
        f"got {int(dut.ctrl0_level.value)}"
    )
    await FallingEdge(dut.aclk)
    dut.irq0_flags_set.value = 15
    await Timer(1, units="ns")
    assert dut.bvalid.value == 0, (
        f"SMOKE FAIL: bvalid at cycle 11 expected 0, "
        f"got {int(dut.bvalid.value)}"
    )
    await FallingEdge(dut.aclk)
    dut.irq0_flags_set.value = 0
    await Timer(1, units="ns")
    assert dut.irq0_flags.value == 15, (
        f"SMOKE FAIL: irq0_flags at cycle 12 expected 15, "
        f"got {int(dut.irq0_flags.value)}"
    )
    await FallingEdge(dut.aclk)
    dut.awaddr.value = 16
    dut.awvalid.value = 1
    dut.bready.value = 1
    dut.wdata.value = 8
    dut.wstrb.value = 255
    dut.wvalid.value = 1
    await FallingEdge(dut.aclk)
    dut.awvalid.value = 0
    dut.wvalid.value = 0
    await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.bvalid.value == 1, (
        f"SMOKE FAIL: bvalid at cycle 15 expected 1, "
        f"got {int(dut.bvalid.value)}"
    )
    assert dut.bresp.value == 0, (
        f"SMOKE FAIL: bresp at cycle 15 expected 0, "
        f"got {int(dut.bresp.value)}"
    )
    assert dut.irq0_flags.value == 7, (
        f"SMOKE FAIL: irq0_flags at cycle 15 expected 7, "
        f"got {int(dut.irq0_flags.value)}"
    )
    await FallingEdge(dut.aclk)
    dut.araddr.value = 16
    dut.arvalid.value = 1
    dut.rready.value = 1
    await Timer(1, units="ns")
    assert dut.bvalid.value == 0, (
        f"SMOKE FAIL: bvalid at cycle 16 expected 0, "
        f"got {int(dut.bvalid.value)}"
    )
    await FallingEdge(dut.aclk)
    dut.arvalid.value = 0
    await Timer(1, units="ns")
    assert dut.rvalid.value == 1, (
        f"SMOKE FAIL: rvalid at cycle 17 expected 1, "
        f"got {int(dut.rvalid.value)}"
    )
    assert dut.rdata.value == 7, (
        f"SMOKE FAIL: rdata at cycle 17 expected 7, "
        f"got {int(dut.rdata.value)}"
    )
    assert dut.rresp.value == 0, (
        f"SMOKE FAIL: rresp at cycle 17 expected 0, "
        f"got {int(dut.rresp.value)}"
    )
    await FallingEdge(dut.aclk)
    dut.awaddr.value = 32
    dut.awvalid.value = 1
    dut.bready.value = 1
    dut.wdata.value = 11574711341044573863
    dut.wstrb.value = 255
    dut.wvalid.value = 1
    await FallingEdge(dut.aclk)
    dut.awvalid.value = 0
    dut.wvalid.value = 0
    await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.bvalid.value == 1, (
        f"SMOKE FAIL: bvalid at cycle 20 expected 1, "
        f"got {int(dut.bvalid.value)}"
    )
    assert dut.bresp.value == 0, (
        f"SMOKE FAIL: bresp at cycle 20 expected 0, "
        f"got {int(dut.bresp.value)}"
    )
    assert dut.scratch_value.value == 11574711341044573863, (
        f"SMOKE FAIL: scratch_value at cycle 20 expected 11574711341044573863, "
        f"got {int(dut.scratch_value.value)}"
    )
    await FallingEdge(dut.aclk)
    dut.awaddr.value = 32
    dut.awvalid.value = 1
    dut.bready.value = 1
    dut.wdata.value = 6872032732664977752
    dut.wstrb.value = 85
    dut.wvalid.value = 1
    await Timer(1, units="ns")
    assert dut.bvalid.value == 0, (
        f"SMOKE FAIL: bvalid at cycle 21 expected 0, "
        f"got {int(dut.bvalid.value)}"
    )
    await FallingEdge(dut.aclk)
    dut.awvalid.value = 0
    dut.wvalid.value = 0
    await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.bvalid.value == 1, (
        f"SMOKE FAIL: bvalid at cycle 23 expected 1, "
        f"got {int(dut.bvalid.value)}"
    )
    assert dut.bresp.value == 0, (
        f"SMOKE FAIL: bresp at cycle 23 expected 0, "
        f"got {int(dut.bresp.value)}"
    )
    assert dut.scratch_value.value == 11555852212657366616, (
        f"SMOKE FAIL: scratch_value at cycle 23 expected 11555852212657366616, "
        f"got {int(dut.scratch_value.value)}"
    )
    await FallingEdge(dut.aclk)
    dut.araddr.value = 32
    dut.arvalid.value = 1
    dut.rready.value = 1
    await Timer(1, units="ns")
    assert dut.bvalid.value == 0, (
        f"SMOKE FAIL: bvalid at cycle 24 expected 0, "
        f"got {int(dut.bvalid.value)}"
    )
    await FallingEdge(dut.aclk)
    dut.arvalid.value = 0
    await Timer(1, units="ns")
    assert dut.rvalid.value == 1, (
        f"SMOKE FAIL: rvalid at cycle 25 expected 1, "
        f"got {int(dut.rvalid.value)}"
    )
    assert dut.rdata.value == 11555852212657366616, (
        f"SMOKE FAIL: rdata at cycle 25 expected 11555852212657366616, "
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
    dut.status0_busy.value = 1
    dut.status0_code.value = 15
    await FallingEdge(dut.aclk)
    dut.arvalid.value = 0
    await Timer(1, units="ns")
    assert dut.rvalid.value == 1, (
        f"SMOKE FAIL: rvalid at cycle 27 expected 1, "
        f"got {int(dut.rvalid.value)}"
    )
    assert dut.rdata.value == 241, (
        f"SMOKE FAIL: rdata at cycle 27 expected 241, "
        f"got {int(dut.rdata.value)}"
    )
    assert dut.rresp.value == 0, (
        f"SMOKE FAIL: rresp at cycle 27 expected 0, "
        f"got {int(dut.rresp.value)}"
    )
    await FallingEdge(dut.aclk)
    dut.awaddr.value = 24
    dut.awvalid.value = 1
    dut.bready.value = 1
    dut.wdata.value = 15
    dut.wstrb.value = 255
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
    assert dut.cmd0_go.value == 1, (
        f"SMOKE FAIL: cmd0_go at cycle 30 expected 1, "
        f"got {int(dut.cmd0_go.value)}"
    )
    assert dut.cmd0_code.value == 7, (
        f"SMOKE FAIL: cmd0_code at cycle 30 expected 7, "
        f"got {int(dut.cmd0_code.value)}"
    )
    await FallingEdge(dut.aclk)
    dut.araddr.value = 24
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

    dut._log.info("SMOKE PASS: axil_regblock")
