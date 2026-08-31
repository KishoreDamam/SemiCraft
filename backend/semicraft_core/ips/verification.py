"""Per-IP verification scaffolds, bound to the DUT (Phase-4 P4-09).

P3-06 built a monitor/checker/scoreboard generator and landed it standalone:
"Not wired into ``generate_files`` — like P3-05, this lands standalone." It
stayed that way through all of Phase 4, compile-gated and unattached, which
made it exactly the kind of artifact this project keeps finding and killing —
one that exists, passes its own tests, and verifies nothing. This module
attaches it.

What "attached" has to mean
---------------------------

Emitting a checker file next to the RTL would not be enough: a file nobody
compiles is no better than a file nobody generates. The bar is that a scaffold
**fails a broken DUT**, which needs three things to hold at once:

1. the scaffold is instantiated against the DUT (via ``bind`` — see
   :mod:`semicraft_core.checkers.bind` for why that rather than a testbench
   change);
2. the simulator treats its ``$error`` as fatal — Verilator turns ``$error``
   into an implicit ``$stop`` and aborts with a non-zero status, so
   :func:`~semicraft_core.sim.run_smoke` reports ``fail``; and
3. something actually breaks the DUT and observes the failure.

The third is the run gate's mutation half. Without it the first two are
assumptions.

What the AXI4-Lite scaffold checks
----------------------------------

Deliberately *not* the reset values and field semantics the directed testbench
and its SVA already cover. The scaffold's job is the properties a directed
vector sequence structurally cannot check, because a directed sequence only
ever observes the cycles it was written to observe:

- **Liveness.** Every ``awvalid`` is followed by ``bvalid``, and every
  ``arvalid`` by ``rvalid``, within a bounded number of cycles. Nothing else in
  the project checks that a transaction *completes*; the directed checks read
  the response at a cycle they already assume it arrives on, so a target that
  simply stopped responding would fail with a wrong-value message that says
  nothing about liveness — or, on a cycle nobody checks, not fail at all.
- **Read-data stability.** ``rdata``/``rresp`` do not move on cycles when no
  read was accepted. A directed read samples one cycle and never looks again,
  so a target that spuriously rewrote its read register between transactions
  would go unnoticed.

``max_cycles`` is slack (16) rather than tight, on purpose. The check arms on
``awvalid``/``arvalid``, not on the handshake, because a handshake is an
expression and only bare identifiers survive restyling (see
:mod:`semicraft_core.checkers.restyle`). Arming on ``valid`` means a master
legitimately stalled behind an outstanding response would also be counted, so
the bound must be loose enough not to punish one. It is a hang detector, and a
hang is unbounded — 16 catches it exactly as well as 4 would.

No scoreboard here
------------------

An expected-value scoreboard needs a model of what the *next* value should be.
For an AXI register block that model is
:class:`~.regblock.RegisterModel`, which lives in Python and drives the
directed testbench — there is nothing to compare against inside the DUT's own
scope, and pushing a hardware-derived "expected" value would only compare the
design against itself. A scoreboard belongs where the ordering is the property:
a FIFO, where data out must equal data in, in order. That is recorded as the
next place to use it rather than faked here.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

from ..checkers.bind import BindSpec, generate_bind
from ..checkers.generate import (
    generate_checker,
    generate_monitor,
    generate_scoreboard,
)
from ..checkers.restyle import (
    is_identifier,
    restyle_checker,
    restyle_monitor,
    restyle_scoreboard,
)
from ..checkers.spec import (
    CheckerSpec,
    LatencyCheck,
    MonitorSpec,
    ResetPolarity,
    ScoreboardSpec,
    Signal,
    StabilityCheck,
)
from .contract import IpContractError
from .regblock import AXI_CLOCK, AXI_RESET

__all__ = [
    "VerificationSpec",
    "axil_verification",
    "read_port_verification",
    "check_spec_is_restylable",
    "render_verification",
    "verification_filename",
]

# Slack, not a tight bound: see the module docstring.
AXI_RESPONSE_MAX_CYCLES = 16


@dataclass(frozen=True, slots=True)
class VerificationSpec:
    """The scaffolds one IP binds into itself.

    Every member is optional so an IP can attach only what it can honestly
    check. ``monitors`` is a sequence rather than a single spec because one
    monitor per channel — each with a bare-identifier qualifier — is both more
    readable and more restylable than one monitor gated on an expression.
    """

    monitors: tuple[MonitorSpec, ...] = ()
    checker: CheckerSpec | None = None
    scoreboard: ScoreboardSpec | None = None
    # Instance names are part of the generated output, so they are pinned here
    # rather than derived, keeping goldens stable if the renderer changes.
    instance_prefix: str = field(default="u_")


def verification_filename(module_name: str) -> str:
    """The scaffold file's name: ``<module>_checks.sv``."""
    return f"{module_name}_checks.sv"


