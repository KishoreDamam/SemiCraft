"""Decoder snippet (WP-05f): binary-to-one-hot decoder.

Follows the ``counter.py`` reference structure (WP-03): an options model, a
pure ``generate()`` building IR, a pure ``explain()``, and a module-level
``SNIPPET`` instance. This is a purely combinational snippet, so its options
extend :class:`CommonOptions` directly (no clock/reset fields).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal

from pydantic import Field

from ..ir.build import IN, OUT, bit, vec
from ..ir.nodes import (
    BinOp,
    BinOpKind,
    Const,
    ContAssign,
    Header,
    Module,
    Param,
    Port,
    Ref,
    Ternary,
    UnaryOp,
    UnaryOpKind,
)
from ..version import VERSION
from .contract import CommonOptions, ExplanationDoc, SignalDoc

# ---------------------------------------------------------------------------
# Options
# ---------------------------------------------------------------------------


class DecoderOptions(CommonOptions):
    """Configuration for the decoder snippet.

    Extends :class:`CommonOptions` (language, wrapper, comments, naming) — a
    decoder is purely combinational and has no clock or reset.
    """

    num_outputs: Literal[2, 4, 8, 16] = Field(
        default=8,
        description=(
            "Number of one-hot outputs (dout is this many bits wide). The "
            "select input width is automatically clog2(num_outputs)."
        ),
    )
    enable: bool = Field(
        default=True,
        description=(
            "Add an 'en' input. When low, all outputs are forced to their "
            "disabled state (all-zero for active_high, all-one for "
            "active_low) regardless of sel."
        ),
    )
    output_polarity: Literal["active_high", "active_low"] = Field(
        default="active_high",
        description=(
            "Output assertion level. 'active_high' asserts the selected "
            "output as 1 (others 0); 'active_low' asserts the selected "
            "output as 0 (others 1)."
        ),
    )


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

_MODULE_NAME = "decoder"


def _sel_width(opts: DecoderOptions) -> int:
    """Select input width: clog2(num_outputs)."""
    return max(1, math.ceil(math.log2(opts.num_outputs)))


def _active_high_expr(opts: DecoderOptions) -> BinOp:
    """``1'b1 << sel`` widened to NUM_OUTPUTS bits: one-hot 'sel' bit set."""
    one = Const(1, width=Ref("NUM_OUTPUTS"))
    return BinOp(BinOpKind.SHL, one, Ref("sel"))


def _disabled_expr(opts: DecoderOptions) -> Const:
    """All-zero (active_high) disabled state, NUM_OUTPUTS bits wide."""
    return Const(0, width=Ref("NUM_OUTPUTS"))


def _dout_expr(opts: DecoderOptions):
    """Build the ``dout`` continuous-assign RHS for the chosen options.

    active_high: ``en ? (1 << sel) : '0`` (or plain ``1 << sel`` without
    enable). active_low: the whole active-high expression inverted with a
    bitwise NOT, so the selected bit reads 0 and all others read 1; the
    disabled state (no enable) becomes all-ones after inversion.
    """
    active_high = _active_high_expr(opts)
    if opts.enable:
        expr = Ternary(cond=Ref("en"), then=active_high, else_=_disabled_expr(opts))
    else:
        expr = active_high

    if opts.output_polarity == "active_low":
        return UnaryOp(UnaryOpKind.NOT_BITWISE, expr)
    return expr


def generate(opts: DecoderOptions) -> Module:
    """Build the decoder IR ``Module`` (pure). One ``ContAssign``.

    The generator only decides *what* logic exists; the renderer decides
    fragment vs full-module rendering and identifier styling (IR_SPEC design
    rules 2-4).
    """
    sel_width = _sel_width(opts)

    ports: list[Port] = [Port("sel", IN, vec(sel_width), doc="Binary select input")]
    if opts.enable:
        ports.append(
            Port(
                "en",
                IN,
                bit(),
                doc="Decoder enable; when low all outputs go to their disabled state",
            )
        )
    ports.append(
        Port(
            "dout",
            OUT,
            vec("NUM_OUTPUTS"),
            doc=f"One-hot {opts.output_polarity.replace('_', '-')} decoded output",
        )
    )

    assign = ContAssign(lhs=Ref("dout"), rhs=_dout_expr(opts))

    return Module(
        name=_MODULE_NAME,
        header=Header(
            license="",  # filled by generate() entry point with the config hash
            config_hash="",
            tool_version=VERSION,
            description=_description(opts),
        ),
        params=[
            Param(
                "NUM_OUTPUTS",
                Const(opts.num_outputs),
                doc="Number of one-hot decoded outputs",
            )
        ],
        ports=ports,
        items=[assign],
    )


