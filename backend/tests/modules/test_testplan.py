"""Test-plan document generator (Phase 3, P3-07).

Two kinds of coverage:

- real-module content assertions/determinism via ``generate_files()`` (every
  shipped module always has clock+reset, so these exercise the "normal" path
  end-to-end against the actual golden pipeline);
- synthetic ``ModuleDef``/``TbSpec``/IR-``Module`` fixtures built directly in
  this file for the combinations no shipped module currently produces: no
  reset, no clock, declared ``port_constraints``, and a set ``assertion_spec``
  (P3-07 brief explicitly calls these out). Building a tiny synthetic IR
  module (via ``ir.build``/``ir.nodes``) is the only way to exercise them
  without waiting on a future module WP.
"""

from __future__ import annotations

from dataclasses import dataclass

import pytest
from semicraft_core.assertions.spec import (
    AssertionSpec,
    ResetContext,
    ResetKnownValue,
    Stability,
)
from semicraft_core.generate import generate_files
from semicraft_core.ir.build import IN, OUT, bit
from semicraft_core.ir.nodes import (
    AlwaysFF,
    Assign,
    ClockSpec,
    Const,
    Header,
    Module,
    Port,
    Ref,
    ResetKind,
    ResetSpec,
)
from semicraft_core.modules.contract import Check, PortConstraint, PortGroup, TbSpec
from semicraft_core.snippets.contract import ClockedOptions, ExplanationDoc, SignalDoc
from semicraft_core.testplan import generate_testplan

# --------------------------------------------------------------------------- #
# Synthetic fixtures
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class _FakeItem:
    """Minimal ``ModuleDef``-shaped double: fixed ``tb_spec``/``port_groups``,
    independent of ``opts`` (only ``generate_testplan`` needs these two)."""

    name: str
    _tb_spec: TbSpec
    _port_groups: list[PortGroup]

    def tb_spec(self, opts) -> TbSpec:
        return self._tb_spec

    def port_groups(self, opts) -> list[PortGroup]:
        return self._port_groups


_OPTS = ClockedOptions()  # default naming (snake, no prefix/suffix), sv, sync/active-low


def _explanation(
    purpose: str = "A synthetic widget for testplan tests.",
    configuration: list[str] | None = None,
    reset_behavior: str = "Reset clears q to 0.",
    enable_behavior: str | None = None,
    limitations: list[str] | None = None,
) -> ExplanationDoc:
    return ExplanationDoc(
        purpose=purpose,
        configuration=configuration or ["Width: 1 bit"],
        signals=[
            SignalDoc(name="clk", direction="input", description="Clock."),
            SignalDoc(name="rst_n", direction="input", description="Active-low reset."),
            SignalDoc(name="d", direction="input", description="Data in."),
            SignalDoc(name="q", direction="output", description="Data out."),
        ],
        reset_behavior=reset_behavior,
        enable_behavior=enable_behavior,
        assumptions=["d is synchronous to clk."],
        limitations=limitations if limitations is not None else ["No CDC handling."],
    )


def _header() -> Header:
    return Header(
        license="License text.",
        config_hash="deadbeef0000",
        tool_version="0.0.0-test",
        description="Synthetic test widget.",
    )


def _clocked_module(
    name: str = "widget", *, reset: bool = True, active_low: bool = True
) -> Module:
    """A tiny one-bit passthrough register, with or without a reset port."""
    ports = [Port("clk", IN, bit(), doc="Clock")]
    reset_spec = None
    if reset:
        ports.append(Port("rst", IN, bit(), doc="Reset"))
        reset_spec = ResetSpec(name="rst", kind=ResetKind.SYNC, active_low=active_low)
    ports += [Port("d", IN, bit(), doc="Data in"), Port("q", OUT, bit(), doc="Data out")]

    body = [Assign(Ref("q"), Ref("d"))]
    reset_body = [Assign(Ref("q"), Const(0))] if reset else []
    always = AlwaysFF(clock=ClockSpec("clk"), reset=reset_spec, reset_body=reset_body, body=body)

    return Module(name=name, header=_header(), params=[], ports=ports, items=[always])


