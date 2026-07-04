"""Demux snippet (WP-05d): parameterizable one-to-many data demultiplexer.

Follows the ``counter.py`` reference structure (WP-03): an options model
extending :class:`CommonOptions` (purely combinational — no clock/reset), a
pure ``generate()`` building IR, a pure ``explain()``, and a module-level
``SNIPPET`` instance.

Design notes (IMPLEMENTATION_PLAN.md §5 WP-05 row "demux"):

- The plan's ``default_value: zeros|hold`` option is dropped for the
  combinational MVP: "hold" only makes sense with state (a clocked demux),
  which is out of scope here. Only the "zeros" behavior is implemented, and
  this is called out explicitly in ``explain()`` assumptions rather than
  exposed as a single-value enum option (an enum with one legal value would
  be dead API surface).
- All outputs are assigned zero *first* in the ``AlwaysComb`` body (no
  latches, IR_SPEC design rule / WP-02 validation), then a ``Case`` on ``sel``
  overwrites the selected output with ``din``. Unmapped ``sel`` values (when
  ``num_outputs`` is not a power of two) leave every output at its
  already-assigned zero default. IR validation rule 5 requires every
  non-enum ``Case`` to declare a ``default`` arm regardless, so an empty
  (no-op) default is attached explicitly.
"""

from __future__ import annotations

from dataclasses import dataclass

from pydantic import Field

from ..ir.build import IN, OUT, vec
from ..ir.nodes import (
    AlwaysComb,
    Assign,
    Case,
    CaseItem,
    Comment,
    CommentLevel,
    Const,
    Header,
    Module,
    Param,
    Port,
    Ref,
)
from ..version import VERSION
from .contract import CommonOptions, ExplanationDoc, SignalDoc

# ---------------------------------------------------------------------------
# Options
# ---------------------------------------------------------------------------


class DemuxOptions(CommonOptions):
    """Configuration for the demux snippet.

    Extends :class:`CommonOptions` directly (language, wrapper, comments,
    naming) — this snippet is purely combinational, so it must NOT extend
    :class:`ClockedOptions` (no clock, no reset).
    """

    num_outputs: int = Field(
        default=4,
        ge=2,
        le=16,
        description=(
            "Number of demultiplexed outputs (out0..out{N-1}). Need not be a "
            "power of two; unmapped select values leave every output at zero."
        ),
    )
    width: int = Field(
        default=8,
        ge=1,
        le=512,
        description="Data width in bits. din and every output are WIDTH bits wide.",
    )


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

_MODULE_NAME = "demux"


def _sel_width(num_outputs: int) -> int:
    """Bits needed to select among ``num_outputs`` outputs (ceil(log2(N)))."""
    return max(1, (num_outputs - 1).bit_length())


def _output_name(i: int) -> str:
    return f"out{i}"


def generate(opts: DemuxOptions) -> Module:
    """Build the demux IR ``Module`` (pure). One ``AlwaysComb``, no ``Param``
    for the data width — WIDTH is a real module parameter; SEL_WIDTH is a
    derived ``localparam`` since it is computed from ``num_outputs``, not
    independently configurable.

    The generator only decides *what* logic exists (zero-default outputs plus
    a routing case); the renderer decides ``always_comb`` vs ``always @(*)``
    and reg/wire inference (IR_SPEC design rules 2-3).
    """
    sel_width = _sel_width(opts.num_outputs)

    # --- ports (order per clean-rtl: control/select, then data) -------------
    ports: list[Port] = [
        Port("din", IN, vec("WIDTH"), doc="Data input routed to the selected output"),
        Port(
            "sel",
            IN,
            vec("SEL_WIDTH"),
            doc=f"Output select ({sel_width}-bit; chooses out0..out{opts.num_outputs - 1})",
        ),
    ]
    for i in range(opts.num_outputs):
        ports.append(
            Port(
                _output_name(i),
                OUT,
                vec("WIDTH"),
                doc=f"Demultiplexed output {i}; driven by din when sel == {i}, else zero",
            )
        )

    # --- combinational body ---------------------------------------------
    # All outputs default to zero first (no latches — every output is fully
    # assigned on every path through the always_comb block).
    body: list = [
        Comment(
            f"{opts.num_outputs}-way demux, {opts.width}-bit data, "
            "zero-default outputs (no latches)",
            level=CommentLevel.VERBOSE,
        )
    ]
    zero = Const(0, width=Ref("WIDTH"))
    for i in range(opts.num_outputs):
        body.append(Assign(Ref(_output_name(i)), zero))

    # Case routes din to the selected output. Unmapped sel values (possible
    # when num_outputs is not a power of two) are handled by an explicit
    # (no-op) default arm -- IR validation rule 5 requires every non-enum
    # Case to have a default, even though every output already carries its
    # zero default from the assignments above.
    items = [
        CaseItem(
            labels=[Const(i, width=Ref("SEL_WIDTH"))],
            body=[Assign(Ref(_output_name(i)), Ref("din"))],
        )
        for i in range(opts.num_outputs)
    ]
    body.append(Case(sel=Ref("sel"), items=items, default=[]))

    always = AlwaysComb(body=body)

    return Module(
        name=_MODULE_NAME,
        header=Header(
            license="",  # filled by generate() entry point with the config hash
            config_hash="",
            tool_version=VERSION,
            description=_description(opts),
        ),
        params=[
            Param("WIDTH", Const(opts.width), doc="Data width in bits"),
            Param(
                "SEL_WIDTH",
                Const(sel_width),
                local=True,
                doc="Select width in bits, derived from num_outputs",
            ),
        ],
        ports=ports,
        items=[always],
    )


