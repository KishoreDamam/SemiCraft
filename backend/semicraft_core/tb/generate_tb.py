"""Build a smoke testbench from a module's ``TbSpec`` and its rendered RTL.

Public seam::

    generate_tb(module_def, opts, rtl_module) -> str

``rtl_module`` is the *stamped* IR :class:`~..ir.nodes.Module` the RTL file was
rendered from (header carries the config hash / disclaimer / tool version). This
is the correctness anchor: the testbench resolves every port/net name through the
**same** style name map the RTL renderer used (:func:`build_name_map`), so an
active-low reset that renders ``rst_n`` in the RTL is driven as ``rst_n`` here,
and a parameterised port width resolves to the same concrete width the DUT's
default parameters give. Names and widths therefore match the rendered RTL exactly
(the trap called out in the P2-13 brief).

Timing model (documented in docs/TB_SPEC.md):

- The clock is free-running (``#5`` half period). Reset is asserted from time 0,
  held ``reset_cycles`` rising edges, then deasserted.
- Each directed *cycle* ``c`` is anchored to a falling edge: on that ``negedge``
  the cycle's input vector is driven and (after a ``#1`` settle) the cycle's
  checks sample the DUT. Because inputs are driven on the falling edge, they are
  stable well before the next rising edge samples them (no drive/sample race);
  and because checks read after the settle, a sampled net reflects the registered
  state from prior rising edges plus the just-driven combinational inputs — which
  is exactly the convention the per-module ``TbSpec`` cycle indices assume.

Modules whose options produce no clock (``TbSpec.clock is None``) get no smoke
testbench: :func:`generate_tb` returns ``""`` and the caller emits no ``tb`` file.
"""

from __future__ import annotations

import textwrap

from ..ir.nodes import (
    AlwaysFF,
    BinOp,
    BinOpKind,
    Const,
    DataType,
    Expr,
    GenFor,
    Module,
    Ref,
    ResetSpec,
)
from ..license import DISCLAIMER
from ..render.style import StyleOptions, build_name_map
from .nodes import (
    AssertProperty,
    ClockGen,
    Decl,
    Delay,
    Display,
    DriveSignal,
    DutInstance,
    ExpectSignal,
    Finish,
    Initial,
    Stmt,
    TbComment,
    TbModule,
    TimeoutGuard,
    WaitCycles,
)
from .render_tb import render_tb

# Header disclaimer wrap width — matches the RTL banner (render/base.py).
_WRAP_WIDTH = 74
_DUT_INSTANCE = "dut"
_SETTLE_NS = 1

# Watchdog budget: the TimeoutGuard counts posedge clk while the stimulus runs.
# A healthy run reaches ``$finish`` in roughly ``reset_cycles + n_cycles`` rising
# edges, so the guard is set to that total scaled by _TIMEOUT_SLACK (plus a fixed
# floor) — comfortably beyond the longest healthy run, firing only if a hung DUT
# stalls the stimulus process. Must never trip on a passing TB (CI run gate).
_TIMEOUT_SLACK = 8
_TIMEOUT_FLOOR = 16


def _constrain_value(value: int, width: int, constraint) -> int:
    """Fit a stimulus ``value`` to its port: clamp to any declared bounds, then
    mask to the resolved port ``width``.

    ``constraint`` is the port's :class:`~..modules.contract.PortConstraint` or
    ``None``. With no constraint the value is only width-masked; because every
    module's existing vectors already fit their port width, masking is a no-op
    for them (byte-identical output). The mask is the safety net that keeps a
    driven literal from ever exceeding the net it feeds.
    """
    if constraint is not None:
        if constraint.min_value is not None and value < constraint.min_value:
            value = constraint.min_value
        if constraint.max_value is not None and value > constraint.max_value:
            value = constraint.max_value
    if width >= 1:
        value &= (1 << width) - 1
    return value


def _style_from_options(opts) -> StyleOptions:
    """Derive render :class:`StyleOptions` from validated options.

    Kept in step with ``semicraft_core.generate._style_from_options`` so the TB
    name map is byte-identical to the one the RTL renderer built.
    """
    naming = opts.naming
    return StyleOptions(
        naming=naming.convention,
        prefix=naming.prefix,
        suffix=naming.suffix,
        comment_verbosity=opts.comment_verbosity,
    )


