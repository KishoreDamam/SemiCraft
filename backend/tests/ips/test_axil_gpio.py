"""AXI4-Lite GPIO: composition, register map, metadata (P4-05a)."""

from __future__ import annotations

import re as _re

import pytest
from semicraft_core.generate import generate_files
from semicraft_core.ips.axil_gpio import (
    IP,
    AxilGpioOptions,
    bundles,
    register_map,
    tb_spec,
)
from semicraft_core.ips.contract import IpDef, check_bundles_against_module
from semicraft_core.ips.regblock import axil_ports, build_axil_regblock, hardware_ports
from semicraft_core.render import StyleOptions, render


def _opts(**kw) -> AxilGpioOptions:
    return AxilGpioOptions(**kw)


def _sv(**kw) -> str:
    return render(IP.generate(_opts(**kw)), language="sv", style=StyleOptions(),
                  include_wrapper=True)


def test_satisfies_the_ip_protocol() -> None:
    assert isinstance(IP, IpDef)
    assert IP.kind == "ip"


# --------------------------------------------------------------------------- #
# Composition
# --------------------------------------------------------------------------- #


def test_is_one_flat_module_with_no_submodule() -> None:
    """The register block is spliced in, not instantiated."""
    sv = _sv()
    assert sv.count("module ") == 1
    assert "endmodule" in sv
    assert sv.count("endmodule") == 1


def test_register_fields_are_internal_signals_not_ports() -> None:
    """field_ports=False is what makes the block spliceable: the hardware face
    becomes signals the enclosing module owns."""
    module = IP.generate(_opts())
    port_names = {p.name for p in module.ports}
    for field in ("dir_value", "out_value", "in_value"):
        assert field not in port_names
    assert _re.search(r"logic \[7:0\] dir_value;", _sv())


def test_axi_face_is_still_ports() -> None:
    port_names = {p.name for p in IP.generate(_opts()).ports}
    assert set(axil_ports()) <= port_names
    assert {"aclk", "areset"} <= port_names
    assert {"gpio_in", "gpio_out", "gpio_oe"} <= port_names


def test_standalone_regblock_still_exposes_fields_as_ports() -> None:
    """The default must stay unchanged — axil-regblock depends on it."""
    regmap = register_map(_opts())
    standalone = build_axil_regblock("rb", regmap, field_ports=True)
    names = {p.name for p in standalone.ports}
    assert {name for name, _d, _w in hardware_ports(regmap)} <= names


def test_only_the_expected_pins_are_added() -> None:
    module = IP.generate(_opts())
    extra = {p.name for p in module.ports} - set(axil_ports()) - {"aclk", "areset"}
    assert extra == {"gpio_in", "gpio_out", "gpio_oe"}


# --------------------------------------------------------------------------- #
# Register map and wiring
# --------------------------------------------------------------------------- #


def test_register_map_is_dir_out_in() -> None:
    regmap = register_map(_opts(num_pins=8))
    assert [(r.name, r.offset) for r in regmap.registers] == [
        ("DIR", 0x0), ("OUT", 0x4), ("IN", 0x8)
    ]
    assert regmap.register("IN").fields[0].access == "ro"
    assert regmap.register("DIR").fields[0].width == 8


def test_field_width_follows_num_pins() -> None:
    assert register_map(_opts(num_pins=13)).register("OUT").fields[0].width == 13


def test_pins_are_wired_to_the_matching_registers() -> None:
    sv = _sv()
    assert "assign gpio_oe = dir_value;" in sv
    assert "assign gpio_out = out_value;" in sv


def test_input_passes_through_the_synchroniser() -> None:
    sv = _sv(input_sync_stages=3)
    assert "in_sync0 <= gpio_in;" in sv
    assert "in_sync1 <= in_sync0;" in sv
    assert "in_sync2 <= in_sync1;" in sv
    assert "assign in_value = in_sync2;" in sv


def test_synchroniser_depth_follows_the_option() -> None:
    for stages in (2, 4):
        sv = _sv(input_sync_stages=stages)
        assert f"in_sync{stages - 1}" in sv
        assert f"in_sync{stages}" not in sv


def test_no_bidirectional_port() -> None:
    """The IR has no `inout`; direction is a separate output so the integrator
    instantiates the tri-state buffer."""
    sv = _sv()
    assert "inout" not in sv
    # The renderer pads the declaration columns, so match on the parts rather
    # than on exact spacing.
    assert _re.search(r"output\s+logic\s+\[7:0\]\s+gpio_oe", sv)
    assert _re.search(r"input\s+logic\s+\[7:0\]\s+gpio_in", sv)


# --------------------------------------------------------------------------- #
# Metadata
# --------------------------------------------------------------------------- #


def test_bundle_matches_the_generated_module() -> None:
    opts = _opts()
    check_bundles_against_module(IP.generate(opts), bundles(opts))


def test_pins_are_not_in_the_axi_bundle() -> None:
    (bundle,) = bundles(_opts())
    assert bundle.protocol == "axi4-lite"
    assert not any(p.signal.startswith("gpio_") for p in bundle.ports)


@pytest.mark.parametrize("num_pins", [1, 8, 13, 32])
def test_tb_only_touches_ports_that_exist(num_pins: int) -> None:
    opts = _opts(num_pins=num_pins)
    declared = {p.name for p in IP.generate(opts).ports}
    spec = tb_spec(opts)
    for check in spec.checks:
        assert check.signal in declared
    for vector in spec.vectors:
        for signal in vector:
            assert signal in declared


def test_tb_checks_the_synchroniser_latency() -> None:
    """There must be a read of IN that expects the *old* value while the new
    one is still in flight — otherwise a missing synchroniser is invisible."""
    spec = tb_spec(_opts())
    rdata = [c.expected for c in spec.checks if c.signal == "rdata"]
    assert 0 in rdata, "no read expects the pre-synchronisation value"
    assert any(v != 0 for v in rdata), "no read expects a settled value"


def test_reserved_write_is_exercised_when_pins_do_not_fill_the_word() -> None:
    narrow = {c.expected for c in tb_spec(_opts(num_pins=8)).checks if c.signal == "bresp"}
    full = {c.expected for c in tb_spec(_opts(num_pins=32)).checks if c.signal == "bresp"}
    assert 0b10 in narrow  # SLVERR on the reserved-bit write
    assert full == {0}  # nothing is reserved at full width, so no error path


def test_generates_the_full_ip_file_set() -> None:
    res = generate_files("axil-gpio", {})
    assert [f.kind for f in res.files] == [
        "rtl", "doc", "tb", "tb", "tb", "rtl", "doc"
    ]
    # rtl, datasheet, SV TB, cocotb TB, verification scaffold, example
    # instantiation, test plan. The two `rtl` and two `doc` entries are
    # distinguished by path, not kind (GeneratedFile.kind is frozen).
    assert [f.path for f in res.files if f.kind == "tb"][-1].endswith("_checks.sv")
    assert [f.path for f in res.files if f.kind == "rtl"][-1].endswith(
        ("_example.sv", "_example.v")
    )
    doc = next(f.text for f in res.files if f.kind == "doc")
    assert "## Register map" in doc
    assert "`DIR`" in doc and "`IN`" in doc