# ---------------------------------------------------------------------------
# Explanation
# ---------------------------------------------------------------------------


def _description(opts: DemuxOptions) -> str:
    return f"{opts.num_outputs}-way demultiplexer, {opts.width}-bit data"


def _is_power_of_two(n: int) -> bool:
    return n > 0 and (n & (n - 1)) == 0


def explain(opts: DemuxOptions) -> ExplanationDoc:
    """Fully populated explanation for the chosen options."""
    sel_width = _sel_width(opts.num_outputs)

    configuration = [
        f"Number of outputs: {opts.num_outputs}",
        f"Data width: {opts.width} bits",
        f"Select width: {sel_width} bits",
        "Non-selected outputs: driven to zero (combinational MVP; no 'hold' variant)",
        f"Output language: {'SystemVerilog' if opts.language == 'sv' else 'Verilog-2001'}",
    ]

    signals = [
        SignalDoc(
            name="din",
            direction="input",
            description=f"{opts.width}-bit data input routed to the selected output.",
        ),
        SignalDoc(
            name="sel",
            direction="input",
            description=(
                f"{sel_width}-bit output select; chooses which of the "
                f"{opts.num_outputs} outputs receives din."
            ),
        ),
    ]
    for i in range(opts.num_outputs):
        signals.append(
            SignalDoc(
                name=_output_name(i),
                direction="output",
                description=(
                    f"Demultiplexed output {i}; equals din when sel == {i}, "
                    "otherwise zero."
                ),
            )
        )

    assumptions = [
        "Purely combinational: outputs settle one propagation delay after din "
        "or sel changes; there is no clock or reset.",
        "The dropped 'hold' default-value variant (retaining the previous "
        "output value on deselect) would require state and is out of scope "
        "for this combinational snippet; non-selected outputs always drive "
        "zero.",
    ]
    if not _is_power_of_two(opts.num_outputs):
        assumptions.append(
            f"num_outputs={opts.num_outputs} is not a power of two: sel values "
            f"from {opts.num_outputs} to {(1 << sel_width) - 1} are unmapped and "
            "leave every output at zero."
        )

    limitations = [
        "No output enable or valid flag: a downstream consumer cannot "
        "distinguish 'deselected' from 'selected with din == 0'.",
        "Single clock domain concept does not apply; this snippet performs no "
        "clock-domain crossing (CDC) synchronization since it is combinational.",
    ]

    return ExplanationDoc(
        purpose=(
            f"A {opts.width}-bit wide, {opts.num_outputs}-way combinational "
            "demultiplexer: routes din to the output selected by sel, "
            "driving all other outputs to zero."
        ),
        configuration=configuration,
        signals=signals,
        reset_behavior="No reset: this snippet is purely combinational.",
        enable_behavior=None,
        assumptions=assumptions,
        limitations=limitations,
    )


# ---------------------------------------------------------------------------
# SnippetDef instance (discovered by the registry)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class _DemuxSnippet:
    """Bundles the demux's metadata and pure ``generate``/``explain`` fns.

    Satisfies the :class:`~.contract.SnippetDef` protocol structurally.
    """

    id: str = "demux"
    name: str = "Demultiplexer"
    description: str = "Parameterizable one-to-many combinational data demultiplexer."
    options_model: type[DemuxOptions] = DemuxOptions

    def generate(self, opts: DemuxOptions) -> Module:
        return generate(opts)

    def explain(self, opts: DemuxOptions) -> ExplanationDoc:
        return explain(opts)


SNIPPET = _DemuxSnippet()


__all__ = ["DemuxOptions", "generate", "explain", "SNIPPET"]
