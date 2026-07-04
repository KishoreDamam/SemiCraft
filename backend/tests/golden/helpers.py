"""Property-test helpers for snippet tests (IMPLEMENTATION_PLAN.md §5 WP-08 task 5).

Importable from any test file, e.g.::

    from tests.golden.helpers import assert_port_present, assert_port_absent

Kept intentionally light on assumptions about renderer formatting: port
presence/absence is checked at the identifier-boundary level (word-boundary
regex) rather than exact-column matching, so it stays valid across both
languages and all naming/style options.
"""

from __future__ import annotations

import re

from semicraft_core import generate

__all__ = ["assert_port_present", "assert_port_absent", "assert_output_differs"]


def _word_present(code: str, name: str) -> bool:
    """True if ``name`` appears in ``code`` as a whole identifier (word boundary)."""
    return re.search(rf"\b{re.escape(name)}\b", code) is not None


def assert_port_present(code: str, name: str) -> None:
    """Assert the identifier ``name`` (e.g. a port name) appears in ``code``."""
    assert _word_present(code, name), f"expected {name!r} to be present in code:\n{code}"


def assert_port_absent(code: str, name: str) -> None:
    """Assert the identifier ``name`` does NOT appear anywhere in ``code``."""
    assert not _word_present(code, name), (
        f"expected {name!r} to be absent from code, but it was found:\n{code}"
    )


def assert_output_differs(snippet_id: str, opts_a: dict, opts_b: dict) -> None:
    """Assert two option dicts for ``snippet_id`` produce different generated code.

    Useful for confirming an option actually has an effect (complementary to the
    golden snapshots, which pin exact output).
    """
    code_a = generate(snippet_id, opts_a).code
    code_b = generate(snippet_id, opts_b).code
    assert code_a != code_b, (
        f"expected {snippet_id!r} options {opts_a!r} and {opts_b!r} to produce "
        "different output, but they matched"
    )