def _param_values(module: Module) -> dict[str, int]:
    """Concrete default value of each module parameter (for width resolution)."""
    return {p.name: _eval_int(p.default, {}) for p in module.params}


def _eval_int(expr: Expr, params: dict[str, int]) -> int:
    """Evaluate a (structural) width expression to a concrete integer.

    Handles the forms module generators actually produce for port widths:
    literal ``Const``, a parameter ``Ref``, and ``+``/``-``/``*`` ``BinOp``s over
    them. Anything else is a generator using a construct the smoke-TB stub does
    not model — surfaced as an error rather than a silently wrong width.
    """
    if isinstance(expr, Const):
        return expr.value
    if isinstance(expr, Ref):
        if expr.name not in params:
            raise ValueError(f"cannot resolve width parameter {expr.name!r} for smoke TB")
        return params[expr.name]
    if isinstance(expr, BinOp):
        a = _eval_int(expr.a, params)
        b = _eval_int(expr.b, params)
        if expr.op is BinOpKind.ADD:
            return a + b
        if expr.op is BinOpKind.SUB:
            return a - b
        if expr.op is BinOpKind.MUL:
            return a * b
    raise ValueError(f"unsupported width expression for smoke TB: {expr!r}")


def _width_of(dtype: DataType, params: dict[str, int]) -> int:
    """Concrete bit width of a port ``DataType`` (scalar -> 1)."""
    if dtype.width is None:
        return 1
    return _eval_int(dtype.width, params)


def _find_reset(module: Module, canonical_reset: str) -> ResetSpec | None:
    """The ``ResetSpec`` for ``canonical_reset``, scanning clocked processes
    (including those nested in a ``GenFor``)."""
    ffs: list[AlwaysFF] = []
    for item in module.items:
        if isinstance(item, AlwaysFF):
            ffs.append(item)
        elif isinstance(item, GenFor):
            ffs.extend(i for i in item.items if isinstance(i, AlwaysFF))
    for ff in ffs:
        if ff.reset is not None and ff.reset.name == canonical_reset:
            return ff.reset
    return None


def _banner(module: Module) -> tuple[str, ...]:
    """Header comment lines mirroring the RTL banner (config hash + disclaimer)."""
    h = module.header
    lines = [
        f"// SemiCraft v{h.tool_version}",
        f"// Testbench: {module.name}_tb (config hash: {h.config_hash})",
        f"// Smoke testbench (stub, compile-checked only) for {module.name}",
        "//",
    ]
    for line in textwrap.wrap(h.license or DISCLAIMER, width=_WRAP_WIDTH):
        lines.append(f"// {line}")
    return tuple(lines)


