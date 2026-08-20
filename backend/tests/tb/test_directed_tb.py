"""P3-04 directed-TB generator upgrade tests.

Covers the three things P3-04 adds on top of the P2 smoke TB:

1. A ``TimeoutGuard`` watchdog wrapping every run (fail-loud on a hung DUT),
   with a budget that comfortably exceeds a healthy run.
2. Stimulus tables that honour the resolved port width and optional per-port
   ``PortConstraint`` bounds from the module's ``TbSpec``.
3. An assertion-wiring hook: ``TbSpec.assertion_spec`` flows through
   ``generate_assertions`` into the rendered SVA block; inert (no SVA emitted)
   when no module declares one — which is every current module.

Expected values still come *only* from ``TbSpec.checks`` — the watchdog and the
stimulus generalisation never invent or alter a check.
"""

from __future__ import annotations

import re

import pytest
from semicraft_core.assertions.spec import AssertionSpec, NoUnknown
from semicraft_core.generate import generate_files
from semicraft_core.modules import pwm
from semicraft_core.modules.contract import PortConstraint, TbSpec
from semicraft_core.snippets import registry
from semicraft_core.tb.generate_tb import _constrain_value, generate_tb

MODULE_IDS = sorted(m.id for m in registry.by_kind("module"))


class _FakeDef:
    """Minimal ModuleDef stand-in: only ``tb_spec`` is exercised by generate_tb."""

    def __init__(self, spec: TbSpec) -> None:
        self._spec = spec

    def tb_spec(self, opts) -> TbSpec:  # noqa: ARG002 - fixed spec, opts unused
        return self._spec


def _pwm_ctx(**opts_kw):
    """A real (opts, rtl_module) pair to drive generate_tb with a synthetic spec."""
    opts = pwm.PwmOptions(**opts_kw)
    return opts, pwm.generate(opts)


def _tb(item_id: str, options: dict | None = None) -> str:
    res = generate_files(item_id, options or {})
    return next(f.text for f in res.files if f.kind == "tb")


# --------------------------------------------------------------------------- #
# 1. Watchdog
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("item_id", MODULE_IDS)
def test_every_tb_has_watchdog(item_id: str) -> None:
    tb = _tb(item_id)
    # Rendered TimeoutGuard shape (render_tb): fork / repeat (N) @(posedge clk) /
    # $fatal(...) / join_none.
    assert "fork" in tb
    assert "join_none" in tb
    assert re.search(r'\$fatal\(1, "TIMEOUT: \w+_tb exceeded \d+ cycles"\);', tb)
    # The watchdog is forked before the run starts (covers init + reset + run).
    assert tb.index("join_none") < tb.index("Initialise inputs and assert reset")


@pytest.mark.parametrize("item_id", MODULE_IDS)
def test_watchdog_budget_exceeds_run(item_id: str) -> None:
    """The watchdog cycle budget must be strictly larger than the number of
    clock edges a healthy run consumes, so it never fires on a passing TB."""
    res = generate_files(item_id, {})
    tb = next(f.text for f in res.files if f.kind == "tb")
    # The watchdog counts posedges with a static-int for-loop (Verilator-clean):
    # for (watchdog_i = 0; watchdog_i < N; watchdog_i++) @(posedge clk);
    budget = int(re.search(r"watchdog_i < (\d+);", tb).group(1))
    # Count every wait the stimulus performs (reset hold + directed cycles): the
    # reset/negedge ``repeat`` waits plus bare single-edge waits. The watchdog's
    # own for-loop starts with ``for`` (not ``repeat`` or a bare ``@``), so it is
    # not counted here — no subtraction needed.
    edges = 0
    for m in re.finditer(r"repeat \((\d+)\) @\((?:pos|neg)edge clk\);", tb):
        edges += int(m.group(1))
    edges += len(re.findall(r"^\s*@\((?:pos|neg)edge clk\);", tb, flags=re.M))
    assert budget > edges > 0


def test_watchdog_preserves_pass_and_finish() -> None:
    tb = _tb("pwm")
    assert "SMOKE PASS: pwm" in tb
    assert "$finish;" in tb


# --------------------------------------------------------------------------- #
# 2. Stimulus tables: width mask + per-port constraints
# --------------------------------------------------------------------------- #


def test_constrain_value_masks_to_width() -> None:
    # No constraint: value is masked to the port width (byte-identical for
    # in-range values, truncated for out-of-range ones).
    assert _constrain_value(5, 4, None) == 5
    assert _constrain_value(0x1F, 4, None) == 0x0F  # 31 & 0b1111
    assert _constrain_value(7, 1, None) == 1


