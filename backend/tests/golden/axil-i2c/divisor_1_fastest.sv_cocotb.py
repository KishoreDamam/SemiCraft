# SemiCraft v0.4.0
# cocotb testbench for axil_i2c (config hash: 8fe3b2c829db)
# BETA: the SystemVerilog testbench is the supported default backend.
#
# Generated code is provided as-is, without warranty of any kind. Free for
# commercial and non-commercial use at the user's own risk.

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, RisingEdge, Timer


@cocotb.test(timeout_time=10800, timeout_unit="ns")
async def smoke(dut):
    """Directed smoke test for axil_i2c (generated).

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
    dut.scl_in.value = 0
    dut.sda_in.value = 0
    dut.areset_n.value = 0
    for _ in range(2):
        await RisingEdge(dut.aclk)
    await Timer(1, units="ns")
    dut.areset_n.value = 1

    # Directed vectors; sample checks after a settle on the falling edge
    await FallingEdge(dut.aclk)
    dut.scl_in.value = 1
    dut.sda_in.value = 1
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 0, (
        f"SMOKE FAIL: scl_oe at cycle 0 expected 0, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 0, (
        f"SMOKE FAIL: sda_oe at cycle 0 expected 0, "
        f"got {int(dut.sda_oe.value)}"
    )
    assert dut.bvalid.value == 0, (
        f"SMOKE FAIL: bvalid at cycle 0 expected 0, "
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
        f"SMOKE FAIL: bvalid at cycle 3 expected 1, "
        f"got {int(dut.bvalid.value)}"
    )
    assert dut.bresp.value == 0, (
        f"SMOKE FAIL: bresp at cycle 3 expected 0, "
        f"got {int(dut.bresp.value)}"
    )
    await FallingEdge(dut.aclk)
    dut.awaddr.value = 4
    dut.awvalid.value = 1
    dut.bready.value = 1
    dut.wdata.value = 19
    dut.wstrb.value = 15
    dut.wvalid.value = 1
    await Timer(1, units="ns")
    assert dut.bvalid.value == 0, (
        f"SMOKE FAIL: bvalid at cycle 4 expected 0, "
        f"got {int(dut.bvalid.value)}"
    )
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
    assert dut.scl_oe.value == 0, (
        f"SMOKE FAIL: scl_oe at cycle 7 expected 0, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 0, (
        f"SMOKE FAIL: sda_oe at cycle 7 expected 0, "
        f"got {int(dut.sda_oe.value)}"
    )
    await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 0, (
        f"SMOKE FAIL: scl_oe at cycle 8 expected 0, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 0, (
        f"SMOKE FAIL: sda_oe at cycle 8 expected 0, "
        f"got {int(dut.sda_oe.value)}"
    )
    await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 0, (
        f"SMOKE FAIL: scl_oe at cycle 9 expected 0, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 1, (
        f"SMOKE FAIL: sda_oe at cycle 9 expected 1, "
        f"got {int(dut.sda_oe.value)}"
    )
    await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 1, (
        f"SMOKE FAIL: scl_oe at cycle 10 expected 1, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 1, (
        f"SMOKE FAIL: sda_oe at cycle 10 expected 1, "
        f"got {int(dut.sda_oe.value)}"
    )
    await FallingEdge(dut.aclk)
    dut.scl_in.value = 0
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 1, (
        f"SMOKE FAIL: scl_oe at cycle 11 expected 1, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 1, (
        f"SMOKE FAIL: sda_oe at cycle 11 expected 1, "
        f"got {int(dut.sda_oe.value)}"
    )
    await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 0, (
        f"SMOKE FAIL: scl_oe at cycle 12 expected 0, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 1, (
        f"SMOKE FAIL: sda_oe at cycle 12 expected 1, "
        f"got {int(dut.sda_oe.value)}"
    )
    await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 0, (
        f"SMOKE FAIL: scl_oe at cycle 13 expected 0, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 1, (
        f"SMOKE FAIL: sda_oe at cycle 13 expected 1, "
        f"got {int(dut.sda_oe.value)}"
    )
    for _ in range(2):
        await FallingEdge(dut.aclk)
    dut.scl_in.value = 1
    for _ in range(3):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 1, (
        f"SMOKE FAIL: scl_oe at cycle 18 expected 1, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 1, (
        f"SMOKE FAIL: sda_oe at cycle 18 expected 1, "
        f"got {int(dut.sda_oe.value)}"
    )
    await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 1, (
        f"SMOKE FAIL: scl_oe at cycle 19 expected 1, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 0, (
        f"SMOKE FAIL: sda_oe at cycle 19 expected 0, "
        f"got {int(dut.sda_oe.value)}"
    )
    await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 0, (
        f"SMOKE FAIL: scl_oe at cycle 20 expected 0, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 0, (
        f"SMOKE FAIL: sda_oe at cycle 20 expected 0, "
        f"got {int(dut.sda_oe.value)}"
    )
    await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 0, (
        f"SMOKE FAIL: scl_oe at cycle 21 expected 0, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 0, (
        f"SMOKE FAIL: sda_oe at cycle 21 expected 0, "
        f"got {int(dut.sda_oe.value)}"
    )
    await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 1, (
        f"SMOKE FAIL: scl_oe at cycle 22 expected 1, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 0, (
        f"SMOKE FAIL: sda_oe at cycle 22 expected 0, "
        f"got {int(dut.sda_oe.value)}"
    )
    await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 1, (
        f"SMOKE FAIL: scl_oe at cycle 23 expected 1, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 1, (
        f"SMOKE FAIL: sda_oe at cycle 23 expected 1, "
        f"got {int(dut.sda_oe.value)}"
    )
    await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 0, (
        f"SMOKE FAIL: scl_oe at cycle 24 expected 0, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 1, (
        f"SMOKE FAIL: sda_oe at cycle 24 expected 1, "
        f"got {int(dut.sda_oe.value)}"
    )
    await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 0, (
        f"SMOKE FAIL: scl_oe at cycle 25 expected 0, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 1, (
        f"SMOKE FAIL: sda_oe at cycle 25 expected 1, "
        f"got {int(dut.sda_oe.value)}"
    )
    await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 1, (
        f"SMOKE FAIL: scl_oe at cycle 26 expected 1, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 1, (
        f"SMOKE FAIL: sda_oe at cycle 26 expected 1, "
        f"got {int(dut.sda_oe.value)}"
    )
    await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 1, (
        f"SMOKE FAIL: scl_oe at cycle 27 expected 1, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 1, (
        f"SMOKE FAIL: sda_oe at cycle 27 expected 1, "
        f"got {int(dut.sda_oe.value)}"
    )
    await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 0, (
        f"SMOKE FAIL: scl_oe at cycle 28 expected 0, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 1, (
        f"SMOKE FAIL: sda_oe at cycle 28 expected 1, "
        f"got {int(dut.sda_oe.value)}"
    )
    await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 0, (
        f"SMOKE FAIL: scl_oe at cycle 29 expected 0, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 1, (
        f"SMOKE FAIL: sda_oe at cycle 29 expected 1, "
        f"got {int(dut.sda_oe.value)}"
    )
    await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 1, (
        f"SMOKE FAIL: scl_oe at cycle 30 expected 1, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 1, (
        f"SMOKE FAIL: sda_oe at cycle 30 expected 1, "
        f"got {int(dut.sda_oe.value)}"
    )
    await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 1, (
        f"SMOKE FAIL: scl_oe at cycle 31 expected 1, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 0, (
        f"SMOKE FAIL: sda_oe at cycle 31 expected 0, "
        f"got {int(dut.sda_oe.value)}"
    )
    await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 0, (
        f"SMOKE FAIL: scl_oe at cycle 32 expected 0, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 0, (
        f"SMOKE FAIL: sda_oe at cycle 32 expected 0, "
        f"got {int(dut.sda_oe.value)}"
    )
    await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 0, (
        f"SMOKE FAIL: scl_oe at cycle 33 expected 0, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 0, (
        f"SMOKE FAIL: sda_oe at cycle 33 expected 0, "
        f"got {int(dut.sda_oe.value)}"
    )
    await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 1, (
        f"SMOKE FAIL: scl_oe at cycle 34 expected 1, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 0, (
        f"SMOKE FAIL: sda_oe at cycle 34 expected 0, "
        f"got {int(dut.sda_oe.value)}"
    )
    await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 1, (
        f"SMOKE FAIL: scl_oe at cycle 35 expected 1, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 1, (
        f"SMOKE FAIL: sda_oe at cycle 35 expected 1, "
        f"got {int(dut.sda_oe.value)}"
    )
    await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 0, (
        f"SMOKE FAIL: scl_oe at cycle 36 expected 0, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 1, (
        f"SMOKE FAIL: sda_oe at cycle 36 expected 1, "
        f"got {int(dut.sda_oe.value)}"
    )
    await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 0, (
        f"SMOKE FAIL: scl_oe at cycle 37 expected 0, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 1, (
        f"SMOKE FAIL: sda_oe at cycle 37 expected 1, "
        f"got {int(dut.sda_oe.value)}"
    )
    await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 1, (
        f"SMOKE FAIL: scl_oe at cycle 38 expected 1, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 1, (
        f"SMOKE FAIL: sda_oe at cycle 38 expected 1, "
        f"got {int(dut.sda_oe.value)}"
    )
    await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 1, (
        f"SMOKE FAIL: scl_oe at cycle 39 expected 1, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 0, (
        f"SMOKE FAIL: sda_oe at cycle 39 expected 0, "
        f"got {int(dut.sda_oe.value)}"
    )
    await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 0, (
        f"SMOKE FAIL: scl_oe at cycle 40 expected 0, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 0, (
        f"SMOKE FAIL: sda_oe at cycle 40 expected 0, "
        f"got {int(dut.sda_oe.value)}"
    )
    await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 0, (
        f"SMOKE FAIL: scl_oe at cycle 41 expected 0, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 0, (
        f"SMOKE FAIL: sda_oe at cycle 41 expected 0, "
        f"got {int(dut.sda_oe.value)}"
    )
    await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 1, (
        f"SMOKE FAIL: scl_oe at cycle 42 expected 1, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 0, (
        f"SMOKE FAIL: sda_oe at cycle 42 expected 0, "
        f"got {int(dut.sda_oe.value)}"
    )
    await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 1, (
        f"SMOKE FAIL: scl_oe at cycle 43 expected 1, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 0, (
        f"SMOKE FAIL: sda_oe at cycle 43 expected 0, "
        f"got {int(dut.sda_oe.value)}"
    )
    await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 0, (
        f"SMOKE FAIL: scl_oe at cycle 44 expected 0, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 0, (
        f"SMOKE FAIL: sda_oe at cycle 44 expected 0, "
        f"got {int(dut.sda_oe.value)}"
    )
    await FallingEdge(dut.aclk)
    dut.sda_in.value = 0
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 0, (
        f"SMOKE FAIL: scl_oe at cycle 45 expected 0, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 0, (
        f"SMOKE FAIL: sda_oe at cycle 45 expected 0, "
        f"got {int(dut.sda_oe.value)}"
    )
    await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 1, (
        f"SMOKE FAIL: scl_oe at cycle 46 expected 1, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 0, (
        f"SMOKE FAIL: sda_oe at cycle 46 expected 0, "
        f"got {int(dut.sda_oe.value)}"
    )
    await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 1, (
        f"SMOKE FAIL: scl_oe at cycle 47 expected 1, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 0, (
        f"SMOKE FAIL: sda_oe at cycle 47 expected 0, "
        f"got {int(dut.sda_oe.value)}"
    )
    await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 0, (
        f"SMOKE FAIL: scl_oe at cycle 48 expected 0, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 0, (
        f"SMOKE FAIL: sda_oe at cycle 48 expected 0, "
        f"got {int(dut.sda_oe.value)}"
    )
    await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 0, (
        f"SMOKE FAIL: scl_oe at cycle 49 expected 0, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 0, (
        f"SMOKE FAIL: sda_oe at cycle 49 expected 0, "
        f"got {int(dut.sda_oe.value)}"
    )
    await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 1, (
        f"SMOKE FAIL: scl_oe at cycle 50 expected 1, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 0, (
        f"SMOKE FAIL: sda_oe at cycle 50 expected 0, "
        f"got {int(dut.sda_oe.value)}"
    )
    await FallingEdge(dut.aclk)
    dut.sda_in.value = 1
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 1, (
        f"SMOKE FAIL: scl_oe at cycle 51 expected 1, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 1, (
        f"SMOKE FAIL: sda_oe at cycle 51 expected 1, "
        f"got {int(dut.sda_oe.value)}"
    )
    await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 0, (
        f"SMOKE FAIL: scl_oe at cycle 52 expected 0, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 1, (
        f"SMOKE FAIL: sda_oe at cycle 52 expected 1, "
        f"got {int(dut.sda_oe.value)}"
    )
    await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 0, (
        f"SMOKE FAIL: scl_oe at cycle 53 expected 0, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 1, (
        f"SMOKE FAIL: sda_oe at cycle 53 expected 1, "
        f"got {int(dut.sda_oe.value)}"
    )
    await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 0, (
        f"SMOKE FAIL: scl_oe at cycle 54 expected 0, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 0, (
        f"SMOKE FAIL: sda_oe at cycle 54 expected 0, "
        f"got {int(dut.sda_oe.value)}"
    )
    for _ in range(4):
        await FallingEdge(dut.aclk)
    dut.araddr.value = 0
    dut.arvalid.value = 1
    dut.rready.value = 1
    await FallingEdge(dut.aclk)
    dut.arvalid.value = 0
    await Timer(1, units="ns")
    assert dut.rvalid.value == 1, (
        f"SMOKE FAIL: rvalid at cycle 59 expected 1, "
        f"got {int(dut.rvalid.value)}"
    )
    assert dut.rdata.value == 2, (
        f"SMOKE FAIL: rdata at cycle 59 expected 2, "
        f"got {int(dut.rdata.value)}"
    )
    assert dut.rresp.value == 0, (
        f"SMOKE FAIL: rresp at cycle 59 expected 0, "
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
        f"SMOKE FAIL: bvalid at cycle 62 expected 1, "
        f"got {int(dut.bvalid.value)}"
    )
    assert dut.bresp.value == 0, (
        f"SMOKE FAIL: bresp at cycle 62 expected 0, "
        f"got {int(dut.bresp.value)}"
    )
    await FallingEdge(dut.aclk)
    dut.awaddr.value = 4
    dut.awvalid.value = 1
    dut.bready.value = 1
    dut.wdata.value = 21
    dut.wstrb.value = 15
    dut.wvalid.value = 1
    await Timer(1, units="ns")
    assert dut.bvalid.value == 0, (
        f"SMOKE FAIL: bvalid at cycle 63 expected 0, "
        f"got {int(dut.bvalid.value)}"
    )
    await FallingEdge(dut.aclk)
    dut.awvalid.value = 0
    dut.wvalid.value = 0
    await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.bvalid.value == 1, (
        f"SMOKE FAIL: bvalid at cycle 65 expected 1, "
        f"got {int(dut.bvalid.value)}"
    )
    assert dut.bresp.value == 0, (
        f"SMOKE FAIL: bresp at cycle 65 expected 0, "
        f"got {int(dut.bresp.value)}"
    )
    await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.bvalid.value == 0, (
        f"SMOKE FAIL: bvalid at cycle 66 expected 0, "
        f"got {int(dut.bvalid.value)}"
    )
    for _ in range(2):
        await FallingEdge(dut.aclk)
    dut.sda_in.value = 0
    for _ in range(4):
        await FallingEdge(dut.aclk)
    dut.sda_in.value = 0
    for _ in range(4):
        await FallingEdge(dut.aclk)
    dut.sda_in.value = 1
    for _ in range(4):
        await FallingEdge(dut.aclk)
    dut.sda_in.value = 0
    for _ in range(4):
        await FallingEdge(dut.aclk)
    dut.sda_in.value = 1
    for _ in range(4):
        await FallingEdge(dut.aclk)
    dut.sda_in.value = 1
    for _ in range(4):
        await FallingEdge(dut.aclk)
    dut.sda_in.value = 0
    for _ in range(4):
        await FallingEdge(dut.aclk)
    dut.sda_in.value = 1
    for _ in range(4):
        await FallingEdge(dut.aclk)
    dut.sda_in.value = 1
    for _ in range(2):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 1, (
        f"SMOKE FAIL: scl_oe at cycle 102 expected 1, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 0, (
        f"SMOKE FAIL: sda_oe at cycle 102 expected 0, "
        f"got {int(dut.sda_oe.value)}"
    )
    await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 0, (
        f"SMOKE FAIL: scl_oe at cycle 103 expected 0, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 0, (
        f"SMOKE FAIL: sda_oe at cycle 103 expected 0, "
        f"got {int(dut.sda_oe.value)}"
    )
    await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 0, (
        f"SMOKE FAIL: scl_oe at cycle 104 expected 0, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 0, (
        f"SMOKE FAIL: sda_oe at cycle 104 expected 0, "
        f"got {int(dut.sda_oe.value)}"
    )
    await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 1, (
        f"SMOKE FAIL: scl_oe at cycle 105 expected 1, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 0, (
        f"SMOKE FAIL: sda_oe at cycle 105 expected 0, "
        f"got {int(dut.sda_oe.value)}"
    )
    for _ in range(8):
        await FallingEdge(dut.aclk)
    dut.araddr.value = 0
    dut.arvalid.value = 1
    dut.rready.value = 1
    await FallingEdge(dut.aclk)
    dut.arvalid.value = 0
    await Timer(1, units="ns")
    assert dut.rvalid.value == 1, (
        f"SMOKE FAIL: rvalid at cycle 114 expected 1, "
        f"got {int(dut.rvalid.value)}"
    )
    assert dut.rdata.value == 10, (
        f"SMOKE FAIL: rdata at cycle 114 expected 10, "
        f"got {int(dut.rdata.value)}"
    )
    assert dut.rresp.value == 0, (
        f"SMOKE FAIL: rresp at cycle 114 expected 0, "
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
        f"SMOKE FAIL: rvalid at cycle 116 expected 1, "
        f"got {int(dut.rvalid.value)}"
    )
    assert dut.rdata.value == 45, (
        f"SMOKE FAIL: rdata at cycle 116 expected 45, "
        f"got {int(dut.rdata.value)}"
    )
    assert dut.rresp.value == 0, (
        f"SMOKE FAIL: rresp at cycle 116 expected 0, "
        f"got {int(dut.rresp.value)}"
    )

    dut._log.info("SMOKE PASS: axil_i2c")
