# SemiCraft v0.3.0
# cocotb testbench for axil_uart (config hash: bc1dcff66931)
# BETA: the SystemVerilog testbench is the supported default backend.
#
# Generated code is provided as-is, without warranty of any kind. Free for
# commercial and non-commercial use at the user's own risk.

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, RisingEdge, Timer


@cocotb.test(timeout_time=6480, timeout_unit="ns")
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
    assert dut.rdata.value == 2, (
        f"SMOKE FAIL: rdata at cycle 2 expected 2, "
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
    for _ in range(2):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.uart_tx.value == 1, (
        f"SMOKE FAIL: uart_tx at cycle 9 expected 1, "
        f"got {int(dut.uart_tx.value)}"
    )
    for _ in range(2):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.uart_tx.value == 1, (
        f"SMOKE FAIL: uart_tx at cycle 11 expected 1, "
        f"got {int(dut.uart_tx.value)}"
    )
    for _ in range(2):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.uart_tx.value == 0, (
        f"SMOKE FAIL: uart_tx at cycle 13 expected 0, "
        f"got {int(dut.uart_tx.value)}"
    )
    for _ in range(2):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.uart_tx.value == 1, (
        f"SMOKE FAIL: uart_tx at cycle 15 expected 1, "
        f"got {int(dut.uart_tx.value)}"
    )
    for _ in range(2):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.uart_tx.value == 0, (
        f"SMOKE FAIL: uart_tx at cycle 17 expected 0, "
        f"got {int(dut.uart_tx.value)}"
    )
    for _ in range(2):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.uart_tx.value == 0, (
        f"SMOKE FAIL: uart_tx at cycle 19 expected 0, "
        f"got {int(dut.uart_tx.value)}"
    )
    for _ in range(2):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.uart_tx.value == 1, (
        f"SMOKE FAIL: uart_tx at cycle 21 expected 1, "
        f"got {int(dut.uart_tx.value)}"
    )
    for _ in range(2):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.uart_tx.value == 0, (
        f"SMOKE FAIL: uart_tx at cycle 23 expected 0, "
        f"got {int(dut.uart_tx.value)}"
    )
    for _ in range(2):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.uart_tx.value == 1, (
        f"SMOKE FAIL: uart_tx at cycle 25 expected 1, "
        f"got {int(dut.uart_tx.value)}"
    )
    await FallingEdge(dut.aclk)
    dut.araddr.value = 0
    dut.arvalid.value = 1
    dut.rready.value = 1
    await Timer(1, units="ns")
    assert dut.uart_tx.value == 1, (
        f"SMOKE FAIL: uart_tx at cycle 26 expected 1, "
        f"got {int(dut.uart_tx.value)}"
    )
    await FallingEdge(dut.aclk)
    dut.arvalid.value = 0
    await Timer(1, units="ns")
    assert dut.rvalid.value == 1, (
        f"SMOKE FAIL: rvalid at cycle 27 expected 1, "
        f"got {int(dut.rvalid.value)}"
    )
    assert dut.rdata.value == 0, (
        f"SMOKE FAIL: rdata at cycle 27 expected 0, "
        f"got {int(dut.rdata.value)}"
    )
    assert dut.rresp.value == 0, (
        f"SMOKE FAIL: rresp at cycle 27 expected 0, "
        f"got {int(dut.rresp.value)}"
    )
    await FallingEdge(dut.aclk)
    dut.uart_rx.value = 0
    for _ in range(2):
        await FallingEdge(dut.aclk)
    dut.uart_rx.value = 1
    for _ in range(2):
        await FallingEdge(dut.aclk)
    dut.uart_rx.value = 0
    for _ in range(2):
        await FallingEdge(dut.aclk)
    dut.uart_rx.value = 1
    for _ in range(2):
        await FallingEdge(dut.aclk)
    dut.uart_rx.value = 1
    for _ in range(2):
        await FallingEdge(dut.aclk)
    dut.uart_rx.value = 0
    for _ in range(2):
        await FallingEdge(dut.aclk)
    dut.uart_rx.value = 1
    for _ in range(2):
        await FallingEdge(dut.aclk)
    dut.uart_rx.value = 0
    for _ in range(2):
        await FallingEdge(dut.aclk)
    dut.uart_rx.value = 0
    for _ in range(2):
        await FallingEdge(dut.aclk)
    dut.uart_rx.value = 1
    for _ in range(8):
        await FallingEdge(dut.aclk)
    dut.araddr.value = 0
    dut.arvalid.value = 1
    dut.rready.value = 1
    await FallingEdge(dut.aclk)
    dut.arvalid.value = 0
    await Timer(1, units="ns")
    assert dut.rvalid.value == 1, (
        f"SMOKE FAIL: rvalid at cycle 55 expected 1, "
        f"got {int(dut.rvalid.value)}"
    )
    assert dut.rdata.value == 2, (
        f"SMOKE FAIL: rdata at cycle 55 expected 2, "
        f"got {int(dut.rdata.value)}"
    )
    assert dut.rresp.value == 0, (
        f"SMOKE FAIL: rresp at cycle 55 expected 0, "
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
        f"SMOKE FAIL: rvalid at cycle 57 expected 1, "
        f"got {int(dut.rvalid.value)}"
    )
    assert dut.rdata.value == 45, (
        f"SMOKE FAIL: rdata at cycle 57 expected 45, "
        f"got {int(dut.rdata.value)}"
    )
    assert dut.rresp.value == 0, (
        f"SMOKE FAIL: rresp at cycle 57 expected 0, "
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
        f"SMOKE FAIL: bvalid at cycle 60 expected 1, "
        f"got {int(dut.bvalid.value)}"
    )
    assert dut.bresp.value == 0, (
        f"SMOKE FAIL: bresp at cycle 60 expected 0, "
        f"got {int(dut.bresp.value)}"
    )
    await FallingEdge(dut.aclk)
    dut.araddr.value = 0
    dut.arvalid.value = 1
    dut.rready.value = 1
    await Timer(1, units="ns")
    assert dut.bvalid.value == 0, (
        f"SMOKE FAIL: bvalid at cycle 61 expected 0, "
        f"got {int(dut.bvalid.value)}"
    )
    await FallingEdge(dut.aclk)
    dut.arvalid.value = 0
    await Timer(1, units="ns")
    assert dut.rvalid.value == 1, (
        f"SMOKE FAIL: rvalid at cycle 62 expected 1, "
        f"got {int(dut.rvalid.value)}"
    )
    assert dut.rdata.value == 0, (
        f"SMOKE FAIL: rdata at cycle 62 expected 0, "
        f"got {int(dut.rdata.value)}"
    )
    assert dut.rresp.value == 0, (
        f"SMOKE FAIL: rresp at cycle 62 expected 0, "
        f"got {int(dut.rresp.value)}"
    )

    dut._log.info("SMOKE PASS: axil_uart")
