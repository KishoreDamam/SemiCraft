"""AXI4-Lite interrupt controller: composition, trigger modes, latency (P4-08)."""

from __future__ import annotations

import pytest
from semicraft_core.generate import generate_files
from semicraft_core.ips.axil_intc import (
    IP,
    AxilIntcOptions,
    bundles,
    register_map,
    tb_spec,
)
from semicraft_core.ips.contract import IpDef, check_bundles_against_module
from semicraft_core.ips.regblock import axil_ports
from semicraft_core.render import StyleOptions, render


def _opts(**kw) -> AxilIntcOptions:
    return AxilIntcOptions(**kw)


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
    sv = _sv()
    assert sv.count("module ") == 1
    assert sv.count("endmodule") == 1


def test_only_the_request_lines_are_added_to_the_axi_face() -> None:
    module = IP.generate(_opts())
    extra = {p.name for p in module.ports} - set(axil_ports()) - {"aclk", "areset"}
    assert extra == {"irq_in", "irq_out"}


def test_register_fields_are_internal_signals_not_ports() -> None:
    port_names = {p.name for p in IP.generate(_opts()).ports}
    for field in ("pending_value", "enable_value", "status_value"):
        assert field not in port_names


# --------------------------------------------------------------------------- #
# Register map
# --------------------------------------------------------------------------- #


def test_register_map_layout() -> None:
    regmap = register_map(_opts())
    assert [(r.name, r.offset) for r in regmap.registers] == [
        ("PENDING", 0x0), ("ENABLE", 0x4), ("STATUS", 0x8)
    ]
    assert regmap.register("PENDING").fields[0].access == "w1c"
    assert regmap.register("ENABLE").fields[0].access == "rw"
    assert regmap.register("STATUS").fields[0].access == "ro"


def test_field_width_follows_num_irq() -> None:
    assert register_map(_opts(num_irq=13)).register("PENDING").fields[0].width == 13


# --------------------------------------------------------------------------- #
# Wiring
# --------------------------------------------------------------------------- #


def test_mask_gates_the_output_not_the_latch() -> None:
    sv = _sv()
    assert "assign status_value = pending_value & enable_value;" in sv
    assert "assign irq_out = |status_value;" in sv
    # ENABLE must not appear in the set-request expression.
    (line,) = [ln for ln in sv.splitlines() if "assign pending_value_set" in ln]
    assert "enable_value" not in line


def test_request_passes_through_the_synchroniser() -> None:
    sv = _sv(input_sync_stages=3)
    assert "irq_sync0 <= irq_in;" in sv
    assert "irq_sync1 <= irq_sync0;" in sv
    assert "irq_sync2 <= irq_sync1;" in sv


def test_edge_history_comes_from_the_last_stage_not_from_inside_the_chain() -> None:
    """Taking the previous value from irq_sync0 would put the metastability
    hazard back into the latch the synchroniser exists to protect."""
    sv = _sv(input_sync_stages=3)
    assert "irq_hist <= irq_sync2;" in sv
    assert "assign pending_value_set = irq_sync2 & (~irq_hist);" in sv


def test_level_trigger_has_no_history_flop() -> None:
    sv = _sv(trigger="level")
    assert "irq_hist" not in sv
    assert "assign pending_value_set = irq_sync1;" in sv


def test_synchroniser_depth_follows_the_option() -> None:
    for stages in (2, 4):
        sv = _sv(input_sync_stages=stages)
        assert f"irq_sync{stages - 1}" in sv
        assert f"irq_sync{stages}" not in sv


# --------------------------------------------------------------------------- #
# Metadata
# --------------------------------------------------------------------------- #


def test_bundle_matches_the_generated_module() -> None:
    opts = _opts()
    check_bundles_against_module(IP.generate(opts), bundles(opts))


def test_request_lines_are_not_in_the_axi_bundle() -> None:
    (bundle,) = bundles(_opts())
    assert bundle.protocol == "axi4-lite"
    assert not any(p.signal.startswith("irq") for p in bundle.ports)


def test_trigger_mode_reaches_the_datasheet() -> None:
    edge = IP.explain(_opts())
    level = IP.explain(_opts(trigger="level"))
    assert any("Edge-triggered" in line for line in edge.limitations)
    assert any("Level-triggered" in line for line in level.limitations)


# --------------------------------------------------------------------------- #
# Testbench
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("kw", [
    {}, {"num_irq": 1}, {"num_irq": 32}, {"trigger": "level"},
    {"input_sync_stages": 4},
])
def test_tb_only_touches_ports_that_exist(kw: dict) -> None:
    opts = _opts(**kw)
    declared = {p.name for p in IP.generate(opts).ports}
    spec = tb_spec(opts)
    for check in spec.checks:
        assert check.signal in declared
    for vector in spec.vectors:
        for signal in vector:
            assert signal in declared


def test_tb_pins_the_synchroniser_latency() -> None:
    """A read issued on the settling cycle must expect the request to be absent
    still — otherwise latching one flop early is invisible in simulation."""
    spec = tb_spec(_opts())
    rdata = [c.expected for c in spec.checks if c.signal == "rdata"]
    assert rdata[0] == 0, "the first read does not require the pre-settled value"
    assert any(v != 0 for v in rdata), "no read expects a latched request"


def test_the_two_trigger_modes_produce_different_expectations() -> None:
    """The final section holds a source asserted across a write-1-to-clear, so
    edge and level must disagree about what the following read returns."""
    edge = [c.expected for c in tb_spec(_opts()).checks if c.signal == "rdata"]
    level = [c.expected for c in tb_spec(_opts(trigger="level")).checks
             if c.signal == "rdata"]
    assert edge != level


def test_reserved_write_is_exercised_when_sources_do_not_fill_the_word() -> None:
    narrow = {c.expected for c in tb_spec(_opts(num_irq=8)).checks if c.signal == "bresp"}
    full = {c.expected for c in tb_spec(_opts(num_irq=32)).checks if c.signal == "bresp"}
    assert 0b10 in narrow
    assert full == {0}


def test_generates_the_full_ip_file_set() -> None:
    res = generate_files("axil-intc", {})
    assert [f.kind for f in res.files] == ["rtl", "doc", "tb", "tb", "tb", "doc"]
    # rtl, datasheet, SV TB, cocotb TB, verification scaffold, test plan.
    assert [f.path for f in res.files if f.kind == "tb"][-1].endswith("_checks.sv")
    doc = next(f.text for f in res.files if f.kind == "doc")
    assert "## Register map" in doc
    assert "`PENDING`" in doc and "`STATUS`" in doc
