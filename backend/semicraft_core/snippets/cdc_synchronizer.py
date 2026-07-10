"""CDC synchronizer snippet (WP-05h): multi-stage flip-flop synchronizer for
clock-domain crossing (CDC).

Follows the ``counter.py`` template (WP-03 reference): an options model
extending :class:`ClockedOptions`, a pure ``generate()`` building IR, a pure
``explain()``, and a module-level ``SNIPPET`` instance. Unlike most clocked
snippets, the reset is *conditional*: when ``use_reset`` is false the
synchronizer has no reset at all (``AlwaysFF.reset=None``, empty
``reset_body``) — reset/polarity options are accepted but have no effect, and
this is called out in port docs and the explanation.

Design (mirrors the ``clock-domain-crossing`` skill's 2-FF synchronizer,
generalized to ``stages`` and ``width``): a chain of ``sync_ff1..sync_ffN``
registers, all clocked by the destination-domain clock ``clk``, shifts the
asynchronous input ``d_async`` toward ``q`` one stage per cycle:

    sync_ff1 <= d_async
    sync_ff2 <= sync_ff1
    ...
    q        <= sync_ffN   (or sync_ff1 directly when stages == 1... but
                             stages is constrained to 2..4, so there is
                             always at least one internal stage before q)

Latency from ``d_async`` to ``q`` is exactly ``stages`` clock cycles. All
stages live in a single ``AlwaysFF`` (one process, one clock domain — SemiCraft
never models the source domain, which is the whole point of a synchronizer:
it is instantiated *inside* the destination domain and takes an already
async/CDC-crossing signal as its input).
"""

from __future__ import annotations

from dataclasses import dataclass

from pydantic import Field

from ..ir.build import IN, OUT, bit, vec
from ..ir.nodes import (
    AlwaysFF,
    Assign,
    ClockSpec,
    Comment,
    CommentLevel,
    Const,
    Header,
    Module,
    Param,
    Port,
    Ref,
    ResetKind,
    ResetSpec,
    Signal,
)
from ..version import VERSION
from .contract import ClockedOptions, ExplanationDoc, SignalDoc

# ---------------------------------------------------------------------------
# Options
# ---------------------------------------------------------------------------


class CdcSynchronizerOptions(ClockedOptions):
    """Configuration for the CDC synchronizer snippet.

    Extends :class:`ClockedOptions` (language, reset, wrapper, comments,
    naming). Reset is conditional here: when ``use_reset`` is false, the
    inherited ``reset_style``/``reset_polarity`` fields are accepted (so the
    common schema stays uniform) but are ignored — the generated register
    chain has no reset input or logic at all.
    """

    stages: int = Field(
        default=2,
        ge=2,
        le=4,
        description=(
            "Number of synchronizer flip-flop stages (module parameter "
            "STAGES). More stages reduce the probability of metastability "
            "propagating to q, at the cost of additional latency (one cycle "
            "per stage)."
        ),
    )
    width: int = Field(
        default=1,
        ge=1,
        le=8,
        description=(
            "Bit width of d_async/q. width=1 is the standard single-bit "
            "control-signal synchronizer. width>1 replicates independent "
            "synchronizer bits in parallel and is only safe for gray-coded "
            "or quasi-static multi-bit signals (see assumptions) — it is "
            "NOT safe for arbitrary multi-bit data buses."
        ),
    )
    use_reset: bool = Field(
        default=False,
        description=(
            "When true, add a reset input (name/polarity from reset_style/"
            "reset_polarity) that clears the synchronizer chain. When false "
            "(default), the synchronizer has no reset at all: reset_style and "
            "reset_polarity are ignored, and the register chain simply powers "
            "up in an unknown state and synchronizes from there — the usual "
            "choice for synchronizers, since resetting them can itself "
            "reintroduce a CDC problem on the reset signal."
        ),
    )


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

_MODULE_NAME = "cdc_synchronizer"


def _stage_names(opts: CdcSynchronizerOptions) -> list[str]:
    """Internal chain register names: sync_ff1 .. sync_ff{stages}."""
    return [f"sync_ff{i}" for i in range(1, opts.stages + 1)]


def _dtype(opts: CdcSynchronizerOptions):
    return bit() if opts.width == 1 else vec("WIDTH")


def _reset_spec(opts: CdcSynchronizerOptions) -> ResetSpec | None:
    """Reset is conditional: None entirely when use_reset is false."""
    if not opts.use_reset:
        return None
    return ResetSpec(
        name="rst",
        kind=ResetKind.SYNC if opts.reset_style == "sync" else ResetKind.ASYNC,
        active_low=opts.reset_polarity == "active_low",
    )


def _reset_value_const(opts: CdcSynchronizerOptions) -> Const:
    """Zero reset literal for one stage (bit or WIDTH-wide)."""
    return Const(0) if opts.width == 1 else Const(0, width=Ref("WIDTH"))


