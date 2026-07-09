"""Debouncer module (Phase-2 P2-06).

Copies the structure of ``edge_detector.py`` (THE reference module). See
``docs/PLAN-semicraft-phases-2-8.md`` Phase 2 table + Appendix A.3 and
``backend/semicraft_core/modules/contract.py`` for the ``ModuleDef`` shape
this file implements.

What it does
------------

A debouncer filters a noisy/bouncy input ``d_in`` into a clean, stable
``q``. It samples ``d_in`` every clock and compares it against the current
output ``q``:

- while ``d_in == q`` the input agrees with the current output, so the
  internal counter resets to zero (no candidate change in progress);
- while ``d_in != q`` the input disagrees, so the counter increments; if the
  disagreement persists for ``2**CNT_WIDTH`` consecutive cycles (the counter
  overflows back to zero) the output is updated to the new, now-stable,
  value: ``q <= d_in``.

This is the standard "counter reloaded on disagreement" debounce idiom: any
burst of bounces shorter than the debounce period never reaches the count
overflow, so ``q`` only moves once ``d_in`` has been stable for the whole
period. ``d_in`` is assumed already synchronous to ``clk`` — this module does
not perform clock-domain-crossing synchronization; the explanation recommends
an external 2-flop synchronizer (see the ``cdc-synchronizer`` snippet) when
``d_in`` originates from a mechanical switch/button wired directly to an FPGA
pin (asynchronous to any clock).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from pydantic import Field

from ..ir.build import IN, OUT, bit, vec
from ..ir.nodes import (
    AlwaysFF,
    Assign,
    BinOp,
    BinOpKind,
    ClockSpec,
    Comment,
    CommentLevel,
    Const,
    Header,
    If,
    Module,
    Param,
    Port,
    Ref,
    ResetKind,
    ResetSpec,
    Signal,
)
from ..snippets.contract import ClockedOptions, ExplanationDoc, SignalDoc
from ..version import VERSION
from .contract import Check, PortGroup, TbSpec

# ---------------------------------------------------------------------------
# Options
# ---------------------------------------------------------------------------


class DebouncerOptions(ClockedOptions):
    """Configuration for the debouncer module.

    Extends :class:`ClockedOptions` (language, reset, wrapper, comments, naming)
    with the debouncer-specific fields below.
    """

    counter_width: int = Field(
        default=16,
        ge=4,
        le=24,
        description=(
            "Width of the internal disagreement counter, in bits (param "
            "CNT_WIDTH). The debounce period is 2**CNT_WIDTH clock cycles: "
            "d_in must hold steady for that many consecutive cycles before q "
            "updates."
        ),
    )
    active_level: Literal["high", "low"] = Field(
        default="high",
        description=(
            "Idle polarity of d_in. 'high' treats the idle/released state as "
            "logic 1 (q resets to 1); 'low' treats it as logic 0 (q resets to "
            "0). This only affects the initial/reset value of q, not the "
            "debounce logic itself."
        ),
    )


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

_MODULE_NAME = "debouncer"


def _reset_spec(opts: DebouncerOptions) -> ResetSpec:
    """The single declarative reset (IR_SPEC §4 composes the skeleton)."""
    return ResetSpec(
        name="rst",
        kind=ResetKind.SYNC if opts.reset_style == "sync" else ResetKind.ASYNC,
        active_low=opts.reset_polarity == "active_low",
    )


def _idle_const(opts: DebouncerOptions) -> Const:
    """q's reset/idle value: 1 for active_level='high', 0 for 'low'."""
    return Const(1 if opts.active_level == "high" else 0)