# ---------------------------------------------------------------------------
# Explanation
# ---------------------------------------------------------------------------


def _description(opts: DecoderOptions) -> str:
    pol = "active-high" if opts.output_polarity == "active_high" else "active-low"
    return f"{opts.num_outputs}-output binary decoder, {pol}"


def _polarity_text(opts: DecoderOptions) -> str:
    if opts.output_polarity == "active_high":
        return (
            "Active-high: the output bit at index 'sel' is driven to 1 and all "
            "other output bits are driven to 0."
        )
    return (
        "Active-low: the output bit at index 'sel' is driven to 0 and all "
        "other output bits are driven to 1 (bitwise inversion of the "
        "active-high pattern)."
    )


def explain(opts: DecoderOptions) -> ExplanationDoc:
    """Fully populated explanation for the chosen options."""
    sel_width = _sel_width(opts)
    disabled_word = "all-zero" if opts.output_polarity == "active_high" else "all-one"

    configuration = [
        f"Number of outputs: {opts.num_outputs} (select width: {sel_width} bits)",
        f"Enable input: {'yes' if opts.enable else 'no'}",
        f"Output polarity: {opts.output_polarity}",
        f"Output language: {'SystemVerilog' if opts.language == 'sv' else 'Verilog-2001'}",
    ]

    signals = [
        SignalDoc(
            name="sel",
            direction="input",
            description=f"{sel_width}-bit binary select input.",
        )
    ]
    if opts.enable:
        signals.append(
            SignalDoc(
                name="en",
                direction="input",
                description=(
                    "Decoder enable; when low, dout is forced to its "
                    f"disabled state ({disabled_word})."
                ),
            )
        )
    signals.append(
        SignalDoc(
            name="dout",
            direction="output",
            description=(
                f"{opts.num_outputs}-bit one-hot decoded output "
                f"({opts.output_polarity})."
            ),
        )
    )

    enable_behavior = (
        "When en is high, dout is one-hot driven based on sel. When en is "
        f"low, dout is forced to its disabled state ({disabled_word}), "
        "regardless of sel."
        if opts.enable
        else None
    )

    assumptions = [
        "sel is a stable binary value in [0, num_outputs) at the time dout is sampled.",
        "This snippet is purely combinational; dout changes immediately with sel/en.",
    ]

    limitations = [
        _polarity_text(opts),
        "No clock or reset: this snippet has no registered state and performs "
        "no clock-domain crossing (CDC) synchronization.",
    ]

    return ExplanationDoc(
        purpose=(
            f"A combinational {opts.num_outputs}-output binary decoder"
            + (" with enable" if opts.enable else "")
            + f", {opts.output_polarity} outputs."
        ),
        configuration=configuration,
        signals=signals,
        reset_behavior="Not applicable: this snippet is purely combinational and has no reset.",
        enable_behavior=enable_behavior,
        assumptions=assumptions,
        limitations=limitations,
    )


# ---------------------------------------------------------------------------
# SnippetDef instance (discovered by the registry)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class _DecoderSnippet:
    """Bundles the decoder's metadata and pure ``generate``/``explain`` fns.

    Satisfies the :class:`~.contract.SnippetDef` protocol structurally.
    """

    id: str = "decoder"
    name: str = "Decoder"
    description: str = "Binary-to-one-hot decoder (configurable width, enable, polarity)."
    options_model: type[DecoderOptions] = DecoderOptions

    def generate(self, opts: DecoderOptions) -> Module:
        return generate(opts)

    def explain(self, opts: DecoderOptions) -> ExplanationDoc:
        return explain(opts)


SNIPPET = _DecoderSnippet()


__all__ = ["DecoderOptions", "generate", "explain", "SNIPPET"]