def generate_tb(module_def, opts, rtl_module: Module) -> str:
    """Render the smoke testbench for ``module_def``/``opts`` as SV text.

    Returns ``""`` when the module has no clock (no smoke TB is applicable).
    """
    spec = module_def.tb_spec(opts)
    if spec.clock is None:
        return ""

    style = _style_from_options(opts)
    names = build_name_map(rtl_module, style)

    def styled(canonical: str) -> str:
        return names.get(canonical, canonical)

    params = _param_values(rtl_module)
    ports = list(rtl_module.ports)
    width_of = {p.name: _width_of(p.dtype, params) for p in ports}

    clk_net = styled(spec.clock)
    input_names = {p.name for p in ports if p.dir.value == "input"}

    # --- net declarations + DUT connections (one net per port, port order) ----
    decls = tuple(Decl(name=styled(p.name), width=width_of[p.name]) for p in ports)
    connections = tuple((styled(p.name), styled(p.name)) for p in ports)
    dut = DutInstance(module=rtl_module.name, instance=_DUT_INSTANCE, connections=connections)

    # --- reset polarity (assert/deassert levels) ------------------------------
    reset_net: str | None = None
    reset_assert = reset_deassert = 0
    if spec.reset is not None:
        rspec = _find_reset(rtl_module, spec.reset)
        active_low = rspec.active_low if rspec is not None else False
        reset_net = styled(spec.reset)
        reset_assert = 0 if active_low else 1
        reset_deassert = 1 if active_low else 0

    stmts: list[Stmt] = []

    # Directed cycles: drive vectors on the falling edge, check after settle.
    max_check_cycle = max((c.cycle for c in spec.checks), default=-1)
    n_cycles = max(len(spec.vectors), max_check_cycle + 1)

    # Watchdog first, so it covers the whole run (init + reset + directed
    # cycles). A hung DUT now fails loudly instead of stalling the simulator;
    # the budget scales with the TB length so it never fires on a healthy run.
    timeout_cycles = (spec.reset_cycles + n_cycles + _TIMEOUT_FLOOR) * _TIMEOUT_SLACK
    stmts.append(TbComment("Watchdog: fail loudly if the run hangs"))
    stmts.append(
        TimeoutGuard(
            cycles=timeout_cycles,
            message=f"TIMEOUT: {rtl_module.name}_tb exceeded {timeout_cycles} cycles",
        )
    )

    # Initialise every driven input to 0, then assert reset.
    stmts.append(TbComment("Initialise inputs and assert reset"))
    for p in ports:
        if p.name in input_names and p.name != spec.clock and p.name != spec.reset:
            stmts.append(DriveSignal(styled(p.name), 0, width_of[p.name]))
    if reset_net is not None:
        stmts.append(DriveSignal(reset_net, reset_assert, 1))
        stmts.append(WaitCycles(spec.reset_cycles, "posedge"))
        stmts.append(DriveSignal(reset_net, reset_deassert, 1))

    # Directed cycles: drive vectors on the falling edge, check after settle.
    checks_by_cycle: dict[int, list] = {}
    for chk in spec.checks:
        checks_by_cycle.setdefault(chk.cycle, []).append(chk)

    if n_cycles:
        stmts.append(TbComment("Apply directed vectors; sample checks on the falling edge"))
    # Coalesce runs of idle cycles (no drives, no checks) into a single
    # `repeat (N) @(negedge clk);` — a per-cycle statement is unreadable and
    # explodes compile time for cycle counts in the tens of thousands
    # (clock-divider at divide_by=65536 produced a 65k-line TB that timed out
    # the CI compile gate).
    pending_waits = 0
    for c in range(n_cycles):
        pending_waits += 1
        has_drives = c < len(spec.vectors) and bool(spec.vectors[c])
        if not has_drives and c not in checks_by_cycle:
            continue
        stmts.append(WaitCycles(pending_waits, "negedge"))
        pending_waits = 0
        if has_drives:
            for sig in sorted(spec.vectors[c]):
                w = width_of.get(sig, 1)
                val = _constrain_value(
                    spec.vectors[c][sig], w, spec.port_constraints.get(sig)
                )
                stmts.append(DriveSignal(styled(sig), val, w))
        if c in checks_by_cycle:
            stmts.append(Delay(_SETTLE_NS))
            for chk in checks_by_cycle[c]:
                w = width_of.get(chk.signal, 1)
                stmts.append(
                    ExpectSignal(styled(chk.signal), chk.expected, w, f"cycle {c}")
                )

    stmts.append(Display(f"SMOKE PASS: {rtl_module.name}"))
    stmts.append(Finish())

    # Optional concurrent SVA: emitted only when the module attaches an
    # assertion recipe to its TbSpec. No current module does, so this is inert
    # (asserts stays empty and the TB renders exactly as before, aside from the
    # watchdog). The recipe's signal names are taken verbatim — property text is
    # opaque (TB_SPEC §5), so naming-style transforms are not reapplied inside
    # it; a module attaching one is responsible for spelling the names to match
    # its rendered RTL.
    asserts: tuple[AssertProperty, ...] = ()
    if spec.assertion_spec is not None:
        # Lazy import: the assertions package pulls in the TB node family, so a
        # module-load-time import here would form a cycle
        # (contract -> assertions -> tb -> generate_tb). Importing at call time
        # keeps the package-load graph acyclic.
        from ..assertions.generate import generate_assertions

        asserts = generate_assertions(spec.assertion_spec)

    tb = TbModule(
        name=f"{rtl_module.name}_tb",
        decls=decls,
        clock=ClockGen(signal=clk_net),
        dut=dut,
        initial=Initial(tuple(stmts)),
        banner=_banner(rtl_module),
        asserts=asserts,
    )
    return render_tb(tb)


__all__ = ["generate_tb"]
