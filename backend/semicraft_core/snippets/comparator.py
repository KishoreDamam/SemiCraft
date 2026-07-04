"""Comparator snippet (WP-05g): parameterizable width comparator.

Follows the ``counter.py`` template (WP-03 reference): an options model, a
pure ``generate()`` building IR, a pure ``explain()``, and a module-level
``SNIPPET`` instance. This is a purely combinational snippet, so its options
extend :class:`CommonOptions` directly (no clock/reset fields).

Each selected relational operator gets its own 1-bit output port and its own
``ContAssign`` driven by a matching ``BinOp`` over the ``a``/``b`` inputs. When
``signed_compare`` is set, ``a``/``b`` are declared with a signed
:class:`DataType` so the renderer emits signed comparisons (the IR expression
tree is identical either way; only the operand type changes, per IR_SPEC
design rules 2-4 — the generator never decides signed-vs-unsigned comparison
*syntax*, only the operand type it requests).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from pydantic import Field, model_validator

from ..ir.build import IN, OUT, width
from ..ir.nodes import (
    BinOp,
    BinOpKind,
    Const,
    ContAssign,
    DataType,
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

# Canonical output order (config-hash / port-order independent of input order).
_CANONICAL_OP_ORDER: tuple[str, ...] = ("eq", "ne", "lt", "le", "gt", "ge")

_OP_BINOP: dict[str, BinOpKind] = {
    "eq": BinOpKind.EQ,
    "ne": BinOpKind.NE,
    "lt": BinOpKind.LT,
    "le": BinOpKind.LE,
    "gt": BinOpKind.GT,
    "ge": BinOpKind.GE,
}

_OP_WORD: dict[str, str] = {
    "eq": "equal to",
    "ne": "not equal to",
    "lt": "less than",
    "le": "less than or equal to",
    "gt": "greater than",
    "ge": "greater than or equal to",
}


class ComparatorOptions(CommonOptions):
    """Configuration for the comparator snippet.

    Purely combinational: extends :class:`CommonOptions` only (no reset/clock
    fields per IMPLEMENTATION_PLAN §5 WP-05 common requirements).
    """

    width: int = Field(
        default=8,
        ge=1,
        le=1024,
        description="Bit width of both comparator inputs (module parameter WIDTH).",
    )
    signed_compare: bool = Field(
        default=False,
        description=(
            "When true, 'a' and 'b' are declared signed (two's-complement) and "
            "the relational operators compare signed values. When false, they "
            "are compared as unsigned vectors."
        ),
    )
    outputs: list[Literal["eq", "ne", "lt", "le", "gt", "ge"]] = Field(
        default_factory=lambda: ["eq", "lt", "gt"],
        description=(
            "Which relational outputs to emit, at least one of: 'eq' (a==b), "
            "'ne' (a!=b), 'lt' (a<b), 'le' (a<=b), 'gt' (a>b), 'ge' (a>=b). "
            "Each selected operator gets its own 1-bit output port. Order does "
            "not matter — outputs are always emitted in canonical order "
            "(eq, ne, lt, le, gt, ge) so the config hash and generated code "
            "are independent of the order they were requested in."
        ),
    )

    # ``outputs`` cross-field rules: non-empty, unique, and normalized to
    # canonical order so requesting the same set in a different order yields
    # byte-identical code and an identical config hash (ground rule §1:
    # determinism / PRD §11: never let input order leak into output).
    @model_validator(mode="after")
    def _check(self) -> ComparatorOptions:
        if not self.outputs:
            raise ValueError("outputs must be non-empty: select at least one comparison output")
        if len(set(self.outputs)) != len(self.outputs):
            raise ValueError(f"outputs must not contain duplicates: {self.outputs}")
        # Normalize to canonical order so requesting the same set of outputs
        # in a different order yields byte-identical code and config hash.
        self.outputs = [op for op in _CANONICAL_OP_ORDER if op in self.outputs]
        return self


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

_MODULE_NAME = "comparator"


def _operand_dtype(opts: ComparatorOptions) -> DataType:
    """WIDTH-wide operand type; signed when ``signed_compare`` is set."""
    return DataType(width=width("WIDTH"), signed=opts.signed_compare)


def generate(opts: ComparatorOptions) -> Module:
    """Build the comparator IR ``Module`` (pure). One ``ContAssign`` per
    selected output, each driven by a matching ``BinOp``.

    The generator only decides *what* logic exists (which comparisons, and the
    operand type); the renderer decides fragment vs full-module rendering,
    signed-comparison syntax, and identifier styling (IR_SPEC design rules 2-4).
    """
    operand_dtype = _operand_dtype(opts)

    ports: list[Port] = [
        Port("a", IN, operand_dtype, doc="First comparison operand"),
        Port("b", IN, operand_dtype, doc=_b_port_doc(opts)),
    ]
    for op in opts.outputs:
        ports.append(Port(op, OUT, DataType(width=None), doc=_output_doc(op)))

    items = [
        ContAssign(lhs=Ref(op), rhs=BinOp(_OP_BINOP[op], Ref("a"), Ref("b"))) for op in opts.outputs
    ]

    return Module(
        name=_MODULE_NAME,
        header=Header(
            license="",  # filled by generate() entry point with the config hash
            config_hash="",
            tool_version=VERSION,
            description=_description(opts),
        ),
        params=[Param("WIDTH", Const(opts.width), doc="Comparator operand width in bits")],
        ports=ports,
        items=items,
    )


# ---------------------------------------------------------------------------
# Explanation
# ---------------------------------------------------------------------------


def _description(opts: ComparatorOptions) -> str:
    sign_word = "signed" if opts.signed_compare else "unsigned"
    return f"{opts.width}-bit {sign_word} comparator ({', '.join(opts.outputs)})"


def _b_port_doc(opts: ComparatorOptions) -> str:
    return "Second comparison operand"


def _output_doc(op: str) -> str:
    return f"Comparison result: 1 when a is {_OP_WORD[op]} b, else 0."


def explain(opts: ComparatorOptions) -> ExplanationDoc:
    """Fully populated explanation for the chosen options."""
    sign_word = "signed (two's-complement)" if opts.signed_compare else "unsigned"

    configuration = [
        f"Width: {opts.width} bits",
        f"Comparison mode: {sign_word}",
        f"Outputs: {', '.join(opts.outputs)}",
        f"Output language: {'SystemVerilog' if opts.language == 'sv' else 'Verilog-2001'}",
    ]

    signals = [
        SignalDoc(
            name="a", direction="input", description=f"First {opts.width}-bit comparison operand."
        ),
        SignalDoc(
            name="b", direction="input", description=f"Second {opts.width}-bit comparison operand."
        ),
    ]
    for op in opts.outputs:
        signals.append(SignalDoc(name=op, direction="output", description=_output_doc(op)))

    assumptions = [
        "a and b are the same width (WIDTH bits); this snippet does not "
        "support comparing operands of different widths.",
    ]
    if opts.signed_compare:
        assumptions.append(
            "a and b are two's-complement signed values; the comparison "
            "operators interpret the MSB as the sign bit."
        )
    else:
        assumptions.append(
            "a and b are unsigned values; the comparison operators treat all "
            "bits as magnitude (no sign bit)."
        )

    limitations = [
        "This snippet is purely combinational; outputs change immediately "
        "with a/b and are not registered.",
        "No clock or reset: this snippet performs no clock-domain crossing "
        "(CDC) synchronization on its inputs.",
    ]

    return ExplanationDoc(
        purpose=(
            f"A combinational {opts.width}-bit {sign_word} comparator producing "
            f"{', '.join(opts.outputs)} outputs from operands a and b."
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
class _ComparatorSnippet:
    """Bundles the comparator's metadata and pure ``generate``/``explain`` fns.

    Satisfies the :class:`~.contract.SnippetDef` protocol structurally.
    """

    id: str = "comparator"
    name: str = "Comparator"
    description: str = (
        "Parameterizable width comparator (signed/unsigned, selectable relational outputs)."
    )
    options_model: type[ComparatorOptions] = ComparatorOptions

    def generate(self, opts: ComparatorOptions) -> Module:
        return generate(opts)

    def explain(self, opts: ComparatorOptions) -> ExplanationDoc:
        return explain(opts)


SNIPPET = _ComparatorSnippet()


__all__ = ["ComparatorOptions", "generate", "explain", "SNIPPET"]