def test_constrain_value_clamps_then_masks() -> None:
    c = PortConstraint(min_value=2, max_value=10)
    assert _constrain_value(0, 8, c) == 2  # clamped up
    assert _constrain_value(255, 8, c) == 10  # clamped down
    assert _constrain_value(6, 8, c) == 6  # untouched
    # Clamp happens before the mask: a max of 10 fits 4 bits, so no truncation.
    assert _constrain_value(255, 4, c) == 10


def test_in_range_vectors_are_byte_identical_via_masking() -> None:
    """The real pwm spec (values already fit ``duty``'s width) must render the
    same driven literals whether or not masking is applied — the no-op case."""
    opts, rtl = _pwm_ctx(duty_input="port")
    real = pwm.tb_spec(opts)
    tb = generate_tb(_FakeDef(real), opts, rtl)
    # duty is RES=8 bits; its drives are the raw spec values, width 8.
    assert "duty = 8'd0;" in tb
    assert "duty = 8'd128;" in tb  # mid = 1 << 7
    assert "duty = 8'd255;" in tb  # hi = (1<<8)-1


def test_port_constraint_bounds_driven_value() -> None:
    """A per-port constraint on the spec clamps the driven literal (and the
    width mask still applies on top)."""
    opts, rtl = _pwm_ctx(duty_input="port")
    spec = TbSpec(
        clock="clk",
        reset="rst",
        reset_cycles=2,
        vectors=[{"duty": 300}],  # exceeds 8-bit port and the constraint max
        checks=[],
        port_constraints={"duty": PortConstraint(min_value=1, max_value=200)},
    )
    tb = generate_tb(_FakeDef(spec), opts, rtl)
    assert "duty = 8'd200;" in tb  # clamped to 200, fits 8 bits
    assert "8'd300" not in tb


# --------------------------------------------------------------------------- #
# 3. Assertion-wiring hook
# --------------------------------------------------------------------------- #


# Modules that attach a real ``TbSpec.assertion_spec`` (P3-05a wiring), under
# *default* options — which is what ``_tb`` builds.
#
# pwm is deliberately absent: only its counter is reset and `pwm_out` is
# combinational from it, so there is no reset value that is true of every
# configuration. Attaching a property that merely usually holds would be worse
# than attaching none.
#
# edge-detector is present because `registered_output` defaults to True, making
# `pulse` a flop with a real reset value. Its combinational-output cases emit no
# SVA — covered by test_edge_detector_combinational_output_has_no_sva below,
# since this parametrization only ever sees default options.
_MODULES_WITH_ASSERTIONS = {
    "clock-divider",
    "debouncer",
    "edge-detector",
    "gray-counter",
    "lfsr",
    "rr-arbiter",
}


@pytest.mark.parametrize("item_id", MODULE_IDS)
def test_assertion_hook_emits_sva_only_for_wired_modules(item_id: str) -> None:
    """The SVA block appears exactly for modules that declare an assertion_spec.

    Was ``test_assertion_hook_inert_for_current_modules`` while no module used
    the hook. It is not enough to relax that to "some modules may emit SVA" —
    the useful invariant is the *exact* correspondence, so an accidental spec
    (or an accidentally dropped one) still fails a test.
    """
    assert pwm.tb_spec  # sanity
    tb = _tb(item_id)
    if item_id in _MODULES_WITH_ASSERTIONS:
        assert "// Concurrent assertions (SVA)" in tb
        assert "assert property" in tb
    else:
        assert "assert property" not in tb
        assert "Concurrent assertions (SVA)" not in tb


def test_edge_detector_combinational_output_has_no_sva() -> None:
    """`registered_output=False` makes `pulse` a continuous assign.

    There is then no reset value to assert — `pulse` follows `d` even while
    reset is asserted — so the module must attach nothing rather than a
    property that only holds in the registered configuration.
    """
    from semicraft_core.modules import edge_detector

    opts = edge_detector.MODULE.options_model.model_validate({"registered_output": False})
    assert edge_detector.MODULE.tb_spec(opts).assertion_spec is None

    opts_registered = edge_detector.MODULE.options_model.model_validate(
        {"registered_output": True}
    )
    assert edge_detector.MODULE.tb_spec(opts_registered).assertion_spec is not None


def test_pwm_attaches_no_assertion_spec() -> None:
    """pwm is intentionally unwired — see _MODULES_WITH_ASSERTIONS.

    Pinned so that "pwm has no SVA" stays a deliberate decision with a stated
    reason, rather than something that could be silently changed.
    """
    opts = pwm.MODULE.options_model.model_validate({})
    assert pwm.MODULE.tb_spec(opts).assertion_spec is None