def generate(opts: CdcSynchronizerOptions) -> Module:
    """Build the CDC synchronizer IR ``Module`` (pure). One internal ``Signal``
    per stage but the last, one ``AlwaysFF`` shifting d_async -> ... -> q.

    The generator only decides *what* logic exists (chain length, reset
    presence); the renderer decides always_ff sensitivity/reset composition
    and identifier styling (IR_SPEC design rules 2-4).
    """
    dtype = _dtype(opts)
    stage_names = _stage_names(opts)
    reset = _reset_spec(opts)

    # --- ports (order per clean-rtl: clock, reset, control, data) -----------
    ports: list[Port] = [Port("clk", IN, bit(), doc="Destination-domain clock")]
    if opts.use_reset:
        ports.append(Port("rst", IN, bit(), doc=_reset_doc(opts)))
    ports.append(
        Port(
            "d_async",
            IN,
            dtype,
            doc="Asynchronous input, not synchronous to clk (source of the CDC)",
        )
    )
    ports.append(
        Port("q", OUT, dtype, doc=f"Synchronized output, {opts.stages} clk cycles behind d_async")
    )

    # --- internal chain: one Signal per stage before the last (the last
    # stage IS q, so it is not a separate internal signal) -------------------
    internal_stage_names = stage_names[:-1]
    signals = [
        Signal(name, dtype, doc=f"Synchronizer stage {i + 1}")
        for i, name in enumerate(internal_stage_names)
    ]

    # --- clocked body: shift d_async -> sync_ff1 -> ... -> q ----------------
    body: list = [
        Comment(
            f"{opts.stages}-stage CDC synchronizer, destination-domain clock only",
            level=CommentLevel.VERBOSE,
        )
    ]
    if opts.width > 1:
        body.append(
            Comment(
                "WIDTH > 1: each bit is synchronized independently by its own "
                "flip-flop chain. This is only safe for gray-coded or "
                "quasi-static signals -- individual bits may resolve on "
                "different clock cycles, so arbitrary multi-bit data is NOT "
                "guaranteed to arrive coherently.",
                level=CommentLevel.NORMAL,
            )
        )

    chain_targets = [*internal_stage_names, "q"]
    chain_sources = ["d_async", *internal_stage_names]
    for target, source in zip(chain_targets, chain_sources, strict=True):
        body.append(Assign(Ref(target), Ref(source)))

    reset_body = []
    if opts.use_reset:
        reset_body = [Assign(Ref(name), _reset_value_const(opts)) for name in chain_targets]

    always = AlwaysFF(
        clock=ClockSpec("clk"),
        reset=reset,
        reset_body=reset_body,
        body=body,
    )

    # The chain is structurally unrolled, so the stage count is not emitted as
    # a parameter (an unreferenced STAGES localparam trips Verilator's
    # UNUSEDPARAM under -Wall); it is documented in the header/explanation.
    params = []
    if opts.width > 1:
        params.append(Param("WIDTH", Const(opts.width), doc="Synchronizer bit width"))

    return Module(
        name=_MODULE_NAME,
        header=Header(
            license="",  # filled by generate() entry point with the config hash
            config_hash="",
            tool_version=VERSION,
            description=_description(opts),
        ),
        params=params,
        ports=ports,
        items=[*signals, always],
    )


# ---------------------------------------------------------------------------
# Explanation
# ---------------------------------------------------------------------------


def _description(opts: CdcSynchronizerOptions) -> str:
    width_word = f"{opts.width}-bit" if opts.width > 1 else "single-bit"
    return f"{opts.stages}-stage {width_word} CDC synchronizer"


def _reset_doc(opts: CdcSynchronizerOptions) -> str:
    style = "Async" if opts.reset_style == "async" else "Sync"
    pol = "low" if opts.reset_polarity == "active_low" else "high"
    return f"{style} reset, active-{pol} (clears the synchronizer chain)"


def _reset_behavior_text(opts: CdcSynchronizerOptions) -> str:
    if not opts.use_reset:
        return (
            "This synchronizer has no reset input: use_reset is false, so "
            "reset_style/reset_polarity are ignored and the register chain is "
            "not reset. The chain powers up in an unknown state and begins "
            "synchronizing d_async from whatever value it starts in; this is "
            "the conventional choice for synchronizers, since driving a reset "
            "into a synchronizer chain from another clock domain can itself "
            "become a new CDC hazard."
        )
    style = "asynchronously" if opts.reset_style == "async" else "synchronously"
    pol = (
        "active-low (asserted when 0)"
        if opts.reset_polarity == "active_low"
        else "active-high (asserted when 1)"
    )
    edge = (
        "on assertion of reset (independent of clk)"
        if opts.reset_style == "async"
        else "on the rising clock edge while reset is asserted"
    )
    return f"The {pol} reset clears every stage of the synchronizer chain {style} {edge}."


