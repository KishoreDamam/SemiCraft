# SemiCraft v0.4.0
# cocotb testbench for axil_spi (config hash: 165e9bc926f2)
# BETA: the SystemVerilog testbench is the supported default backend.
#
# Generated code is provided as-is, without warranty of any kind. Free for
# commercial and non-commercial use at the user's own risk.

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, RisingEdge, Timer


@cocotb.test(timeout_time=5680, timeout_unit="ns")
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
    assert dut.sclk.value == 0, (
        f"SMOKE FAIL: sclk at cycle 0 expected 0, "
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
    dut.miso.value = 1
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
    dut.miso.value = 1
    await Timer(1, units="ns")
    assert dut.bvalid.value == 0, (
        f"SMOKE FAIL: bvalid at cycle 7 expected 0, "
        f"got {int(dut.bvalid.value)}"
    )
    await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.mosi.value == 0, (
        f"SMOKE FAIL: mosi at cycle 8 expected 0, "
        f"got {int(dut.mosi.value)}"
    )
    await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.sclk.value == 1, (
        f"SMOKE FAIL: sclk at cycle 9 expected 1, "
        f"got {int(dut.sclk.value)}"
    )
    for _ in range(2):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.sclk.value == 0, (
        f"SMOKE FAIL: sclk at cycle 11 expected 0, "
        f"got {int(dut.sclk.value)}"
    )
    await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.mosi.value == 1, (
        f"SMOKE FAIL: mosi at cycle 12 expected 1, "
        f"got {int(dut.mosi.value)}"
    )
    for _ in range(4):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.mosi.value == 0, (
        f"SMOKE FAIL: mosi at cycle 16 expected 0, "
        f"got {int(dut.mosi.value)}"
    )
    for _ in range(4):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.mosi.value == 0, (
        f"SMOKE FAIL: mosi at cycle 20 expected 0, "
        f"got {int(dut.mosi.value)}"
    )
    for _ in range(4):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.mosi.value == 1, (
        f"SMOKE FAIL: mosi at cycle 24 expected 1, "
        f"got {int(dut.mosi.value)}"
    )
    for _ in range(4):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.mosi.value == 0, (
        f"SMOKE FAIL: mosi at cycle 28 expected 0, "
        f"got {int(dut.mosi.value)}"
    )
    for _ in range(4):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.mosi.value == 1, (
        f"SMOKE FAIL: mosi at cycle 32 expected 1, "
        f"got {int(dut.mosi.value)}"
    )
    for _ in range(4):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.mosi.value == 1, (
        f"SMOKE FAIL: mosi at cycle 36 expected 1, "
        f"got {int(dut.mosi.value)}"
    )
    for _ in range(3):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.sclk.value == 0, (
        f"SMOKE FAIL: sclk at cycle 39 expected 0, "
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
        f"SMOKE FAIL: rvalid at cycle 41 expected 1, "
        f"got {int(dut.rvalid.value)}"
    )
    assert dut.rdata.value == 2, (
        f"SMOKE FAIL: rdata at cycle 41 expected 2, "
        f"got {int(dut.rdata.value)}"
    )
    assert dut.rresp.value == 0, (
        f"SMOKE FAIL: rresp at cycle 41 expected 0, "
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
        f"SMOKE FAIL: rvalid at cycle 43 expected 1, "
        f"got {int(dut.rvalid.value)}"
    )
    assert dut.rdata.value == 255, (
        f"SMOKE FAIL: rdata at cycle 43 expected 255, "
        f"got {int(dut.rdata.value)}"
    )
    assert dut.rresp.value == 0, (
        f"SMOKE FAIL: rresp at cycle 43 expected 0, "
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
        f"SMOKE FAIL: bvalid at cycle 46 expected 1, "
        f"got {int(dut.bvalid.value)}"
    )
    assert dut.bresp.value == 0, (
        f"SMOKE FAIL: bresp at cycle 46 expected 0, "
        f"got {int(dut.bresp.value)}"
    )
    await FallingEdge(dut.aclk)
    dut.araddr.value = 0
    dut.arvalid.value = 1
    dut.rready.value = 1
    await Timer(1, units="ns")
    assert dut.bvalid.value == 0, (
        f"SMOKE FAIL: bvalid at cycle 47 expected 0, "
        f"got {int(dut.bvalid.value)}"
    )
    await FallingEdge(dut.aclk)
    dut.arvalid.value = 0
    await Timer(1, units="ns")
    assert dut.rvalid.value == 1, (
        f"SMOKE FAIL: rvalid at cycle 48 expected 1, "
        f"got {int(dut.rvalid.value)}"
    )
    assert dut.rdata.value == 0, (
        f"SMOKE FAIL: rdata at cycle 48 expected 0, "
        f"got {int(dut.rdata.value)}"
    )
    assert dut.rresp.value == 0, (
        f"SMOKE FAIL: rresp at cycle 48 expected 0, "
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
        f"SMOKE FAIL: bvalid at cycle 51 expected 1, "
        f"got {int(dut.bvalid.value)}"
    )
    assert dut.bresp.value == 0, (
        f"SMOKE FAIL: bresp at cycle 51 expected 0, "
        f"got {int(dut.bresp.value)}"
    )
    assert dut.cs_n.value == 1, (
        f"SMOKE FAIL: cs_n at cycle 51 expected 1, "
        f"got {int(dut.cs_n.value)}"
    )
    await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.bvalid.value == 0, (
        f"SMOKE FAIL: bvalid at cycle 52 expected 0, "
        f"got {int(dut.bvalid.value)}"
    )

    dut._log.info("SMOKE PASS: axil_spi")
