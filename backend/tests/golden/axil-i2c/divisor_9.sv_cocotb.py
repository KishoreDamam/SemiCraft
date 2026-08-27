# SemiCraft v0.3.0
# cocotb testbench for axil_i2c (config hash: 0cc3df490d7c)
# BETA: the SystemVerilog testbench is the supported default backend.
#
# Generated code is provided as-is, without warranty of any kind. Free for
# commercial and non-commercial use at the user's own risk.

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, RisingEdge, Timer


@cocotb.test(timeout_time=68240, timeout_unit="ns")
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
    for _ in range(9):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 0, (
        f"SMOKE FAIL: scl_oe at cycle 16 expected 0, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 0, (
        f"SMOKE FAIL: sda_oe at cycle 16 expected 0, "
        f"got {int(dut.sda_oe.value)}"
    )
    for _ in range(9):
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
    for _ in range(9):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 1, (
        f"SMOKE FAIL: scl_oe at cycle 34 expected 1, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 1, (
        f"SMOKE FAIL: sda_oe at cycle 34 expected 1, "
        f"got {int(dut.sda_oe.value)}"
    )
    for _ in range(9):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 1, (
        f"SMOKE FAIL: scl_oe at cycle 43 expected 1, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 1, (
        f"SMOKE FAIL: sda_oe at cycle 43 expected 1, "
        f"got {int(dut.sda_oe.value)}"
    )
    for _ in range(9):
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
    for _ in range(7):
        await FallingEdge(dut.aclk)
    dut.scl_in.value = 0
    for _ in range(2):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 0, (
        f"SMOKE FAIL: scl_oe at cycle 61 expected 0, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 1, (
        f"SMOKE FAIL: sda_oe at cycle 61 expected 1, "
        f"got {int(dut.sda_oe.value)}"
    )
    for _ in range(16):
        await FallingEdge(dut.aclk)
    dut.scl_in.value = 1
    for _ in range(11):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 1, (
        f"SMOKE FAIL: scl_oe at cycle 88 expected 1, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 1, (
        f"SMOKE FAIL: sda_oe at cycle 88 expected 1, "
        f"got {int(dut.sda_oe.value)}"
    )
    for _ in range(9):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 1, (
        f"SMOKE FAIL: scl_oe at cycle 97 expected 1, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 0, (
        f"SMOKE FAIL: sda_oe at cycle 97 expected 0, "
        f"got {int(dut.sda_oe.value)}"
    )
    for _ in range(9):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 0, (
        f"SMOKE FAIL: scl_oe at cycle 106 expected 0, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 0, (
        f"SMOKE FAIL: sda_oe at cycle 106 expected 0, "
        f"got {int(dut.sda_oe.value)}"
    )
    for _ in range(9):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 0, (
        f"SMOKE FAIL: scl_oe at cycle 115 expected 0, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 0, (
        f"SMOKE FAIL: sda_oe at cycle 115 expected 0, "
        f"got {int(dut.sda_oe.value)}"
    )
    for _ in range(9):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 1, (
        f"SMOKE FAIL: scl_oe at cycle 124 expected 1, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 0, (
        f"SMOKE FAIL: sda_oe at cycle 124 expected 0, "
        f"got {int(dut.sda_oe.value)}"
    )
    for _ in range(9):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 1, (
        f"SMOKE FAIL: scl_oe at cycle 133 expected 1, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 1, (
        f"SMOKE FAIL: sda_oe at cycle 133 expected 1, "
        f"got {int(dut.sda_oe.value)}"
    )
    for _ in range(9):
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
    for _ in range(9):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 0, (
        f"SMOKE FAIL: scl_oe at cycle 151 expected 0, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 1, (
        f"SMOKE FAIL: sda_oe at cycle 151 expected 1, "
        f"got {int(dut.sda_oe.value)}"
    )
    for _ in range(9):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 1, (
        f"SMOKE FAIL: scl_oe at cycle 160 expected 1, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 1, (
        f"SMOKE FAIL: sda_oe at cycle 160 expected 1, "
        f"got {int(dut.sda_oe.value)}"
    )
    for _ in range(9):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 1, (
        f"SMOKE FAIL: scl_oe at cycle 169 expected 1, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 1, (
        f"SMOKE FAIL: sda_oe at cycle 169 expected 1, "
        f"got {int(dut.sda_oe.value)}"
    )
    for _ in range(9):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 0, (
        f"SMOKE FAIL: scl_oe at cycle 178 expected 0, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 1, (
        f"SMOKE FAIL: sda_oe at cycle 178 expected 1, "
        f"got {int(dut.sda_oe.value)}"
    )
    for _ in range(9):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 0, (
        f"SMOKE FAIL: scl_oe at cycle 187 expected 0, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 1, (
        f"SMOKE FAIL: sda_oe at cycle 187 expected 1, "
        f"got {int(dut.sda_oe.value)}"
    )
    for _ in range(9):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 1, (
        f"SMOKE FAIL: scl_oe at cycle 196 expected 1, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 1, (
        f"SMOKE FAIL: sda_oe at cycle 196 expected 1, "
        f"got {int(dut.sda_oe.value)}"
    )
    for _ in range(9):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 1, (
        f"SMOKE FAIL: scl_oe at cycle 205 expected 1, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 0, (
        f"SMOKE FAIL: sda_oe at cycle 205 expected 0, "
        f"got {int(dut.sda_oe.value)}"
    )
    for _ in range(9):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 0, (
        f"SMOKE FAIL: scl_oe at cycle 214 expected 0, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 0, (
        f"SMOKE FAIL: sda_oe at cycle 214 expected 0, "
        f"got {int(dut.sda_oe.value)}"
    )
    for _ in range(9):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 0, (
        f"SMOKE FAIL: scl_oe at cycle 223 expected 0, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 0, (
        f"SMOKE FAIL: sda_oe at cycle 223 expected 0, "
        f"got {int(dut.sda_oe.value)}"
    )
    for _ in range(9):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 1, (
        f"SMOKE FAIL: scl_oe at cycle 232 expected 1, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 0, (
        f"SMOKE FAIL: sda_oe at cycle 232 expected 0, "
        f"got {int(dut.sda_oe.value)}"
    )
    for _ in range(9):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 1, (
        f"SMOKE FAIL: scl_oe at cycle 241 expected 1, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 1, (
        f"SMOKE FAIL: sda_oe at cycle 241 expected 1, "
        f"got {int(dut.sda_oe.value)}"
    )
    for _ in range(9):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 0, (
        f"SMOKE FAIL: scl_oe at cycle 250 expected 0, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 1, (
        f"SMOKE FAIL: sda_oe at cycle 250 expected 1, "
        f"got {int(dut.sda_oe.value)}"
    )
    for _ in range(9):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 0, (
        f"SMOKE FAIL: scl_oe at cycle 259 expected 0, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 1, (
        f"SMOKE FAIL: sda_oe at cycle 259 expected 1, "
        f"got {int(dut.sda_oe.value)}"
    )
    for _ in range(9):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 1, (
        f"SMOKE FAIL: scl_oe at cycle 268 expected 1, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 1, (
        f"SMOKE FAIL: sda_oe at cycle 268 expected 1, "
        f"got {int(dut.sda_oe.value)}"
    )
    for _ in range(9):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 1, (
        f"SMOKE FAIL: scl_oe at cycle 277 expected 1, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 0, (
        f"SMOKE FAIL: sda_oe at cycle 277 expected 0, "
        f"got {int(dut.sda_oe.value)}"
    )
    for _ in range(9):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 0, (
        f"SMOKE FAIL: scl_oe at cycle 286 expected 0, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 0, (
        f"SMOKE FAIL: sda_oe at cycle 286 expected 0, "
        f"got {int(dut.sda_oe.value)}"
    )
    for _ in range(9):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 0, (
        f"SMOKE FAIL: scl_oe at cycle 295 expected 0, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 0, (
        f"SMOKE FAIL: sda_oe at cycle 295 expected 0, "
        f"got {int(dut.sda_oe.value)}"
    )
    for _ in range(9):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 1, (
        f"SMOKE FAIL: scl_oe at cycle 304 expected 1, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 0, (
        f"SMOKE FAIL: sda_oe at cycle 304 expected 0, "
        f"got {int(dut.sda_oe.value)}"
    )
    for _ in range(9):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 1, (
        f"SMOKE FAIL: scl_oe at cycle 313 expected 1, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 0, (
        f"SMOKE FAIL: sda_oe at cycle 313 expected 0, "
        f"got {int(dut.sda_oe.value)}"
    )
    for _ in range(9):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 0, (
        f"SMOKE FAIL: scl_oe at cycle 322 expected 0, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 0, (
        f"SMOKE FAIL: sda_oe at cycle 322 expected 0, "
        f"got {int(dut.sda_oe.value)}"
    )
    for _ in range(9):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 0, (
        f"SMOKE FAIL: scl_oe at cycle 331 expected 0, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 0, (
        f"SMOKE FAIL: sda_oe at cycle 331 expected 0, "
        f"got {int(dut.sda_oe.value)}"
    )
    for _ in range(9):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 1, (
        f"SMOKE FAIL: scl_oe at cycle 340 expected 1, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 0, (
        f"SMOKE FAIL: sda_oe at cycle 340 expected 0, "
        f"got {int(dut.sda_oe.value)}"
    )
    for _ in range(7):
        await FallingEdge(dut.aclk)
    dut.sda_in.value = 0
    for _ in range(2):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 1, (
        f"SMOKE FAIL: scl_oe at cycle 349 expected 1, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 0, (
        f"SMOKE FAIL: sda_oe at cycle 349 expected 0, "
        f"got {int(dut.sda_oe.value)}"
    )
    for _ in range(9):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 0, (
        f"SMOKE FAIL: scl_oe at cycle 358 expected 0, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 0, (
        f"SMOKE FAIL: sda_oe at cycle 358 expected 0, "
        f"got {int(dut.sda_oe.value)}"
    )
    for _ in range(9):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 0, (
        f"SMOKE FAIL: scl_oe at cycle 367 expected 0, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 0, (
        f"SMOKE FAIL: sda_oe at cycle 367 expected 0, "
        f"got {int(dut.sda_oe.value)}"
    )
    for _ in range(9):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 1, (
        f"SMOKE FAIL: scl_oe at cycle 376 expected 1, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 0, (
        f"SMOKE FAIL: sda_oe at cycle 376 expected 0, "
        f"got {int(dut.sda_oe.value)}"
    )
    for _ in range(9):
        await FallingEdge(dut.aclk)
    dut.sda_in.value = 1
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 1, (
        f"SMOKE FAIL: scl_oe at cycle 385 expected 1, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 1, (
        f"SMOKE FAIL: sda_oe at cycle 385 expected 1, "
        f"got {int(dut.sda_oe.value)}"
    )
    for _ in range(9):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 0, (
        f"SMOKE FAIL: scl_oe at cycle 394 expected 0, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 1, (
        f"SMOKE FAIL: sda_oe at cycle 394 expected 1, "
        f"got {int(dut.sda_oe.value)}"
    )
    for _ in range(9):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 0, (
        f"SMOKE FAIL: scl_oe at cycle 403 expected 0, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 1, (
        f"SMOKE FAIL: sda_oe at cycle 403 expected 1, "
        f"got {int(dut.sda_oe.value)}"
    )
    for _ in range(9):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 0, (
        f"SMOKE FAIL: scl_oe at cycle 412 expected 0, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 0, (
        f"SMOKE FAIL: sda_oe at cycle 412 expected 0, "
        f"got {int(dut.sda_oe.value)}"
    )
    for _ in range(12):
        await FallingEdge(dut.aclk)
    dut.araddr.value = 0
    dut.arvalid.value = 1
    dut.rready.value = 1
    await FallingEdge(dut.aclk)
    dut.arvalid.value = 0
    await Timer(1, units="ns")
    assert dut.rvalid.value == 1, (
        f"SMOKE FAIL: rvalid at cycle 425 expected 1, "
        f"got {int(dut.rvalid.value)}"
    )
    assert dut.rdata.value == 2, (
        f"SMOKE FAIL: rdata at cycle 425 expected 2, "
        f"got {int(dut.rdata.value)}"
    )
    assert dut.rresp.value == 0, (
        f"SMOKE FAIL: rresp at cycle 425 expected 0, "
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
        f"SMOKE FAIL: bvalid at cycle 428 expected 1, "
        f"got {int(dut.bvalid.value)}"
    )
    assert dut.bresp.value == 0, (
        f"SMOKE FAIL: bresp at cycle 428 expected 0, "
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
        f"SMOKE FAIL: bvalid at cycle 429 expected 0, "
        f"got {int(dut.bvalid.value)}"
    )
    await FallingEdge(dut.aclk)
    dut.awvalid.value = 0
    dut.wvalid.value = 0
    await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.bvalid.value == 1, (
        f"SMOKE FAIL: bvalid at cycle 431 expected 1, "
        f"got {int(dut.bvalid.value)}"
    )
    assert dut.bresp.value == 0, (
        f"SMOKE FAIL: bresp at cycle 431 expected 0, "
        f"got {int(dut.bresp.value)}"
    )
    await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.bvalid.value == 0, (
        f"SMOKE FAIL: bvalid at cycle 432 expected 0, "
        f"got {int(dut.bvalid.value)}"
    )
    for _ in range(34):
        await FallingEdge(dut.aclk)
    dut.sda_in.value = 0
    for _ in range(36):
        await FallingEdge(dut.aclk)
    dut.sda_in.value = 0
    for _ in range(36):
        await FallingEdge(dut.aclk)
    dut.sda_in.value = 1
    for _ in range(36):
        await FallingEdge(dut.aclk)
    dut.sda_in.value = 0
    for _ in range(36):
        await FallingEdge(dut.aclk)
    dut.sda_in.value = 1
    for _ in range(36):
        await FallingEdge(dut.aclk)
    dut.sda_in.value = 1
    for _ in range(36):
        await FallingEdge(dut.aclk)
    dut.sda_in.value = 0
    for _ in range(36):
        await FallingEdge(dut.aclk)
    dut.sda_in.value = 1
    for _ in range(36):
        await FallingEdge(dut.aclk)
    dut.sda_in.value = 1
    for _ in range(2):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 1, (
        f"SMOKE FAIL: scl_oe at cycle 756 expected 1, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 0, (
        f"SMOKE FAIL: sda_oe at cycle 756 expected 0, "
        f"got {int(dut.sda_oe.value)}"
    )
    for _ in range(9):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 0, (
        f"SMOKE FAIL: scl_oe at cycle 765 expected 0, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 0, (
        f"SMOKE FAIL: sda_oe at cycle 765 expected 0, "
        f"got {int(dut.sda_oe.value)}"
    )
    for _ in range(9):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 0, (
        f"SMOKE FAIL: scl_oe at cycle 774 expected 0, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 0, (
        f"SMOKE FAIL: sda_oe at cycle 774 expected 0, "
        f"got {int(dut.sda_oe.value)}"
    )
    for _ in range(9):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 1, (
        f"SMOKE FAIL: scl_oe at cycle 783 expected 1, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 0, (
        f"SMOKE FAIL: sda_oe at cycle 783 expected 0, "
        f"got {int(dut.sda_oe.value)}"
    )
    for _ in range(48):
        await FallingEdge(dut.aclk)
    dut.araddr.value = 0
    dut.arvalid.value = 1
    dut.rready.value = 1
    await FallingEdge(dut.aclk)
    dut.arvalid.value = 0
    await Timer(1, units="ns")
    assert dut.rvalid.value == 1, (
        f"SMOKE FAIL: rvalid at cycle 832 expected 1, "
        f"got {int(dut.rvalid.value)}"
    )
    assert dut.rdata.value == 10, (
        f"SMOKE FAIL: rdata at cycle 832 expected 10, "
        f"got {int(dut.rdata.value)}"
    )
    assert dut.rresp.value == 0, (
        f"SMOKE FAIL: rresp at cycle 832 expected 0, "
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
        f"SMOKE FAIL: rvalid at cycle 834 expected 1, "
        f"got {int(dut.rvalid.value)}"
    )
    assert dut.rdata.value == 45, (
        f"SMOKE FAIL: rdata at cycle 834 expected 45, "
        f"got {int(dut.rdata.value)}"
    )
    assert dut.rresp.value == 0, (
        f"SMOKE FAIL: rresp at cycle 834 expected 0, "
        f"got {int(dut.rresp.value)}"
    )

    dut._log.info("SMOKE PASS: axil_i2c")
