# SemiCraft v0.4.0
# cocotb testbench for axil_i2c (config hash: 26587d292b6d)
# BETA: the SystemVerilog testbench is the supported default backend.
#
# Generated code is provided as-is, without warranty of any kind. Free for
# commercial and non-commercial use at the user's own risk.

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, RisingEdge, Timer


@cocotb.test(timeout_time=89840, timeout_unit="ns")
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
    for _ in range(12):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 0, (
        f"SMOKE FAIL: scl_oe at cycle 19 expected 0, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 0, (
        f"SMOKE FAIL: sda_oe at cycle 19 expected 0, "
        f"got {int(dut.sda_oe.value)}"
    )
    for _ in range(12):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 0, (
        f"SMOKE FAIL: scl_oe at cycle 31 expected 0, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 1, (
        f"SMOKE FAIL: sda_oe at cycle 31 expected 1, "
        f"got {int(dut.sda_oe.value)}"
    )
    for _ in range(12):
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
    for _ in range(12):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 1, (
        f"SMOKE FAIL: scl_oe at cycle 55 expected 1, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 1, (
        f"SMOKE FAIL: sda_oe at cycle 55 expected 1, "
        f"got {int(dut.sda_oe.value)}"
    )
    for _ in range(12):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 0, (
        f"SMOKE FAIL: scl_oe at cycle 67 expected 0, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 1, (
        f"SMOKE FAIL: sda_oe at cycle 67 expected 1, "
        f"got {int(dut.sda_oe.value)}"
    )
    for _ in range(9):
        await FallingEdge(dut.aclk)
    dut.scl_in.value = 0
    for _ in range(3):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 0, (
        f"SMOKE FAIL: scl_oe at cycle 79 expected 0, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 1, (
        f"SMOKE FAIL: sda_oe at cycle 79 expected 1, "
        f"got {int(dut.sda_oe.value)}"
    )
    for _ in range(21):
        await FallingEdge(dut.aclk)
    dut.scl_in.value = 1
    for _ in range(15):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 1, (
        f"SMOKE FAIL: scl_oe at cycle 115 expected 1, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 1, (
        f"SMOKE FAIL: sda_oe at cycle 115 expected 1, "
        f"got {int(dut.sda_oe.value)}"
    )
    for _ in range(12):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 1, (
        f"SMOKE FAIL: scl_oe at cycle 127 expected 1, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 0, (
        f"SMOKE FAIL: sda_oe at cycle 127 expected 0, "
        f"got {int(dut.sda_oe.value)}"
    )
    for _ in range(12):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 0, (
        f"SMOKE FAIL: scl_oe at cycle 139 expected 0, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 0, (
        f"SMOKE FAIL: sda_oe at cycle 139 expected 0, "
        f"got {int(dut.sda_oe.value)}"
    )
    for _ in range(12):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 0, (
        f"SMOKE FAIL: scl_oe at cycle 151 expected 0, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 0, (
        f"SMOKE FAIL: sda_oe at cycle 151 expected 0, "
        f"got {int(dut.sda_oe.value)}"
    )
    for _ in range(12):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 1, (
        f"SMOKE FAIL: scl_oe at cycle 163 expected 1, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 0, (
        f"SMOKE FAIL: sda_oe at cycle 163 expected 0, "
        f"got {int(dut.sda_oe.value)}"
    )
    for _ in range(12):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 1, (
        f"SMOKE FAIL: scl_oe at cycle 175 expected 1, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 1, (
        f"SMOKE FAIL: sda_oe at cycle 175 expected 1, "
        f"got {int(dut.sda_oe.value)}"
    )
    for _ in range(12):
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
    for _ in range(12):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 0, (
        f"SMOKE FAIL: scl_oe at cycle 199 expected 0, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 1, (
        f"SMOKE FAIL: sda_oe at cycle 199 expected 1, "
        f"got {int(dut.sda_oe.value)}"
    )
    for _ in range(12):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 1, (
        f"SMOKE FAIL: scl_oe at cycle 211 expected 1, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 1, (
        f"SMOKE FAIL: sda_oe at cycle 211 expected 1, "
        f"got {int(dut.sda_oe.value)}"
    )
    for _ in range(12):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 1, (
        f"SMOKE FAIL: scl_oe at cycle 223 expected 1, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 1, (
        f"SMOKE FAIL: sda_oe at cycle 223 expected 1, "
        f"got {int(dut.sda_oe.value)}"
    )
    for _ in range(12):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 0, (
        f"SMOKE FAIL: scl_oe at cycle 235 expected 0, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 1, (
        f"SMOKE FAIL: sda_oe at cycle 235 expected 1, "
        f"got {int(dut.sda_oe.value)}"
    )
    for _ in range(12):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 0, (
        f"SMOKE FAIL: scl_oe at cycle 247 expected 0, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 1, (
        f"SMOKE FAIL: sda_oe at cycle 247 expected 1, "
        f"got {int(dut.sda_oe.value)}"
    )
    for _ in range(12):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 1, (
        f"SMOKE FAIL: scl_oe at cycle 259 expected 1, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 1, (
        f"SMOKE FAIL: sda_oe at cycle 259 expected 1, "
        f"got {int(dut.sda_oe.value)}"
    )
    for _ in range(12):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 1, (
        f"SMOKE FAIL: scl_oe at cycle 271 expected 1, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 0, (
        f"SMOKE FAIL: sda_oe at cycle 271 expected 0, "
        f"got {int(dut.sda_oe.value)}"
    )
    for _ in range(12):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 0, (
        f"SMOKE FAIL: scl_oe at cycle 283 expected 0, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 0, (
        f"SMOKE FAIL: sda_oe at cycle 283 expected 0, "
        f"got {int(dut.sda_oe.value)}"
    )
    for _ in range(12):
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
    for _ in range(12):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 1, (
        f"SMOKE FAIL: scl_oe at cycle 307 expected 1, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 0, (
        f"SMOKE FAIL: sda_oe at cycle 307 expected 0, "
        f"got {int(dut.sda_oe.value)}"
    )
    for _ in range(12):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 1, (
        f"SMOKE FAIL: scl_oe at cycle 319 expected 1, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 1, (
        f"SMOKE FAIL: sda_oe at cycle 319 expected 1, "
        f"got {int(dut.sda_oe.value)}"
    )
    for _ in range(12):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 0, (
        f"SMOKE FAIL: scl_oe at cycle 331 expected 0, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 1, (
        f"SMOKE FAIL: sda_oe at cycle 331 expected 1, "
        f"got {int(dut.sda_oe.value)}"
    )
    for _ in range(12):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 0, (
        f"SMOKE FAIL: scl_oe at cycle 343 expected 0, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 1, (
        f"SMOKE FAIL: sda_oe at cycle 343 expected 1, "
        f"got {int(dut.sda_oe.value)}"
    )
    for _ in range(12):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 1, (
        f"SMOKE FAIL: scl_oe at cycle 355 expected 1, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 1, (
        f"SMOKE FAIL: sda_oe at cycle 355 expected 1, "
        f"got {int(dut.sda_oe.value)}"
    )
    for _ in range(12):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 1, (
        f"SMOKE FAIL: scl_oe at cycle 367 expected 1, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 0, (
        f"SMOKE FAIL: sda_oe at cycle 367 expected 0, "
        f"got {int(dut.sda_oe.value)}"
    )
    for _ in range(12):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 0, (
        f"SMOKE FAIL: scl_oe at cycle 379 expected 0, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 0, (
        f"SMOKE FAIL: sda_oe at cycle 379 expected 0, "
        f"got {int(dut.sda_oe.value)}"
    )
    for _ in range(12):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 0, (
        f"SMOKE FAIL: scl_oe at cycle 391 expected 0, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 0, (
        f"SMOKE FAIL: sda_oe at cycle 391 expected 0, "
        f"got {int(dut.sda_oe.value)}"
    )
    for _ in range(12):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 1, (
        f"SMOKE FAIL: scl_oe at cycle 403 expected 1, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 0, (
        f"SMOKE FAIL: sda_oe at cycle 403 expected 0, "
        f"got {int(dut.sda_oe.value)}"
    )
    for _ in range(12):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 1, (
        f"SMOKE FAIL: scl_oe at cycle 415 expected 1, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 0, (
        f"SMOKE FAIL: sda_oe at cycle 415 expected 0, "
        f"got {int(dut.sda_oe.value)}"
    )
    for _ in range(12):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 0, (
        f"SMOKE FAIL: scl_oe at cycle 427 expected 0, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 0, (
        f"SMOKE FAIL: sda_oe at cycle 427 expected 0, "
        f"got {int(dut.sda_oe.value)}"
    )
    for _ in range(12):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 0, (
        f"SMOKE FAIL: scl_oe at cycle 439 expected 0, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 0, (
        f"SMOKE FAIL: sda_oe at cycle 439 expected 0, "
        f"got {int(dut.sda_oe.value)}"
    )
    for _ in range(12):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 1, (
        f"SMOKE FAIL: scl_oe at cycle 451 expected 1, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 0, (
        f"SMOKE FAIL: sda_oe at cycle 451 expected 0, "
        f"got {int(dut.sda_oe.value)}"
    )
    for _ in range(9):
        await FallingEdge(dut.aclk)
    dut.sda_in.value = 0
    for _ in range(3):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 1, (
        f"SMOKE FAIL: scl_oe at cycle 463 expected 1, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 0, (
        f"SMOKE FAIL: sda_oe at cycle 463 expected 0, "
        f"got {int(dut.sda_oe.value)}"
    )
    for _ in range(12):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 0, (
        f"SMOKE FAIL: scl_oe at cycle 475 expected 0, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 0, (
        f"SMOKE FAIL: sda_oe at cycle 475 expected 0, "
        f"got {int(dut.sda_oe.value)}"
    )
    for _ in range(12):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 0, (
        f"SMOKE FAIL: scl_oe at cycle 487 expected 0, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 0, (
        f"SMOKE FAIL: sda_oe at cycle 487 expected 0, "
        f"got {int(dut.sda_oe.value)}"
    )
    for _ in range(12):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 1, (
        f"SMOKE FAIL: scl_oe at cycle 499 expected 1, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 0, (
        f"SMOKE FAIL: sda_oe at cycle 499 expected 0, "
        f"got {int(dut.sda_oe.value)}"
    )
    for _ in range(12):
        await FallingEdge(dut.aclk)
    dut.sda_in.value = 1
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 1, (
        f"SMOKE FAIL: scl_oe at cycle 511 expected 1, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 1, (
        f"SMOKE FAIL: sda_oe at cycle 511 expected 1, "
        f"got {int(dut.sda_oe.value)}"
    )
    for _ in range(12):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 0, (
        f"SMOKE FAIL: scl_oe at cycle 523 expected 0, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 1, (
        f"SMOKE FAIL: sda_oe at cycle 523 expected 1, "
        f"got {int(dut.sda_oe.value)}"
    )
    for _ in range(12):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 0, (
        f"SMOKE FAIL: scl_oe at cycle 535 expected 0, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 1, (
        f"SMOKE FAIL: sda_oe at cycle 535 expected 1, "
        f"got {int(dut.sda_oe.value)}"
    )
    for _ in range(12):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 0, (
        f"SMOKE FAIL: scl_oe at cycle 547 expected 0, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 0, (
        f"SMOKE FAIL: sda_oe at cycle 547 expected 0, "
        f"got {int(dut.sda_oe.value)}"
    )
    for _ in range(15):
        await FallingEdge(dut.aclk)
    dut.araddr.value = 0
    dut.arvalid.value = 1
    dut.rready.value = 1
    await FallingEdge(dut.aclk)
    dut.arvalid.value = 0
    await Timer(1, units="ns")
    assert dut.rvalid.value == 1, (
        f"SMOKE FAIL: rvalid at cycle 563 expected 1, "
        f"got {int(dut.rvalid.value)}"
    )
    assert dut.rdata.value == 2, (
        f"SMOKE FAIL: rdata at cycle 563 expected 2, "
        f"got {int(dut.rdata.value)}"
    )
    assert dut.rresp.value == 0, (
        f"SMOKE FAIL: rresp at cycle 563 expected 0, "
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
        f"SMOKE FAIL: bvalid at cycle 566 expected 1, "
        f"got {int(dut.bvalid.value)}"
    )
    assert dut.bresp.value == 0, (
        f"SMOKE FAIL: bresp at cycle 566 expected 0, "
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
        f"SMOKE FAIL: bvalid at cycle 567 expected 0, "
        f"got {int(dut.bvalid.value)}"
    )
    await FallingEdge(dut.aclk)
    dut.awvalid.value = 0
    dut.wvalid.value = 0
    await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.bvalid.value == 1, (
        f"SMOKE FAIL: bvalid at cycle 569 expected 1, "
        f"got {int(dut.bvalid.value)}"
    )
    assert dut.bresp.value == 0, (
        f"SMOKE FAIL: bresp at cycle 569 expected 0, "
        f"got {int(dut.bresp.value)}"
    )
    await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.bvalid.value == 0, (
        f"SMOKE FAIL: bvalid at cycle 570 expected 0, "
        f"got {int(dut.bvalid.value)}"
    )
    for _ in range(45):
        await FallingEdge(dut.aclk)
    dut.sda_in.value = 0
    for _ in range(48):
        await FallingEdge(dut.aclk)
    dut.sda_in.value = 0
    for _ in range(48):
        await FallingEdge(dut.aclk)
    dut.sda_in.value = 1
    for _ in range(48):
        await FallingEdge(dut.aclk)
    dut.sda_in.value = 0
    for _ in range(48):
        await FallingEdge(dut.aclk)
    dut.sda_in.value = 1
    for _ in range(48):
        await FallingEdge(dut.aclk)
    dut.sda_in.value = 1
    for _ in range(48):
        await FallingEdge(dut.aclk)
    dut.sda_in.value = 0
    for _ in range(48):
        await FallingEdge(dut.aclk)
    dut.sda_in.value = 1
    for _ in range(48):
        await FallingEdge(dut.aclk)
    dut.sda_in.value = 1
    for _ in range(3):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 1, (
        f"SMOKE FAIL: scl_oe at cycle 1002 expected 1, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 0, (
        f"SMOKE FAIL: sda_oe at cycle 1002 expected 0, "
        f"got {int(dut.sda_oe.value)}"
    )
    for _ in range(12):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 0, (
        f"SMOKE FAIL: scl_oe at cycle 1014 expected 0, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 0, (
        f"SMOKE FAIL: sda_oe at cycle 1014 expected 0, "
        f"got {int(dut.sda_oe.value)}"
    )
    for _ in range(12):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 0, (
        f"SMOKE FAIL: scl_oe at cycle 1026 expected 0, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 0, (
        f"SMOKE FAIL: sda_oe at cycle 1026 expected 0, "
        f"got {int(dut.sda_oe.value)}"
    )
    for _ in range(12):
        await FallingEdge(dut.aclk)
    await Timer(1, units="ns")
    assert dut.scl_oe.value == 1, (
        f"SMOKE FAIL: scl_oe at cycle 1038 expected 1, "
        f"got {int(dut.scl_oe.value)}"
    )
    assert dut.sda_oe.value == 0, (
        f"SMOKE FAIL: sda_oe at cycle 1038 expected 0, "
        f"got {int(dut.sda_oe.value)}"
    )
    for _ in range(63):
        await FallingEdge(dut.aclk)
    dut.araddr.value = 0
    dut.arvalid.value = 1
    dut.rready.value = 1
    await FallingEdge(dut.aclk)
    dut.arvalid.value = 0
    await Timer(1, units="ns")
    assert dut.rvalid.value == 1, (
        f"SMOKE FAIL: rvalid at cycle 1102 expected 1, "
        f"got {int(dut.rvalid.value)}"
    )
    assert dut.rdata.value == 10, (
        f"SMOKE FAIL: rdata at cycle 1102 expected 10, "
        f"got {int(dut.rdata.value)}"
    )
    assert dut.rresp.value == 0, (
        f"SMOKE FAIL: rresp at cycle 1102 expected 0, "
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
        f"SMOKE FAIL: rvalid at cycle 1104 expected 1, "
        f"got {int(dut.rvalid.value)}"
    )
    assert dut.rdata.value == 45, (
        f"SMOKE FAIL: rdata at cycle 1104 expected 45, "
        f"got {int(dut.rdata.value)}"
    )
    assert dut.rresp.value == 0, (
        f"SMOKE FAIL: rresp at cycle 1104 expected 0, "
        f"got {int(dut.rresp.value)}"
    )

    dut._log.info("SMOKE PASS: axil_i2c")
