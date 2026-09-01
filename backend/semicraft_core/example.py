"""Compilable example instantiations for an IP (Phase-4 P4-11).

An example in a datasheet that nobody compiles is the same failure this project
keeps finding: an artifact that exists, looks authoritative, and is never
checked. A wrong port name or a stale signal in a copy-pasteable snippet is
worse than no snippet at all, because a reader trusts it.

So the example is emitted as a **real ``.sv``/``.v`` file**, not a fenced block
in the markdown, and the golden gate lints it with ``verilator --lint-only
-Wall`` against the IP it instantiates. If a port is renamed, dropped, or
retyped, the example stops linting and CI goes red — the same bar every other
generated artifact in this project has to clear.

What it is, and what it is not
------------------------------

It is a wrapper module that exposes the IP's ports as its own and instantiates
the IP, with the connections **grouped and commented from the IP's own
metadata** — ``port_groups(opts)`` for the grouping, ``bundles(opts)`` for the
protocol and role annotation. That grouping is the documentation value: it says
which nine signals form one AXI4-Lite target port and which three are pads,
which is exactly what a reader has to work out before wiring anything.

It is not an integration example. The wrapper passes every port straight
through, because that is the only shape that is both derivable from metadata
and lint-clean for every IP in the catalog. A reader replaces the wrapper's
ports with their own logic; what the file guarantees is that the *instantiation*
— names, widths, directions — is correct and compiles today.

Text, not IR — and deliberately temporary
-----------------------------------------

The synthesizable IR has no module-instance node, so this emits SystemVerilog
text directly, the same way :mod:`semicraft_core.checkers.generate` does.

That is a stopgap and should be recorded as one. **Phase 5's subsystem
generator needs real instantiation in the IR** — it wires groups of IPs into a
top wrapper, which is instantiation as a first-class construct, not as printed
text. When that node lands (an IR_SPEC change, so a recorded decision), this
emitter should be rewritten on top of it rather than left to drift as a second,
parallel way of writing the same construct.
"""

from __future__ import annotations

import textwrap
from collections.abc import Callable

from .ir.nodes import Module, PortDir
from .license import DISCLAIMER
from .modules.contract import PortGroup
from .version import VERSION

__all__ = ["example_filename", "example_module", "ungrouped_ports"]

# Matches render.base._WRAP_WIDTH so the example's banner wraps identically to
# the RTL's.
_WRAP_WIDTH = 74


def example_filename(module_name: str, language: str) -> str:
    """``<module>_example.sv`` / ``.v``, matching the RTL's language."""
    return f"{module_name}_example.{'sv' if language == 'sv' else 'v'}"


def _net_type(language: str) -> str:
    """The wrapper's nets.

    Verilog-2001 needs ``wire`` on both directions: every port here is driven by
    the instance or drives it, so nothing is procedurally assigned and nothing
    may be ``reg`` — unlike the DUT itself, whose registered outputs are.
    """
    return "logic" if language == "sv" else "wire"


def _range(width: int) -> str:
    return f"[{width - 1}:0]" if width > 1 else ""


def _bundle_note(group: PortGroup, bundles) -> str:
    """``(bundle `s_axil`, axi4-lite target)`` when a group *is* a bundle."""
    ports = set(group.ports)
    for bundle in bundles:
        if ports and ports <= {p.signal for p in bundle.ports}:
            return f" (bundle `{bundle.name}`, {bundle.protocol} {bundle.role})"
    return ""


def example_module(
    rtl_module: Module,
    port_groups: list[PortGroup],
    bundles,
    widths: dict[str, int],
    rename: Callable[[str], str],
    *,
    language: str,
    config_hash_value: str,
    description: str,
) -> str:
    """Render the example wrapper as HDL text (pure).

    ``port_groups``/``bundles`` are the IP's own metadata, already restyled by
    the caller, so the grouping comments name the ports the RTL declares.

    Every port of ``rtl_module`` appears exactly once: ports the metadata does
    not group are emitted last under an explicit heading rather than dropped,
    because a silently missing connection is the one failure mode a
    pass-through wrapper can still have. :func:`ungrouped_ports` lets a test
    assert the catalog never reaches that path.
    """
    net = _net_type(language)
    name = f"{rtl_module.name}_example"
    styled = [(rename(p.name), p) for p in rtl_module.ports]
    width_of = {rename(p.name): widths.get(p.name, 1) for p in rtl_module.ports}

    dir_width = max(len("output"), 5)
    name_width = max((len(n) for n, _ in styled), default=1)
    range_width = max((len(_range(width_of[n])) for n, _ in styled), default=0)

    lines = [
        f"// SemiCraft v{VERSION}",
        f"// Example instantiation: {rtl_module.name} (config hash: {config_hash_value})",
        f"// {description}",
        "//",
        "// A compiling starting point, not an integration example: this wrapper",
        "// passes every port straight through. Replace its ports with your own",
        "// logic; what is guaranteed here is that the instantiation below is",
        "// correct for this configuration and lints clean against the IP.",
        "//",
        # Wrapped at the same width the RTL renderer uses, so the two banners
        # read as one family rather than two.
        *(f"// {line}" for line in textwrap.wrap(DISCLAIMER, width=_WRAP_WIDTH)),
        "",
        f"module {name} (",
    ]

    decls = []
    for styled_name, port in styled:
        direction = "input " if port.dir == PortDir.INPUT else "output"
        rng = _range(width_of[styled_name]).ljust(range_width)
        decls.append(
            f"    {direction.ljust(dir_width)} {net} {rng} {styled_name}".rstrip()
        )
    lines.append(",\n".join(decls))
    lines.append(");")
    lines.append("")

    conn_width = name_width
    lines.append(f"    {rtl_module.name} u_{rtl_module.name} (")

    emitted: set[str] = set()
    body: list[str] = []
    for group in port_groups:
        members = [n for n in group.ports if n in width_of and n not in emitted]
        if not members:
            continue
        body.append(f"        // {group.name}{_bundle_note(group, bundles)}")
        for member in members:
            body.append(f"        .{member.ljust(conn_width)} ({member}),")
            emitted.add(member)

    leftover = [n for n, _ in styled if n not in emitted]
    if leftover:
        body.append("        // Ports the IP's metadata does not place in a group")
        for member in leftover:
            body.append(f"        .{member.ljust(conn_width)} ({member}),")

    if body:
        body[-1] = body[-1].rstrip(",")
    lines.extend(body)
    lines.append("    );")
    lines.append("")
    lines.append("endmodule")
    lines.append("")
    return "\n".join(lines)


def ungrouped_ports(rtl_module: Module, port_groups: list[PortGroup]) -> list[str]:
    """Canonical port names no ``port_groups`` entry mentions.

    Resolves each declared name through the same reset-suffix convention the
    datasheet uses (``generate.resolve_doc_port_name``): ``port_groups`` lists
    canonical names except for an active-low reset, which the metadata already
    suffixes with ``_n``.

    Exposed so a test can assert the catalog keeps this empty: the emitter
    handles leftovers rather than dropping them, but an IP reaching that path
    means its ``port_groups`` metadata has fallen behind its ports, and the
    datasheet's port table would be incomplete too.
    """
    from .generate import resolve_doc_port_name

    canonical = {p.name for p in rtl_module.ports}
    grouped = {
        resolve_doc_port_name(name, canonical, lambda n: n)
        for group in port_groups
        for name in group.ports
    }
    return [p.name for p in rtl_module.ports if p.name not in grouped]
