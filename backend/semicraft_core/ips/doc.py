"""Datasheet sections for IP metadata (Phase-4 P4-01).

Two renderers that :func:`semicraft_core.generate.generate_files` appends to
an IP's markdown datasheet, after the port table the module path already
emits:

- :func:`register_map_md` — the software-visible register layout.
- :func:`bundles_md` — the bus-side port bundles.

Both take plain data and return a list of markdown lines, matching the style
of ``generate._md_port_table``. Pure and deterministic: the same metadata
renders byte-identically, and ordering comes from the model (which validates
that registers and fields are listed in ascending order) rather than from any
sorting done here.

Field rows are printed **most-significant first**, the datasheet convention,
which is the reverse of the ascending-``lsb`` order the model stores. That
one inversion is the only place this module reorders anything.
"""

from __future__ import annotations

from .bundles import PortBundle
from .regmap import Register, RegisterMap

__all__ = ["register_map_md", "bundles_md", "format_hex"]

_ACCESS_LABEL = {"rw": "RW", "ro": "RO", "wo": "WO", "w1c": "W1C"}


def format_hex(value: int, bits: int) -> str:
    """``value`` as a zero-padded hex literal wide enough for ``bits`` bits."""
    return f"0x{value:0{max(1, (bits + 3) // 4)}X}"


def _register_summary_row(reg: Register, data_width: int, addr_nibbles: int) -> str:
    return (
        f"| `0x{reg.offset:0{addr_nibbles}X}` | `{reg.name}` | "
        f"`{format_hex(reg.read_reset_value(), data_width)}` | {reg.description} |"
    )


def _register_detail(reg: Register, data_width: int, addr_nibbles: int) -> list[str]:
    lines = [f"### `{reg.name}` — offset `0x{reg.offset:0{addr_nibbles}X}`", ""]
    if reg.description:
        lines += [reg.description, ""]

    if not reg.fields:
        lines += [
            f"No sub-fields: the register is a single opaque {data_width}-bit value.",
            "",
        ]
        return lines

    lines += [
        "| Bits | Field | Access | Reset | Description |",
        "| --- | --- | --- | --- | --- |",
    ]
    for f in reversed(reg.fields):  # datasheet order: most-significant first
        lines.append(
            f"| `{f.bit_range}` | `{f.name}` | {_ACCESS_LABEL[f.access]} | "
            f"`{format_hex(f.reset, f.width)}` | {f.description} |"
        )
    lines.append("")
    if reg.reserved_mask(data_width):
        lines += [
            (
                "Bits not listed above are reserved and read as zero. What a "
                "write to them does is the register block's policy — see the "
                "IP's own documentation."
            ),
            "",
        ]
    return lines


def register_map_md(regmap: RegisterMap) -> list[str]:
    """Render the ``## Register map`` section for ``regmap``."""
    decoded = 1 << regmap.addr_width
    used = regmap.span_bytes()
    addr_nibbles = max(2, (regmap.addr_width + 3) // 4)

    lines = [
        "## Register map",
        "",
        (
            f"`{regmap.name}` — {regmap.data_width}-bit data, "
            f"{regmap.addr_width}-bit byte address ({decoded} B decoded, {used} B used), "
            f"{regmap.stride_bytes}-byte stride. Offsets are relative to the IP's "
            f"base address."
        ),
        "",
    ]

    if not regmap.registers:
        lines += ["This IP declares no registers.", ""]
        return lines

    lines += [
        "| Offset | Name | Reset | Description |",
        "| --- | --- | --- | --- |",
    ]
    lines += [
        _register_summary_row(reg, regmap.data_width, addr_nibbles)
        for reg in regmap.registers
    ]
    lines.append("")
    lines.append(
        "Reset values are as *software* reads them, so a write-only (WO) field "
        "contributes zero."
    )
    lines.append("")

    for reg in regmap.registers:
        lines += _register_detail(reg, regmap.data_width, addr_nibbles)
    return lines


def bundles_md(bundles: list[PortBundle], directions: dict[str, str]) -> list[str]:
    """Render the ``## Bus interfaces`` section.

    ``directions`` maps canonical port name -> ``"input"``/``"output"``, taken
    from the generated IR module so the table cannot disagree with the RTL.
    A port missing from ``directions`` is impossible once
    :func:`..contract.check_bundles_against_module` has run, which
    ``generate_files`` does before calling this.
    """
    lines = ["## Bus interfaces", ""]
    if not bundles:
        lines += ["This IP declares no bus interfaces.", ""]
        return lines

    lines += [
        (
            "Each bundle below is a *naming* grouping of ordinary flat ports — the "
            "generated RTL declares them individually, exactly as listed. No "
            "SystemVerilog `interface` construct is emitted."
        ),
        "",
    ]

    for bundle in bundles:
        lines.append(f"### `{bundle.name}` — `{bundle.protocol}` {bundle.role}")
        lines.append("")
        if bundle.description:
            lines += [bundle.description, ""]
        domain = []
        if bundle.clock:
            domain.append(f"clocked by `{bundle.clock}`")
        if bundle.reset:
            domain.append(f"reset by `{bundle.reset}`")
        if domain:
            lines += [f"Timing: {', '.join(domain)}.", ""]
        lines += [
            "| Protocol role | Port | Direction |",
            "| --- | --- | --- |",
        ]
        for p in bundle.ports:
            lines.append(
                f"| `{p.role_name}` | `{p.signal}` | {directions.get(p.signal, '')} |"
            )
        lines.append("")
    return lines
