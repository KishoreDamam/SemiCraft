# SemiCraft v0.4.0
# cocotb testbench for axil_spi (config hash: 48d96e5ea16b)
# BETA: the SystemVerilog testbench is the supported default backend.
#
# Generated code is provided as-is, without warranty of any kind. Free for
# commercial and non-commercial use at the user's own risk.

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, RisingEdge, Timer


@cocotb.test(timeout_time=15920, timeout_unit="ns")
async def smoke(dut):
    """Directed smoke test for axil_spi (generated).

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
    dut.miso.value = 0
    dut.areset_n.value = 0
    for _ in range(2):
        await RisingEdge(dut.aclk)
    await Timer(1, units="ns")
    dut.areset_n.value = 1

    # Directed vectors; sample checks after a settle on the falling edge
    await FallingEdge(dut.aclk)
    dut.awaddr.value = 4
    dut.awvalid.value = 1
    dut.bready.value = 1
    dut.wdata.value = 1
    dut.wstrb.value = 15
    dut.wvalid.value = 1
    await Timer(1, units="ns")
    assert dut.sclk.value == 1, (
        f"SMOKE FAIL: sclk at cycle 0 expected 1, "
        f"got {int(dut.sclk.value)}"
    )
    assert dut.cs_n.value == 1, (
        f"SMOKE FAIL: cs_n at cycle 0 expected 1, "
        f"got {int(dut.cs_n.value)}"
    )
    assert dut.bvalid.value == 0, (
        f"SMOKE FAIL: bvalid at cycle 0 expected 0, "
        f"got {int(dut.bvalid.value)}"
    )
    await FallingEdge(dut.aclk)
    dut.awvalid.value = 0
    dut.wvalid.value = 0
    await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.bvalid.value == 1, (
        f"SMOKE FAIL: bvalid at cycle 2 expected 1, "
        f"got {int(dut.bvalid.value)}"
    )
    assert dut.bresp.value == 0, (
        f"SMOKE FAIL: bresp at cycle 2 expected 0, "
        f"got {int(dut.bresp.value)}"
    )
    assert dut.cs_n.value == 0, (
        f"SMOKE FAIL: cs_n at cycle 2 expected 0, "
        f"got {int(dut.cs_n.value)}"
    )
    await FallingEdge(dut.aclk)
    dut.miso.value = 0
    await Timer(1, units="ns")
    assert dut.bvalid.value == 0, (
        f"SMOKE FAIL: bvalid at cycle 3 expected 0, "
        f"got {int(dut.bvalid.value)}"
    )
    await FallingEdge(dut.aclk)
    dut.awaddr.value = 8
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
        f"SMOKE FAIL: bvalid at cycle 6 expected 1, "
        f"got {int(dut.bvalid.value)}"
    )
    assert dut.bresp.value == 0, (
        f"SMOKE FAIL: bresp at cycle 6 expected 0, "
        f"got {int(dut.bresp.value)}"
    )
    await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.bvalid.value == 0, (
        f"SMOKE FAIL: bvalid at cycle 7 expected 0, "
        f"got {int(dut.bvalid.value)}"
    )
    for _ in range(10):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.sclk.value == 0, (
        f"SMOKE FAIL: sclk at cycle 17 expected 0, "
        f"got {int(dut.sclk.value)}"
    )
    await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.mosi.value == 0, (
        f"SMOKE FAIL: mosi at cycle 18 expected 0, "
        f"got {int(dut.mosi.value)}"
    )
    for _ in range(6):
        await FallingEdge(dut.aclk)
    dut.miso.value = 0
    for _ in range(3):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.sclk.value == 1, (
        f"SMOKE FAIL: sclk at cycle 27 expected 1, "
        f"got {int(dut.sclk.value)}"
    )
    for _ in range(11):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.mosi.value == 1, (
        f"SMOKE FAIL: mosi at cycle 38 expected 1, "
        f"got {int(dut.mosi.value)}"
    )
    for _ in range(6):
        await FallingEdge(dut.aclk)
    dut.miso.value = 0
    for _ in range(14):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.mosi.value == 0, (
        f"SMOKE FAIL: mosi at cycle 58 expected 0, "
        f"got {int(dut.mosi.value)}"
    )
    for _ in range(6):
        await FallingEdge(dut.aclk)
    dut.miso.value = 1
    for _ in range(14):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.mosi.value == 0, (
        f"SMOKE FAIL: mosi at cycle 78 expected 0, "
        f"got {int(dut.mosi.value)}"
    )
    for _ in range(6):
        await FallingEdge(dut.aclk)
    dut.miso.value = 0
    for _ in range(14):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.mosi.value == 1, (
        f"SMOKE FAIL: mosi at cycle 98 expected 1, "
        f"got {int(dut.mosi.value)}"
    )
    for _ in range(6):
        await FallingEdge(dut.aclk)
    dut.miso.value = 1
    for _ in range(14):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.mosi.value == 0, (
        f"SMOKE FAIL: mosi at cycle 118 expected 0, "
        f"got {int(dut.mosi.value)}"
    )
    for _ in range(6):
        await FallingEdge(dut.aclk)
    dut.miso.value = 1
    for _ in range(14):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.mosi.value == 1, (
        f"SMOKE FAIL: mosi at cycle 138 expected 1, "
        f"got {int(dut.mosi.value)}"
    )
    for _ in range(6):
        await FallingEdge(dut.aclk)
    dut.miso.value = 0
    for _ in range(14):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.mosi.value == 1, (
        f"SMOKE FAIL: mosi at cycle 158 expected 1, "
        f"got {int(dut.mosi.value)}"
    )
    for _ in range(6):
        await FallingEdge(dut.aclk)
    dut.miso.value = 1
    for _ in range(3):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.sclk.value == 1, (
        f"SMOKE FAIL: sclk at cycle 167 expected 1, "
        f"got {int(dut.sclk.value)}"
    )
    await FallingEdge(dut.aclk)
    dut.araddr.value = 0
    dut.arvalid.value = 1
    dut.rready.value = 1
    await FallingEdge(dut.aclk)
    dut.arvalid.value = 0
    await Timer(1, units="ns")
    assert dut.rvalid.value == 1, (
        f"SMOKE FAIL: rvalid at cycle 169 expected 1, "
        f"got {int(dut.rvalid.value)}"
    )
    assert dut.rdata.value == 2, (
        f"SMOKE FAIL: rdata at cycle 169 expected 2, "
        f"got {int(dut.rdata.value)}"
    )
    assert dut.rresp.value == 0, (
        f"SMOKE FAIL: rresp at cycle 169 expected 0, "
        f"got {int(dut.rresp.value)}"
    )
    await FallingEdge(dut.aclk)
    dut.araddr.value = 12
    dut.arvalid.value = 1
    dut.rready.value = 1
    await FallingEdge(dut.aclk)
    dut.arvalid.value = 0
    await Timer(1, units="ns")
    assert dut.rvalid.value == 1, (
        f"SMOKE FAIL: rvalid at cycle 171 expected 1, "
        f"got {int(dut.rvalid.value)}"
    )
    assert dut.rdata.value == 45, (
        f"SMOKE FAIL: rdata at cycle 171 expected 45, "
        f"got {int(dut.rdata.value)}"
    )
    assert dut.rresp.value == 0, (
        f"SMOKE FAIL: rresp at cycle 171 expected 0, "
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
        f"SMOKE FAIL: bvalid at cycle 174 expected 1, "
        f"got {int(dut.bvalid.value)}"
    )
    assert dut.bresp.value == 0, (
        f"SMOKE FAIL: bresp at cycle 174 expected 0, "
        f"got {int(dut.bresp.value)}"
    )
    await FallingEdge(dut.aclk)
    dut.araddr.value = 0
    dut.arvalid.value = 1
    dut.rready.value = 1
    await Timer(1, units="ns")
    assert dut.bvalid.value == 0, (
        f"SMOKE FAIL: bvalid at cycle 175 expected 0, "
        f"got {int(dut.bvalid.value)}"
    )
    await FallingEdge(dut.aclk)
    dut.arvalid.value = 0
    await Timer(1, units="ns")
    assert dut.rvalid.value == 1, (
        f"SMOKE FAIL: rvalid at cycle 176 expected 1, "
        f"got {int(dut.rvalid.value)}"
    )
    assert dut.rdata.value == 0, (
        f"SMOKE FAIL: rdata at cycle 176 expected 0, "
        f"got {int(dut.rdata.value)}"
    )
    assert dut.rresp.value == 0, (
        f"SMOKE FAIL: rresp at cycle 176 expected 0, "
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
        f"SMOKE FAIL: bvalid at cycle 179 expected 1, "
        f"got {int(dut.bvalid.value)}"
    )
    assert dut.bresp.value == 0, (
        f"SMOKE FAIL: bresp at cycle 179 expected 0, "
        f"got {int(dut.bresp.value)}"
    )
    assert dut.cs_n.value == 1, (
        f"SMOKE FAIL: cs_n at cycle 179 expected 1, "
        f"got {int(dut.cs_n.value)}"
    )
    await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.bvalid.value == 0, (
        f"SMOKE FAIL: bvalid at cycle 180 expected 0, "
        f"got {int(dut.bvalid.value)}"
    )

    dut._log.info("SMOKE PASS: axil_spi")