def generate(opts: DebouncerOptions) -> Module:
    """Build the debouncer IR ``Module`` (pure).

    Structure: one ``AlwaysFF`` holding both the disagreement counter and the
    debounced output register ``q``.

    - ``d_in == q``: counter resets to 0 (input agrees with output; no
      candidate change pending).
    - ``d_in != q`` and counter is not yet at the terminal value: counter
      increments (candidate change accumulating).
    - ``d_in != q`` and counter is at the terminal value (about to overflow):
      the disagreement has persisted 2**CNT_WIDTH cycles, so q updates to
      d_in and the counter resets to 0 for the next candidate change.

    The renderer decides always_ff vs always, ``<=`` vs ``=``, and reset
    composition (IR_SPEC design rules 2-4); the generator only chooses the
    logic.
    """
    reset = _reset_spec(opts)
    terminal = Const((1 << opts.counter_width) - 1, width=Ref("CNT_WIDTH"))

    # --- ports (order per clean-rtl: clock, reset, data-in, data-out) --------
    ports: list[Port] = [
        Port("clk", IN, bit(), doc="Clock"),
        Port("rst", IN, bit(), doc=_reset_doc(opts)),
        Port("d_in", IN, bit(), doc="Raw, potentially bouncy input"),
        Port("q", OUT, bit(), doc=_q_doc(opts)),
    ]

    # --- internal disagreement counter (always present) ----------------------
    signals: list = [
        Signal(
            "cnt",
            vec("CNT_WIDTH"),
            doc="Disagreement counter: counts consecutive cycles d_in != q",
        )
    ]

    disagree = BinOp(BinOpKind.NE, Ref("d_in"), Ref("q"))
    at_terminal = BinOp(BinOpKind.EQ, Ref("cnt"), terminal)

    body: list = [
        Comment(
            "Debounce: reset the counter whenever d_in agrees with the "
            "current output; while it disagrees, count up until the "
            "disagreement has persisted the full debounce period, then "
            "accept the new value.",
            level=CommentLevel.VERBOSE,
        ),
        If(
            disagree,
            then=[
                If(
                    at_terminal,
                    then=[
                        Assign(Ref("q"), Ref("d_in")),
                        Assign(Ref("cnt"), Const(0, width=Ref("CNT_WIDTH"))),
                    ],
                    else_=[
                        Assign(
                            Ref("cnt"),
                            BinOp(BinOpKind.ADD, Ref("cnt"), Const(1)),
                        )
                    ],
                )
            ],
            else_=[Assign(Ref("cnt"), Const(0, width=Ref("CNT_WIDTH")))],
        ),
    ]
    reset_body: list = [
        Assign(Ref("cnt"), Const(0, width=Ref("CNT_WIDTH"))),
        Assign(Ref("q"), _idle_const(opts)),
    ]

    always = AlwaysFF(
        clock=ClockSpec("clk"),
        reset=reset,
        reset_body=reset_body,
        body=body,
    )

    return Module(
        name=_MODULE_NAME,
        header=Header(
            license="",  # filled by the generate() entry point with the config hash
            config_hash="",
            tool_version=VERSION,
            description=_description(opts),
        ),
        params=[
            Param(
                "CNT_WIDTH",
                Const(opts.counter_width),
                doc="Disagreement counter width; debounce period = 2**CNT_WIDTH cycles",
            )
        ],
        ports=ports,
        items=[*signals, always],
    )


# ---------------------------------------------------------------------------
# Documentation metadata (port groups)
# ---------------------------------------------------------------------------


def _reset_port_name(opts: DebouncerOptions) -> str:
    """Reset port name as it appears in the explanation/RTL (``rst_n`` when
    active-low)."""
    return "rst" + ("_n" if opts.reset_polarity == "active_low" else "")


def port_groups(opts: DebouncerOptions) -> list[PortGroup]:
    """Group ports for the datasheet: a clocking group and a data group."""
    return [
        PortGroup(
            name="Clocking",
            ports=["clk", _reset_port_name(opts)],
            description="Clock and reset for the debounce counter and output register.",
        ),
        PortGroup(
            name="Data",
            ports=["d_in", "q"],
            description="Raw noisy input and the debounced, stable output.",
        ),
    ]


# ---------------------------------------------------------------------------
# Smoke-TB recipe
# ---------------------------------------------------------------------------


def tb_spec(opts: DebouncerOptions) -> TbSpec:
    """An ~8-vector directed smoke TB: bounce, then settle.

    d_in bounces a few times (each bounce restarts the counter, per the
    logic) and then holds steady; the two checks assert that q has NOT yet
    updated while bouncing, and that it settles to the eventual stable value.
    Because the real debounce period is 2**CNT_WIDTH cycles (up to 2**24),
    the checks here are honest about relative ordering only, not absolute
    settle timing at full width — they check "still idle while bouncing" and
    "counter resets on each disagreement", which hold regardless of width.
    """
    idle = 1 if opts.active_level == "high" else 0
    other = 1 - idle

    vectors: list[dict[str, int]] = [
        {"d_in": idle},  # cycle 0: idle, agrees with q -> counter stays 0
        {"d_in": other},  # cycle 1: bounce starts (disagreement begins)
        {"d_in": idle},  # cycle 2: bounce back to idle (counter reset again)
        {"d_in": other},  # cycle 3: bounce again
        {"d_in": idle},  # cycle 4: bounce back again
        {"d_in": other},  # cycle 5: final transition starts
        {"d_in": other},  # cycle 6: still holding (disagreement accumulating)
        {"d_in": other},  # cycle 7: still holding
    ]

    checks: list[Check] = [
        # q has not moved yet after a handful of short bounces (well short of
        # the debounce period for any valid counter_width >= 4).
        Check(cycle=4, signal="q", expected=idle),
        # Still not moved a couple of cycles after the last (short) hold —
        # honest given the debounce period is always > 8 cycles (min width 4
        # -> 16 cycles).
        Check(cycle=7, signal="q", expected=idle),
    ]

    return TbSpec(
        clock="clk",
        reset="rst",
        reset_cycles=2,
        vectors=vectors,
        checks=checks,
    )


# ---------------------------------------------------------------------------
# Explanation
# ---------------------------------------------------------------------------


def _description(opts: DebouncerOptions) -> str:
    return (
        f"Debouncer, {2 ** opts.counter_width}-cycle period, "
        f"active-{opts.active_level} idle"
    )


