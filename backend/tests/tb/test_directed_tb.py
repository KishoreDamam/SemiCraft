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


@pytest.mark.parametrize("item_id", MODULE_IDS)
def test_assertion_hook_inert_for_current_modules(item_id: str) -> None:
    """No current module declares an assertion_spec, so no SVA block is emitted
    and the run gate / goldens are unaffected by the hook."""
    assert pwm.tb_spec  # sanity
    tb = _tb(item_id)
    assert "assert property" not in tb
    assert "Concurrent assertions (SVA)" not in tb


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
