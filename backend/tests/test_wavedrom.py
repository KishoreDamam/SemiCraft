"""WaveDrom timing diagrams derived from the directed testbench (P4-10).

The point of these tests is that the diagram is *derived*, not authored. A
hand-drawn waveform in a datasheet is the classic place for documentation to
drift from behaviour, so the checks here are about the derivation chain:

    diagram  <-  TbSpec.vectors / TbSpec.checks  <-  verified by the run gate

`test_output_values_come_from_the_checks` walks the whole rendered wave back to
the check list, and `test_changing_a_check_changes_the_diagram` confirms it is
a function of the spec rather than a constant that happens to look right.
"""

from __future__ import annotations

import json

import pytest
from semicraft_core.generate import generate_files
from semicraft_core.modules.contract import Check, TbSpec
from semicraft_core.snippets import registry
from semicraft_core.tb.generate_tb import _param_values, _width_of
from semicraft_core.wavedrom import (
    DEFAULT_MAX_CYCLES,
    timing_diagram,
    timing_section_md,
)

IP_IDS = [
    "axil-gpio",
    "axil-i2c",
    "axil-intc",
    "axil-regblock",
    "axil-spi",
    "axil-timer",
    "axil-uart",
    "sync-fifo",
    "sync-ram",
]


def _diagram(item_id: str, options: dict | None = None, **kw):
    item = registry.get(item_id)
    opts = item.options_model.model_validate(options or {})
    module = item.generate(opts)
    params = _param_values(module)
    widths = {p.name: _width_of(p.dtype, params) for p in module.ports}
    return item, opts, module, timing_diagram(
        item.tb_spec(opts), module, widths, lambda n: n,
        title=f"{module.name} — directed sequence", **kw,
    )


def _rows(diagram) -> list[dict]:
    return [r for r in json.loads(diagram.json_text)["signal"] if r]


# --------------------------------------------------------------------------- #
# Structure
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("item_id", IP_IDS, ids=IP_IDS)
def test_every_ip_renders_a_diagram(item_id: str) -> None:
    _item, _opts, _module, diagram = _diagram(item_id)
    assert diagram is not None


@pytest.mark.parametrize("item_id", IP_IDS, ids=IP_IDS)
def test_every_wave_is_the_same_length(item_id: str) -> None:
    """A wave one character short silently misaligns every cycle after it, and
    the diagram still renders — so the length is the one thing that must be
    checked structurally rather than by eye."""
    _item, opts, _module, diagram = _diagram(item_id)
    rows = _rows(diagram)
    lengths = {len(r["wave"]) for r in rows}
    assert len(lengths) == 1, (
        f"{item_id}: waves have differing lengths {sorted(lengths)}"
    )
    spec = registry.get(item_id).tb_spec(opts)
    prologue = spec.reset_cycles if spec.reset is not None else 0
    assert lengths.pop() == prologue + diagram.cycles


@pytest.mark.parametrize("item_id", IP_IDS, ids=IP_IDS)
def test_every_row_names_a_real_port(item_id: str) -> None:
    _item, _opts, module, diagram = _diagram(item_id)
    ports = {p.name for p in module.ports}
    for row in _rows(diagram):
        assert row["name"] in ports, f"{item_id}: {row['name']!r} is not a port"


@pytest.mark.parametrize("item_id", IP_IDS, ids=IP_IDS)
def test_data_labels_match_the_data_slots(item_id: str) -> None:
    """WaveDrom consumes `data` positionally against each `=`; a mismatch
    shifts every label after it onto the wrong cycle."""
    _item, _opts, _module, diagram = _diagram(item_id)
    for row in _rows(diagram):
        assert row["wave"].count("=") == len(row.get("data", [])), (
            f"{item_id}: {row['name']} has {row['wave'].count('=')} data slots "
            f"but {len(row.get('data', []))} labels"
        )


# WaveDrom's wave alphabet, restricted to what this generator is allowed to
# emit. Nothing here can render the diagram to check it looks right - that
# needs a JavaScript runtime - so the next best thing is refusing to emit a
# character WaveDrom would not understand.
_LEGAL_WAVE_CHARS = set("01=x.")


@pytest.mark.parametrize("item_id", IP_IDS, ids=IP_IDS)
def test_waves_use_only_legal_characters(item_id: str) -> None:
    _item, _opts, _module, diagram = _diagram(item_id)
    signal = json.loads(diagram.json_text)["signal"]
    clock, rest = signal[0], [r for r in signal[1:] if r]
    assert set(clock["wave"]) <= {"p", "."}
    for row in rest:
        illegal = set(row["wave"]) - _LEGAL_WAVE_CHARS
        assert not illegal, f"{item_id}: {row['name']} emits {illegal}"


@pytest.mark.parametrize("item_id", IP_IDS, ids=IP_IDS)
def test_diagram_is_deterministic(item_id: str) -> None:
    a = _diagram(item_id)[3]
    b = _diagram(item_id)[3]
    assert a.json_text == b.json_text


# --------------------------------------------------------------------------- #
# The derivation chain
# --------------------------------------------------------------------------- #


def _decoded(row: dict) -> list[int | None]:
    """Per-cycle integer value of a row, or None where the wave says unknown."""
    out: list[int | None] = []
    data = list(row.get("data", []))
    current: int | None = None
    for ch in row["wave"]:
        if ch == "x":
            current = None
        elif ch == "=":
            current = int(data.pop(0), 16)
        elif ch in "01":
            current = int(ch)
        elif ch == ".":
            pass
        else:  # pragma: no cover - the clock row is filtered out by callers
            raise AssertionError(f"unexpected wave character {ch!r}")
        out.append(current)
    return out