def explain(opts: CdcSynchronizerOptions) -> ExplanationDoc:
    """Fully populated explanation for the chosen options."""
    stage_names = _stage_names(opts)
    width_word = f"{opts.width}-bit" if opts.width > 1 else "single-bit"

    reset_config_text = (
        f"enabled ({opts.reset_style}, {opts.reset_polarity})"
        if opts.use_reset
        else "none (use_reset is false)"
    )
    configuration = [
        f"Stages: {opts.stages}",
        f"Width: {opts.width} bit(s)",
        f"Reset: {reset_config_text}",
        f"Output language: {'SystemVerilog' if opts.language == 'sv' else 'Verilog-2001'}",
    ]

    signals = [
        SignalDoc(
            name="clk",
            direction="input",
            description="Destination-domain clock; all stages update on the rising edge.",
        ),
    ]
    if opts.use_reset:
        signals.append(
            SignalDoc(
                name="rst" + ("_n" if opts.reset_polarity == "active_low" else ""),
                direction="input",
                description=_reset_doc(opts) + " reset input.",
            )
        )
    signals.append(
        SignalDoc(
            name="d_async",
            direction="input",
            description=(
                f"Asynchronous {width_word} input; not synchronous to clk. "
                "This is the signal being crossed into the clk domain."
            ),
        )
    )
    for i, name in enumerate(stage_names[:-1]):
        signals.append(
            SignalDoc(
                name=name,
                direction="internal",
                description=(
                    f"Synchronizer stage {i + 1} of {opts.stages} "
                    "(metastability-prone; not for use elsewhere)."
                ),
            )
        )
    signals.append(
        SignalDoc(
            name="q",
            direction="output",
            description=(
                f"Synchronized {width_word} output, stable and glitch-free "
                f"{opts.stages} clk cycles after d_async changes."
            ),
        )
    )

    assumptions = [
        "d_async may change asynchronously to clk at any time (that is the "
        "entire reason this snippet exists); its source-domain logic is "
        "outside the scope of this snippet.",
        "d_async is not combinationally derived from multiple signals that "
        "must stay consistent with each other; each bit passed through this "
        "synchronizer is treated as an independent single-bit signal.",
        f"{opts.stages} stages give a metastability resolution time of "
        f"{opts.stages} clk periods before q is sampled by downstream logic; "
        "choose more stages for higher-frequency or higher-reliability "
        "designs.",
    ]
    if opts.width > 1:
        assumptions.append(
            "WIDTH > 1: this snippet instantiates WIDTH independent "
            "single-bit synchronizer chains, one per bit. Individual bits can "
            "resolve metastability on different clock cycles, so this is "
            "only safe for gray-coded counters/pointers or quasi-static "
            "(rarely-changing, one-bit-at-a-time) signals. It is NOT safe "
            "for an arbitrary multi-bit data bus that changes multiple bits "
            "at once -- use a handshake or async FIFO for that instead."
        )

    limitations = [
        "This snippet provides no protection against metastability beyond "
        f"the {opts.stages}-stage synchronizer chain itself; it does not "
        "guarantee zero probability of metastability propagating downstream, "
        "only a reduced (not eliminated) failure rate.",
        "This synchronizer does not guarantee pulses on d_async are captured: "
        "a pulse narrower than one clk period, or asserted too close to a "
        "sampling edge, can be missed entirely. Use a level signal, a "
        "toggle/pulse synchronizer, or a handshake protocol if pulse capture "
        "is required.",
        "No output enable, handshake, or data-valid signaling; q is always "
        "driven and there is no indication of when a new synchronized value "
        "has arrived.",
    ]

    return ExplanationDoc(
        purpose=(
            f"A {opts.stages}-stage {width_word} flip-flop synchronizer that "
            "safely transfers an asynchronous signal (d_async) into the clk "
            "clock domain (q), reducing the probability that metastability "
            "propagates to downstream logic."
        ),
        configuration=configuration,
        signals=signals,
        reset_behavior=_reset_behavior_text(opts),
        enable_behavior=None,
        assumptions=assumptions,
        limitations=limitations,
    )


# ---------------------------------------------------------------------------
# SnippetDef instance (discovered by the registry)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class _CdcSynchronizerSnippet:
    """Bundles the CDC synchronizer's metadata and pure ``generate``/``explain``
    fns. Satisfies the :class:`~.contract.SnippetDef` protocol structurally.
    """

    id: str = "cdc-synchronizer"
    name: str = "CDC Synchronizer"
    description: str = (
        "Multi-stage flip-flop synchronizer for safely crossing an "
        "asynchronous signal into a destination clock domain."
    )
    options_model: type[CdcSynchronizerOptions] = CdcSynchronizerOptions

    def generate(self, opts: CdcSynchronizerOptions) -> Module:
        return generate(opts)

    def explain(self, opts: CdcSynchronizerOptions) -> ExplanationDoc:
        return explain(opts)


SNIPPET = _CdcSynchronizerSnippet()


__all__ = ["CdcSynchronizerOptions", "generate", "explain", "SNIPPET"]
