"""cocotb testbench backend (P3-08, **beta**).

An alternative to the SystemVerilog smoke testbench: the same ``TbSpec`` recipe
emitted as a Python `cocotb <https://www.cocotb.org/>`_ test module. The SV
backend stays the default and the golden/CI gates continue to run it; this one
is opt-in (see :data:`~semicraft_core.generate.EMIT_COCOTB_TB`) and marked beta.

Why a second backend at all: cocotb testbenches are ordinary Python, so a user
can extend generated stimulus with loops, data structures, and their own
libraries without learning SystemVerilog testbench constructs. The plan calls
for it as the Phase-3 "alternative backend" (P3-08).

Semantics are deliberately identical to the SV backend, statement for statement,
so the two cannot drift into disagreeing about what the module does:

- free-running clock, 10 ns period (5 ns half period);
- every input initialised to 0, reset asserted at time 0;
- reset held ``TbSpec.reset_cycles`` **rising** edges, then a 1 ns settle, then
  deasserted. The settle is not cosmetic — it is normative (TB_SPEC §6a): a
  deassert sharing a timestep with that rising edge races the DUT's own clocked
  process, which cost 17 golden testbenches a correct run before P3-09a;
- directed cycle ``c`` anchored to a **falling** edge: drive the cycle's vector,
  settle 1 ns, then sample checks — no drive/sample race with the DUT's rising
  edge;
- values width-masked and ``PortConstraint``-clamped by the *same*
  ``_constrain_value`` the SV backend uses;
- a timeout mirroring the SV ``TimeoutGuard`` budget, expressed as cocotb's own
  ``timeout_time`` rather than a hand-rolled watchdog;
- on success, prints the same ``SMOKE PASS: <module>`` marker the sim runner
  greps for, so ``sim.runner``'s pass semantics apply unchanged.

Nets are resolved through the **same** style name map as the RTL and the SV TB
(``render.style.build_name_map``), so all three agree on identifiers by
construction rather than by convention.

Toolchain constraint (verified, not assumed)
--------------------------------------------

Generated code targets the **cocotb 1.x** API: ``Clock(..., units="ns")`` and
``cocotb.runner``. cocotb 2.x renamed these (``unit=``, ``cocotb_tools.runner``)
**and** its Verilator VPI shim calls ``VerilatedVpi::doInertialPuts()`` /
``evalNeeded()``, which do not exist in Verilator 5.020 — the newest version
available from apt on Ubuntu noble, and the one this project's sandbox and CI
use. cocotb 2.0.1 therefore fails to build against it; 1.9.2 runs clean. The
dev dependency is pinned to ``cocotb==1.9.2`` for that reason. Revisit the pin
only together with a newer Verilator.
"""

from __future__ import annotations

import re
import textwrap

from ..ir.nodes import Module
from ..license import DISCLAIMER
from ..render.style import build_name_map
from .generate_tb import (
    _SETTLE_NS,
    _TIMEOUT_FLOOR,
    _TIMEOUT_SLACK,
    _constrain_value,
    _find_reset,
    _param_values,
    _style_from_options,
    _width_of,
)

__all__ = ["generate_cocotb_tb", "cocotb_tb_filename"]

_CLOCK_PERIOD_NS = 10
_WRAP_WIDTH = 76
_INDENT = "    "


def cocotb_tb_filename(module_name: str) -> str:
    """Filename for a module's cocotb testbench.

    ``test_<module>.py``: cocotb's runner discovers test modules by import name,
    and pytest-style ``test_*`` is the convention its own examples use.
    """
    return f"test_{module_name}.py"


def _banner(module: Module) -> list[str]:
    """Python comment banner mirroring the RTL/SV-TB header."""
    h = module.header
    lines = [
        f"# SemiCraft v{h.tool_version}",
        f"# cocotb testbench for {module.name} (config hash: {h.config_hash})",
        "# BETA: the SystemVerilog testbench is the supported default backend.",
        "#",
    ]
    lines.extend(f"# {line}" for line in textwrap.wrap(h.license or DISCLAIMER, width=_WRAP_WIDTH))
    return lines