# --------------------------------------------------------------------------- #
# The shared AXI4-Lite scaffold
# --------------------------------------------------------------------------- #


def axil_verification(module_name: str, *, data_width: int = 32) -> VerificationSpec:
    """Monitor + checker for any IP with an AXI4-Lite target port.

    Shared by every AXI IP in the catalog rather than written seven times: they
    all splice in the same register-block frontend, so they have the same bus
    face and therefore the same bus properties. An IP with extra properties of
    its own composes this with additional checks; none needs to today.

    Names are **canonical** — ``areset``, not ``areset_n``. The render style is
    applied by :func:`render_verification`, exactly as ``tb_spec`` recipes are
    restyled before the testbench is emitted.
    """
    write_monitor = MonitorSpec(
        name=f"{module_name}_wr_monitor",
        clock=AXI_CLOCK,
        fields=[Signal("bvalid"), Signal("bresp", 2)],
        qualifier="bvalid",
    )
    read_monitor = MonitorSpec(
        name=f"{module_name}_rd_monitor",
        clock=AXI_CLOCK,
        fields=[Signal("rvalid"), Signal("rdata", data_width), Signal("rresp", 2)],
        qualifier="rvalid",
    )
    checker = CheckerSpec(
        name=f"{module_name}_axil_checker",
        clock=AXI_CLOCK,
        reset=ResetPolarity(signal=AXI_RESET, active_low=True),
        ports=[
            Signal("awvalid"),
            Signal("bvalid"),
            Signal("arvalid"),
            Signal("rvalid"),
            Signal("rdata", data_width),
            Signal("rresp", 2),
        ],
        checks=[
            LatencyCheck(
                name="write_response_arrives",
                request="awvalid",
                response="bvalid",
                max_cycles=AXI_RESPONSE_MAX_CYCLES,
            ),
            LatencyCheck(
                name="read_data_arrives",
                request="arvalid",
                response="rvalid",
                max_cycles=AXI_RESPONSE_MAX_CYCLES,
            ),
            StabilityCheck(
                name="rdata_holds_between_reads",
                signal="rdata",
                enable="arvalid",
                width=data_width,
            ),
            StabilityCheck(
                name="rresp_holds_between_reads",
                signal="rresp",
                enable="arvalid",
                width=2,
            ),
        ],
    )
    return VerificationSpec(monitors=(write_monitor, read_monitor), checker=checker)


def read_port_verification(
    module_name: str,
    *,
    clock: str,
    data: str,
    enable: str,
    data_width: int,
    reset: ResetPolarity | None = None,
) -> VerificationSpec:
    """Monitor + read-hold checker for a memory-style IP.

    The FIFO and the RAM both register their read data behind an enable
    (``if (rd_en && !empty) rd_data <= ...``, ``if (re) dout <= ...``), so
    "read data does not move while the enable is low" is a real property of
    both — and one a directed testbench cannot see, because it samples the read
    data on the cycles it expects a value and never looks between them. A
    read register that forgot its enable would still return the right word on
    every directed read; it would just also follow the address around in
    between, burning power and breaking the hold semantics the datasheet
    promises.

    That is the whole scaffold for these two. There is no liveness check
    because there is no handshake to be live about: a read is unconditional and
    answers next cycle by construction.
    """
    monitor = MonitorSpec(
        name=f"{module_name}_rd_monitor",
        clock=clock,
        fields=[Signal(enable), Signal(data, data_width)],
        qualifier=enable,
    )
    checker = CheckerSpec(
        name=f"{module_name}_rd_checker",
        clock=clock,
        reset=reset,
        ports=[Signal(enable), Signal(data, data_width)],
        checks=[
            StabilityCheck(
                name="read_data_holds_between_reads",
                signal=data,
                enable=enable,
                width=data_width,
            )
        ],
    )
    return VerificationSpec(monitors=(monitor,), checker=checker)


# --------------------------------------------------------------------------- #
# Validation
# --------------------------------------------------------------------------- #


def _opaque_fields(spec: VerificationSpec) -> list[tuple[str, str, str]]:
    """Every ``(owner, field, text)`` the restyler can only rename verbatim."""
    out: list[tuple[str, str, str]] = []
    for mon in spec.monitors:
        if mon.qualifier is not None:
            out.append((mon.name, "qualifier", mon.qualifier))
    if spec.checker is not None:
        for check in spec.checker.checks:
            if isinstance(check, StabilityCheck):
                out.append((check.name, "enable", check.enable))
            elif isinstance(check, LatencyCheck):
                out.append((check.name, "request", check.request))
                out.append((check.name, "response", check.response))
    if spec.scoreboard is not None and spec.scoreboard.wrapper is not None:
        wrapper = spec.scoreboard.wrapper
        out.append((wrapper.module_name, "push_expr", wrapper.push_expr))
        out.append((wrapper.module_name, "compare_expr", wrapper.compare_expr))
    return out


