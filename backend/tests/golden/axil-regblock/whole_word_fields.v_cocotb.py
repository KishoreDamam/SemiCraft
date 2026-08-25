# SemiCraft v0.3.0
# cocotb testbench for axil_regblock (config hash: 763ad261e462)
# BETA: the SystemVerilog testbench is the supported default backend.
#
# Generated code is provided as-is, without warranty of any kind. Free for
# commercial and non-commercial use at the user's own risk.

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, RisingEdge, Timer


@cocotb.test(timeout_time=3840, timeout_unit="ns")
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
    dut.status0_value.value = 0
    dut.irq0_value_set.value = 0
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
    assert dut.ctrl0_value.value == 0, (
        f"SMOKE FAIL: ctrl0_value at cycle 0 expected 0, "
        f"got {int(dut.ctrl0_value.value)}"
    )
    assert dut.irq0_value.value == 0, (
        f"SMOKE FAIL: irq0_value at cycle 0 expected 0, "
        f"got {int(dut.irq0_value.value)}"
    )
    assert dut.cmd0_value.value == 0, (
        f"SMOKE FAIL: cmd0_value at cycle 0 expected 0, "
        f"got {int(dut.cmd0_value.value)}"
    )
    assert dut.scratch_value.value == 0, (
        f"SMOKE FAIL: scratch_value at cycle 0 expected 0, "
        f"got {int(dut.scratch_value.value)}"
    )
    await FallingEdge(dut.aclk)
    dut.awaddr.value = 0
    dut.awvalid.value = 1
    dut.bready.value = 1
    dut.wdata.value = 4294967295
    dut.wstrb.value = 15
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
    assert dut.ctrl0_value.value == 4294967295, (
        f"SMOKE FAIL: ctrl0_value at cycle 3 expected 4294967295, "
        f"got {int(dut.ctrl0_value.value)}"
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
    assert dut.rdata.value == 4294967295, (
        f"SMOKE FAIL: rdata at cycle 5 expected 4294967295, "
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
    dut.irq0_value_set.value = 4294967295
    await FallingEdge(dut.aclk)
    dut.irq0_value_set.value = 0
    await Timer(1, units="ns")
    assert dut.irq0_value.value == 4294967295, (
        f"SMOKE FAIL: irq0_value at cycle 9 expected 4294967295, "
        f"got {int(dut.irq0_value.value)}"
    )
    await FallingEdge(dut.aclk)
    dut.awaddr.value = 8
    dut.awvalid.value = 1
    dut.bready.value = 1
    dut.wdata.value = 2147483648
    dut.wstrb.value = 15
    dut.wvalid.value = 1
    await FallingEdge(dut.aclk)
    dut.awvalid.value = 0
    dut.wvalid.value = 0
    await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.bvalid.value == 1, (
        f"SMOKE FAIL: bvalid at cycle 12 expected 1, "
        f"got {int(dut.bvalid.value)}"
    )
    assert dut.bresp.value == 0, (
        f"SMOKE FAIL: bresp at cycle 12 expected 0, "
        f"got {int(dut.bresp.value)}"
    )
    assert dut.irq0_value.value == 2147483647, (
        f"SMOKE FAIL: irq0_value at cycle 12 expected 2147483647, "
        f"got {int(dut.irq0_value.value)}"
    )
    await FallingEdge(dut.aclk)
    dut.araddr.value = 8
    dut.arvalid.value = 1
    dut.rready.value = 1
    await Timer(1, units="ns")
    assert dut.bvalid.value == 0, (
        f"SMOKE FAIL: bvalid at cycle 13 expected 0, "
        f"got {int(dut.bvalid.value)}"
    )
    await FallingEdge(dut.aclk)
    dut.arvalid.value = 0
    await Timer(1, units="ns")
    assert dut.rvalid.value == 1, (
        f"SMOKE FAIL: rvalid at cycle 14 expected 1, "
        f"got {int(dut.rvalid.value)}"
    )
    assert dut.rdata.value == 2147483647, (
        f"SMOKE FAIL: rdata at cycle 14 expected 2147483647, "
        f"got {int(dut.rdata.value)}"
    )
    assert dut.rresp.value == 0, (
        f"SMOKE FAIL: rresp at cycle 14 expected 0, "
        f"got {int(dut.rresp.value)}"
    )
    await FallingEdge(dut.aclk)
    dut.awaddr.value = 16
    dut.awvalid.value = 1
    dut.bready.value = 1
    dut.wdata.value = 2694947491
    dut.wstrb.value = 15
    dut.wvalid.value = 1
    await FallingEdge(dut.aclk)
    dut.awvalid.value = 0
    dut.wvalid.value = 0
    await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.bvalid.value == 1, (
        f"SMOKE FAIL: bvalid at cycle 17 expected 1, "
        f"got {int(dut.bvalid.value)}"
    )
    assert dut.bresp.value == 0, (
        f"SMOKE FAIL: bresp at cycle 17 expected 0, "
        f"got {int(dut.bresp.value)}"
    )
    assert dut.scratch_value.value == 2694947491, (
        f"SMOKE FAIL: scratch_value at cycle 17 expected 2694947491, "
        f"got {int(dut.scratch_value.value)}"
    )
    await FallingEdge(dut.aclk)
    dut.awaddr.value = 16
    dut.awvalid.value = 1
    dut.bready.value = 1
    dut.wdata.value = 1600019804
    dut.wstrb.value = 5
    dut.wvalid.value = 1
    await Timer(1, units="ns")
    assert dut.bvalid.value == 0, (
        f"SMOKE FAIL: bvalid at cycle 18 expected 0, "
        f"got {int(dut.bvalid.value)}"
    )
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
    assert dut.scratch_value.value == 2690556508, (
        f"SMOKE FAIL: scratch_value at cycle 20 expected 2690556508, "
        f"got {int(dut.scratch_value.value)}"
    )
    await FallingEdge(dut.aclk)
    dut.araddr.value = 16
    dut.arvalid.value = 1
    dut.rready.value = 1
    await Timer(1, units="ns")
    assert dut.bvalid.value == 0, (
        f"SMOKE FAIL: bvalid at cycle 21 expected 0, "
        f"got {int(dut.bvalid.value)}"
    )
    await FallingEdge(dut.aclk)
    dut.arvalid.value = 0
    await Timer(1, units="ns")
    assert dut.rvalid.value == 1, (
        f"SMOKE FAIL: rvalid at cycle 22 expected 1, "
        f"got {int(dut.rvalid.value)}"
    )
    assert dut.rdata.value == 2690556508, (
        f"SMOKE FAIL: rdata at cycle 22 expected 2690556508, "
        f"got {int(dut.rdata.value)}"
    )
    assert dut.rresp.value == 0, (
        f"SMOKE FAIL: rresp at cycle 22 expected 0, "
        f"got {int(dut.rresp.value)}"
    )
    await FallingEdge(dut.aclk)
    dut.araddr.value = 4
    dut.arvalid.value = 1
    dut.rready.value = 1
    dut.status0_value.value = 4294967295
    await FallingEdge(dut.aclk)
    dut.arvalid.value = 0
    await Timer(1, units="ns")
    assert dut.rvalid.value == 1, (
        f"SMOKE FAIL: rvalid at cycle 24 expected 1, "
        f"got {int(dut.rvalid.value)}"
    )
    assert dut.rdata.value == 4294967295, (
        f"SMOKE FAIL: rdata at cycle 24 expected 4294967295, "
        f"got {int(dut.rdata.value)}"
    )
    assert dut.rresp.value == 0, (
        f"SMOKE FAIL: rresp at cycle 24 expected 0, "
        f"got {int(dut.rresp.value)}"
    )
    await FallingEdge(dut.aclk)
    dut.awaddr.value = 12
    dut.awvalid.value = 1
    dut.bready.value = 1
    dut.wdata.value = 4294967295
    dut.wstrb.value = 15
    dut.wvalid.value = 1
    await FallingEdge(dut.aclk)
    dut.awvalid.value = 0
    dut.wvalid.value = 0
    await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.bvalid.value == 1, (
        f"SMOKE FAIL: bvalid at cycle 27 expected 1, "
        f"got {int(dut.bvalid.value)}"
    )
    assert dut.bresp.value == 0, (
        f"SMOKE FAIL: bresp at cycle 27 expected 0, "
        f"got {int(dut.bresp.value)}"
    )
    assert dut.cmd0_value.value == 4294967295, (
        f"SMOKE FAIL: cmd0_value at cycle 27 expected 4294967295, "
        f"got {int(dut.cmd0_value.value)}"
    )
    await FallingEdge(dut.aclk)
    dut.araddr.value = 12
    dut.arvalid.value = 1
    dut.rready.value = 1
    await Timer(1, units="ns")
    assert dut.bvalid.value == 0, (
        f"SMOKE FAIL: bvalid at cycle 28 expected 0, "
        f"got {int(dut.bvalid.value)}"
    )
    await FallingEdge(dut.aclk)
    dut.arvalid.value = 0
    await Timer(1, units="ns")
    assert dut.rvalid.value == 1, (
        f"SMOKE FAIL: rvalid at cycle 29 expected 1, "
        f"got {int(dut.rvalid.value)}"
    )
    assert dut.rdata.value == 0, (
        f"SMOKE FAIL: rdata at cycle 29 expected 0, "
        f"got {int(dut.rdata.value)}"
    )
    assert dut.rresp.value == 0, (
        f"SMOKE FAIL: rresp at cycle 29 expected 0, "
        f"got {int(dut.rresp.value)}"
    )

    dut._log.info("SMOKE PASS: axil_regblock")
