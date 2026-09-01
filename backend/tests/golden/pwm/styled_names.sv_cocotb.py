# SemiCraft v0.4.0
# cocotb testbench for pwm (config hash: 30a28f1388c6)
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
    cocotb.start_soon(Clock(dut.p_clk, 10, units="ns").start())

    # Initialise inputs and assert reset
    dut.p_duty.value = 0
    dut.p_rst_n.value = 0
    for _ in range(2):
        await RisingEdge(dut.p_clk)
    await Timer(1, units="ns")
    dut.p_rst_n.value = 1

    # Directed vectors; sample checks after a settle on the falling edge
    await FallingEdge(dut.p_clk)
    dut.p_duty.value = 0
    await Timer(1, units="ns")
    assert dut.p_pwmOut.value == 0, (
        f"SMOKE FAIL: p_pwmOut at cycle 0 expected 0, "
        f"got {int(dut.p_pwmOut.value)}"
    )
    await FallingEdge(dut.p_clk)
    dut.p_duty.value = 128
    await Timer(1, units="ns")
    assert dut.p_pwmOut.value == 1, (
        f"SMOKE FAIL: p_pwmOut at cycle 1 expected 1, "
        f"got {int(dut.p_pwmOut.value)}"
    )
    await FallingEdge(dut.p_clk)
    dut.p_duty.value = 128
    await FallingEdge(dut.p_clk)
    dut.p_duty.value = 255
    await FallingEdge(dut.p_clk)
    dut.p_duty.value = 255

    dut._log.info("SMOKE PASS: pwm")
