"""Generated documentation names the ports the RTL actually declares.

The bug this file exists for: the datasheet's port table printed the names
declared in ``port_groups()``/``ExplanationDoc.signals`` verbatim, never
applying the render name map. Under any naming convention, prefix or suffix —
for every module and every IP — it listed ports that do not exist in the
generated RTL. No golden case set a naming style, so nothing could see it.

That is the third bug of this exact shape here: P3-05a's assertion specs naming
canonical resets, P4-07's hardcoded testbench clock net, and this. The pattern
is always the same — a generator that speaks canonical names and forgets that
every identifier it emits has to go through ``build_name_map`` first.

These tests check the datasheet directly. The systemic guard is the
``styled_names`` golden case, which now covers every catalog item.
"""

from __future__ import annotations

import re

import pytest
from semicraft_core.generate import (
    _style_from_options,
    generate_files,
    resolve_doc_port_name,
)
from semicraft_core.render.style import build_name_map
from semicraft_core.snippets import registry

_STYLE = {"naming": {"convention": "camel", "prefix": "p_"}}
_DOC_PORT = re.compile(r"^\| `(\w+)` \| (?:input|output) \|", re.MULTILINE)

DOCUMENTED_IDS = [
    i.id for i in registry.by_kind("module") + registry.by_kind("ip")
]


def _rendered_ports(item_id: str, options: dict) -> set[str]:
    item = registry.get(item_id)
    opts = item.options_model.model_validate(options)
    module = item.generate(opts)
    names = build_name_map(module, _style_from_options(opts))
    return {names.get(p.name, p.name) for p in module.ports}


@pytest.mark.parametrize("item_id", DOCUMENTED_IDS, ids=DOCUMENTED_IDS)
@pytest.mark.parametrize("options", [{}, _STYLE], ids=["default", "styled"])
def test_datasheet_port_table_names_real_ports(item_id: str, options: dict) -> None:
    doc = next(f.text for f in generate_files(item_id, options).files if f.kind == "doc")
    listed = set(_DOC_PORT.findall(doc))
    assert listed, f"{item_id}: no port rows found in the datasheet"
    unknown = listed - _rendered_ports(item_id, options)
    assert not unknown, (
        f"{item_id} {options}: the datasheet lists ports the RTL does not "
        f"declare: {sorted(unknown)}"
    )


@pytest.mark.parametrize("item_id", DOCUMENTED_IDS, ids=DOCUMENTED_IDS)
def test_a_naming_style_actually_changes_the_datasheet(item_id: str) -> None:
    """Guards the guard: if the style stopped reaching the doc at all, the test
    above would still pass by listing canonical names against a canonical RTL."""
    plain = next(
        f.text for f in generate_files(item_id, {}).files if f.kind == "doc"
    )
    styled = next(
        f.text for f in generate_files(item_id, _STYLE).files if f.kind == "doc"
    )
    assert set(_DOC_PORT.findall(plain)) != set(_DOC_PORT.findall(styled))


# --------------------------------------------------------------------------- #
# The reset-suffix convention the resolution rests on
# --------------------------------------------------------------------------- #


def test_canonical_names_resolve_through_the_map() -> None:
    assert resolve_doc_port_name("aclk", {"aclk"}, lambda n: "p_" + n) == "p_aclk"


def test_a_documentation_only_reset_suffix_is_stripped_first() -> None:
    """`port_groups()` declares an active-low reset as `areset_n` while the IR
    port is `areset` — a documentation convention P3-07 already documented."""
    assert (
        resolve_doc_port_name("areset_n", {"areset"}, lambda n: f"p_{n}_n")
        == "p_areset_n"
    )


def test_a_name_that_is_not_a_port_is_passed_through() -> None:
    """An ExplanationDoc may mention an internal signal; mangling it would be
    worse than leaving it alone."""
    assert resolve_doc_port_name("cnt", {"clk"}, lambda n: "p_" + n) == "cnt"


def test_a_real_port_ending_in_n_is_not_mistaken_for_a_reset() -> None:
    """`cs_n` on the SPI master is a genuine canonical port name, not a
    suffixed reset — the canonical lookup has to win."""
    assert resolve_doc_port_name("cs_n", {"cs_n"}, lambda n: "p_" + n) == "p_cs_n"
