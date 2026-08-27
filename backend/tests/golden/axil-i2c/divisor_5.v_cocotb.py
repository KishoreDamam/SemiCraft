# SemiCraft v0.3.0
# cocotb testbench for axil_i2c (config hash: 6cb6c5115fb9)
# BETA: the SystemVerilog testbench is the supported default backend.
#
# Generated code is provided as-is, without warranty of any kind. Free for
# commercial and non-commercial use at the user's own risk.

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, RisingEdge, Timer


@cocotb.test(timeout_time=39440, timeout_unit="ns")
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
    for _ in range(5):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 0, (
        f"SMOKE FAIL: scl_oe at cycle 12 expected 0, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 0, (
        f"SMOKE FAIL: sda_oe at cycle 12 expected 0, "
        f"got {int(dut.sda_oe.value)}"
    )
    for _ in range(5):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 0, (
        f"SMOKE FAIL: scl_oe at cycle 17 expected 0, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 1, (
        f"SMOKE FAIL: sda_oe at cycle 17 expected 1, "
        f"got {int(dut.sda_oe.value)}"
    )
    for _ in range(5):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 1, (
        f"SMOKE FAIL: scl_oe at cycle 22 expected 1, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 1, (
        f"SMOKE FAIL: sda_oe at cycle 22 expected 1, "
        f"got {int(dut.sda_oe.value)}"
    )
    for _ in range(5):
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
    for _ in range(5):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 0, (
        f"SMOKE FAIL: scl_oe at cycle 32 expected 0, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 1, (
        f"SMOKE FAIL: sda_oe at cycle 32 expected 1, "
        f"got {int(dut.sda_oe.value)}"
    )
    for _ in range(3):
        await FallingEdge(dut.aclk)
    dut.scl_in.value = 0
    for _ in range(2):
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
    for _ in range(8):
        await FallingEdge(dut.aclk)
    dut.scl_in.value = 1
    for _ in range(7):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 1, (
        f"SMOKE FAIL: scl_oe at cycle 52 expected 1, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 1, (
        f"SMOKE FAIL: sda_oe at cycle 52 expected 1, "
        f"got {int(dut.sda_oe.value)}"
    )
    for _ in range(5):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 1, (
        f"SMOKE FAIL: scl_oe at cycle 57 expected 1, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 0, (
        f"SMOKE FAIL: sda_oe at cycle 57 expected 0, "
        f"got {int(dut.sda_oe.value)}"
    )
    for _ in range(5):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 0, (
        f"SMOKE FAIL: scl_oe at cycle 62 expected 0, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 0, (
        f"SMOKE FAIL: sda_oe at cycle 62 expected 0, "
        f"got {int(dut.sda_oe.value)}"
    )
    for _ in range(5):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 0, (
        f"SMOKE FAIL: scl_oe at cycle 67 expected 0, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 0, (
        f"SMOKE FAIL: sda_oe at cycle 67 expected 0, "
        f"got {int(dut.sda_oe.value)}"
    )
    for _ in range(5):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 1, (
        f"SMOKE FAIL: scl_oe at cycle 72 expected 1, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 0, (
        f"SMOKE FAIL: sda_oe at cycle 72 expected 0, "
        f"got {int(dut.sda_oe.value)}"
    )
    for _ in range(5):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 1, (
        f"SMOKE FAIL: scl_oe at cycle 77 expected 1, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 1, (
        f"SMOKE FAIL: sda_oe at cycle 77 expected 1, "
        f"got {int(dut.sda_oe.value)}"
    )
    for _ in range(5):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 0, (
        f"SMOKE FAIL: scl_oe at cycle 82 expected 0, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 1, (
        f"SMOKE FAIL: sda_oe at cycle 82 expected 1, "
        f"got {int(dut.sda_oe.value)}"
    )
    for _ in range(5):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 0, (
        f"SMOKE FAIL: scl_oe at cycle 87 expected 0, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 1, (
        f"SMOKE FAIL: sda_oe at cycle 87 expected 1, "
        f"got {int(dut.sda_oe.value)}"
    )
    for _ in range(5):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 1, (
        f"SMOKE FAIL: scl_oe at cycle 92 expected 1, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 1, (
        f"SMOKE FAIL: sda_oe at cycle 92 expected 1, "
        f"got {int(dut.sda_oe.value)}"
    )
    for _ in range(5):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 1, (
        f"SMOKE FAIL: scl_oe at cycle 97 expected 1, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 1, (
        f"SMOKE FAIL: sda_oe at cycle 97 expected 1, "
        f"got {int(dut.sda_oe.value)}"
    )
    for _ in range(5):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 0, (
        f"SMOKE FAIL: scl_oe at cycle 102 expected 0, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 1, (
        f"SMOKE FAIL: sda_oe at cycle 102 expected 1, "
        f"got {int(dut.sda_oe.value)}"
    )
    for _ in range(5):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 0, (
        f"SMOKE FAIL: scl_oe at cycle 107 expected 0, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 1, (
        f"SMOKE FAIL: sda_oe at cycle 107 expected 1, "
        f"got {int(dut.sda_oe.value)}"
    )
    for _ in range(5):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 1, (
        f"SMOKE FAIL: scl_oe at cycle 112 expected 1, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 1, (
        f"SMOKE FAIL: sda_oe at cycle 112 expected 1, "
        f"got {int(dut.sda_oe.value)}"
    )
    for _ in range(5):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 1, (
        f"SMOKE FAIL: scl_oe at cycle 117 expected 1, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 0, (
        f"SMOKE FAIL: sda_oe at cycle 117 expected 0, "
        f"got {int(dut.sda_oe.value)}"
    )
    for _ in range(5):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 0, (
        f"SMOKE FAIL: scl_oe at cycle 122 expected 0, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 0, (
        f"SMOKE FAIL: sda_oe at cycle 122 expected 0, "
        f"got {int(dut.sda_oe.value)}"
    )
    for _ in range(5):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 0, (
        f"SMOKE FAIL: scl_oe at cycle 127 expected 0, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 0, (
        f"SMOKE FAIL: sda_oe at cycle 127 expected 0, "
        f"got {int(dut.sda_oe.value)}"
    )
    for _ in range(5):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 1, (
        f"SMOKE FAIL: scl_oe at cycle 132 expected 1, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 0, (
        f"SMOKE FAIL: sda_oe at cycle 132 expected 0, "
        f"got {int(dut.sda_oe.value)}"
    )
    for _ in range(5):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 1, (
        f"SMOKE FAIL: scl_oe at cycle 137 expected 1, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 1, (
        f"SMOKE FAIL: sda_oe at cycle 137 expected 1, "
        f"got {int(dut.sda_oe.value)}"
    )
    for _ in range(5):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 0, (
        f"SMOKE FAIL: scl_oe at cycle 142 expected 0, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 1, (
        f"SMOKE FAIL: sda_oe at cycle 142 expected 1, "
        f"got {int(dut.sda_oe.value)}"
    )
    for _ in range(5):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 0, (
        f"SMOKE FAIL: scl_oe at cycle 147 expected 0, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 1, (
        f"SMOKE FAIL: sda_oe at cycle 147 expected 1, "
        f"got {int(dut.sda_oe.value)}"
    )
    for _ in range(5):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 1, (
        f"SMOKE FAIL: scl_oe at cycle 152 expected 1, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 1, (
        f"SMOKE FAIL: sda_oe at cycle 152 expected 1, "
        f"got {int(dut.sda_oe.value)}"
    )
    for _ in range(5):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 1, (
        f"SMOKE FAIL: scl_oe at cycle 157 expected 1, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 0, (
        f"SMOKE FAIL: sda_oe at cycle 157 expected 0, "
        f"got {int(dut.sda_oe.value)}"
    )
    for _ in range(5):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 0, (
        f"SMOKE FAIL: scl_oe at cycle 162 expected 0, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 0, (
        f"SMOKE FAIL: sda_oe at cycle 162 expected 0, "
        f"got {int(dut.sda_oe.value)}"
    )
    for _ in range(5):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 0, (
        f"SMOKE FAIL: scl_oe at cycle 167 expected 0, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 0, (
        f"SMOKE FAIL: sda_oe at cycle 167 expected 0, "
        f"got {int(dut.sda_oe.value)}"
    )
    for _ in range(5):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 1, (
        f"SMOKE FAIL: scl_oe at cycle 172 expected 1, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 0, (
        f"SMOKE FAIL: sda_oe at cycle 172 expected 0, "
        f"got {int(dut.sda_oe.value)}"
    )
    for _ in range(5):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 1, (
        f"SMOKE FAIL: scl_oe at cycle 177 expected 1, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 0, (
        f"SMOKE FAIL: sda_oe at cycle 177 expected 0, "
        f"got {int(dut.sda_oe.value)}"
    )
    for _ in range(5):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 0, (
        f"SMOKE FAIL: scl_oe at cycle 182 expected 0, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 0, (
        f"SMOKE FAIL: sda_oe at cycle 182 expected 0, "
        f"got {int(dut.sda_oe.value)}"
    )
    for _ in range(5):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 0, (
        f"SMOKE FAIL: scl_oe at cycle 187 expected 0, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 0, (
        f"SMOKE FAIL: sda_oe at cycle 187 expected 0, "
        f"got {int(dut.sda_oe.value)}"
    )
    for _ in range(5):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 1, (
        f"SMOKE FAIL: scl_oe at cycle 192 expected 1, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 0, (
        f"SMOKE FAIL: sda_oe at cycle 192 expected 0, "
        f"got {int(dut.sda_oe.value)}"
    )
    for _ in range(3):
        await FallingEdge(dut.aclk)
    dut.sda_in.value = 0
    for _ in range(2):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 1, (
        f"SMOKE FAIL: scl_oe at cycle 197 expected 1, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 0, (
        f"SMOKE FAIL: sda_oe at cycle 197 expected 0, "
        f"got {int(dut.sda_oe.value)}"
    )
    for _ in range(5):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 0, (
        f"SMOKE FAIL: scl_oe at cycle 202 expected 0, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 0, (
        f"SMOKE FAIL: sda_oe at cycle 202 expected 0, "
        f"got {int(dut.sda_oe.value)}"
    )
    for _ in range(5):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 0, (
        f"SMOKE FAIL: scl_oe at cycle 207 expected 0, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 0, (
        f"SMOKE FAIL: sda_oe at cycle 207 expected 0, "
        f"got {int(dut.sda_oe.value)}"
    )
    for _ in range(5):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 1, (
        f"SMOKE FAIL: scl_oe at cycle 212 expected 1, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 0, (
        f"SMOKE FAIL: sda_oe at cycle 212 expected 0, "
        f"got {int(dut.sda_oe.value)}"
    )
    for _ in range(5):
        await FallingEdge(dut.aclk)
    dut.sda_in.value = 1
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 1, (
        f"SMOKE FAIL: scl_oe at cycle 217 expected 1, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 1, (
        f"SMOKE FAIL: sda_oe at cycle 217 expected 1, "
        f"got {int(dut.sda_oe.value)}"
    )
    for _ in range(5):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 0, (
        f"SMOKE FAIL: scl_oe at cycle 222 expected 0, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 1, (
        f"SMOKE FAIL: sda_oe at cycle 222 expected 1, "
        f"got {int(dut.sda_oe.value)}"
    )
    for _ in range(5):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 0, (
        f"SMOKE FAIL: scl_oe at cycle 227 expected 0, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 1, (
        f"SMOKE FAIL: sda_oe at cycle 227 expected 1, "
        f"got {int(dut.sda_oe.value)}"
    )
    for _ in range(5):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 0, (
        f"SMOKE FAIL: scl_oe at cycle 232 expected 0, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 0, (
        f"SMOKE FAIL: sda_oe at cycle 232 expected 0, "
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
        f"SMOKE FAIL: rvalid at cycle 241 expected 1, "
        f"got {int(dut.rvalid.value)}"
    )
    assert dut.rdata.value == 2, (
        f"SMOKE FAIL: rdata at cycle 241 expected 2, "
        f"got {int(dut.rdata.value)}"
    )
    assert dut.rresp.value == 0, (
        f"SMOKE FAIL: rresp at cycle 241 expected 0, "
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
        f"SMOKE FAIL: bvalid at cycle 244 expected 1, "
        f"got {int(dut.bvalid.value)}"
    )
    assert dut.bresp.value == 0, (
        f"SMOKE FAIL: bresp at cycle 244 expected 0, "
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
        f"SMOKE FAIL: bvalid at cycle 245 expected 0, "
        f"got {int(dut.bvalid.value)}"
    )
    await FallingEdge(dut.aclk)
    dut.awvalid.value = 0
    dut.wvalid.value = 0
    await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.bvalid.value == 1, (
        f"SMOKE FAIL: bvalid at cycle 247 expected 1, "
        f"got {int(dut.bvalid.value)}"
    )
    assert dut.bresp.value == 0, (
        f"SMOKE FAIL: bresp at cycle 247 expected 0, "
        f"got {int(dut.bresp.value)}"
    )
    await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.bvalid.value == 0, (
        f"SMOKE FAIL: bvalid at cycle 248 expected 0, "
        f"got {int(dut.bvalid.value)}"
    )
    for _ in range(18):
        await FallingEdge(dut.aclk)
    dut.sda_in.value = 0
    for _ in range(20):
        await FallingEdge(dut.aclk)
    dut.sda_in.value = 0
    for _ in range(20):
        await FallingEdge(dut.aclk)
    dut.sda_in.value = 1
    for _ in range(20):
        await FallingEdge(dut.aclk)
    dut.sda_in.value = 0
    for _ in range(20):
        await FallingEdge(dut.aclk)
    dut.sda_in.value = 1
    for _ in range(20):
        await FallingEdge(dut.aclk)
    dut.sda_in.value = 1
    for _ in range(20):
        await FallingEdge(dut.aclk)
    dut.sda_in.value = 0
    for _ in range(20):
        await FallingEdge(dut.aclk)
    dut.sda_in.value = 1
    for _ in range(20):
        await FallingEdge(dut.aclk)
    dut.sda_in.value = 1
    for _ in range(2):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 1, (
        f"SMOKE FAIL: scl_oe at cycle 428 expected 1, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 0, (
        f"SMOKE FAIL: sda_oe at cycle 428 expected 0, "
        f"got {int(dut.sda_oe.value)}"
    )
    for _ in range(5):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 0, (
        f"SMOKE FAIL: scl_oe at cycle 433 expected 0, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 0, (
        f"SMOKE FAIL: sda_oe at cycle 433 expected 0, "
        f"got {int(dut.sda_oe.value)}"
    )
    for _ in range(5):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 0, (
        f"SMOKE FAIL: scl_oe at cycle 438 expected 0, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 0, (
        f"SMOKE FAIL: sda_oe at cycle 438 expected 0, "
        f"got {int(dut.sda_oe.value)}"
    )
    for _ in range(5):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 1, (
        f"SMOKE FAIL: scl_oe at cycle 443 expected 1, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 0, (
        f"SMOKE FAIL: sda_oe at cycle 443 expected 0, "
        f"got {int(dut.sda_oe.value)}"
    )
    for _ in range(28):
        await FallingEdge(dut.aclk)
    dut.araddr.value = 0
    dut.arvalid.value = 1
    dut.rready.value = 1
    await FallingEdge(dut.aclk)
    dut.arvalid.value = 0
    await Timer(1, units="ns")
    assert dut.rvalid.value == 1, (
        f"SMOKE FAIL: rvalid at cycle 472 expected 1, "
        f"got {int(dut.rvalid.value)}"
    )
    assert dut.rdata.value == 10, (
        f"SMOKE FAIL: rdata at cycle 472 expected 10, "
        f"got {int(dut.rdata.value)}"
    )
    assert dut.rresp.value == 0, (
        f"SMOKE FAIL: rresp at cycle 472 expected 0, "
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
        f"SMOKE FAIL: rvalid at cycle 474 expected 1, "
        f"got {int(dut.rvalid.value)}"
    )
    assert dut.rdata.value == 45, (
        f"SMOKE FAIL: rdata at cycle 474 expected 45, "
        f"got {int(dut.rdata.value)}"
    )
    assert dut.rresp.value == 0, (
        f"SMOKE FAIL: rresp at cycle 474 expected 0, "
        f"got {int(dut.rresp.value)}"
    )

    dut._log.info("SMOKE PASS: axil_i2c")
