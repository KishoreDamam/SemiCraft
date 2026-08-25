# SemiCraft v0.3.0
# cocotb testbench for pwm (config hash: cc91486794aa)
# BETA: the SystemVerilog testbench is the supported default backend.
#
# Generated code is provided as-is, without warranty of any kind. Free for
# commercial and non-commercial use at the user's own risk.

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, RisingEdge, Timer


@cocotb.test(timeout_time=1840, timeout_unit="ns")
async def smoke(dut):
    """Directed smoke test for pwm (generated).

    Mirrors the SystemVerilog smoke testbench cycle for cycle.
    """
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())

    # Initialise inputs and assert reset
    dut.rst_n.value = 0
    for _ in range(2):
        await RisingEdge(dut.clk)
    await Timer(1, units="ns")
    dut.rst_n.value = 1

    # Directed vectors; sample checks after a settle on the falling edge
    await FallingEdge(dut.clk)
    await Timer(1, units="ns")
    assert dut.pwm_out.value == 1, (
        f"SMOKE FAIL: pwm_out at cycle 0 expected 1, "
        f"got {int(dut.pwm_out.value)}"
    )
    await FallingEdge(dut.clk)
    await Timer(1, units="ns")
    assert dut.pwm_out.value == 1, (
        f"SMOKE FAIL: pwm_out at cycle 1 expected 1, "
        f"got {int(dut.pwm_out.value)}"
    )
    for _ in range(3):
        await FallingEdge(dut.clk)

    dut._log.info("SMOKE PASS: pwm")