def generate_cocotb_tb(module_def, opts, rtl_module: Module) -> str:
    """Render the cocotb smoke testbench for ``module_def``/``opts`` as Python text.

    Returns ``""`` when the module has no clock, matching ``generate_tb``: a
    combinational module has no smoke-TB recipe to emit.

    Pure and deterministic — identical inputs yield byte-identical text, with no
    timestamps or randomness (ground rule §1).
    """
    spec = module_def.tb_spec(opts)
    if spec.clock is None:
        return ""

    names = build_name_map(rtl_module, _style_from_options(opts))

    def styled(canonical: str) -> str:
        return names.get(canonical, canonical)

    params = _param_values(rtl_module)
    ports = list(rtl_module.ports)
    width_of = {p.name: _width_of(p.dtype, params) for p in ports}
    input_names = {p.name for p in ports if p.dir.value == "input"}

    clk = styled(spec.clock)

    reset_net: str | None = None
    reset_assert = reset_deassert = 0
    if spec.reset is not None:
        rspec = _find_reset(rtl_module, spec.reset)
        active_low = rspec.active_low if rspec is not None else False
        reset_net = styled(spec.reset)
        reset_assert = 0 if active_low else 1
        reset_deassert = 1 if active_low else 0

    n_cycles = max(len(spec.vectors), (max((c.cycle for c in spec.checks), default=-1) + 1))
    # Same budget as the SV TimeoutGuard, converted from cycles to ns so it can
    # be expressed as cocotb's own test timeout.
    timeout_ns = (spec.reset_cycles + n_cycles + _TIMEOUT_FLOOR) * _TIMEOUT_SLACK * _CLOCK_PERIOD_NS

    checks_by_cycle: dict[int, list] = {}
    for chk in spec.checks:
        checks_by_cycle.setdefault(chk.cycle, []).append(chk)

    # The body is built first so the import line can be derived from what it
    # actually uses. A fixed `FallingEdge, RisingEdge, Timer` was correct only
    # while every module had a reset: `RisingEdge` appears solely in the
    # reset-hold loop, so the first IP without a reset (P4-04's RAM) emitted an
    # unused import. Ruff lints the committed cocotb goldens and caught it.
    out: list[str] = []
    out.append(f'@cocotb.test(timeout_time={timeout_ns}, timeout_unit="ns")')
    out.append("async def smoke(dut):")
    out.append(f'{_INDENT}"""Directed smoke test for {rtl_module.name} (generated).')
    out.append("")
    out.append(f"{_INDENT}Mirrors the SystemVerilog smoke testbench cycle for cycle.")
    out.append(f'{_INDENT}"""')
    # Clock. `units=` is the cocotb 1.x spelling; see the module docstring for
    # why this backend targets 1.x.
    out.append(
        f'{_INDENT}cocotb.start_soon(Clock(dut.{clk}, {_CLOCK_PERIOD_NS}, units="ns").start())'
    )
    out.append("")
    out.append(f"{_INDENT}# Initialise inputs and assert reset")
    for p in ports:
        if p.name in input_names and p.name not in (spec.clock, spec.reset):
            out.append(f"{_INDENT}dut.{styled(p.name)}.value = 0")
    if reset_net is not None:
        out.append(f"{_INDENT}dut.{reset_net}.value = {reset_assert}")
        if spec.reset_cycles == 1:
            out.append(f"{_INDENT}await RisingEdge(dut.{clk})")
        else:
            out.append(f"{_INDENT}for _ in range({spec.reset_cycles}):")
            out.append(f"{_INDENT * 2}await RisingEdge(dut.{clk})")
        # Normative settle before deassert (TB_SPEC §6a).
        out.append(f'{_INDENT}await Timer({_SETTLE_NS}, units="ns")')
        out.append(f"{_INDENT}dut.{reset_net}.value = {reset_deassert}")
    out.append("")

    if n_cycles:
        out.append(f"{_INDENT}# Directed vectors; sample checks after a settle on the falling edge")
    pending = 0
    for c in range(n_cycles):
        pending += 1
        has_drives = c < len(spec.vectors) and bool(spec.vectors[c])
        if not has_drives and c not in checks_by_cycle:
            continue
        if pending == 1:
            out.append(f"{_INDENT}await FallingEdge(dut.{clk})")
        else:
            out.append(f"{_INDENT}for _ in range({pending}):")
            out.append(f"{_INDENT * 2}await FallingEdge(dut.{clk})")
        pending = 0
        if has_drives:
            for sig in sorted(spec.vectors[c]):
                w = width_of.get(sig, 1)
                val = _constrain_value(spec.vectors[c][sig], w, spec.port_constraints.get(sig))
                out.append(f"{_INDENT}dut.{styled(sig)}.value = {val}")
        if c in checks_by_cycle:
            out.append(f'{_INDENT}await Timer({_SETTLE_NS}, units="ns")')
            for chk in checks_by_cycle[c]:
                net = styled(chk.signal)
                out.append(
                    f"{_INDENT}assert dut.{net}.value == {chk.expected}, ("
                )
                # Split across two f-strings so the emitted line stays inside
                # the project's 100-column limit. A single line held up for
                # every module because their expected values are small; a
                # 32- or 64-bit register value pushed it over, and ruff — which
                # lints the committed cocotb goldens and is the only thing
                # checking that generated *Python* is clean — flagged it.
                out.append(
                    f'{_INDENT * 2}f"SMOKE FAIL: {net} at cycle {chk.cycle} '
                    f'expected {chk.expected}, "'
                )
                out.append(f'{_INDENT * 2}f"got {{int(dut.{net}.value)}}"')
                out.append(f"{_INDENT})")
    if pending:
        # Trailing idle cycles still advance time, matching the SV TB.
        out.append(f"{_INDENT}for _ in range({pending}):")
        out.append(f"{_INDENT * 2}await FallingEdge(dut.{clk})")

    out.append("")
    # Same marker the sim runner greps for, so pass semantics are shared.
    out.append(f'{_INDENT}dut._log.info("SMOKE PASS: {rtl_module.name}")')
    out.append("")
    triggers = sorted(
        name
        for name in ("FallingEdge", "RisingEdge", "Timer")
        if any(re.search(rf"\b{name}\(", line) for line in out)
    )
    header = [*_banner(rtl_module), "", "import cocotb", "from cocotb.clock import Clock"]
    if triggers:
        header.append(f"from cocotb.triggers import {', '.join(triggers)}")
    header.extend(("", ""))
    # No trailing "\n" here: the body's last element is already an empty
    # string, so the join supplies exactly one final newline. Adding another
    # would rewrite every committed cocotb golden for no reason.
    return "\n".join([*header, *out])
