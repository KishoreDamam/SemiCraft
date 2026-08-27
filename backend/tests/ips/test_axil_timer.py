"""AXI4-Lite timer: composition, register map, timing derivation (P4-08)."""

from __future__ import annotations

import re as _re

import pytest
from semicraft_core.generate import generate_files
from semicraft_core.ips.axil_timer import (
    IP,
    AxilTimerOptions,
    _irq_cycle,
    bundles,
    register_map,
    tb_spec,
)
from semicraft_core.ips.contract import IpDef, check_bundles_against_module
from semicraft_core.ips.regblock import axil_ports
from semicraft_core.render import StyleOptions, render


def _opts(**kw) -> AxilTimerOptions:
    return AxilTimerOptions(**kw)


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


def test_register_fields_are_internal_signals_not_ports() -> None:
    port_names = {p.name for p in IP.generate(_opts()).ports}
    for field in ("ctrl_enable", "reload_value", "count_value", "status_expired"):
        assert field not in port_names


def test_only_the_interrupt_is_added_to_the_axi_face() -> None:
    module = IP.generate(_opts())
    extra = {p.name for p in module.ports} - set(axil_ports()) - {"aclk", "areset"}
    assert extra == {"irq"}


# --------------------------------------------------------------------------- #
# Register map
# --------------------------------------------------------------------------- #


def test_register_map_layout() -> None:
    regmap = register_map(_opts())
    assert [(r.name, r.offset) for r in regmap.registers] == [
        ("CTRL", 0x00), ("RELOAD", 0x04), ("COUNT", 0x08),
        ("PRESCALE", 0x0C), ("STATUS", 0x10),
    ]
    assert regmap.register("COUNT").fields[0].access == "ro"
    assert regmap.register("STATUS").fields[0].access == "w1c"


def test_counter_and_prescaler_widths_follow_the_options() -> None:
    regmap = register_map(_opts(counter_width=12, prescale_width=5))
    assert regmap.register("RELOAD").fields[0].width == 12
    assert regmap.register("COUNT").fields[0].width == 12
    assert regmap.register("PRESCALE").fields[0].width == 5


# --------------------------------------------------------------------------- #
# Wiring
# --------------------------------------------------------------------------- #


def test_interrupt_is_the_flag_and_the_mask() -> None:
    assert "assign irq = status_expired && ctrl_irq_enable;" in _sv()


def test_disabled_means_reloaded_not_paused() -> None:
    sv = _sv()
    assert _re.search(r"if \(!ctrl_enable\) begin\s+pre_cnt <= .*?;\s+"
                      r"count_value <= reload_value;", sv, _re.S)


def test_one_shot_stops_by_clearing_running() -> None:
    """CTRL.enable is software's; hardware stops the counter with `running`."""
    sv = _sv()
    assert _re.search(r"if \(ctrl_auto_reload\) begin\s+count_value <= reload_value;"
                      r"\s+end else begin\s+running <= 1'b0;", sv, _re.S)


def test_expiry_raises_the_w1c_set_request() -> None:
    sv = _sv()
    assert "status_expired_set <= 1'b1;" in sv
    # ...and it is defaulted low, so it is a one-cycle pulse rather than a level.
    assert "status_expired_set <= 1'b0;" in sv


# --------------------------------------------------------------------------- #
# Metadata
# --------------------------------------------------------------------------- #


def test_bundle_matches_the_generated_module() -> None:
    opts = _opts()
    check_bundles_against_module(IP.generate(opts), bundles(opts))


def test_interrupt_is_not_in_the_axi_bundle() -> None:
    (bundle,) = bundles(_opts())
    assert bundle.protocol == "axi4-lite"
    assert not any(p.signal == "irq" for p in bundle.ports)


# --------------------------------------------------------------------------- #
# Testbench
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("kw", [
    {}, {"counter_width": 4}, {"prescale_width": 1}, {"prescale_width": 32},
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


def test_every_expiry_is_checked_from_both_sides() -> None:
    """A "high at cycle N" check alone passes for a timer that fired early, so
    each expiry must also require irq low on the cycle before."""
    checks = tb_spec(_opts()).checks
    rises = sorted(c.cycle for c in checks if c.signal == "irq" and c.expected == 1)
    lows = {c.cycle for c in checks if c.signal == "irq" and c.expected == 0}
    assert len(rises) == 2, "expected one periodic and one one-shot expiry"
    for cycle in rises:
        assert cycle - 1 in lows, f"no low check guarding the rise at cycle {cycle}"


def test_irq_cycle_matches_the_documented_period() -> None:
    """Two clocks of composition cost on top of (RELOAD+1)*(PRESCALE+1)."""
    for reload, prescale in ((3, 1), (0, 0), (7, 3)):
        period = (reload + 1) * (prescale + 1)
        assert _irq_cycle(0, reload, prescale) == period + 3


def test_reserved_write_is_always_exercised() -> None:
    """CTRL has reserved bits at every counter width, so the SLVERR path is
    reachable even when RELOAD fills the data word."""
    for width in (4, 32):
        resps = {c.expected for c in tb_spec(_opts(counter_width=width)).checks
                 if c.signal == "bresp"}
        assert 0b10 in resps


def test_generates_the_full_ip_file_set() -> None:
    res = generate_files("axil-timer", {})
    assert [f.kind for f in res.files] == ["rtl", "doc", "tb", "tb", "doc"]
    doc = next(f.text for f in res.files if f.kind == "doc")
    assert "## Register map" in doc
    assert "`CTRL`" in doc and "`STATUS`" in doc