def check_spec_is_restylable(spec: VerificationSpec) -> None:
    """Reject a spec whose opaque fields would survive restyling unchanged.

    :mod:`~semicraft_core.checkers.restyle` renames an opaque field only when
    it is a bare identifier, because renaming inside real expression text would
    mean parsing SystemVerilog. That is a documented limitation, and this guard
    is what keeps it from being reachable by accident: a catalog IP that wrote
    ``"awvalid && awready"`` would bind against identifiers that do not exist
    under any non-default naming style, and would do so *silently* — the file
    still generates, and only a simulation under that style would notice.

    Raises :class:`~.contract.IpContractError` naming the offending field.
    """
    for owner, name, text in _opaque_fields(spec):
        if not is_identifier(text):
            raise IpContractError(
                f"verification spec {owner!r}: {name}={text!r} is an expression, "
                f"not a bare signal name. Only bare identifiers are renamed "
                f"through the render style, so this would reference undefined "
                f"nets under any non-default naming convention. Split the "
                f"expression into a check that names one signal, or add the "
                f"combination as a signal on the DUT."
            )


# --------------------------------------------------------------------------- #
# Rendering
# --------------------------------------------------------------------------- #


def _bind_ports_for_monitor(spec: MonitorSpec) -> tuple[str, ...]:
    return (spec.clock, *(f.name for f in spec.fields))


def _bind_ports_for_checker(spec: CheckerSpec) -> tuple[str, ...]:
    names = [spec.clock]
    if spec.reset is not None:
        names.append(spec.reset.signal)
    names += [p.name for p in spec.ports]
    return tuple(names)


def _bind_ports_for_wrapper(spec: ScoreboardSpec) -> tuple[str, ...]:
    assert spec.wrapper is not None
    wrapper = spec.wrapper
    return (
        wrapper.clock,
        wrapper.push_signal,
        wrapper.compare_signal,
        *(p.name for p in wrapper.ports),
    )


_BANNER = (
    "// Verification scaffolds for {dut}, generated by SemiCraft (P4-09).\n"
    "//\n"
    "// Simulation only: these modules drive nothing and are attached with\n"
    "// SystemVerilog `bind`, so adding this file to a compile changes no\n"
    "// synthesised logic and needs no edit to the design or the testbench.\n"
    "// Compile it alongside {dut}.sv and the checks attach themselves.\n"
)


def render_verification(
    spec: VerificationSpec, dut_module: str, rename: Callable[[str], str]
) -> str:
    """Render the complete ``<module>_checks.sv`` text for one IP (pure).

    ``rename`` is the render style's canonical-to-styled name map, the same one
    the RTL and the testbench use, so every scaffold port and every ``bind``
    connection resolves to a net that actually exists in the rendered DUT.

    Returns ``""`` for a spec with nothing in it, so a caller can emit the file
    unconditionally and get no file when there is nothing to say.
    """
    check_spec_is_restylable(spec)

    monitors = tuple(restyle_monitor(m, rename) for m in spec.monitors)
    checker = None if spec.checker is None else restyle_checker(spec.checker, rename)
    scoreboard = (
        None if spec.scoreboard is None else restyle_scoreboard(spec.scoreboard, rename)
    )
    if not monitors and checker is None and scoreboard is None:
        return ""

    parts: list[str] = [_BANNER.format(dut=dut_module)]
    binds: list[str] = []

    for mon in monitors:
        parts.append(generate_monitor(mon))
        binds.append(
            generate_bind(
                BindSpec(
                    target=dut_module,
                    scaffold=mon.name,
                    instance=f"{spec.instance_prefix}{mon.name}",
                    ports=_bind_ports_for_monitor(mon),
                )
            )
        )

    if checker is not None:
        parts.append(generate_checker(checker))
        binds.append(
            generate_bind(
                BindSpec(
                    target=dut_module,
                    scaffold=checker.name,
                    instance=f"{spec.instance_prefix}{checker.name}",
                    ports=_bind_ports_for_checker(checker),
                )
            )
        )

    if scoreboard is not None:
        parts.append(generate_scoreboard(scoreboard))
        if scoreboard.wrapper is not None:
            binds.append(
                generate_bind(
                    BindSpec(
                        target=dut_module,
                        scaffold=scoreboard.wrapper.module_name,
                        instance=f"{spec.instance_prefix}{scoreboard.wrapper.module_name}",
                        ports=_bind_ports_for_wrapper(scoreboard),
                    )
                )
            )

    parts.append(
        "// Attach the scaffolds. `bind` connects to nets resolved in the DUT's\n"
        "// own scope, which is why every port above is named after one.\n"
        + "\n".join(binds)
    )
    return "\n".join(parts)
