"""Round-robin arbiter module (Phase-2 P2-10).

Copies the structure of ``edge_detector.py`` (THE reference module). See
``docs/PLAN-semicraft-phases-2-8.md`` Phase 2 table + Appendix A.3 and
``backend/semicraft_core/modules/contract.py`` for the ``ModuleDef`` shape
this file implements.

What it does
------------

An N-way round-robin arbiter grants a shared resource to at most one of ``N``
requesters (``req[N-1:0]``) each cycle, rotating priority so that under
sustained contention every requester is served in turn. The grant is one-hot
(exactly one bit set when any request is pending, all-zero otherwise), and
``grant_valid`` is simply ``|grant``.

Scheme — mask-based two-pass rotate priority
--------------------------------------------

A pointer register ``ptr`` (``clog2(N)`` bits) names the requester that
currently holds *highest* priority. From it we build a thermometer mask of the
requesters at-or-above the pointer::

    mask       = {N{1'b1}} << ptr        // ones in positions [ptr .. N-1]
    masked_req = req & mask

Two fixed-priority (lowest-index-first) encoders run in parallel:

    masked_gnt   = lowest set bit of masked_req   (the "rotated" window)
    unmasked_gnt = lowest set bit of req          (wrap-around fallback)

The winner is the masked encoder when the masked window has any requester,
otherwise the unmasked encoder (which wraps priority back to index 0)::

    grant_nxt = |masked_req ? masked_gnt : unmasked_gnt

Each fixed-priority bit is the classic ``req[i] & ~|req[i-1:0]`` idiom, so
exactly one bit of ``grant_nxt`` is set whenever ``req`` is non-zero and none is
set when ``req == 0`` — verified by construction (see the explanation).

Pointer update / fairness
-------------------------

On the cycle a grant is issued, the pointer advances so the just-served
requester drops to lowest priority next time:

- ``hold_grant = False`` (pure rotate): ``ptr <= (granted_index + 1) mod N`` —
  the served requester rotates to the back, giving a strict round-robin order.
  Under full load each requester is served at least once every ``N`` cycles.
- ``hold_grant = True`` (hold): ``ptr <= granted_index`` — while the granted
  requester keeps asserting ``req`` it keeps the grant (no rotation preemption
  by others); only when it drops does priority move on to the next requester.

The ``(i+1) mod N`` wrap is resolved at generation time (``N`` is structural),
so the pointer only ever takes values ``0 .. N-1`` and the thermometer mask is
always well-formed.

grant_style
-----------

- ``registered`` (default, recommended): ``grant`` is a flop
  (``grant <= grant_nxt``), one cycle of latency, cleaner output timing — the
  combinational grant/priority path is kept off the module boundary.
- ``combinational``: ``grant`` is a continuous assignment of ``grant_nxt``
  (same-cycle grant, no latency, but a longer critical path from ``req`` through
  the two-pass priority network to ``grant``).

In both styles the pointer advances off the combinational decision
``grant_nxt`` each cycle, so the internal arbitration sequence — and therefore
fairness — is identical; ``registered`` only delays the *visible* grant by one
cycle.
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
    Bit,
    ClockSpec,
    Comment,
    CommentLevel,
    Concat,
    Const,
    ContAssign,
    Header,
    If,
    Module,
    Port,
    Ref,
    Repl,
    ResetKind,
    ResetSpec,
    Signal,
    Slice,
    Ternary,
    UnaryOp,
    UnaryOpKind,
)
from ..snippets.contract import ClockedOptions, ExplanationDoc, SignalDoc
from ..version import VERSION
from .contract import Check, PortGroup, TbSpec

# ---------------------------------------------------------------------------
# Options
# ---------------------------------------------------------------------------


class RrArbiterOptions(ClockedOptions):
    """Configuration for the round-robin arbiter module.

    Extends :class:`ClockedOptions` (language, reset, wrapper, comments, naming)
    with the arbiter-specific fields below.
    """

    num_requesters: int = Field(
        default=4,
        ge=2,
        le=16,
        description=(
            "Number of requesters N. Fixes the width of req/grant (N bits) and "
            "the pointer width (clog2(N) bits). N is structural: the priority "
            "network is generated for this exact N."
        ),
    )
    grant_style: Literal["registered", "combinational"] = Field(
        default="registered",
        description=(
            "'registered' (recommended): grant is a flop (one-cycle latency, "
            "cleaner boundary timing). 'combinational': grant is a same-cycle "
            "continuous assignment of the rotated-priority decision (no latency, "
            "longer critical path)."
        ),
    )
    hold_grant: bool = Field(
        default=False,
        description=(
            "When True, while the granted requester keeps asserting req the "
            "grant holds on it (no rotation preemption by others); priority "
            "rotates only once it deasserts. When False, priority rotates after "
            "every grant (pure round-robin)."
        ),
    )


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

_MODULE_NAME = "rr_arbiter"


def _ptr_width(opts: RrArbiterOptions) -> int:
    """Pointer width = clog2(N) bits (>= 1); indexes requesters 0..N-1."""
    return max(1, (opts.num_requesters - 1).bit_length())


def _reset_spec(opts: RrArbiterOptions) -> ResetSpec:
    """The single declarative reset (IR_SPEC §4 composes the skeleton)."""
    return ResetSpec(
        name="rst",
        kind=ResetKind.SYNC if opts.reset_style == "sync" else ResetKind.ASYNC,
        active_low=opts.reset_polarity == "active_low",
    )


def _priority_onehot(name: str, n: int) -> Concat:
    """One-hot vector selecting the lowest set bit of the N-bit signal ``name``.

    Bit ``i`` is ``name[i] & ~|name[i-1:0]`` (the classic fixed-priority,
    lowest-index-first encoder); bit 0 is just ``name[0]``. The ``Concat`` lists
    parts MSB-first, so index N-1 comes first and index 0 last.
    """
    parts = []
    for i in reversed(range(n)):
        bit_i = Bit(Ref(name), Const(i))
        if i == 0:
            parts.append(bit_i)
        else:
            lower = Slice(Ref(name), Const(i - 1), Const(0))
            parts.append(BinOp(BinOpKind.AND, bit_i, UnaryOp(UnaryOpKind.RED_NOR, lower)))
    return Concat(parts)


def _pointer_update(opts: RrArbiterOptions) -> If:
    """If/elif chain advancing ``ptr`` based on which bit of ``grant_nxt`` is set.

    For grant of index ``i`` the next pointer is ``(i+1) mod N`` (rotate) or
    ``i`` (hold_grant). With no grant (grant_nxt == 0) no branch fires and ``ptr``
    holds its value.
    """
    n = opts.num_requesters
    pw = _ptr_width(opts)

    def next_val(i: int) -> Const:
        nxt = i if opts.hold_grant else (i + 1) % n
        return Const(nxt, width=Const(pw))

    def branch(i: int):
        return Bit(Ref("grant_nxt"), Const(i)), [Assign(Ref("ptr"), next_val(i))]

    cond0, then0 = branch(0)
    elifs = [branch(i) for i in range(1, n)]
    return If(cond0, then=then0, elifs=elifs)


def generate(opts: RrArbiterOptions) -> Module:
    """Build the round-robin arbiter IR ``Module`` (pure).

    Structure (mask-based two-pass rotate priority, see module docstring):

    - ``masked_req = req & ({N{1'b1}} << ptr)`` — requesters at-or-above ptr;
    - ``masked_gnt`` / ``unmasked_gnt`` — lowest-index-first one-hot encoders;
    - ``grant_nxt = |masked_req ? masked_gnt : unmasked_gnt`` — the winner;
    - ``grant`` — registered (``grant <= grant_nxt``) or combinational
      (``assign grant = grant_nxt``) per ``grant_style``;
    - ``grant_valid = |grant``;
    - ``ptr`` register — advances past the granted index (rotate) or holds it.

    The renderer decides always_ff vs always, ``<=`` vs ``=``, and reset
    composition (IR_SPEC design rules 2-4); the generator only chooses the logic.
    """
    n = opts.num_requesters
    reset = _reset_spec(opts)
    zero_ptr = Const(0, width=Const(_ptr_width(opts)))

    # --- ports (order per clean-rtl: clock, reset, request-in, grant-out) ----
    ports = _ports(opts)

    # --- internal signals ----------------------------------------------------
    signals = [
        Signal("ptr", vec(_ptr_width(opts)), doc="Highest-priority requester index (rotates)"),
        Signal("masked_req", vec(n), doc="Requests at or above the priority pointer"),
        Signal("masked_gnt", vec(n), doc="Lowest-index grant within the masked window"),
        Signal("unmasked_gnt", vec(n), doc="Lowest-index grant over all requests (wrap-around)"),
        Signal("grant_nxt", vec(n), doc="Combinational rotate-priority grant decision"),
    ]

    # mask = {N{1'b1}} << ptr ; masked_req = req & mask
    mask = BinOp(BinOpKind.SHL, Repl(Const(n), Const(1)), Ref("ptr"))
    masked_req = ContAssign(Ref("masked_req"), BinOp(BinOpKind.AND, Ref("req"), mask))
    masked_gnt = ContAssign(Ref("masked_gnt"), _priority_onehot("masked_req", n))
    unmasked_gnt = ContAssign(Ref("unmasked_gnt"), _priority_onehot("req", n))
    grant_nxt = ContAssign(
        Ref("grant_nxt"),
        Ternary(
            UnaryOp(UnaryOpKind.RED_OR, Ref("masked_req")),
            Ref("masked_gnt"),
            Ref("unmasked_gnt"),
        ),
    )
    grant_valid = ContAssign(Ref("grant_valid"), UnaryOp(UnaryOpKind.RED_OR, Ref("grant")))

    scheme_comment = Comment(
        "Round-robin: mask requests at/above the pointer, take the lowest such "
        "(else wrap to the lowest overall), then advance the pointer past the "
        "granted requester so it rotates to lowest priority.",
        level=CommentLevel.VERBOSE,
    )

    items: list = [
        *signals,
        scheme_comment,
        masked_req,
        masked_gnt,
        unmasked_gnt,
        grant_nxt,
    ]

    if opts.grant_style == "combinational":
        # grant is a same-cycle continuous assignment; only ptr is clocked.
        items.append(ContAssign(Ref("grant"), Ref("grant_nxt")))
        items.append(grant_valid)
        items.append(
            AlwaysFF(
                clock=ClockSpec("clk"),
                reset=reset,
                reset_body=[Assign(Ref("ptr"), zero_ptr)],
                body=[_pointer_update(opts)],
            )
        )
    else:
        # grant is a flop; register it alongside the pointer in one process.
        items.append(grant_valid)
        items.append(
            AlwaysFF(
                clock=ClockSpec("clk"),
                reset=reset,
                reset_body=[
                    Assign(Ref("ptr"), zero_ptr),
                    Assign(Ref("grant"), Const(0, width=Const(n))),
                ],
                body=[_pointer_update(opts), Assign(Ref("grant"), Ref("grant_nxt"))],
            )
        )

    return Module(
        name=_MODULE_NAME,
        header=Header(
            license="",  # filled by the generate() entry point with the config hash
            config_hash="",
            tool_version=VERSION,
            description=_description(opts),
        ),
        params=[],
        ports=ports,
        items=items,
    )


def _ports(opts: RrArbiterOptions):
    """Module ports (clock, reset, req in, grant/grant_valid out)."""
    n = opts.num_requesters
    return [
        Port("clk", IN, bit(), doc="Clock"),
        Port("rst", IN, bit(), doc=_reset_doc(opts)),
        Port("req", IN, vec(n), doc="Request lines, one per requester"),
        Port("grant", OUT, vec(n), doc=_grant_doc(opts)),
        Port("grant_valid", OUT, bit(), doc="High when a grant is asserted (|grant)"),
    ]


# ---------------------------------------------------------------------------
# Documentation metadata (port groups)
# ---------------------------------------------------------------------------


def _reset_port_name(opts: RrArbiterOptions) -> str:
    """Reset port name as it appears in the explanation/RTL (``rst_n`` when
    active-low)."""
    return "rst" + ("_n" if opts.reset_polarity == "active_low" else "")


def port_groups(opts: RrArbiterOptions) -> list[PortGroup]:
    """Group ports for the datasheet: a clocking group and an arbitration group."""
    return [
        PortGroup(
            name="Clocking",
            ports=["clk", _reset_port_name(opts)],
            description="Clock and reset for the priority pointer (and grant register).",
        ),
        PortGroup(
            name="Arbitration",
            ports=["req", "grant", "grant_valid"],
            description=(
                "Per-requester request lines, the one-hot grant, and its "
                "valid flag (|grant)."
            ),
        ),
    ]


# ---------------------------------------------------------------------------
# Smoke-TB recipe
# ---------------------------------------------------------------------------


def tb_spec(opts: RrArbiterOptions) -> TbSpec:
    """A ~10-vector directed smoke TB exercising rotation, single-request, and
    back-to-back grants.

    ``req`` is driven as an integer bitmask (one bit per requester). The checks
    are honest given the two-pass guarantee (the sole requester is always the
    winner) and account for the one-cycle latency of the ``registered`` grant
    style. They are declarative recipes; they are NOT executed yet (the P2-13 TB
    generator will consume this).
    """
    n = opts.num_requesters
    all_req = (1 << n) - 1
    only_lo = 1  # requester 0
    only_hi = 1 << (n - 1)  # top requester

    vectors: list[dict[str, int]] = [
        {"req": 0},  # cycle 0: idle
        {"req": only_lo},  # cycle 1: single request (requester 0)
        {"req": only_lo},  # cycle 2: still requesting
        {"req": all_req},  # cycle 3: full contention (rotation begins)
        {"req": all_req},  # cycle 4
        {"req": all_req},  # cycle 5
        {"req": all_req},  # cycle 6
        {"req": 0},  # cycle 7: idle again
        {"req": only_hi},  # cycle 8: single request (top requester)
        {"req": only_hi},  # cycle 9: back-to-back hold on the same requester
    ]

    latency = 1 if opts.grant_style == "registered" else 0

    checks: list[Check] = [
        # A pending request produces a valid grant (one cycle later if registered).
        Check(cycle=1 + latency, signal="grant_valid", expected=1),
        # With only requester 0 asserting, the two-pass encoder must grant it
        # regardless of the pointer state.
        Check(cycle=1 + latency, signal="grant", expected=only_lo),
        # No request -> no grant.
        Check(cycle=7 + latency, signal="grant_valid", expected=0),
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


def _description(opts: RrArbiterOptions) -> str:
    style = "registered" if opts.grant_style == "registered" else "combinational"
    hold = ", hold-grant" if opts.hold_grant else ""
    return f"{opts.num_requesters}-way round-robin arbiter, {style} grant{hold}"


def _reset_doc(opts: RrArbiterOptions) -> str:
    style = "Async" if opts.reset_style == "async" else "Sync"
    pol = "low" if opts.reset_polarity == "active_low" else "high"
    return f"{style} reset, active-{pol}"


def _grant_doc(opts: RrArbiterOptions) -> str:
    style = "registered" if opts.grant_style == "registered" else "combinational"
    return f"One-hot grant (zero when idle), {style}"


def _reset_behavior_text(opts: RrArbiterOptions) -> str:
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
    target = (
        "the priority pointer to 0 and the grant register to all-zero"
        if opts.grant_style == "registered"
        else "the priority pointer to 0"
    )
    return (
        f"The {pol} reset clears {target} {style} {edge}, so after reset "
        "requester 0 holds highest priority and no grant is asserted."
    )


def explain(opts: RrArbiterOptions) -> ExplanationDoc:
    """Fully populated explanation for the chosen options."""
    n = opts.num_requesters
    grant_word = (
        "registered (grant is a flop, one extra cycle of latency, cleaner "
        "boundary timing)"
        if opts.grant_style == "registered"
        else "combinational (grant asserts the same cycle, no latency, longer "
        "critical path from req through the priority network)"
    )
    hold_word = (
        "hold — while the granted requester keeps asserting req it keeps the "
        "grant; priority rotates only once it deasserts"
        if opts.hold_grant
        else "rotate — priority advances past the granted requester every grant "
        "(pure round-robin)"
    )
    configuration = [
        f"Requesters: {n} (req/grant are {n} bits, pointer is {_ptr_width(opts)} bits)",
        f"Grant style: {grant_word}",
        f"Arbitration policy: {hold_word}",
        f"Reset: {opts.reset_style}, "
        f"{'active-low' if opts.reset_polarity == 'active_low' else 'active-high'}",
        f"Output language: {'SystemVerilog' if opts.language == 'sv' else 'Verilog-2001'}",
    ]

    signals = [
        SignalDoc(
            name="clk",
            direction="input",
            description=(
                "Clock; the priority pointer (and grant register) update on the "
                "rising edge."
            ),
        ),
        SignalDoc(
            name="rst" + ("_n" if opts.reset_polarity == "active_low" else ""),
            direction="input",
            description=_reset_doc(opts) + " reset input.",
        ),
        SignalDoc(
            name="req",
            direction="input",
            description=f"{n} request lines; req[i] asserts that requester i wants the resource.",
        ),
        SignalDoc(
            name="ptr",
            direction="internal",
            description=(
                "Priority pointer: index of the requester that currently holds "
                "highest priority. Advances past the granted index (or holds it "
                "when hold_grant is set)."
            ),
        ),
        SignalDoc(
            name="masked_req",
            direction="internal",
            description="req masked to the requesters at or above ptr (req & ({N{1'b1}} << ptr)).",
        ),
        SignalDoc(
            name="grant_nxt",
            direction="internal",
            description=(
                "Combinational grant decision: the lowest-index request in the "
                "masked window, or — if that window is empty — the lowest-index "
                "request overall (wrap-around)."
            ),
        ),
        SignalDoc(
            name="grant",
            direction="output",
            description=(
                "One-hot grant (all-zero when no request is pending), "
                + (
                    "registered (asserted one cycle after the decision)."
                    if opts.grant_style == "registered"
                    else "combinational (asserted the same cycle as the request)."
                )
            ),
        ),
        SignalDoc(
            name="grant_valid",
            direction="output",
            description="High whenever a grant is asserted; equal to |grant.",
        ),
    ]

    assumptions = [
        "A single free-running clock drives the arbiter; req is sampled synchronously to it.",
        "Requesters keep req asserted until granted (there is no separate "
        "grant-acknowledge handshake).",
    ]

    limitations = [
        "Unweighted round-robin: every requester has equal priority in the "
        "rotation; there is no way to bias or prioritise a requester.",
        "No grant/acknowledge protocol: grant is asserted per the fixed latency "
        "of the chosen grant_style; the arbiter does not wait for an ack before "
        "rotating.",
        f"N ({n}) is fixed at generation time: the priority network is unrolled "
        "for this exact requester count and is not a runtime parameter.",
    ]
    if opts.grant_style == "combinational":
        limitations.append(
            "Combinational grant places the full two-pass priority network on "
            "the req-to-grant critical path; at large N consider the registered "
            "style for timing closure."
        )

    grant_when = (
        "one cycle after" if opts.grant_style == "registered" else "the same cycle as"
    )
    return ExplanationDoc(
        purpose=(
            f"An {n}-way round-robin arbiter: it grants a shared resource to at "
            f"most one requester per cycle (one-hot grant, asserted {grant_when} "
            "the request), rotating priority so that under sustained contention "
            f"every requester is served at least once every {n} cycles."
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
class _RrArbiterModule:
    """Bundles the round-robin arbiter's metadata and pure functions.

    Satisfies the :class:`~.contract.ModuleDef` protocol structurally.
    """

    id: str = "rr-arbiter"
    name: str = "Round-Robin Arbiter"
    description: str = (
        "Grants a shared resource to at most one of N requesters per cycle "
        "(one-hot grant), rotating priority so every requester is served in "
        "turn under contention."
    )
    kind: str = "module"
    maturity: str = "stable"
    options_model: type[RrArbiterOptions] = RrArbiterOptions

    def generate(self, opts: RrArbiterOptions) -> Module:
        return generate(opts)

    def explain(self, opts: RrArbiterOptions) -> ExplanationDoc:
        return explain(opts)

    def port_groups(self, opts: RrArbiterOptions) -> list[PortGroup]:
        return port_groups(opts)

    def tb_spec(self, opts: RrArbiterOptions) -> TbSpec:
        return tb_spec(opts)


MODULE = _RrArbiterModule()


__all__ = [
    "RrArbiterOptions",
    "generate",
    "explain",
    "port_groups",
    "tb_spec",
    "MODULE",
]
