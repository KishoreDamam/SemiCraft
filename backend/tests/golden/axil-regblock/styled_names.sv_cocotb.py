# SemiCraft v0.4.0
# cocotb testbench for axil_regblock (config hash: 9e0a82cbd583)
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
    dut.p_status0Busy.value = 0
    dut.p_status0Code.value = 0
    dut.p_irq0FlagsSet.value = 0
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
    assert dut.p_wready.value == 1, (
        f"SMOKE FAIL: p_wready at cycle 0 expected 1, "
        f"got {int(dut.p_wready.value)}"
    )
    assert dut.p_arready.value == 1, (
        f"SMOKE FAIL: p_arready at cycle 0 expected 1, "
        f"got {int(dut.p_arready.value)}"
    )
    assert dut.p_ctrl0Enable.value == 1, (
        f"SMOKE FAIL: p_ctrl0Enable at cycle 0 expected 1, "
        f"got {int(dut.p_ctrl0Enable.value)}"
    )
    assert dut.p_ctrl0Mode.value == 0, (
        f"SMOKE FAIL: p_ctrl0Mode at cycle 0 expected 0, "
        f"got {int(dut.p_ctrl0Mode.value)}"
    )
    assert dut.p_ctrl0Level.value == 0, (
        f"SMOKE FAIL: p_ctrl0Level at cycle 0 expected 0, "
        f"got {int(dut.p_ctrl0Level.value)}"
    )
    assert dut.p_irq0Flags.value == 0, (
        f"SMOKE FAIL: p_irq0Flags at cycle 0 expected 0, "
        f"got {int(dut.p_irq0Flags.value)}"
    )
    assert dut.p_cmd0Go.value == 0, (
        f"SMOKE FAIL: p_cmd0Go at cycle 0 expected 0, "
        f"got {int(dut.p_cmd0Go.value)}"
    )
    assert dut.p_cmd0Code.value == 0, (
        f"SMOKE FAIL: p_cmd0Code at cycle 0 expected 0, "
        f"got {int(dut.p_cmd0Code.value)}"
    )
    assert dut.p_scratchValue.value == 0, (
        f"SMOKE FAIL: p_scratchValue at cycle 0 expected 0, "
        f"got {int(dut.p_scratchValue.value)}"
    )
    await FallingEdge(dut.p_aclk)
    dut.p_awaddr.value = 0
    dut.p_awvalid.value = 1
    dut.p_bready.value = 1
    dut.p_wdata.value = 246
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
    assert dut.p_ctrl0Enable.value == 0, (
        f"SMOKE FAIL: p_ctrl0Enable at cycle 3 expected 0, "
        f"got {int(dut.p_ctrl0Enable.value)}"
    )
    assert dut.p_ctrl0Mode.value == 3, (
        f"SMOKE FAIL: p_ctrl0Mode at cycle 3 expected 3, "
        f"got {int(dut.p_ctrl0Mode.value)}"
    )
    assert dut.p_ctrl0Level.value == 15, (
        f"SMOKE FAIL: p_ctrl0Level at cycle 3 expected 15, "
        f"got {int(dut.p_ctrl0Level.value)}"
    )
    await FallingEdge(dut.p_aclk)
    dut.p_araddr.value = 0
    dut.p_arvalid.value = 1
    dut.p_rready.value = 1
    await Timer(1, units="ns")
    assert dut.p_bvalid.value == 0, (
        f"SMOKE FAIL: p_bvalid at cycle 4 expected 0, "
        f"got {int(dut.p_bvalid.value)}"
    )
    await FallingEdge(dut.p_aclk)
    dut.p_arvalid.value = 0
    await Timer(1, units="ns")
    assert dut.p_rvalid.value == 1, (
        f"SMOKE FAIL: p_rvalid at cycle 5 expected 1, "
        f"got {int(dut.p_rvalid.value)}"
    )
    assert dut.p_rdata.value == 246, (
        f"SMOKE FAIL: p_rdata at cycle 5 expected 246, "
        f"got {int(dut.p_rdata.value)}"
    )
    assert dut.p_rresp.value == 0, (
        f"SMOKE FAIL: p_rresp at cycle 5 expected 0, "
        f"got {int(dut.p_rresp.value)}"
    )
    await FallingEdge(dut.p_aclk)
    dut.p_araddr.value = 1
    dut.p_arvalid.value = 1
    dut.p_rready.value = 1
    await FallingEdge(dut.p_aclk)
    dut.p_arvalid.value = 0
    await Timer(1, units="ns")
    assert dut.p_rvalid.value == 1, (
        f"SMOKE FAIL: p_rvalid at cycle 7 expected 1, "
        f"got {int(dut.p_rvalid.value)}"
    )
    assert dut.p_rdata.value == 0, (
        f"SMOKE FAIL: p_rdata at cycle 7 expected 0, "
        f"got {int(dut.p_rdata.value)}"
    )
    assert dut.p_rresp.value == 2, (
        f"SMOKE FAIL: p_rresp at cycle 7 expected 2, "
        f"got {int(dut.p_rresp.value)}"
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
        f"SMOKE FAIL: p_bvalid at cycle 10 expected 1, "
        f"got {int(dut.p_bvalid.value)}"
    )
    assert dut.p_bresp.value == 2, (
        f"SMOKE FAIL: p_bresp at cycle 10 expected 2, "
        f"got {int(dut.p_bresp.value)}"
    )
    assert dut.p_ctrl0Enable.value == 0, (
        f"SMOKE FAIL: p_ctrl0Enable at cycle 10 expected 0, "
        f"got {int(dut.p_ctrl0Enable.value)}"
    )
    assert dut.p_ctrl0Mode.value == 3, (
        f"SMOKE FAIL: p_ctrl0Mode at cycle 10 expected 3, "
        f"got {int(dut.p_ctrl0Mode.value)}"
    )
    assert dut.p_ctrl0Level.value == 15, (
        f"SMOKE FAIL: p_ctrl0Level at cycle 10 expected 15, "
        f"got {int(dut.p_ctrl0Level.value)}"
    )
    await FallingEdge(dut.p_aclk)
    dut.p_irq0FlagsSet.value = 15
    await Timer(1, units="ns")
    assert dut.p_bvalid.value == 0, (
        f"SMOKE FAIL: p_bvalid at cycle 11 expected 0, "
        f"got {int(dut.p_bvalid.value)}"
    )
    await FallingEdge(dut.p_aclk)
    dut.p_irq0FlagsSet.value = 0
    await Timer(1, units="ns")
    assert dut.p_irq0Flags.value == 15, (
        f"SMOKE FAIL: p_irq0Flags at cycle 12 expected 15, "
        f"got {int(dut.p_irq0Flags.value)}"
    )
    await FallingEdge(dut.p_aclk)
    dut.p_awaddr.value = 8
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
        f"SMOKE FAIL: p_bvalid at cycle 15 expected 1, "
        f"got {int(dut.p_bvalid.value)}"
    )
    assert dut.p_bresp.value == 0, (
        f"SMOKE FAIL: p_bresp at cycle 15 expected 0, "
        f"got {int(dut.p_bresp.value)}"
    )
    assert dut.p_irq0Flags.value == 7, (
        f"SMOKE FAIL: p_irq0Flags at cycle 15 expected 7, "
        f"got {int(dut.p_irq0Flags.value)}"
    )
    await FallingEdge(dut.p_aclk)
    dut.p_araddr.value = 8
    dut.p_arvalid.value = 1
    dut.p_rready.value = 1
    await Timer(1, units="ns")
    assert dut.p_bvalid.value == 0, (
        f"SMOKE FAIL: p_bvalid at cycle 16 expected 0, "
        f"got {int(dut.p_bvalid.value)}"
    )
    await FallingEdge(dut.p_aclk)
    dut.p_arvalid.value = 0
    await Timer(1, units="ns")
    assert dut.p_rvalid.value == 1, (
        f"SMOKE FAIL: p_rvalid at cycle 17 expected 1, "
        f"got {int(dut.p_rvalid.value)}"
    )
    assert dut.p_rdata.value == 7, (
        f"SMOKE FAIL: p_rdata at cycle 17 expected 7, "
        f"got {int(dut.p_rdata.value)}"
    )
    assert dut.p_rresp.value == 0, (
        f"SMOKE FAIL: p_rresp at cycle 17 expected 0, "
        f"got {int(dut.p_rresp.value)}"
    )
    await FallingEdge(dut.p_aclk)
    dut.p_awaddr.value = 16
    dut.p_awvalid.value = 1
    dut.p_bready.value = 1
    dut.p_wdata.value = 2694947491
    dut.p_wstrb.value = 15
    dut.p_wvalid.value = 1
    await FallingEdge(dut.p_aclk)
    dut.p_awvalid.value = 0
    dut.p_wvalid.value = 0
    await FallingEdge(dut.p_aclk)
    await Timer(1, units="ns")
    assert dut.p_bvalid.value == 1, (
        f"SMOKE FAIL: p_bvalid at cycle 20 expected 1, "
        f"got {int(dut.p_bvalid.value)}"
    )
    assert dut.p_bresp.value == 0, (
        f"SMOKE FAIL: p_bresp at cycle 20 expected 0, "
        f"got {int(dut.p_bresp.value)}"
    )
    assert dut.p_scratchValue.value == 2694947491, (
        f"SMOKE FAIL: p_scratchValue at cycle 20 expected 2694947491, "
        f"got {int(dut.p_scratchValue.value)}"
    )
    await FallingEdge(dut.p_aclk)
    dut.p_awaddr.value = 16
    dut.p_awvalid.value = 1
    dut.p_bready.value = 1
    dut.p_wdata.value = 1600019804
    dut.p_wstrb.value = 5
    dut.p_wvalid.value = 1
    await Timer(1, units="ns")
    assert dut.p_bvalid.value == 0, (
        f"SMOKE FAIL: p_bvalid at cycle 21 expected 0, "
        f"got {int(dut.p_bvalid.value)}"
    )
    await FallingEdge(dut.p_aclk)
    dut.p_awvalid.value = 0
    dut.p_wvalid.value = 0
    await FallingEdge(dut.p_aclk)
    await Timer(1, units="ns")
    assert dut.p_bvalid.value == 1, (
        f"SMOKE FAIL: p_bvalid at cycle 23 expected 1, "
        f"got {int(dut.p_bvalid.value)}"
    )
    assert dut.p_bresp.value == 0, (
        f"SMOKE FAIL: p_bresp at cycle 23 expected 0, "
        f"got {int(dut.p_bresp.value)}"
    )
    assert dut.p_scratchValue.value == 2690556508, (
        f"SMOKE FAIL: p_scratchValue at cycle 23 expected 2690556508, "
        f"got {int(dut.p_scratchValue.value)}"
    )
    await FallingEdge(dut.p_aclk)
    dut.p_araddr.value = 16
    dut.p_arvalid.value = 1
    dut.p_rready.value = 1
    await Timer(1, units="ns")
    assert dut.p_bvalid.value == 0, (
        f"SMOKE FAIL: p_bvalid at cycle 24 expected 0, "
        f"got {int(dut.p_bvalid.value)}"
    )
    await FallingEdge(dut.p_aclk)
    dut.p_arvalid.value = 0
    await Timer(1, units="ns")
    assert dut.p_rvalid.value == 1, (
        f"SMOKE FAIL: p_rvalid at cycle 25 expected 1, "
        f"got {int(dut.p_rvalid.value)}"
    )
    assert dut.p_rdata.value == 2690556508, (
        f"SMOKE FAIL: p_rdata at cycle 25 expected 2690556508, "
        f"got {int(dut.p_rdata.value)}"
    )
    assert dut.p_rresp.value == 0, (
        f"SMOKE FAIL: p_rresp at cycle 25 expected 0, "
        f"got {int(dut.p_rresp.value)}"
    )
    await FallingEdge(dut.p_aclk)
    dut.p_araddr.value = 4
    dut.p_arvalid.value = 1
    dut.p_rready.value = 1
    dut.p_status0Busy.value = 1
    dut.p_status0Code.value = 15
    await FallingEdge(dut.p_aclk)
    dut.p_arvalid.value = 0
    await Timer(1, units="ns")
    assert dut.p_rvalid.value == 1, (
        f"SMOKE FAIL: p_rvalid at cycle 27 expected 1, "
        f"got {int(dut.p_rvalid.value)}"
    )
    assert dut.p_rdata.value == 241, (
        f"SMOKE FAIL: p_rdata at cycle 27 expected 241, "
        f"got {int(dut.p_rdata.value)}"
    )
    assert dut.p_rresp.value == 0, (
        f"SMOKE FAIL: p_rresp at cycle 27 expected 0, "
        f"got {int(dut.p_rresp.value)}"
    )
    await FallingEdge(dut.p_aclk)
    dut.p_awaddr.value = 12
    dut.p_awvalid.value = 1
    dut.p_bready.value = 1
    dut.p_wdata.value = 15
    dut.p_wstrb.value = 15
    dut.p_wvalid.value = 1
    await FallingEdge(dut.p_aclk)
    dut.p_awvalid.value = 0
    dut.p_wvalid.value = 0
    await FallingEdge(dut.p_aclk)
    await Timer(1, units="ns")
    assert dut.p_bvalid.value == 1, (
        f"SMOKE FAIL: p_bvalid at cycle 30 expected 1, "
        f"got {int(dut.p_bvalid.value)}"
    )
    assert dut.p_bresp.value == 0, (
        f"SMOKE FAIL: p_bresp at cycle 30 expected 0, "
        f"got {int(dut.p_bresp.value)}"
    )
    assert dut.p_cmd0Go.value == 1, (
        f"SMOKE FAIL: p_cmd0Go at cycle 30 expected 1, "
        f"got {int(dut.p_cmd0Go.value)}"
    )
    assert dut.p_cmd0Code.value == 7, (
        f"SMOKE FAIL: p_cmd0Code at cycle 30 expected 7, "
        f"got {int(dut.p_cmd0Code.value)}"
    )
    await FallingEdge(dut.p_aclk)
    dut.p_araddr.value = 12
    dut.p_arvalid.value = 1
    dut.p_rready.value = 1
    await Timer(1, units="ns")
    assert dut.p_bvalid.value == 0, (
        f"SMOKE FAIL: p_bvalid at cycle 31 expected 0, "
        f"got {int(dut.p_bvalid.value)}"
    )
    await FallingEdge(dut.p_aclk)
    dut.p_arvalid.value = 0
    await Timer(1, units="ns")
    assert dut.p_rvalid.value == 1, (
        f"SMOKE FAIL: p_rvalid at cycle 32 expected 1, "
        f"got {int(dut.p_rvalid.value)}"
    )
    assert dut.p_rdata.value == 0, (
        f"SMOKE FAIL: p_rdata at cycle 32 expected 0, "
        f"got {int(dut.p_rdata.value)}"
    )
    assert dut.p_rresp.value == 0, (
        f"SMOKE FAIL: p_rresp at cycle 32 expected 0, "
        f"got {int(dut.p_rresp.value)}"
    )

    dut._log.info("SMOKE PASS: axil_regblock")
