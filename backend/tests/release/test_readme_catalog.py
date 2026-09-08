"""Ties the README's catalog to the registry (launch blocker B2).

The README described the Phase-1 snippet MVP through v0.4.0: ten snippet
categories presented as *the* supported set, while the product had grown to
26 items across three kinds. Modules, IPs and the entire verification stack —
three phases of work — appeared only as roadmap bullets. Nothing failed,
because nothing connected the README's claims to the catalog.

That is the same shape as the defects this project keeps finding: an artifact
that exists, reads plausibly, and is checked by nothing. The README is the
first thing anyone sees, so it is the worst place in the repository for it.

This test connects them. Adding a catalog item without listing it, removing one
without delisting it, or misstating the total all fail here.

Deliberately not asserted: the descriptions. Marketing copy should be free to
say something more useful than the registry's one-liner. What must not drift is
*which blocks exist* and *how many*.
"""

from __future__ import annotations

import re
from pathlib import Path

from semicraft_core.snippets import registry

_README = Path(__file__).resolve().parents[3] / "README.md"

# Heading -> registry kind. The headings are part of the contract this test
# enforces; renaming one in the README means renaming it here too, which is a
# visible edit rather than a silent drift.
_SECTIONS = {"### Snippets": "snippet", "### Modules": "module", "### IP blocks": "ip"}

_TABLE_ROW = re.compile(r"^\|\s*`([a-z0-9-]+)`\s*\|", re.MULTILINE)
_TOTAL = re.compile(r"^(\d+) items\.", re.MULTILINE)


def _readme() -> str:
    return _README.read_text(encoding="utf-8")


def _section_body(text: str, heading: str) -> str:
    start = text.index(heading) + len(heading)
    rest = text[start:]
    # Up to the next heading of the same or higher level.
    end = re.search(r"^#{1,3} ", rest, re.MULTILINE)
    return rest[: end.start()] if end else rest


def _listed_ids(kind: str) -> set[str]:
    heading = next(h for h, k in _SECTIONS.items() if k == kind)
    return set(_TABLE_ROW.findall(_section_body(_readme(), heading)))


def _registry_ids(kind: str) -> set[str]:
    return {item.id for item in registry.by_kind(kind)}


def test_every_catalog_section_is_present() -> None:
    text = _readme()
    for heading in _SECTIONS:
        assert heading in text, f"README has no '{heading}' section to check"


def test_snippets_listed_match_the_registry() -> None:
    assert _listed_ids("snippet") == _registry_ids("snippet")


def test_modules_listed_match_the_registry() -> None:
    assert _listed_ids("module") == _registry_ids("module")


def test_ips_listed_match_the_registry() -> None:
    assert _listed_ids("ip") == _registry_ids("ip")


def test_no_item_is_listed_under_the_wrong_kind() -> None:
    """A module listed among the snippets would satisfy a naive total."""
    for kind in _SECTIONS.values():
        stray = _listed_ids(kind) - _registry_ids(kind)
        assert not stray, f"README lists {sorted(stray)} under {kind}, where they do not belong"


def test_the_stated_total_matches_the_catalog() -> None:
    match = _TOTAL.search(_readme())
    assert match is not None, "README no longer states a catalog total ('<N> items.')"
    stated = int(match.group(1))
    actual = sum(len(_registry_ids(kind)) for kind in _SECTIONS.values())
    assert stated == actual, f"README claims {stated} items; the catalog holds {actual}"


def test_the_readme_does_not_still_call_itself_a_snippet_generator() -> None:
    """The specific stale framing this blocker was about."""
    text = _readme()
    assert "MVP: RTL Snippet Generator" not in text
    assert "Supported snippet categories (MVP)" not in text
