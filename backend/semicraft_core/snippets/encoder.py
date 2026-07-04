"""Encoder snippet (WP-05e): priority or one-hot binary encoder.

Follows the ``counter.py`` reference template (see that module's docstring for
the general anatomy). This snippet is purely combinational, so its options
extend :class:`CommonOptions` directly (no clock/reset fields) and its body is
a single ``AlwaysComb``.

Two encoding kinds:

- ``priority``: an if/elif chain testing bits from **most-significant to
  least-significant**. The highest-indexed set bit wins ties, which means bit
  0 is the *lowest*-priority input (documented explicitly in the explanation
  and in an inline comment, per IMPLEMENTATION_PLAN §5 WP-05e wording).
- ``onehot``: a ``case`` on the full input vector with one onehot literal
  label per valid index, plus a ``default`` (covers non-onehot/all-zero
  inputs) that clears ``dout``/``valid``.

Both kinds default ``dout = 0`` and (when present) ``valid = 0`` before/at the
"no bits set" case, so there is never an inferred latch.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal

from pydantic import Field

from ..ir.build import IN, OUT, bit, vec
from ..ir.nodes import (
    AlwaysComb,
    Assign,
    Bit,
    Case,
    CaseItem,
    Comment,
    CommentLevel,
    Const,
    ConstBase,
    Header,
    If,
    Module,
    Port,
    Ref,
)
from ..version import VERSION
from .contract import CommonOptions, ExplanationDoc, SignalDoc

# ---------------------------------------------------------------------------
# Options
# ---------------------------------------------------------------------------


class EncoderOptions(CommonOptions):
    """Configuration for the encoder snippet.

    Purely combinational: extends :class:`CommonOptions` directly (no reset/
    clock fields).
    """

    kind: Literal["priority", "onehot"] = Field(
        default="priority",
        description=(
            "Encoding scheme. 'priority' resolves multiple set bits by "
            "priority (highest index wins); 'onehot' expects exactly one bit "
            "set and decodes its index directly."
        ),
    )
    num_inputs: Literal[4, 8, 16] = Field(
        default=8,
        description="Number of input bits (din width). Output width is clog2(num_inputs).",
    )
    valid_output: bool = Field(
        default=True,
        description=(
            "Add a 'valid' output that is high when dout reflects a real "
            "encoded input (at least one din bit set for 'priority'; exactly "
            "one for 'onehot')."
        ),
    )


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

_MODULE_NAME = "encoder"


def _out_width(opts: EncoderOptions) -> int:
    """clog2(num_inputs); num_inputs is a power of two so this is exact."""
    return max(1, int(math.log2(opts.num_inputs)))


def _priority_body(opts: EncoderOptions) -> list:
    """If/elif chain from MSB down to bit 0 (highest set bit wins).

    Default (no bits set, or when reached via elif fallthrough): dout=0,
    valid=0 -- matching the "no bits set" and, for valid_output=False, the
    bit-0-set case (documented ambiguity in the explanation).
    """
    n = opts.num_inputs
    out_w = _out_width(opts)

    defaults: list = [Assign(Ref("dout"), Const(0, width=Ref("OUT_WIDTH")))]
    if opts.valid_output:
        defaults.append(Assign(Ref("valid"), Const(0)))

    # Build nested if/elif from MSB (n-1) down to 0; first (highest) match wins.
    cond = Bit(Ref("din"), Const(n - 1))
    then_stmts: list = [
        Assign(Ref("dout"), Const(n - 1, width=Ref("OUT_WIDTH"), base=ConstBase.DEC))
    ]
    if opts.valid_output:
        then_stmts.append(Assign(Ref("valid"), Const(1)))

    elifs = []
    for idx in range(n - 2, -1, -1):
        arm_cond = Bit(Ref("din"), Const(idx))
        arm_body: list = [Assign(Ref("dout"), Const(idx, width=Ref("OUT_WIDTH")))]
        if opts.valid_output:
            arm_body.append(Assign(Ref("valid"), Const(1)))
        elifs.append((arm_cond, arm_body))

    comment = Comment(
        f"Priority encoder: highest-indexed set bit wins (din[{n - 1}] is "
        f"highest priority, din[0] is lowest priority).",
        level=CommentLevel.NORMAL,
    )
    _ = out_w  # width computed via OUT_WIDTH param at render time
    return [comment, *defaults, If(cond, then=then_stmts, elifs=elifs)]


def _onehot_body(opts: EncoderOptions) -> list:
    """Case over the full din vector: one onehot literal label per index.

    Non-onehot inputs (zero or multiple bits set) fall to ``default``, which
    clears dout/valid.
    """
    n = opts.num_inputs

    items = []
    for idx in range(n):
        literal_value = 1 << idx
        label = Const(literal_value, width=Ref("NUM_INPUTS"), base=ConstBase.BIN)
        body: list = [Assign(Ref("dout"), Const(idx, width=Ref("OUT_WIDTH")))]
        if opts.valid_output:
            body.append(Assign(Ref("valid"), Const(1)))
        items.append(CaseItem(labels=[label], body=body))

    default_body: list = [Assign(Ref("dout"), Const(0, width=Ref("OUT_WIDTH")))]
    if opts.valid_output:
        default_body.append(Assign(Ref("valid"), Const(0)))

    comment = Comment(
        "One-hot encoder: din is assumed one-hot; exactly one bit set maps "
        "to its index. Non-one-hot din (zero or multiple bits set) hits the "
        "default arm.",
        level=CommentLevel.NORMAL,
    )
    return [
        comment,
        Case(sel=Ref("din"), items=items, default=default_body),
    ]


def generate(opts: EncoderOptions) -> Module:
    """Build the encoder IR ``Module`` (pure). One ``AlwaysComb``."""
    out_w = _out_width(opts)

    ports: list[Port] = [
        Port("din", IN, vec("NUM_INPUTS"), doc=f"{opts.num_inputs}-bit input vector"),
        Port("dout", OUT, vec("OUT_WIDTH"), doc="Encoded index output"),
    ]
    if opts.valid_output:
        ports.append(
            Port(
                "valid",
                OUT,
                bit(),
                doc="High when dout reflects a valid encoded input",
            )
        )

    body = _priority_body(opts) if opts.kind == "priority" else _onehot_body(opts)

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
            Param_NUM_INPUTS(opts),
            Param_OUT_WIDTH(opts, out_w),
        ],
        ports=ports,
        items=[always],
    )


# Small local factories kept close to generate() for readability; Param is
# imported lazily here to avoid shadowing the module-level import block order.
from ..ir.nodes import Param  # noqa: E402


def Param_NUM_INPUTS(opts: EncoderOptions) -> Param:
    return Param("NUM_INPUTS", Const(opts.num_inputs), doc="Number of input bits")


def Param_OUT_WIDTH(opts: EncoderOptions, out_w: int) -> Param:
    return Param(
        "OUT_WIDTH", Const(out_w), local=True, doc="clog2(NUM_INPUTS): encoded index width"
    )


# ---------------------------------------------------------------------------
# Explanation
# ---------------------------------------------------------------------------


def _description(opts: EncoderOptions) -> str:
    kind_word = "Priority" if opts.kind == "priority" else "One-hot"
    return f"{kind_word} encoder, {opts.num_inputs} inputs"


def explain(opts: EncoderOptions) -> ExplanationDoc:
    """Fully populated explanation for the chosen options."""
    out_w = _out_width(opts)

    configuration = [
        f"Kind: {opts.kind}",
        f"Number of inputs: {opts.num_inputs}",
        f"Output width: {out_w} bits (clog2({opts.num_inputs}))",
        f"Valid output: {'yes' if opts.valid_output else 'no'}",
        f"Output language: {'SystemVerilog' if opts.language == 'sv' else 'Verilog-2001'}",
    ]

    signals = [
        SignalDoc(
            name="din",
            direction="input",
            description=f"{opts.num_inputs}-bit input vector to encode.",
        ),
        SignalDoc(
            name="dout",
            direction="output",
            description=f"{out_w}-bit encoded index of the selected input bit.",
        ),
    ]
    if opts.valid_output:
        signals.append(
            SignalDoc(
                name="valid",
                direction="output",
                description="High when dout reflects a valid encoded input.",
            )
        )

    if opts.kind == "priority":
        priority_stmt = (
            f"Priority order: din[{opts.num_inputs - 1}] is checked first "
            "(highest priority) down to din[0] (lowest priority); the "
            "highest-indexed set bit wins and determines dout."
        )
    else:
        priority_stmt = (
            "Not applicable in one-hot mode: din is decoded directly by "
            "matching its exact one-hot pattern, there is no priority "
            "resolution between bits."
        )

    assumptions = [priority_stmt]
    if opts.kind == "onehot":
        assumptions.append(
            "din is assumed to be one-hot (exactly one bit set) for "
            "meaningful output; the case statement has no notion of "
            "priority and treats any non-matching pattern as invalid."
        )
    if not opts.valid_output:
        assumptions.append(
            "Without the 'valid' output, an all-zero din (no bits set) is "
            "indistinguishable on dout from the case where only din[0] is "
            "set (both produce dout=0); add valid_output to disambiguate."
        )

    limitations = [
        "Purely combinational: no clock, reset, or registered output.",
    ]
    if opts.kind == "onehot":
        limitations.append(
            "In one-hot mode, non-one-hot inputs (zero or multiple bits "
            "set) are not decoded meaningfully; they hit the default arm "
            "which clears dout" + (" and valid" if opts.valid_output else "") + "."
        )
    else:
        limitations.append(
            "In priority mode, ties between multiple set bits are always "
            "resolved in favor of the highest-indexed bit; lower-indexed "
            "set bits are silently ignored."
        )

    return ExplanationDoc(
        purpose=(
            f"A {opts.num_inputs}-to-{out_w} {opts.kind} encoder that "
            f"produces the binary index of the selected input bit"
            + (" with a valid flag" if opts.valid_output else "")
            + "."
        ),
        configuration=configuration,
        signals=signals,
        reset_behavior="Not applicable: this snippet is purely combinational and has no reset.",
        enable_behavior=None,
        assumptions=assumptions,
        limitations=limitations,
    )


# ---------------------------------------------------------------------------
# SnippetDef instance (discovered by the registry)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class _EncoderSnippet:
    """Bundles the encoder's metadata and pure ``generate``/``explain`` fns."""

    id: str = "encoder"
    name: str = "Encoder"
    description: str = "Priority or one-hot binary encoder."
    options_model: type[EncoderOptions] = EncoderOptions

    def generate(self, opts: EncoderOptions) -> Module:
        return generate(opts)

    def explain(self, opts: EncoderOptions) -> ExplanationDoc:
        return explain(opts)


SNIPPET = _EncoderSnippet()


__all__ = ["EncoderOptions", "generate", "explain", "SNIPPET"]
