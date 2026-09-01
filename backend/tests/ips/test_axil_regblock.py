"""The ``axil-regblock`` catalog IP (P4-02)."""

from __future__ import annotations

import pytest
from pydantic import ValidationError
from semicraft_core.generate import generate_files
from semicraft_core.ips.axil_regblock import (
    IP,
    AxilRegblockOptions,
    bundles,
    port_groups,
    register_map,
    tb_spec,
)
from semicraft_core.ips.contract import IpDef, check_bundles_against_module
from semicraft_core.ips.regblock import AXI_RESP_OKAY, AXI_RESP_SLVERR, axil_ports


def _opts(**kw) -> AxilRegblockOptions:
    return AxilRegblockOptions(**kw)


def test_satisfies_the_ip_protocol() -> None:
    assert isinstance(IP, IpDef)
    assert IP.kind == "ip"


def test_no_reset_polarity_option() -> None:
    """AXI4-Lite fixes it active-low, so the knob does not exist rather than
    existing and being rejected."""
    assert "reset_polarity" not in AxilRegblockOptions.model_fields
    assert "reset_style" in AxilRegblockOptions.model_fields
    with pytest.raises(ValidationError):
        _opts(reset_polarity="active_high")


def test_zero_registers_is_a_user_error_not_a_generator_error() -> None:
    """It must surface as a 422-shaped ValidationError, not as the engine's
    IpContractError (which the API maps to 500)."""
    with pytest.raises(ValidationError, match="at least one register"):
        _opts(
            control_regs=0,
            status_regs=0,
            irq_regs=0,
            command_regs=0,
            include_scratch=False,
        )


def test_default_map_exercises_every_access_type() -> None:
    """The defaults case is what the standard CI run gate executes, so it has
    to cover all four access types — a write-only bug once slipped through
    precisely because ``command_regs`` defaulted to zero.
    """
    regmap = register_map(_opts())
    accesses = {f.access for reg in regmap.registers for f in reg.fields}
    assert accesses == {"rw", "ro", "wo", "w1c"}


def test_registers_are_always_numbered() -> None:
    """So a hardware port name does not change meaning when a count changes."""
    names = [r.name for r in register_map(_opts()).registers]
    assert "CTRL0" in names and "CTRL" not in names


def test_offsets_are_stride_aligned_and_contiguous() -> None:
    regmap = register_map(_opts(control_regs=2, status_regs=2))
    offsets = [r.offset for r in regmap.registers]
    assert offsets == list(range(0, len(offsets) * regmap.stride_bytes, regmap.stride_bytes))


def test_address_width_covers_the_span_tightly() -> None:
    regmap = register_map(_opts())
    assert (1 << regmap.addr_width) >= regmap.span_bytes()
    assert (1 << (regmap.addr_width - 1)) < regmap.span_bytes()


def test_split_fields_leaves_reserved_bits_and_whole_word_does_not() -> None:
    from semicraft_core.ips.regblock import write_reserved_mask

    split = register_map(_opts(split_fields=True)).register("CTRL0")
    whole = register_map(_opts(split_fields=False)).register("CTRL0")
    assert write_reserved_mask(split, 32) != 0
    assert write_reserved_mask(whole, 32) == 0


def test_bundle_matches_the_generated_module() -> None:
    opts = _opts()
    check_bundles_against_module(IP.generate(opts), bundles(opts))


def test_bundle_role_names_are_the_protocol_spelling() -> None:
    (bundle,) = bundles(_opts())
    assert bundle.protocol == "axi4-lite"
    assert bundle.role == "target"
    assert {p.role_name for p in bundle.ports} == set(axil_ports())
    assert bundle.clock == "aclk"
    assert bundle.reset == "areset"


def test_hardware_face_is_not_in_the_bundle() -> None:
    """Bundles describe protocol ports; the field outputs are this IP's own
    interface."""
    (bundle,) = bundles(_opts())
    assert not any(p.signal.startswith("ctrl0_") for p in bundle.ports)


def test_port_groups_cover_every_generated_port() -> None:
    opts = _opts()
    module = IP.generate(opts)
    grouped = {p for group in port_groups(opts) for p in group.ports}
    declared = {p.name for p in module.ports}
    # port_groups renders the reset with its `_n` suffix, as the datasheet does.
    declared = {"areset_n" if n == "areset" else n for n in declared}
    assert grouped == declared


# --------------------------------------------------------------------------- #
# Testbench recipe
# --------------------------------------------------------------------------- #


def test_tb_checks_both_response_codes() -> None:
    """A run that never sees an error response would not test the error path."""
    checks = tb_spec(_opts()).checks
    resps = {c.expected for c in checks if c.signal in ("bresp", "rresp")}
    assert resps == {AXI_RESP_OKAY, AXI_RESP_SLVERR}


def test_tb_checks_post_reset_idle_state() -> None:
    checks = {(c.signal, c.expected) for c in tb_spec(_opts()).checks if c.cycle == 0}
    assert ("bvalid", 0) in checks
    assert ("rvalid", 0) in checks
    assert ("awready", 1) in checks


@pytest.mark.parametrize(
    "options",
    [
        {},
        {"split_fields": False},
        {"data_width": 64},
        {"include_scratch": False},
        {"control_regs": 0, "status_regs": 0, "irq_regs": 0, "command_regs": 0},
        {"control_regs": 3, "status_regs": 2, "irq_regs": 2, "command_regs": 2},
    ],
    ids=["defaults", "whole_word", "w64", "no_scratch", "scratch_only", "many"],
)
def test_tb_spec_only_checks_ports_that_exist(options) -> None:
    """Each phase is guarded on the map containing what it needs, so no
    configuration may check a signal the module does not declare."""
    opts = AxilRegblockOptions(**options)
    module = IP.generate(opts)
    declared = {p.name for p in module.ports}
    spec = tb_spec(opts)
    for check in spec.checks:
        assert check.signal in declared, f"{options}: checks missing port {check.signal}"
    for vector in spec.vectors:
        for signal in vector:
            assert signal in declared, f"{options}: drives missing port {signal}"


def test_tb_expected_values_are_not_all_zero() -> None:
    """A sequence whose every expectation is zero would pass against a module
    that does nothing at all."""
    expected = {c.expected for c in tb_spec(_opts()).checks}
    assert len(expected - {0}) >= 4


# --------------------------------------------------------------------------- #
# End-to-end file set
# --------------------------------------------------------------------------- #


def test_generates_the_full_ip_file_set() -> None:
    res = generate_files("axil-regblock", {})
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
    assert "## Bus interfaces" in doc
    assert "`axi4-lite` target" in doc


def test_datasheet_does_not_claim_reserved_writes_are_ignored() -> None:
    """This block rejects them with SLVERR. The generic register-map renderer
    must not state a write policy it does not own — the datasheet said
    "ignore writes" while the RTL returned an error.
    """
    doc = next(f.text for f in generate_files("axil-regblock", {}).files if f.kind == "doc")
    assert "reserved and read as zero" in doc
    assert "ignore writes" not in doc
    assert "SLVERR" in doc  # the real policy, from the IP's limitations