_DEFAULT_PORT_GROUPS = [
    PortGroup(name="Clocking", ports=["clk", "rst_n"], description="Clock and reset."),
    PortGroup(name="Data", ports=["d", "q"], description="Data in/out."),
]

_NO_RESET_PORT_GROUPS = [
    PortGroup(name="Clocking", ports=["clk"], description="Clock only, no reset."),
    PortGroup(name="Data", ports=["d", "q"], description="Data in/out."),
]


def _basic_spec(**overrides) -> TbSpec:
    defaults = dict(
        clock="clk",
        reset="rst",
        reset_cycles=2,
        vectors=[{"d": 0}, {"d": 1}, {"d": 1}],
        checks=[Check(cycle=2, signal="q", expected=1)],
    )
    defaults.update(overrides)
    return TbSpec(**defaults)


# --------------------------------------------------------------------------- #
# Real modules via generate_files() — normal path, byte-identical wiring
# --------------------------------------------------------------------------- #


def test_module_yields_testplan_as_second_doc_file() -> None:
    res = generate_files("edge-detector", {})
    kinds = [f.kind for f in res.files]
    assert kinds == ["rtl", "doc", "tb", "tb", "doc"]  # second tb = cocotb (P3-08)
    doc_files = [f for f in res.files if f.kind == "doc"]
    assert doc_files[0].path == "edge_detector.md"  # datasheet stays first
    assert doc_files[1].path == "edge_detector_testplan.md"


def test_snippet_gets_no_testplan_file() -> None:
    res = generate_files("counter", {})
    assert all(not f.path.endswith("_testplan.md") for f in res.files)
    assert [f.kind for f in res.files] == ["rtl"]


def test_testplan_content_basics() -> None:
    res = generate_files("edge-detector", {})
    tp = next(f for f in res.files if f.path.endswith("_testplan.md"))
    text = tp.text
    assert text.startswith("# Edge Detector — Test Plan")
    assert res.config_hash in text
    assert "## Features Under Test" in text
    assert "## Test Plan" in text
    assert "## Coverage / Stimulus Summary" in text
    assert "### Ports exercised" in text
    assert "## Assertions (SVA)" in text
    assert "## Not Covered / Limitations" in text
    assert "**Gaps:**" in text


def test_testplan_test_plan_table_matches_tb_spec_checks() -> None:
    """Every TP row's expected value/cycle matches a real Check in tb_spec()."""
    from semicraft_core.modules.edge_detector import MODULE, EdgeDetectorOptions

    opts = EdgeDetectorOptions()
    spec = MODULE.tb_spec(opts)
    res = generate_files("edge-detector", {})
    text = next(f for f in res.files if f.path.endswith("_testplan.md")).text

    for chk in spec.checks:
        assert f"pulse == {chk.expected}" in text or f"{chk.signal} == {chk.expected}" in text


def test_testplan_reflects_options() -> None:
    res = generate_files("edge-detector", {"detect": "falling", "registered_output": False})
    text = next(f for f in res.files if f.path.endswith("_testplan.md")).text
    assert "falling" in text


def test_testplan_is_deterministic() -> None:
    a = generate_files("edge-detector", {"detect": "both", "width": 4})
    b = generate_files("edge-detector", {"detect": "both", "width": 4})
    a_tp = next(f for f in a.files if f.path.endswith("_testplan.md")).text
    b_tp = next(f for f in b.files if f.path.endswith("_testplan.md")).text
    assert a_tp == b_tp


