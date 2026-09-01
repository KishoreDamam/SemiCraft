"""Verification-scaffold specs, restyling, and bind emission (P4-09)."""

from __future__ import annotations

import pytest
from semicraft_core.checkers.bind import BindSpec, generate_bind
from semicraft_core.checkers.restyle import (
    is_identifier,
    restyle_checker,
    restyle_monitor,
    restyle_scoreboard,
)
from semicraft_core.checkers.spec import (
    CheckerSpec,
    LatencyCheck,
    MonitorSpec,
    ResetPolarity,
    ScoreboardSpec,
    ScoreboardWrapper,
    Signal,
    StabilityCheck,
)
from semicraft_core.ips.contract import IpContractError
from semicraft_core.ips.verification import (
    VerificationSpec,
    axil_verification,
    check_spec_is_restylable,
    render_verification,
    verification_filename,
)


def _upper(name: str) -> str:
    return name.upper()


# --------------------------------------------------------------------------- #
# is_identifier — the whole rule the restyler rests on
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("text", ["a", "bvalid", "_x", "n1", "a$b"])
def test_bare_identifiers_are_renameable(text: str) -> None:
    assert is_identifier(text)


@pytest.mark.parametrize(
    "text",
    ["bvalid && bready", "a[0]", "~x", "{a, b}", "", " a", "1'b0", "a b"],
)
def test_expressions_are_not(text: str) -> None:
    assert not is_identifier(text)


# --------------------------------------------------------------------------- #
# Restyling
# --------------------------------------------------------------------------- #


def test_monitor_clock_fields_and_bare_qualifier_are_renamed() -> None:
    spec = MonitorSpec("mon", "clk", [Signal("valid"), Signal("data", 8)], "valid")
    out = restyle_monitor(spec, _upper)
    assert out.clock == "CLK"
    assert [f.name for f in out.fields] == ["VALID", "DATA"]
    assert out.qualifier == "VALID"
    assert out.name == "mon", "the module name is a label, not a net"


def test_an_expression_qualifier_is_left_alone() -> None:
    """Renaming inside expression text would mean parsing SystemVerilog."""
    spec = MonitorSpec("mon", "clk", [Signal("valid")], "valid && ready")
    assert restyle_monitor(spec, _upper).qualifier == "valid && ready"


def test_checker_reset_is_renamed() -> None:
    """The case that matters at the *default* configuration: AXI4-Lite fixes
    the reset active-low, so `areset` renders as `areset_n`."""
    spec = CheckerSpec(
        name="chk",
        clock="aclk",
        ports=[Signal("bvalid")],
        checks=[LatencyCheck("live", "awvalid", "bvalid", 4)],
        reset=ResetPolarity("areset", active_low=True),
    )
    out = restyle_checker(spec, lambda n: "areset_n" if n == "areset" else n)
    assert out.reset is not None
    assert out.reset.signal == "areset_n"


def test_checker_item_signals_are_renamed() -> None:
    spec = CheckerSpec(
        name="chk",
        clock="clk",
        ports=[Signal("d", 8), Signal("en")],
        checks=[
            StabilityCheck("stab", signal="d", enable="en", width=8),
            LatencyCheck("live", request="req", response="ack", max_cycles=4),
        ],
        reset=None,
    )
    out = restyle_checker(spec, _upper)
    stab, live = out.checks
    assert (stab.signal, stab.enable) == ("D", "EN")
    assert (live.request, live.response) == ("REQ", "ACK")
    assert (stab.name, live.name) == ("stab", "live"), "check names seed register names"


def test_scoreboard_class_name_and_item_type_survive_restyling() -> None:
    spec = ScoreboardSpec(
        name="sb",
        item_type="logic [7:0]",
        wrapper=ScoreboardWrapper("sb_wrap", "clk", "push", "d", "pop", "q"),
    )
    out = restyle_scoreboard(spec, _upper)
    assert out.name == "sb"
    assert out.item_type == "logic [7:0]"
    assert out.wrapper is not None
    assert (out.wrapper.clock, out.wrapper.push_signal) == ("CLK", "PUSH")
    assert (out.wrapper.push_expr, out.wrapper.compare_expr) == ("D", "Q")


# --------------------------------------------------------------------------- #
# The restylability guard
# --------------------------------------------------------------------------- #


def test_the_shipped_axi_spec_is_restylable() -> None:
    check_spec_is_restylable(axil_verification("axil_gpio"))


def test_an_expression_in_a_catalog_spec_is_refused() -> None:
    """The limitation must be unreachable from the catalog, not merely
    documented: a spec that would bind to undefined nets under a naming style
    fails at generate time rather than in someone's simulation."""
    spec = VerificationSpec(
        checker=CheckerSpec(
            name="chk",
            clock="aclk",
            ports=[Signal("bvalid")],
            checks=[LatencyCheck("live", "awvalid && awready", "bvalid", 4)],
            reset=None,
        )
    )
    with pytest.raises(IpContractError, match="is an expression"):
        check_spec_is_restylable(spec)


# --------------------------------------------------------------------------- #
# bind
# --------------------------------------------------------------------------- #


def test_bind_connects_every_port_by_name() -> None:
    text = generate_bind(BindSpec("dut", "dut_chk", "u_chk", ["clk", "rst_n", "d"]))
    assert text.startswith("bind dut dut_chk u_chk (")
    assert ".clk(clk)," in text
    assert ".d(d)\n" in text, "the last connection must not carry a comma"
    assert text.rstrip().endswith(");")


