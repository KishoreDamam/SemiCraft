"""Snippet: parameterizable multiplexer (WP-05c).

Follows the ``counter.py`` reference template (see that module's docstring for
the general anatomy). This snippet is purely combinational, so its options
extend :class:`CommonOptions` directly (no reset/clock fields).

IR has no array-valued ports in v0.1, so the N data inputs are emitted as
numbered scalar-vector ports ``in0 .. in{N-1}`` rather than a single vector
port with an index range. The select input width is ``clog2(num_inputs)``,
computed here in Python (not by the renderer) and emitted as a `localparam`
(``Param(local=True)``) so the generated code documents the derivation while
still being a plain computed constant -- not a structural knob (``num_inputs``
itself bakes into the port list and is therefore not representable as a
run-time parameter; see the assumptions in ``explain()``).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

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
    ContAssign,
    Header,
    Module,
    Param,
    Port,
    Ref,
    Ternary,
)
from ..version import VERSION
from .contract import CommonOptions, ExplanationDoc, SignalDoc

# ---------------------------------------------------------------------------
# Options
# ---------------------------------------------------------------------------


class MuxOptions(CommonOptions):
    """Configuration for the multiplexer snippet.

    Purely combinational: extends :class:`CommonOptions` only (no reset/clock
    fields per IMPLEMENTATION_PLAN §5 WP-05 common requirements).
    """

    num_inputs: int = Field(
        default=4,
        ge=2,
        le=16,
        description=(
            "Number of data inputs. Emitted as numbered ports in0..in{N-1} "
            "(the IR has no array-valued ports in v0.1). This is a structural "
            "choice: it changes the port list itself, not a runtime parameter."
        ),
    )
    width: int = Field(
        default=8,
        ge=1,
        le=512,
        description="Bit width of each data input and the output (module parameter WIDTH).",
    )
    impl: Literal["case", "ternary"] = Field(
        default="case",
        description=(
            "Select-logic implementation. 'case' emits an always_comb/always "
            "block with a case statement on sel; 'ternary' emits a single "
            "continuous assignment built from a nested ternary chain."
        ),
    )


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

_MODULE_NAME = "mux"


def _clog2(n: int) -> int:
    """Ceiling log2(n), with clog2(1) = 1 (a select needs at least one bit)."""
    if n <= 1:
        return 1
    bits = 0
    val = n - 1
    while val > 0:
        bits += 1
        val >>= 1
    return bits


def _input_names(opts: MuxOptions) -> list[str]:
    return [f"in{i}" for i in range(opts.num_inputs)]


def _is_power_of_two(n: int) -> bool:
    return n > 0 and (n & (n - 1)) == 0


def _case_items(opts: MuxOptions) -> list[CaseItem]:
    names = _input_names(opts)
    sel_width = _clog2(opts.num_inputs)
    items = []
    for i, name in enumerate(names):
        label = Const(i, width=Ref("SEL_WIDTH"))
        items.append(CaseItem(labels=[label], body=[Assign(Ref("out"), Ref(name))]))
    _ = sel_width  # width already captured via the SEL_WIDTH param reference
    return items


def _default_arm() -> list:
    """Default arm: assigns in0. Covers both the well-formed default case and
    non-power-of-2 num_inputs (the unused high sel codes fall through here)."""
    return [Assign(Ref("out"), Ref("in0"))]


def _build_case_body(opts: MuxOptions) -> AlwaysComb:
    case = Case(
        sel=Ref("sel"),
        items=_case_items(opts),
        default=_default_arm(),
    )
    return AlwaysComb(body=[case])


def _build_ternary_expr(opts: MuxOptions):
    """Nested ternary chain: sel == 0 ? in0 : sel == 1 ? in1 : ... : in0.

    The innermost/final fallback is in0 (mirrors the case default arm), so
    behavior is identical across impl choices for out-of-range sel codes.
    """
    from ..ir.nodes import BinOp, BinOpKind

    names = _input_names(opts)
    expr = Ref(names[0])
    # Build from the last input backward so comparisons short-circuit in order.
    for i in range(len(names) - 1, 0, -1):
        cond = BinOp(BinOpKind.EQ, Ref("sel"), Const(i, width=Ref("SEL_WIDTH")))
        expr = Ternary(cond=cond, then=Ref(names[i]), else_=expr)
    return expr


def generate(opts: MuxOptions) -> Module:
    """Build the mux IR ``Module`` (pure). One AlwaysComb+Case or one
    ContAssign+Ternary chain, depending on ``impl``."""
    sel_width = _clog2(opts.num_inputs)

    ports: list[Port] = []
    for name in _input_names(opts):
        ports.append(Port(name, IN, vec("WIDTH"), doc=f"Data input {name}"))
    ports.append(Port("sel", IN, vec("SEL_WIDTH"), doc="Input select"))
    ports.append(Port("out", OUT, vec("WIDTH"), doc="Selected data output"))

    params = [
        Param("WIDTH", Const(opts.width), doc="Data width in bits"),
        Param(
            "SEL_WIDTH",
            Const(sel_width),
            local=True,
            doc="ceil(log2(num_inputs)) select width",
        ),
    ]

    if opts.impl == "case":
        comment = Comment(
            f"{opts.num_inputs}-way {opts.width}-bit mux, case implementation",
            level=CommentLevel.VERBOSE,
        )
        always = _build_case_body(opts)
        # Fold the verbose intent comment into the comb body as a leading
        # statement (mirrors counter.py style: Comment as data, first stmt).
        items = [AlwaysComb(body=[comment, *always.body])]
    else:
        expr = _build_ternary_expr(opts)
        comment = Comment(
            f"{opts.num_inputs}-way {opts.width}-bit mux, ternary implementation",
            level=CommentLevel.VERBOSE,
        )
        items = [comment, ContAssign(lhs=Ref("out"), rhs=expr)]

    return Module(
        name=_MODULE_NAME,
        header=Header(
            license="",  # filled by the generate() entry point with config hash
            config_hash="",
            tool_version=VERSION,
            description=_description(opts),
        ),
        params=params,
        ports=ports,
        items=items,
    )


# ---------------------------------------------------------------------------
# Explanation
# ---------------------------------------------------------------------------


def _description(opts: MuxOptions) -> str:
    return f"{opts.num_inputs}-input {opts.width}-bit multiplexer ({opts.impl})"


def explain(opts: MuxOptions) -> ExplanationDoc:
    """Fully populated explanation for the chosen options."""
    sel_width = _clog2(opts.num_inputs)
    pow2 = _is_power_of_two(opts.num_inputs)

    configuration = [
        f"Number of inputs: {opts.num_inputs}",
        f"Width: {opts.width} bits",
        f"Select width: {sel_width} bits (ceil(log2({opts.num_inputs})))",
        f"Implementation: {opts.impl}",
        f"Output language: {'SystemVerilog' if opts.language == 'sv' else 'Verilog-2001'}",
    ]

    signals = [
        SignalDoc(name=name, direction="input", description=f"Data input {name}.")
        for name in _input_names(opts)
    ]
    signals.append(
        SignalDoc(
            name="sel",
            direction="input",
            description=f"{sel_width}-bit input select (binary-encoded index).",
        )
    )
    signals.append(
        SignalDoc(
            name="out",
            direction="output",
            description=f"Selected {opts.width}-bit data output.",
        )
    )

    assumptions = [
        "num_inputs is a structural choice: it determines the port list itself "
        "(in0..in{N-1}); it is not a runtime-reconfigurable parameter.",
        "sel is assumed to hold a valid binary index in [0, num_inputs). Values "
        "outside that range are handled by the default/fallback arm, not "
        "flagged as an error.",
    ]
    if not pow2:
        assumptions.append(
            f"num_inputs={opts.num_inputs} is not a power of two, so sel "
            f"({sel_width} bits) can encode values with no corresponding "
            "input; those unused codes select the default arm, which assigns "
            "in0."
        )
    else:
        assumptions.append(
            "All sel codes map to a distinct input (num_inputs is a power of "
            "two); the default/fallback arm assigns in0 and is unreachable in "
            "normal operation but is retained for a complete case statement."
        )

    limitations = [
        "No output enable or tri-state behavior; out is always driven.",
        "This snippet performs no clock-domain crossing (CDC) synchronization "
        "on sel or the data inputs.",
    ]

    return ExplanationDoc(
        purpose=(
            f"A {opts.num_inputs}-input, {opts.width}-bit combinational "
            f"multiplexer selecting one of in0..in{opts.num_inputs - 1} onto "
            f"out based on sel, implemented as a {opts.impl} block."
        ),
        configuration=configuration,
        signals=signals,
        reset_behavior="Purely combinational; there is no clock or reset.",
        enable_behavior=None,
        assumptions=assumptions,
        limitations=limitations,
    )


# ---------------------------------------------------------------------------
# SnippetDef instance (discovered by the registry)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class _MuxSnippet:
    """Bundles the mux's metadata and pure ``generate``/``explain`` fns.

    Satisfies the :class:`~.contract.SnippetDef` protocol structurally.
    """

    id: str = "mux"
    name: str = "Multiplexer"
    description: str = "Parameterizable N-way multiplexer (case or ternary implementation)."
    options_model: type[MuxOptions] = MuxOptions

    def generate(self, opts: MuxOptions) -> Module:
        return generate(opts)

    def explain(self, opts: MuxOptions) -> ExplanationDoc:
        return explain(opts)


SNIPPET = _MuxSnippet()


__all__ = ["MuxOptions", "generate", "explain", "SNIPPET"]