def test_existing_doc_and_tb_snapshots_unaffected_by_position() -> None:
    """The pre-existing 'first doc file' convention (datasheet) still resolves
    correctly with a second doc file appended after tb."""
    res = generate_files("edge-detector", {})
    doc = next(f for f in res.files if f.kind == "doc")
    assert doc.path == "edge_detector.md"
    tb = next(f for f in res.files if f.kind == "tb")
    assert tb.path == "edge_detector_tb.sv"


# --------------------------------------------------------------------------- #
# Synthetic: with reset vs. without reset
# --------------------------------------------------------------------------- #


def test_with_reset_reports_reset_line_and_role() -> None:
    rtl = _clocked_module(reset=True, active_low=True)
    item = _FakeItem("Widget", _basic_spec(), _DEFAULT_PORT_GROUPS)
    text = generate_testplan(item, _OPTS, rtl, _explanation(), "abc123")

    assert "**Reset:** `rst_n` — held asserted for 2 cycle(s)" in text
    assert "| `rst_n` | reset | reset sequence only | n/a |" in text
    # The reset port must NOT be misclassified as an unexercised data input.
    assert "`rst_n` is an input that never appears" not in text


def test_without_reset_reports_no_reset() -> None:
    rtl = _clocked_module(reset=False)
    spec = _basic_spec(reset=None)
    item = _FakeItem("Widget", spec, _NO_RESET_PORT_GROUPS)
    text = generate_testplan(item, _OPTS, rtl, _explanation(), "abc123")

    assert "**Reset:** none — this module has no reset port" in text
    assert "reset sequence only" not in text
    # No spurious "no Check samples cycle 0" reset-gap note without a reset.
    # (cycle 0 isn't checked here either way, but the module has no reset to
    # begin with, so the note is about resetless design, not this gate.)


# --------------------------------------------------------------------------- #
# Synthetic: no clock at all (TbSpec.clock is None)
# --------------------------------------------------------------------------- #


def test_no_clock_produces_no_tb_claims() -> None:
    rtl = _clocked_module(reset=True)  # rtl_module content is irrelevant here
    spec = _basic_spec(clock=None, reset=None, vectors=[], checks=[])
    item = _FakeItem("Comb Widget", spec, _DEFAULT_PORT_GROUPS)
    text = generate_testplan(item, _OPTS, rtl, _explanation(), "abc123")

    assert "`TbSpec.clock` is `None`" in text
    assert "no testbench is generated" in text.lower()
    # No Test Plan table, no Ports-exercised table for a clockless module.
    assert "### Ports exercised" not in text
    assert "| ID | Feature / Intent |" not in text


# --------------------------------------------------------------------------- #
# Synthetic: port constraints
# --------------------------------------------------------------------------- #


def test_port_constraints_listed() -> None:
    rtl = _clocked_module(reset=True)
    spec = _basic_spec(
        port_constraints={"d": PortConstraint(min_value=2, max_value=5)}
    )
    item = _FakeItem("Widget", spec, _DEFAULT_PORT_GROUPS)
    text = generate_testplan(item, _OPTS, rtl, _explanation(), "abc123")

    assert "**Port value constraints:**" in text
    assert "`d`: [2, 5]" in text


def test_no_port_constraints_says_none_declared() -> None:
    rtl = _clocked_module(reset=True)
    item = _FakeItem("Widget", _basic_spec(), _DEFAULT_PORT_GROUPS)
    text = generate_testplan(item, _OPTS, rtl, _explanation(), "abc123")

    assert "none declared" in text


# --------------------------------------------------------------------------- #
# Synthetic: assertion_spec set vs. None
# --------------------------------------------------------------------------- #


def test_assertion_spec_none_says_no_sva() -> None:
    rtl = _clocked_module(reset=True)
    item = _FakeItem("Widget", _basic_spec(), _DEFAULT_PORT_GROUPS)
    text = generate_testplan(item, _OPTS, rtl, _explanation(), "abc123")

    assert "`TbSpec.assertion_spec` is `None`" in text
    assert "no concurrent SVA assertions are generated" in text