@pytest.mark.parametrize("item_id", sorted(_MODULES_WITH_ASSERTIONS))
def test_wired_module_assertions_use_rendered_reset_name(item_id: str) -> None:
    """Assertion text must name the *rendered* reset net, not the canonical one.

    A module writes canonical names (``rst``); ``build_name_map`` renders an
    active-low reset as ``rst_n``. Without the restyle step in ``generate_tb``
    the emitted text would reference a net that does not exist — and since
    active-low is the default, that would be broken out of the box.

    The reset name reaches the text by two different routes, so this checks the
    net name rather than one idiom: a guarded item emits ``disable iff (!rst_n)``,
    while ``ResetKnownValue`` emits ``$rose(rst_n)`` and is deliberately
    *unguarded* (it is the assertion *about* reset, so disabling it during reset
    would defeat it). Modules carrying only that item therefore have no
    ``disable iff`` at all.
    """
    tb = _tb(item_id)  # default options => active-low reset
    sva = tb[tb.index("// Concurrent assertions (SVA)") :]

    assert "rst_n" in sva
    # No bare canonical `rst` anywhere in the SVA block. `\brst\b` cannot match
    # inside `rst_n` (`_` is a word character), so this catches exactly the
    # unrestyled spelling.
    assert re.search(r"\brst\b", sva) is None, (
        f"{item_id}: SVA block references the canonical reset name rather than "
        f"the rendered one:\n{sva}"
    )


def test_assertion_spec_wires_into_tb() -> None:
    """A synthetic module attaching an assertion_spec gets a rendered SVA block
    whose property text comes from generate_assertions."""
    opts, rtl = _pwm_ctx(duty_input="port")
    spec = TbSpec(
        clock="clk",
        reset="rst",
        reset_cycles=2,
        vectors=[{}],
        checks=[],
        assertion_spec=AssertionSpec(
            clock="clk",
            items=[NoUnknown(name="pwm_out_known", signal="pwm_out")],
        ),
    )
    tb = generate_tb(_FakeDef(spec), opts, rtl)
    assert "// Concurrent assertions (SVA)" in tb
    assert "pwm_out_known: assert property (@(posedge clk) !$isunknown(pwm_out))" in tb
    assert '$fatal(1, "SVA FAIL: pwm_out_known");' in tb


# --------------------------------------------------------------------------- #
# 4. Expected values still come only from TbSpec.checks
# --------------------------------------------------------------------------- #


def test_checks_render_exactly_the_spec_expected_values() -> None:
    """Every SMOKE FAIL expected literal corresponds to a Check in the spec —
    the generator neither drops nor invents expected values."""
    opts, rtl = _pwm_ctx(duty_input="port")
    spec = pwm.tb_spec(opts)
    tb = generate_tb(_FakeDef(spec), opts, rtl)
    rendered_expected = re.findall(r"expected (\d+), got", tb)
    assert len(rendered_expected) == len(spec.checks)
    assert sorted(int(x) for x in rendered_expected) == sorted(c.expected for c in spec.checks)


# --------------------------------------------------------------------------- #
# 5. Naming style reaches every edge-waiting construct
# --------------------------------------------------------------------------- #

# A prefix + camelCase style renames every net, including the clock. Until
# P4-01 the TB renderer held the clock name in a module-level constant
# (`_CLOCK_NAME = "clk"`), which was right only for the default style: with a
# prefix the DUT clock rendered `p_clk` while every `@(posedge clk)` in the
# stimulus and the watchdog still said `clk`, so the emitted testbench did not
# compile at all. No golden case exercises a naming style, so nothing caught
# it; the reference IP's Verilator run gate did.
_STYLED = {"naming": {"convention": "camel", "prefix": "p_"}}


@pytest.mark.parametrize("item_id", MODULE_IDS)
def test_every_edge_wait_uses_the_styled_clock(item_id: str) -> None:
    """Every ``@(edge X)`` in a styled TB must name the styled clock net.

    Checked as a set rather than a substring search so an edge wait on some
    *other* net would fail too, not just an unstyled one.
    """
    res = generate_files(item_id, _STYLED)
    tb = next(f.text for f in res.files if f.kind == "tb" and f.path.endswith("_tb.sv"))
    edges = set(re.findall(r"@\((?:pos|neg)edge (\w+)\)", tb))
    assert edges == {"p_clk"}, (
        f"{item_id}: testbench waits on {sorted(edges)}; under this naming style "
        f"the only clock net the RTL declares is 'p_clk'"
    )


@pytest.mark.parametrize("item_id", MODULE_IDS)
def test_styled_tb_declares_every_net_it_waits_on(item_id: str) -> None:
    """The net an edge wait names must actually be declared in the TB."""
    res = generate_files(item_id, _STYLED)
    tb = next(f.text for f in res.files if f.kind == "tb" and f.path.endswith("_tb.sv"))
    for net in set(re.findall(r"@\((?:pos|neg)edge (\w+)\)", tb)):
        assert re.search(rf"^\s*(?:logic|reg|wire)\b[^;]*\b{net}\b", tb, flags=re.M), (
            f"{item_id}: testbench waits on '{net}', which it never declares:\n{tb}"
        )