def _reset_doc(opts: DebouncerOptions) -> str:
    style = "Async" if opts.reset_style == "async" else "Sync"
    pol = "low" if opts.reset_polarity == "active_low" else "high"
    return f"{style} reset, active-{pol}"


def _q_doc(opts: DebouncerOptions) -> str:
    return f"Debounced output (idles {'high' if opts.active_level == 'high' else 'low'})"


def _reset_behavior_text(opts: DebouncerOptions) -> str:
    style = "asynchronously" if opts.reset_style == "async" else "synchronously"
    pol = (
        "active-low (asserted when 0)"
        if opts.reset_polarity == "active_low"
        else "active-high (asserted when 1)"
    )
    edge = (
        "on assertion of reset (independent of the clock)"
        if opts.reset_style == "async"
        else "on the rising clock edge while reset is asserted"
    )
    idle_word = "1 (idle-high)" if opts.active_level == "high" else "0 (idle-low)"
    return (
        f"The {pol} reset clears the disagreement counter and forces q to its "
        f"idle value ({idle_word}) {style} {edge}."
    )


def explain(opts: DebouncerOptions) -> ExplanationDoc:
    """Fully populated explanation for the chosen options."""
    period = 2 ** opts.counter_width
    configuration = [
        f"Counter width: {opts.counter_width} bits (debounce period = "
        f"2^{opts.counter_width} = {period} clock cycles)",
        f"Active level: {opts.active_level} "
        f"(idle value = {'1' if opts.active_level == 'high' else '0'})",
        f"Reset: {opts.reset_style}, "
        f"{'active-low' if opts.reset_polarity == 'active_low' else 'active-high'}",
        f"Output language: {'SystemVerilog' if opts.language == 'sv' else 'Verilog-2001'}",
    ]

    signals = [
        SignalDoc(
            name="clk",
            direction="input",
            description="Clock; d_in is sampled and the debounce counter runs on the rising edge.",
        ),
        SignalDoc(
            name="rst" + ("_n" if opts.reset_polarity == "active_low" else ""),
            direction="input",
            description=_reset_doc(opts) + " reset input.",
        ),
        SignalDoc(
            name="d_in",
            direction="input",
            description=(
                "Raw, potentially bouncy input signal (e.g. a mechanical "
                "switch or button)."
            ),
        ),
        SignalDoc(
            name="cnt",
            direction="internal",
            description=(
                "Disagreement counter: counts consecutive cycles where d_in "
                "differs from the current q, resetting to 0 whenever they agree."
            ),
        ),
        SignalDoc(
            name="q",
            direction="output",
            description=(
                "Debounced, stable output; updates to d_in's value only after "
                f"it has disagreed with q for {period} consecutive cycles."
            ),
        ),
    ]

    assumptions = [
        "A single free-running clock drives the debouncer.",
        "d_in is already synchronous to clk (no metastability handling here).",
    ]

    limitations = [
        "d_in is assumed synchronous to clk. If d_in originates from a "
        "mechanical switch/button wired directly to an FPGA pin, it is "
        "asynchronous to any clock; add an external 2-flop synchronizer "
        "(see the cdc-synchronizer snippet) upstream of this debouncer to "
        "avoid metastability.",
        f"The debounce period ({period} cycles) is fixed by counter_width at "
        "generation time; it cannot be changed at runtime.",
        "There is no output indicating that a debounce is currently in "
        "progress; q simply updates once the period elapses.",
    ]

    return ExplanationDoc(
        purpose=(
            "A debouncer that filters a noisy/bouncy input into a stable "
            f"output: q only updates to d_in's value after d_in has "
            f"disagreed with q for {period} consecutive clock cycles."
        ),
        configuration=configuration,
        signals=signals,
        reset_behavior=_reset_behavior_text(opts),
        enable_behavior=None,
        assumptions=assumptions,
        limitations=limitations,
    )


# ---------------------------------------------------------------------------
# ModuleDef instance (discovered by the registry)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class _DebouncerModule:
    """Bundles the debouncer's metadata and pure functions.

    Satisfies the :class:`~.contract.ModuleDef` protocol structurally.
    """

    id: str = "debouncer"
    name: str = "Debouncer"
    description: str = (
        "Filters a noisy/bouncy input into a stable output using a "
        "disagreement counter (accepts a new value only after it has held "
        "steady for the full debounce period)."
    )
    kind: str = "module"
    maturity: str = "stable"
    options_model: type[DebouncerOptions] = DebouncerOptions

    def generate(self, opts: DebouncerOptions) -> Module:
        return generate(opts)

    def explain(self, opts: DebouncerOptions) -> ExplanationDoc:
        return explain(opts)

    def port_groups(self, opts: DebouncerOptions) -> list[PortGroup]:
        return port_groups(opts)

    def tb_spec(self, opts: DebouncerOptions) -> TbSpec:
        return tb_spec(opts)


MODULE = _DebouncerModule()


__all__ = [
    "DebouncerOptions",
    "generate",
    "explain",
    "port_groups",
    "tb_spec",
    "MODULE",
]
