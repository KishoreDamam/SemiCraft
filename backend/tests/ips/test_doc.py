"""Datasheet sections rendered from IP metadata (P4-01)."""

from __future__ import annotations

from semicraft_core.ips.bundles import BundlePort, PortBundle
from semicraft_core.ips.doc import bundles_md, format_hex, register_map_md
from semicraft_core.ips.regmap import Register, RegisterField, RegisterMap

from .reference_ip import ReferenceIpOptions, register_map


def _md(lines: list[str]) -> str:
    return "\n".join(lines)


def test_format_hex_pads_to_the_declared_width() -> None:
    assert format_hex(1, 32) == "0x00000001"
    assert format_hex(1, 1) == "0x1"
    assert format_hex(0xAB, 8) == "0xAB"


def test_register_map_section_lists_every_register() -> None:
    text = _md(register_map_md(register_map(ReferenceIpOptions())))
    assert "## Register map" in text
    assert "| `0x00` | `CTRL` | `0x00000001` |" in text
    assert "| `0x04` | `STATUS` | `0x00000000` |" in text
    # Geometry line: decoded space, used span and stride all come from the model.
    assert "32-bit data, 4-bit byte address (16 B decoded, 8 B used), 4-byte stride" in text


def test_field_rows_are_most_significant_first() -> None:
    """Datasheet convention, and the one place this renderer reorders anything."""
    text = _md(register_map_md(register_map(ReferenceIpOptions())))
    assert text.index("`[2:1]` | `mode`") < text.index("`[0]` | `enable`")


def test_reserved_note_appears_only_when_bits_are_uncovered() -> None:
    note = "Bits not listed above are reserved"
    covered = RegisterMap(
        name="M",
        data_width=8,
        addr_width=4,
        registers=[
            Register(name="FULL", offset=0, fields=[RegisterField(name="all", lsb=0, width=8)])
        ],
    )
    assert note not in _md(register_map_md(covered))

    partial = RegisterMap(
        name="M",
        data_width=8,
        addr_width=4,
        registers=[
            Register(name="SOME", offset=0, fields=[RegisterField(name="bit", lsb=0)])
        ],
    )
    assert note in _md(register_map_md(partial))


def test_register_without_fields_says_so() -> None:
    m = RegisterMap(name="M", registers=[Register(name="DATA", offset=0)])
    text = _md(register_map_md(m))
    assert "No sub-fields: the register is a single opaque 32-bit value." in text


def test_empty_register_map_is_stated_not_omitted() -> None:
    text = _md(register_map_md(RegisterMap(name="M")))
    assert "This IP declares no registers." in text


def test_write_only_reset_reads_as_zero_in_the_summary() -> None:
    """The summary column is what software sees, so a WO reset shows as 0 —
    and the section says why rather than leaving it looking like a bug."""
    m = RegisterMap(
        name="M",
        registers=[
            Register(
                name="CMD",
                offset=0,
                fields=[RegisterField(name="go", lsb=0, access="wo", reset=1)],
            )
        ],
    )
    text = _md(register_map_md(m))
    assert "| `0x00` | `CMD` | `0x00000000` |" in text
    assert "so a write-only (WO) field contributes zero" in text


# --------------------------------------------------------------------------- #
# Bundles
# --------------------------------------------------------------------------- #


def _bundle(**kw) -> PortBundle:
    kw.setdefault("name", "s_csr")
    kw.setdefault("protocol", "native-csr")
    kw.setdefault("role", "target")
    kw.setdefault("ports", [BundlePort(signal="addr", role_name="addr")])
    return PortBundle(**kw)


def test_bundle_section_pairs_roles_with_ports_and_directions() -> None:
    text = _md(
        bundles_md(
            [
                _bundle(
                    ports=[
                        BundlePort(signal="addr", role_name="addr"),
                        BundlePort(signal="rdata", role_name="rdata"),
                    ],
                    clock="clk",
                    reset="rst_n",
                )
            ],
            {"addr": "input", "rdata": "output"},
        )
    )
    assert "### `s_csr` — `native-csr` target" in text
    assert "Timing: clocked by `clk`, reset by `rst_n`." in text
    assert "| `addr` | `addr` | input |" in text
    assert "| `rdata` | `rdata` | output |" in text


def test_bundle_section_states_that_no_sv_interface_is_emitted() -> None:
    """The scope decision is in the artifact, not only in the plan document."""
    text = _md(bundles_md([_bundle()], {"addr": "input"}))
    assert "No SystemVerilog `interface` construct is emitted." in text


def test_bundle_without_clock_omits_the_timing_line() -> None:
    text = _md(bundles_md([_bundle()], {"addr": "input"}))
    assert "Timing:" not in text


def test_empty_bundle_list_is_stated_not_omitted() -> None:
    assert "This IP declares no bus interfaces." in _md(bundles_md([], {}))
