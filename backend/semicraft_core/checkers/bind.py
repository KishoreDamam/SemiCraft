"""SystemVerilog ``bind`` emission for verification scaffolds (P4-09).

P3-06 emits monitor/checker/scoreboard **modules** but says nothing about how
they reach a DUT. This module supplies the missing half, and the choice of
mechanism is the whole point of it.

Why ``bind`` and not a testbench instantiation
----------------------------------------------

The obvious route is to instantiate each scaffold inside the generated
testbench, which means teaching ``TbSpec``/``TbModule``/``render_tb`` about a
new kind of child instance — a change to a frozen contract (TB_SPEC) rippling
through the validator, the renderer and the cocotb backend, all so a checker
can see nets the DUT already exposes.

``bind`` needs none of it. The statement lives in the scaffold's own file, names
the DUT module by name, and connects to identifiers resolved in the *DUT's*
scope, so:

- no testbench, TB node, or TB_SPEC change — the generated TB is byte-identical
  with or without a scaffold;
- the scaffold file is self-contained and reusable: a user drops it into their
  own bench and the checks attach themselves;
- it is what verification engineers already write, so the output reads as
  idiomatic rather than as something a generator invented.

The cost is that ``bind`` is SystemVerilog-only, so a Verilog-2001 build gets
no scaffold. That is not a real loss — the checks are simulation artifacts and
the smoke TB is SystemVerilog either way — but it is why
``generate_files`` emits the file only for an ``sv`` build.

Connections are positional-by-name (``.clk(clk)``) because a scaffold's ports
are generated *from* the DUT's own signal names, already styled. Matching names
on both sides is not a coincidence to be tolerated; it is the invariant that
makes the bind trivially correct, and
:func:`~semicraft_core.ips.verification.render_verification` is what maintains
it.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

__all__ = ["BindSpec", "generate_bind"]


@dataclass(frozen=True, slots=True)
class BindSpec:
    """One ``bind`` statement: attach ``scaffold`` inside every ``target``.

    - ``target`` — the DUT module name to bind into.
    - ``scaffold`` — the scaffold module name to instantiate.
    - ``instance`` — the instance name given to it inside the DUT.
    - ``ports`` — scaffold port names, each connected to the DUT-scope net of
      the *same* name, in declaration order.
    """

    target: str
    scaffold: str
    instance: str
    ports: tuple[str, ...]

    def __init__(
        self, target: str, scaffold: str, instance: str, ports: Sequence[str]
    ) -> None:
        object.__setattr__(self, "target", target)
        object.__setattr__(self, "scaffold", scaffold)
        object.__setattr__(self, "instance", instance)
        object.__setattr__(self, "ports", tuple(ports))


def generate_bind(spec: BindSpec) -> str:
    """Emit one ``bind`` statement as SystemVerilog text (pure).

    Raises :class:`ValueError` on an empty port list — a scaffold with no
    connections would compile and check nothing, which is the failure mode this
    whole work package exists to prevent.
    """
    if not spec.ports:
        raise ValueError(
            f"bind of {spec.scaffold!r} into {spec.target!r} lists no ports; a "
            f"scaffold connected to nothing compiles and checks nothing"
        )
    lines = [f"bind {spec.target} {spec.scaffold} {spec.instance} ("]
    for i, port in enumerate(spec.ports):
        comma = "," if i < len(spec.ports) - 1 else ""
        lines.append(f"    .{port}({port}){comma}")
    lines.append(");")
    return "\n".join(lines) + "\n"