def test_a_bind_with_no_ports_is_refused() -> None:
    with pytest.raises(ValueError, match="checks nothing"):
        generate_bind(BindSpec("dut", "dut_chk", "u_chk", []))


# --------------------------------------------------------------------------- #
# Rendering
# --------------------------------------------------------------------------- #


def test_an_empty_spec_renders_nothing() -> None:
    assert render_verification(VerificationSpec(), "dut", str) == ""


def test_rendered_scaffold_binds_every_module_it_declares() -> None:
    """A declared-but-unbound scaffold is the failure this WP exists to stop."""
    spec = axil_verification("axil_gpio")
    text = render_verification(spec, "axil_gpio", lambda n: n)
    declared = {
        line.split()[1] for line in text.splitlines() if line.startswith("module ")
    }
    bound = {line.split()[2] for line in text.splitlines() if line.startswith("bind ")}
    assert declared == bound
    assert declared


def test_rendering_applies_the_name_map_to_ports_and_binds() -> None:
    text = render_verification(
        axil_verification("axil_gpio"),
        "axil_gpio",
        lambda n: "areset_n" if n == "areset" else n,
    )
    assert "input logic areset_n" in text
    assert ".areset_n(areset_n)" in text
    assert "areset)" not in text.replace("areset_n)", "")


def test_filename_follows_the_module() -> None:
    assert verification_filename("axil_gpio") == "axil_gpio_checks.sv"


# --------------------------------------------------------------------------- #
# What the shared AXI scaffold actually checks
# --------------------------------------------------------------------------- #


def test_axi_scaffold_checks_liveness_and_read_stability() -> None:
    """Deliberately not reset values or field semantics: those are already
    covered by the directed testbench and its SVA."""
    spec = axil_verification("axil_gpio")
    assert spec.checker is not None
    names = [c.name for c in spec.checker.checks]
    assert names == [
        "write_response_arrives",
        "read_data_arrives",
        "rdata_holds_between_reads",
        "rresp_holds_between_reads",
    ]


def test_each_channel_gets_its_own_monitor() -> None:
    """One monitor per channel, each gated on a bare signal — an expression
    qualifier would not survive restyling."""
    spec = axil_verification("axil_gpio")
    assert [m.qualifier for m in spec.monitors] == ["bvalid", "rvalid"]
    for mon in spec.monitors:
        assert mon.qualifier in [f.name for f in mon.fields], (
            "a qualifier must name a port the monitor declares"
        )


def test_data_width_reaches_the_scaffold_ports() -> None:
    spec = axil_verification("axil_gpio", data_width=64)
    assert spec.checker is not None
    rdata = next(p for p in spec.checker.ports if p.name == "rdata")
    assert rdata.width == 64


# --------------------------------------------------------------------------- #
# Every scaffold port must match the DUT port it binds to
# --------------------------------------------------------------------------- #
#
# This is a regression test with a scar. `axil_verification` defaults to a
# 32-bit `rdata`, every composed peripheral fixes its data width at 32, and
# `axil-regblock` - the one IP where the width is an option - was wired up
# without passing it through. A 32-bit scaffold port bound to a 64-bit net does
# not compile, and the only thing that noticed was a Verilator run of one
# option case, thirteen minutes into a gate. Widths are structural; checking
# them needs no simulator and takes milliseconds.

_WIDTH_CASES = [
    ("axil-regblock", {}),
    ("axil-regblock", {"data_width": 64}),
    ("axil-gpio", {}),
    ("axil-gpio", {"num_pins": 32}),
    ("axil-uart", {}),
    ("axil-spi", {}),
    ("axil-i2c", {}),
    ("axil-timer", {}),
    ("axil-intc", {}),
    ("sync-fifo", {}),
    ("sync-fifo", {"width": 32}),
    ("sync-ram", {}),
    ("sync-ram", {"width": 64}),
]


def _scaffold_signals(spec: VerificationSpec):
    """Every (name, width) pair the scaffolds declare as a port."""
    out: list[tuple[str, int]] = []
    for mon in spec.monitors:
        out += [(f.name, f.width) for f in mon.fields]
    if spec.checker is not None:
        out += [(p.name, p.width) for p in spec.checker.ports]
    if spec.scoreboard is not None and spec.scoreboard.wrapper is not None:
        out += [(p.name, p.width) for p in spec.scoreboard.wrapper.ports]
    return out


@pytest.mark.parametrize(
    "item_id,options",
    _WIDTH_CASES,
    ids=[f"{i}-{o or 'defaults'}" for i, o in _WIDTH_CASES],
)
def test_scaffold_ports_match_the_dut_ports(item_id: str, options: dict) -> None:
    from semicraft_core.snippets import registry
    from semicraft_core.tb.generate_tb import _param_values, _width_of

    item = registry.get(item_id)
    opts = item.options_model.model_validate(options)
    module = item.generate(opts)
    params = _param_values(module)
    dut = {p.name: _width_of(p.dtype, params) for p in module.ports}

    spec = item.verification_spec(opts)
    signals = _scaffold_signals(spec)
    if not signals:
        return  # an IP with nothing to check emits no file at all

    for name, width in signals:
        assert name in dut, (
            f"{item_id}: scaffold declares port {name!r}, which the DUT does "
            f"not have. Scaffold ports are canonical names; the DUT ports here "
            f"are too, so this is a typo, not a restyling gap."
        )
        assert width == dut[name], (
            f"{item_id} {options}: scaffold port {name!r} is {width} bits but "
            f"the DUT net is {dut[name]}. `bind` will not compile."
        )
