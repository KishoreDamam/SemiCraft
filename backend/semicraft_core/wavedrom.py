"""WaveDrom timing diagrams derived from the directed testbench (Phase-4 P4-10).

A timing diagram in a datasheet is the classic place for documentation to drift
away from behaviour: it looks authoritative, it is drawn by hand, and nothing
checks it. This project has already fixed that class of bug twice — a datasheet
claiming reserved bits "ignore writes" while the RTL answered SLVERR, and a
generic renderer asserting timing the model did not own.

So this generator draws nothing of its own. Every waveform here is rendered
from the **same** :class:`~.modules.contract.TbSpec` that
:mod:`~semicraft_core.tb.generate_tb` turns into the smoke testbench — the one
Verilator executes against the real RTL in CI on every option case of every IP.
That makes the chain closed:

    diagram  <-  TbSpec.vectors / TbSpec.checks  <-  verified by the run gate

If the RTL stops behaving this way, the run gate goes red. If the ``tb_spec``
recipe changes, the diagram changes with it. A diagram cannot be quietly wrong
while the tests are green, which is the only property that makes it worth
printing.

Honest about what is *not* known
--------------------------------

Inputs are fully determined: the testbench drives them, and a signal absent
from a cycle's vector holds its previous value (the generated TB assigns only
what changed, and Verilog assignments persist). Outputs are different — the
testbench pins them only on the cycles it checks, and says nothing in between.

Those cycles are drawn ``x``. Not as a rendering shortcut: ``x`` is what the
testbench actually knows. The side effect is that the diagram doubles as a
picture of directed coverage — a long ``x`` run on an output is a stretch of
behaviour nobody is checking, which is worth seeing in a datasheet rather than
smoothing over with a plausible-looking line.

Why the JSON is inlined in the datasheet
----------------------------------------

``GeneratedFile.kind`` is a frozen ``Literal["rtl", "tb", "doc"]`` (plan
Appendix A.1), and a ``.json`` data file is none of the three — the same
blocker recorded against the ROM's ``$readmemh`` route. Rather than widen a
frozen contract for a diagram, the JSON goes inline in the markdown datasheet
as a ```wavedrom fenced block, which is how WaveDrom is embedded in markdown
anyway.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass

from .ir.nodes import Module
from .modules.contract import TbSpec

__all__ = [
    "DEFAULT_MAX_CYCLES",
    "TimingDiagram",
    "timing_diagram",
    "timing_section_md",
]

# Enough to cover the reset release and the first few bus transactions, which
# is the instructive part of every sequence in the catalog. The serial IPs run
# for thousands of cycles at their default divisors; drawing all of it would
# produce a diagram nobody can read and a datasheet nobody can diff.
DEFAULT_MAX_CYCLES = 40

_UNKNOWN = "x"


@dataclass(frozen=True, slots=True)
class TimingDiagram:
    """One rendered diagram plus what a reader needs to trust it."""

    title: str
    json_text: str
    cycles: int
    total_cycles: int

    @property
    def truncated(self) -> bool:
        return self.total_cycles > self.cycles


def _wave_of(values: list[int | None], width: int) -> tuple[str, list[str]]:
    """Turn a per-cycle value list into a WaveDrom wave string plus data labels.

    ``None`` means "the testbench does not pin this cycle" and renders ``x``.
    A repeat of the previous cycle's value renders ``.``, which is what keeps a
    30-cycle idle stretch to one character instead of thirty.
    """
    wave: list[str] = []
    data: list[str] = []
    previous: int | None = None
    started = False
    for value in values:
        if value is None:
            wave.append(_UNKNOWN)
            previous, started = None, False
            continue
        if started and value == previous:
            wave.append(".")
            continue
        if width == 1:
            wave.append("1" if value else "0")
        else:
            wave.append("=")
            data.append(f"0x{value:X}")
        previous, started = value, True
    return "".join(wave), data


def _driven_values(
    spec: TbSpec, signal: str, prologue: int, cycles: int
) -> list[int | None]:
    """Per-cycle value of a driven input, including the reset prologue.

    The generated testbench initialises every driven input to 0 before
    asserting reset, so the prologue is zeros, and a cycle whose vector omits
    the signal holds the previous value.
    """
    values: list[int | None] = [0] * prologue
    current = 0
    for c in range(cycles):
        if c < len(spec.vectors) and signal in spec.vectors[c]:
            current = spec.vectors[c][signal]
        values.append(current)
    return values


def _checked_values(
    spec: TbSpec, signal: str, prologue: int, cycles: int
) -> list[int | None]:
    """Per-cycle value of an output: the checked value, or ``None`` for unknown."""
    by_cycle = {c.cycle: c.expected for c in spec.checks if c.signal == signal}
    values: list[int | None] = [None] * prologue
    values.extend(by_cycle.get(c) for c in range(cycles))
    return values


def _reset_wave(spec: TbSpec, module: Module, prologue: int, cycles: int) -> list[int]:
    """Asserted through the prologue, deasserted for every directed cycle.

    Polarity comes from ``generate_tb._find_reset``, the same lookup the
    testbench uses to decide which level to drive — including its handling of a
    reset nested inside a ``GenFor``. Re-deriving it here would be one more
    place for the diagram to disagree with the simulation it claims to show.
    """
    # Function-level import: the tb package pulls in the TB node family, and a
    # module-load-time import would widen this module's import graph for a
    # single lookup.
    from .tb.generate_tb import _find_reset

    assert spec.reset is not None
    found = _find_reset(module, spec.reset)
    active_low = found.active_low if found is not None else False
    asserted = 0 if active_low else 1
    return [asserted] * prologue + [1 - asserted] * cycles


def timing_diagram(
    spec: TbSpec,
    module: Module,
    widths: dict[str, int],
    rename: Callable[[str], str],
    *,
    title: str,
    max_cycles: int = DEFAULT_MAX_CYCLES,
) -> TimingDiagram | None:
    """Render the directed sequence as WaveDrom JSON (pure).

    Returns ``None`` when there is nothing honest to draw: no clock, or a spec
    that drives and checks nothing.

    Only signals the sequence actually touches are drawn. A full port list
    would put nineteen AXI signals on every diagram, most of them flat, and
    bury the three that carry the transaction.
    """
    if spec.clock is None:
        return None

    driven = {sig for vector in spec.vectors for sig in vector}
    checked = {c.signal for c in spec.checks}
    if not driven and not checked:
        return None

    last_activity = max(
        [len(spec.vectors)] + [c.cycle + 1 for c in spec.checks], default=0
    )
    cycles = min(last_activity, max_cycles)
    prologue = spec.reset_cycles if spec.reset is not None else 0
    span = prologue + cycles

    rows: list[dict] = [
        {"name": rename(spec.clock), "wave": "p" + "." * (span - 1)}
    ]
    if spec.reset is not None:
        wave, _ = _wave_of(
            [*_reset_wave(spec, module, prologue, cycles)], 1
        )
        rows.append({"name": rename(spec.reset), "wave": wave})

    ports_in_order = [p.name for p in module.ports]

    def _row(signal: str, values: list[int | None]) -> dict:
        wave, data = _wave_of(values, widths.get(signal, 1))
        row: dict = {"name": rename(signal), "wave": wave}
        if data:
            row["data"] = data
        return row

    inputs = [
        _row(sig, _driven_values(spec, sig, prologue, cycles))
        for sig in ports_in_order
        if sig in driven and sig not in (spec.clock, spec.reset)
    ]
    outputs = [
        _row(sig, _checked_values(spec, sig, prologue, cycles))
        for sig in ports_in_order
        if sig in checked and sig not in driven
    ]

    if inputs:
        rows.append({})  # WaveDrom renders an empty object as a spacer row
        rows.extend(inputs)
    if outputs:
        rows.append({})
        rows.extend(outputs)

    diagram = {
        "signal": rows,
        "head": {"text": title, "tick": 0},
        "config": {"hscale": 1},
    }
    return TimingDiagram(
        title=title,
        json_text=json.dumps(diagram, indent=2, sort_keys=False),
        cycles=cycles,
        total_cycles=last_activity,
    )


def timing_section_md(diagram: TimingDiagram | None) -> list[str]:
    """The datasheet's timing section: a ```wavedrom block plus its caveats."""
    if diagram is None:
        return []
    lines = [
        "## Timing",
        "",
        "Rendered from the same directed testbench recipe the smoke simulation "
        "runs in CI, so this diagram cannot drift from the behaviour the tests "
        "verify.",
        "",
        "Inputs are shown as the testbench drives them. Outputs are shown only "
        "on the cycles it checks them; `x` means the testbench pins no value "
        "there, not that the signal is undefined in hardware.",
        "",
    ]
    if diagram.truncated:
        lines += [
            f"Showing the first {diagram.cycles} of {diagram.total_cycles} "
            f"directed cycles.",
            "",
        ]
    lines += ["```wavedrom", diagram.json_text, "```", ""]
    return lines
