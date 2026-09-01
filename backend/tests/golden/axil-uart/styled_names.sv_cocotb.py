# SemiCraft v0.4.0
# cocotb testbench for axil_uart (config hash: 46430409e63b)
# BETA: the SystemVerilog testbench is the supported default backend.
#
# Generated code is provided as-is, without warranty of any kind. Free for
# commercial and non-commercial use at the user's own risk.

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, RisingEdge, Timer


@cocotb.test(timeout_time=9680, timeout_unit="ns")
async def smoke(dut):
    """Directed smoke test for axil_uart (generated).

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
    dut.p_uartRx.value = 0
    dut.p_areset_n.value = 0
    for _ in range(2):
        await RisingEdge(dut.p_aclk)
    await Timer(1, units="ns")
    dut.p_areset_n.value = 1

    # Directed vectors; sample checks after a settle on the falling edge
    await FallingEdge(dut.p_aclk)
    dut.p_uartRx.value = 1
    await Timer(1, units="ns")
    assert dut.p_uartTx.value == 1, (
        f"SMOKE FAIL: p_uartTx at cycle 0 expected 1, "
        f"got {int(dut.p_uartTx.value)}"
    )
    assert dut.p_bvalid.value == 0, (
        f"SMOKE FAIL: p_bvalid at cycle 0 expected 0, "
        f"got {int(dut.p_bvalid.value)}"
    )
    assert dut.p_rvalid.value == 0, (
        f"SMOKE FAIL: p_rvalid at cycle 0 expected 0, "
        f"got {int(dut.p_rvalid.value)}"
    )
    await FallingEdge(dut.p_aclk)
    dut.p_araddr.value = 12
    dut.p_arvalid.value = 1
    dut.p_rready.value = 1
    await FallingEdge(dut.p_aclk)
    dut.p_arvalid.value = 0
    await Timer(1, units="ns")
    assert dut.p_rvalid.value == 1, (
        f"SMOKE FAIL: p_rvalid at cycle 2 expected 1, "
        f"got {int(dut.p_rvalid.value)}"
    )
    assert dut.p_rdata.value == 4, (
        f"SMOKE FAIL: p_rdata at cycle 2 expected 4, "
        f"got {int(dut.p_rdata.value)}"
    )
    assert dut.p_rresp.value == 0, (
        f"SMOKE FAIL: p_rresp at cycle 2 expected 0, "
        f"got {int(dut.p_rresp.value)}"
    )
    await FallingEdge(dut.p_aclk)
    dut.p_awaddr.value = 4
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
        f"SMOKE FAIL: p_bvalid at cycle 5 expected 1, "
        f"got {int(dut.p_bvalid.value)}"
    )
    assert dut.p_bresp.value == 0, (
        f"SMOKE FAIL: p_bresp at cycle 5 expected 0, "
        f"got {int(dut.p_bresp.value)}"
    )
    await FallingEdge(dut.p_aclk)
    dut.p_araddr.value = 0
    dut.p_arvalid.value = 1
    dut.p_rready.value = 1
    await Timer(1, units="ns")
    assert dut.p_bvalid.value == 0, (
        f"SMOKE FAIL: p_bvalid at cycle 6 expected 0, "
        f"got {int(dut.p_bvalid.value)}"
    )
    await FallingEdge(dut.p_aclk)
    dut.p_arvalid.value = 0
    await Timer(1, units="ns")
    assert dut.p_uartTx.value == 0, (
        f"SMOKE FAIL: p_uartTx at cycle 7 expected 0, "
        f"got {int(dut.p_uartTx.value)}"
    )
    assert dut.p_rvalid.value == 1, (
        f"SMOKE FAIL: p_rvalid at cycle 7 expected 1, "
        f"got {int(dut.p_rvalid.value)}"
    )
    assert dut.p_rdata.value == 1, (
        f"SMOKE FAIL: p_rdata at cycle 7 expected 1, "
        f"got {int(dut.p_rdata.value)}"
    )
    assert dut.p_rresp.value == 0, (
        f"SMOKE FAIL: p_rresp at cycle 7 expected 0, "
        f"got {int(dut.p_rresp.value)}"
    )
    for _ in range(4):
        await FallingEdge(dut.p_aclk)
    await Timer(1, units="ns")
    assert dut.p_uartTx.value == 1, (
        f"SMOKE FAIL: p_uartTx at cycle 11 expected 1, "
        f"got {int(dut.p_uartTx.value)}"
    )
    for _ in range(4):
        await FallingEdge(dut.p_aclk)
    await Timer(1, units="ns")
    assert dut.p_uartTx.value == 1, (
        f"SMOKE FAIL: p_uartTx at cycle 15 expected 1, "
        f"got {int(dut.p_uartTx.value)}"
    )
    for _ in range(4):
        await FallingEdge(dut.p_aclk)
    await Timer(1, units="ns")
    assert dut.p_uartTx.value == 0, (
        f"SMOKE FAIL: p_uartTx at cycle 19 expected 0, "
        f"got {int(dut.p_uartTx.value)}"
    )
    for _ in range(4):
        await FallingEdge(dut.p_aclk)
    await Timer(1, units="ns")
    assert dut.p_uartTx.value == 1, (
        f"SMOKE FAIL: p_uartTx at cycle 23 expected 1, "
        f"got {int(dut.p_uartTx.value)}"
    )
    for _ in range(4):
        await FallingEdge(dut.p_aclk)
    await Timer(1, units="ns")
    assert dut.p_uartTx.value == 0, (
        f"SMOKE FAIL: p_uartTx at cycle 27 expected 0, "
        f"got {int(dut.p_uartTx.value)}"
    )
    for _ in range(4):
        await FallingEdge(dut.p_aclk)
    await Timer(1, units="ns")
    assert dut.p_uartTx.value == 0, (
        f"SMOKE FAIL: p_uartTx at cycle 31 expected 0, "
        f"got {int(dut.p_uartTx.value)}"
    )
    for _ in range(4):
        await FallingEdge(dut.p_aclk)
    await Timer(1, units="ns")
    assert dut.p_uartTx.value == 1, (
        f"SMOKE FAIL: p_uartTx at cycle 35 expected 1, "
        f"got {int(dut.p_uartTx.value)}"
    )
    for _ in range(4):
        await FallingEdge(dut.p_aclk)
    await Timer(1, units="ns")
    assert dut.p_uartTx.value == 0, (
        f"SMOKE FAIL: p_uartTx at cycle 39 expected 0, "
        f"got {int(dut.p_uartTx.value)}"
    )
    for _ in range(4):
        await FallingEdge(dut.p_aclk)
    await Timer(1, units="ns")
    assert dut.p_uartTx.value == 1, (
        f"SMOKE FAIL: p_uartTx at cycle 43 expected 1, "
        f"got {int(dut.p_uartTx.value)}"
    )
    for _ in range(3):
        await FallingEdge(dut.p_aclk)
    dut.p_araddr.value = 0
    dut.p_arvalid.value = 1
    dut.p_rready.value = 1
    await Timer(1, units="ns")
    assert dut.p_uartTx.value == 1, (
        f"SMOKE FAIL: p_uartTx at cycle 46 expected 1, "
        f"got {int(dut.p_uartTx.value)}"
    )
    await FallingEdge(dut.p_aclk)
    dut.p_arvalid.value = 0
    await Timer(1, units="ns")
    assert dut.p_rvalid.value == 1, (
        f"SMOKE FAIL: p_rvalid at cycle 47 expected 1, "
        f"got {int(dut.p_rvalid.value)}"
    )
    assert dut.p_rdata.value == 0, (
        f"SMOKE FAIL: p_rdata at cycle 47 expected 0, "
        f"got {int(dut.p_rdata.value)}"
    )
    assert dut.p_rresp.value == 0, (
        f"SMOKE FAIL: p_rresp at cycle 47 expected 0, "
        f"got {int(dut.p_rresp.value)}"
    )
    await FallingEdge(dut.p_aclk)
    dut.p_uartRx.value = 0
    for _ in range(4):
        await FallingEdge(dut.p_aclk)
    dut.p_uartRx.value = 1
    for _ in range(4):
        await FallingEdge(dut.p_aclk)
    dut.p_uartRx.value = 0
    for _ in range(4):
        await FallingEdge(dut.p_aclk)
    dut.p_uartRx.value = 1
    for _ in range(4):
        await FallingEdge(dut.p_aclk)
    dut.p_uartRx.value = 1
    for _ in range(4):
        await FallingEdge(dut.p_aclk)
    dut.p_uartRx.value = 0
    for _ in range(4):
        await FallingEdge(dut.p_aclk)
    dut.p_uartRx.value = 1
    for _ in range(4):
        await FallingEdge(dut.p_aclk)
    dut.p_uartRx.value = 0
    for _ in range(4):
        await FallingEdge(dut.p_aclk)
    dut.p_uartRx.value = 0
    for _ in range(4):
        await FallingEdge(dut.p_aclk)
    dut.p_uartRx.value = 1
    for _ in range(10):
        await FallingEdge(dut.p_aclk)
    dut.p_araddr.value = 0
    dut.p_arvalid.value = 1
    dut.p_rready.value = 1
    await FallingEdge(dut.p_aclk)
    dut.p_arvalid.value = 0
    await Timer(1, units="ns")
    assert dut.p_rvalid.value == 1, (
        f"SMOKE FAIL: p_rvalid at cycle 95 expected 1, "
        f"got {int(dut.p_rvalid.value)}"
    )
    assert dut.p_rdata.value == 2, (
        f"SMOKE FAIL: p_rdata at cycle 95 expected 2, "
        f"got {int(dut.p_rdata.value)}"
    )
    assert dut.p_rresp.value == 0, (
        f"SMOKE FAIL: p_rresp at cycle 95 expected 0, "
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
        f"SMOKE FAIL: p_rvalid at cycle 97 expected 1, "
        f"got {int(dut.p_rvalid.value)}"
    )
    assert dut.p_rdata.value == 45, (
        f"SMOKE FAIL: p_rdata at cycle 97 expected 45, "
        f"got {int(dut.p_rdata.value)}"
    )
    assert dut.p_rresp.value == 0, (
        f"SMOKE FAIL: p_rresp at cycle 97 expected 0, "
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
        f"SMOKE FAIL: p_bvalid at cycle 100 expected 1, "
        f"got {int(dut.p_bvalid.value)}"
    )
    assert dut.p_bresp.value == 0, (
        f"SMOKE FAIL: p_bresp at cycle 100 expected 0, "
        f"got {int(dut.p_bresp.value)}"
    )
    await FallingEdge(dut.p_aclk)
    dut.p_araddr.value = 0
    dut.p_arvalid.value = 1
    dut.p_rready.value = 1
    await Timer(1, units="ns")
    assert dut.p_bvalid.value == 0, (
        f"SMOKE FAIL: p_bvalid at cycle 101 expected 0, "
        f"got {int(dut.p_bvalid.value)}"
    )
    await FallingEdge(dut.p_aclk)
    dut.p_arvalid.value = 0
    await Timer(1, units="ns")
    assert dut.p_rvalid.value == 1, (
        f"SMOKE FAIL: p_rvalid at cycle 102 expected 1, "
        f"got {int(dut.p_rvalid.value)}"
    )
    assert dut.p_rdata.value == 0, (
        f"SMOKE FAIL: p_rdata at cycle 102 expected 0, "
        f"got {int(dut.p_rdata.value)}"
    )
    assert dut.p_rresp.value == 0, (
        f"SMOKE FAIL: p_rresp at cycle 102 expected 0, "
        f"got {int(dut.p_rresp.value)}"
    )

    dut._log.info("SMOKE PASS: axil_uart")
