"""The IR_SPEC §9 counter example, built via build.py helpers (WP-01 task 4).

This is the canonical "does the IR read like the spec?" test: an 8-bit up
counter with async active-low reset and an enable. It must build and validate.
"""

from __future__ import annotations

from semicraft_core.ir import (
    IN,
    OUT,
    AlwaysFF,
    Assign,
    BinOp,
    BinOpKind,
    ClockSpec,
    Const,
    Header,
    If,
    Module,
    Param,
    Port,
    Ref,
    ResetKind,
    ResetSpec,
    bit,
    validate,
    vec,
    width,
)


def build_counter() -> Module:
    """Build the IR_SPEC §9 counter. Reads closely to the spec's builder code."""
    return Module(
        name="counter",
        header=Header(
            license="Generated as-is, no warranty.",
            config_hash="deadbeef1234",
            tool_version="0.1.0",
            description="Up counter",
        ),
        params=[Param("WIDTH", Const(8), doc="Counter width in bits")],
        ports=[
            Port("clk", IN, bit()),
            Port("rst", IN, bit(), doc="Async reset, active-low"),
            Port("en", IN, bit(), doc="Count enable"),
            Port("count", OUT, vec("WIDTH")),
        ],
        items=[
            AlwaysFF(
                clock=ClockSpec("clk"),
                reset=ResetSpec("rst", kind=ResetKind.ASYNC, active_low=True),
                reset_body=[Assign(Ref("count"), Const(0, width=width("WIDTH")))],
                body=[
                    If(
                        Ref("en"),
                        then=[
                            Assign(
                                Ref("count"),
                                BinOp(BinOpKind.ADD, Ref("count"), Const(1)),
                            )
                        ],
                    )
                ],
            )
        ],
    )


def test_counter_builds() -> None:
    m = build_counter()
    assert m.name == "counter"
    assert [p.name for p in m.ports] == ["clk", "rst", "en", "count"]
    # The count port is a WIDTH-wide vector.
    assert m.ports[-1].dtype.width == Ref("WIDTH")


def test_counter_validates() -> None:
    # Must not raise: the §9 example is a valid module.
    validate(build_counter())