@pytest.mark.parametrize("item_id", IP_IDS, ids=IP_IDS)
def test_output_values_come_from_the_checks(item_id: str) -> None:
    """Every value the diagram shows for an output is a value the testbench
    checks, at the cycle it checks it. This is the whole claim of the module:
    the diagram is a rendering of what CI verifies, not an illustration."""
    item, opts, _module, diagram = _diagram(item_id)
    spec = item.tb_spec(opts)
    prologue = spec.reset_cycles if spec.reset is not None else 0
    driven = {sig for vector in spec.vectors for sig in vector}
    by_signal: dict[str, dict[int, int]] = {}
    for chk in spec.checks:
        by_signal.setdefault(chk.signal, {})[chk.cycle] = chk.expected

    for row in _rows(diagram):
        name = row["name"]
        if name not in by_signal or name in driven:
            continue
        values = _decoded(row)
        for cycle, expected in by_signal[name].items():
            if cycle >= diagram.cycles:
                continue  # beyond the drawn window
            assert values[prologue + cycle] == expected, (
                f"{item_id}: {name} at cycle {cycle} is drawn as "
                f"{values[prologue + cycle]}, but the testbench checks {expected}"
            )


def test_changing_a_check_changes_the_diagram() -> None:
    """A diagram that ignored the spec would still satisfy every structural
    test above, so this pins that it is actually a function of the input."""
    item = registry.get("axil-gpio")
    opts = item.options_model.model_validate({})
    module = item.generate(opts)
    params = _param_values(module)
    widths = {p.name: _width_of(p.dtype, params) for p in module.ports}

    spec = item.tb_spec(opts)
    original = timing_diagram(
        spec, module, widths, lambda n: n, title="t"
    )
    bumped = spec.model_copy(
        update={
            "checks": [
                Check(cycle=c.cycle, signal=c.signal, expected=c.expected ^ 1)
                for c in spec.checks
            ]
        }
    )
    changed = timing_diagram(bumped, module, widths, lambda n: n, title="t")
    assert original is not None and changed is not None
    assert original.json_text != changed.json_text


def test_unchecked_cycles_are_drawn_unknown() -> None:
    """`x` is what the testbench knows, not a rendering shortcut — and it makes
    the diagram double as a picture of directed coverage."""
    _item, _opts, _module, diagram = _diagram("axil-gpio")
    outputs = [r for r in _rows(diagram) if "x" in r["wave"]]
    assert outputs, "no output has an unchecked cycle, which would be surprising"


# --------------------------------------------------------------------------- #
# Windowing and edge cases
# --------------------------------------------------------------------------- #


def test_a_long_sequence_is_truncated_and_says_so() -> None:
    """The serial IPs run for thousands of cycles at their default divisors."""
    _item, _opts, _module, diagram = _diagram("axil-uart")
    assert diagram.truncated
    assert diagram.cycles == DEFAULT_MAX_CYCLES
    assert diagram.total_cycles > DEFAULT_MAX_CYCLES
    md = "\n".join(timing_section_md(diagram))
    assert f"first {DEFAULT_MAX_CYCLES} of {diagram.total_cycles}" in md


def test_a_short_sequence_is_not_marked_truncated() -> None:
    _item, _opts, _module, diagram = _diagram("sync-ram")
    if not diagram.truncated:
        assert "Showing the first" not in "\n".join(timing_section_md(diagram))


def test_an_unreset_ip_gets_no_reset_row() -> None:
    """The RAM has no reset at all (P4-04), so there is no prologue to draw."""
    item = registry.get("sync-ram")
    assert item.tb_spec(item.options_model.model_validate({})).reset is None
    _item, _opts, module, diagram = _diagram("sync-ram")
    names = {r["name"] for r in _rows(diagram)}
    assert "rst" not in names and "rst_n" not in names
    assert "clk" in names


def test_a_spec_with_nothing_to_draw_renders_nothing() -> None:
    empty = TbSpec(clock="clk", reset=None, vectors=[], checks=[])
    module = registry.get("sync-ram").generate(
        registry.get("sync-ram").options_model.model_validate({})
    )
    assert timing_diagram(empty, module, {}, lambda n: n, title="t") is None
    assert timing_section_md(None) == []


def test_naming_style_reaches_the_diagram() -> None:
    """The diagram must name the ports the RTL actually declares — the same
    restyling requirement every other generated artifact has."""
    doc = next(
        f.text
        for f in generate_files(
            "axil-gpio", {"naming": {"convention": "camel", "prefix": "p_"}}
        ).files
        if f.kind == "doc"
    )
    block = doc[doc.index("```wavedrom"):]
    assert '"name": "p_aclk"' in block


# --------------------------------------------------------------------------- #
# Placement in the datasheet
# --------------------------------------------------------------------------- #


def test_timing_follows_the_interface_and_precedes_configuration() -> None:
    doc = next(f.text for f in generate_files("axil-gpio", {}).files if f.kind == "doc")
    assert doc.index("## Register map") < doc.index("## Timing")
    assert doc.index("## Timing") < doc.index("## Configuration")


def test_modules_get_no_timing_section() -> None:
    """P4-10 is a per-IP generator; widening it to every module would rewrite
    fifteen hundred goldens for no decision anyone has made."""
    doc = next(f.text for f in generate_files("clock-divider", {}).files if f.kind == "doc")
    assert "## Timing" not in doc
