# SemiCraft v0.4.0
# cocotb testbench for axil_uart (config hash: 28a987250c5b)
# BETA: the SystemVerilog testbench is the supported default backend.
#
# Generated code is provided as-is, without warranty of any kind. Free for
# commercial and non-commercial use at the user's own risk.

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, RisingEdge, Timer


@cocotb.test(timeout_time=24080, timeout_unit="ns")
async def smoke(dut):
    """Directed smoke test for axil_uart (generated).

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
    dut.uart_rx.value = 0
    dut.areset_n.value = 0
    for _ in range(2):
        await RisingEdge(dut.aclk)
    await Timer(1, units="ns")
    dut.areset_n.value = 1

    # Directed vectors; sample checks after a settle on the falling edge
    await FallingEdge(dut.aclk)
    dut.uart_rx.value = 1
    await Timer(1, units="ns")
    assert dut.uart_tx.value == 1, (
        f"SMOKE FAIL: uart_tx at cycle 0 expected 1, "
        f"got {int(dut.uart_tx.value)}"
    )
    assert dut.bvalid.value == 0, (
        f"SMOKE FAIL: bvalid at cycle 0 expected 0, "
        f"got {int(dut.bvalid.value)}"
    )
    assert dut.rvalid.value == 0, (
        f"SMOKE FAIL: rvalid at cycle 0 expected 0, "
        f"got {int(dut.rvalid.value)}"
    )
    await FallingEdge(dut.aclk)
    dut.araddr.value = 12
    dut.arvalid.value = 1
    dut.rready.value = 1
    await FallingEdge(dut.aclk)
    dut.arvalid.value = 0
    await Timer(1, units="ns")
    assert dut.rvalid.value == 1, (
        f"SMOKE FAIL: rvalid at cycle 2 expected 1, "
        f"got {int(dut.rvalid.value)}"
    )
    assert dut.rdata.value == 13, (
        f"SMOKE FAIL: rdata at cycle 2 expected 13, "
        f"got {int(dut.rdata.value)}"
    )
    assert dut.rresp.value == 0, (
        f"SMOKE FAIL: rresp at cycle 2 expected 0, "
        f"got {int(dut.rresp.value)}"
    )
    await FallingEdge(dut.aclk)
    dut.awaddr.value = 4
    dut.awvalid.value = 1
    dut.bready.value = 1
    dut.wdata.value = 75
    dut.wstrb.value = 15
    dut.wvalid.value = 1
    await FallingEdge(dut.aclk)
    dut.awvalid.value = 0
    dut.wvalid.value = 0
    await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.bvalid.value == 1, (
        f"SMOKE FAIL: bvalid at cycle 5 expected 1, "
        f"got {int(dut.bvalid.value)}"
    )
    assert dut.bresp.value == 0, (
        f"SMOKE FAIL: bresp at cycle 5 expected 0, "
        f"got {int(dut.bresp.value)}"
    )
    await FallingEdge(dut.aclk)
    dut.araddr.value = 0
    dut.arvalid.value = 1
    dut.rready.value = 1
    await Timer(1, units="ns")
    assert dut.bvalid.value == 0, (
        f"SMOKE FAIL: bvalid at cycle 6 expected 0, "
        f"got {int(dut.bvalid.value)}"
    )
    await FallingEdge(dut.aclk)
    dut.arvalid.value = 0
    await Timer(1, units="ns")
    assert dut.uart_tx.value == 0, (
        f"SMOKE FAIL: uart_tx at cycle 7 expected 0, "
        f"got {int(dut.uart_tx.value)}"
    )
    assert dut.rvalid.value == 1, (
        f"SMOKE FAIL: rvalid at cycle 7 expected 1, "
        f"got {int(dut.rvalid.value)}"
    )
    assert dut.rdata.value == 1, (
        f"SMOKE FAIL: rdata at cycle 7 expected 1, "
        f"got {int(dut.rdata.value)}"
    )
    assert dut.rresp.value == 0, (
        f"SMOKE FAIL: rresp at cycle 7 expected 0, "
        f"got {int(dut.rresp.value)}"
    )
    for _ in range(13):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.uart_tx.value == 1, (
        f"SMOKE FAIL: uart_tx at cycle 20 expected 1, "
        f"got {int(dut.uart_tx.value)}"
    )
    for _ in range(13):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.uart_tx.value == 1, (
        f"SMOKE FAIL: uart_tx at cycle 33 expected 1, "
        f"got {int(dut.uart_tx.value)}"
    )
    for _ in range(13):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.uart_tx.value == 0, (
        f"SMOKE FAIL: uart_tx at cycle 46 expected 0, "
        f"got {int(dut.uart_tx.value)}"
    )
    for _ in range(13):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.uart_tx.value == 1, (
        f"SMOKE FAIL: uart_tx at cycle 59 expected 1, "
        f"got {int(dut.uart_tx.value)}"
    )
    for _ in range(13):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.uart_tx.value == 0, (
        f"SMOKE FAIL: uart_tx at cycle 72 expected 0, "
        f"got {int(dut.uart_tx.value)}"
    )
    for _ in range(13):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.uart_tx.value == 0, (
        f"SMOKE FAIL: uart_tx at cycle 85 expected 0, "
        f"got {int(dut.uart_tx.value)}"
    )
    for _ in range(13):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.uart_tx.value == 1, (
        f"SMOKE FAIL: uart_tx at cycle 98 expected 1, "
        f"got {int(dut.uart_tx.value)}"
    )
    for _ in range(13):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.uart_tx.value == 0, (
        f"SMOKE FAIL: uart_tx at cycle 111 expected 0, "
        f"got {int(dut.uart_tx.value)}"
    )
    for _ in range(13):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.uart_tx.value == 1, (
        f"SMOKE FAIL: uart_tx at cycle 124 expected 1, "
        f"got {int(dut.uart_tx.value)}"
    )
    for _ in range(12):
        await FallingEdge(dut.aclk)
    dut.araddr.value = 0
    dut.arvalid.value = 1
    dut.rready.value = 1
    await Timer(1, units="ns")
    assert dut.uart_tx.value == 1, (
        f"SMOKE FAIL: uart_tx at cycle 136 expected 1, "
        f"got {int(dut.uart_tx.value)}"
    )
    await FallingEdge(dut.aclk)
    dut.arvalid.value = 0
    await Timer(1, units="ns")
    assert dut.rvalid.value == 1, (
        f"SMOKE FAIL: rvalid at cycle 137 expected 1, "
        f"got {int(dut.rvalid.value)}"
    )
    assert dut.rdata.value == 0, (
        f"SMOKE FAIL: rdata at cycle 137 expected 0, "
        f"got {int(dut.rdata.value)}"
    )
    assert dut.rresp.value == 0, (
        f"SMOKE FAIL: rresp at cycle 137 expected 0, "
        f"got {int(dut.rresp.value)}"
    )
    await FallingEdge(dut.aclk)
    dut.uart_rx.value = 0
    for _ in range(13):
        await FallingEdge(dut.aclk)
    dut.uart_rx.value = 1
    for _ in range(13):
        await FallingEdge(dut.aclk)
    dut.uart_rx.value = 0
    for _ in range(13):
        await FallingEdge(dut.aclk)
    dut.uart_rx.value = 1
    for _ in range(13):
        await FallingEdge(dut.aclk)
    dut.uart_rx.value = 1
    for _ in range(13):
        await FallingEdge(dut.aclk)
    dut.uart_rx.value = 0
    for _ in range(13):
        await FallingEdge(dut.aclk)
    dut.uart_rx.value = 1
    for _ in range(13):
        await FallingEdge(dut.aclk)
    dut.uart_rx.value = 0
    for _ in range(13):
        await FallingEdge(dut.aclk)
    dut.uart_rx.value = 0
    for _ in range(13):
        await FallingEdge(dut.aclk)
    dut.uart_rx.value = 1
    for _ in range(19):
        await FallingEdge(dut.aclk)
    dut.araddr.value = 0
    dut.arvalid.value = 1
    dut.rready.value = 1
    await FallingEdge(dut.aclk)
    dut.arvalid.value = 0
    await Timer(1, units="ns")
    assert dut.rvalid.value == 1, (
        f"SMOKE FAIL: rvalid at cycle 275 expected 1, "
        f"got {int(dut.rvalid.value)}"
    )
    assert dut.rdata.value == 2, (
        f"SMOKE FAIL: rdata at cycle 275 expected 2, "
        f"got {int(dut.rdata.value)}"
    )
    assert dut.rresp.value == 0, (
        f"SMOKE FAIL: rresp at cycle 275 expected 0, "
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
        f"SMOKE FAIL: rvalid at cycle 277 expected 1, "
        f"got {int(dut.rvalid.value)}"
    )
    assert dut.rdata.value == 45, (
        f"SMOKE FAIL: rdata at cycle 277 expected 45, "
        f"got {int(dut.rdata.value)}"
    )
    assert dut.rresp.value == 0, (
        f"SMOKE FAIL: rresp at cycle 277 expected 0, "
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
        f"SMOKE FAIL: bvalid at cycle 280 expected 1, "
        f"got {int(dut.bvalid.value)}"
    )
    assert dut.bresp.value == 0, (
        f"SMOKE FAIL: bresp at cycle 280 expected 0, "
        f"got {int(dut.bresp.value)}"
    )
    await FallingEdge(dut.aclk)
    dut.araddr.value = 0
    dut.arvalid.value = 1
    dut.rready.value = 1
    await Timer(1, units="ns")
    assert dut.bvalid.value == 0, (
        f"SMOKE FAIL: bvalid at cycle 281 expected 0, "
        f"got {int(dut.bvalid.value)}"
    )
    await FallingEdge(dut.aclk)
    dut.arvalid.value = 0
    await Timer(1, units="ns")
    assert dut.rvalid.value == 1, (
        f"SMOKE FAIL: rvalid at cycle 282 expected 1, "
        f"got {int(dut.rvalid.value)}"
    )
    assert dut.rdata.value == 0, (
        f"SMOKE FAIL: rdata at cycle 282 expected 0, "
        f"got {int(dut.rdata.value)}"
    )
    assert dut.rresp.value == 0, (
        f"SMOKE FAIL: rresp at cycle 282 expected 0, "
        f"got {int(dut.rresp.value)}"
    )

    dut._log.info("SMOKE PASS: axil_uart")