def test_assertion_spec_set_lists_generated_properties() -> None:
    aspec = AssertionSpec(
        clock="clk",
        items=(
            ResetKnownValue(name="q_reset", signal="q", value=0, width=1),
            Stability(name="q_stable", signal="q", enable="en"),
        ),
        reset=ResetContext(signal="rst_n", active_low=True, sync=True),
    )
    rtl = _clocked_module(reset=True)
    spec = _basic_spec(assertion_spec=aspec)
    item = _FakeItem("Widget", spec, _DEFAULT_PORT_GROUPS)
    text = generate_testplan(item, _OPTS, rtl, _explanation(), "abc123")

    assert "`q_reset`" in text
    assert "`q_stable`" in text
    assert "$rose(rst_n)" in text or "$fell" in text  # ResetKnownValue idiom
    assert "disable iff" in text  # guarded Stability item


# --------------------------------------------------------------------------- #
# Synthetic: ports-not-exercised gap logic
# --------------------------------------------------------------------------- #


def test_undriven_input_is_reported_as_a_gap() -> None:
    """d is a declared input port but never appears in any vector."""
    rtl = _clocked_module(reset=True)
    spec = _basic_spec(vectors=[{}, {}, {}])  # d never driven
    item = _FakeItem("Widget", spec, _DEFAULT_PORT_GROUPS)
    text = generate_testplan(item, _OPTS, rtl, _explanation(), "abc123")

    assert "`d` is an input that never appears in any `TbSpec` vector" in text
    assert "held at 0 for the entire run" in text


def test_unchecked_output_is_reported_as_a_gap() -> None:
    rtl = _clocked_module(reset=True)
    spec = _basic_spec(checks=[])  # q is never checked
    item = _FakeItem("Widget", spec, _DEFAULT_PORT_GROUPS)
    text = generate_testplan(item, _OPTS, rtl, _explanation(), "abc123")

    assert "no self-checking assertions" in text.lower()


def test_fully_exercised_module_reports_no_gaps() -> None:
    rtl = _clocked_module(reset=True)
    spec = _basic_spec()  # d driven every cycle, q checked once
    item = _FakeItem("Widget", spec, _DEFAULT_PORT_GROUPS)
    text = generate_testplan(item, _OPTS, rtl, _explanation(), "abc123")

    assert "None found: every port is either driven" in text


# --------------------------------------------------------------------------- #
# Determinism
# --------------------------------------------------------------------------- #


def test_generate_testplan_is_deterministic() -> None:
    rtl = _clocked_module(reset=True)
    item = _FakeItem("Widget", _basic_spec(), _DEFAULT_PORT_GROUPS)
    a = generate_testplan(item, _OPTS, rtl, _explanation(), "abc123")
    b = generate_testplan(item, _OPTS, rtl, _explanation(), "abc123")
    assert a == b


# --------------------------------------------------------------------------- #
# Reset-not-checked-at-cycle-0 note
# --------------------------------------------------------------------------- #


def test_reset_gap_note_present_when_cycle_zero_unchecked() -> None:
    rtl = _clocked_module(reset=True)
    spec = _basic_spec(checks=[Check(cycle=2, signal="q", expected=1)])
    item = _FakeItem("Widget", spec, _DEFAULT_PORT_GROUPS)
    text = generate_testplan(item, _OPTS, rtl, _explanation(), "abc123")
    assert "No `Check` samples cycle 0" in text


def test_reset_gap_note_absent_when_cycle_zero_checked() -> None:
    rtl = _clocked_module(reset=True)
    spec = _basic_spec(checks=[Check(cycle=0, signal="q", expected=0)])
    item = _FakeItem("Widget", spec, _DEFAULT_PORT_GROUPS)
    text = generate_testplan(item, _OPTS, rtl, _explanation(), "abc123")
    assert "No `Check` samples cycle 0" not in text


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
