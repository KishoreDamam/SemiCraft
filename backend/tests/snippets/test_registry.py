"""Registry discovery and duplicate-id detection (WP-03 task 5)."""

from __future__ import annotations

import sys
import types

import pytest
from semicraft_core.snippets import registry
from semicraft_core.snippets.contract import SnippetDef


def test_counter_is_discovered() -> None:
    counter = registry.get("counter")
    assert counter.id == "counter"
    assert isinstance(counter, SnippetDef)


def test_all_is_sorted_by_id() -> None:
    ids = [s.id for s in registry.all()]
    assert ids == sorted(ids)
    assert "counter" in ids


def test_all_returns_snippet_instances() -> None:
    for snippet in registry.all():
        assert isinstance(snippet, SnippetDef)


def test_get_unknown_raises_keyerror_subclass() -> None:
    with pytest.raises(registry.UnknownSnippetError):
        registry.get("does-not-exist")
    # It is a KeyError subclass (API catches either -> 404).
    with pytest.raises(KeyError):
        registry.get("does-not-exist")


def test_duplicate_id_is_hard_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """Two discovered snippets with the same id fail at discovery."""
    # Craft a second module exporting a snippet whose id collides with counter.
    from dataclasses import dataclass

    from semicraft_core.snippets.contract import ExplanationDoc

    @dataclass(frozen=True)
    class _Dupe:
        id: str = "counter"
        name: str = "Dupe"
        description: str = "collides"
        options_model: type = registry.get("counter").options_model

        def generate(self, opts):  # pragma: no cover - not reached
            raise NotImplementedError

        def explain(self, opts) -> ExplanationDoc:  # pragma: no cover
            raise NotImplementedError

    fake_mod = types.ModuleType("semicraft_core.snippets._dupe_test")
    fake_mod.SNIPPET = _Dupe()
    monkeypatch.setitem(sys.modules, "semicraft_core.snippets._dupe_test", fake_mod)

    # Force iter_modules to also yield our injected module name.
    import pkgutil

    real_iter = pkgutil.iter_modules

    def fake_iter(path):
        yield from real_iter(path)
        yield pkgutil.ModuleInfo(None, "_dupe_test", False)

    monkeypatch.setattr("semicraft_core.snippets.registry.pkgutil.iter_modules", fake_iter)
    monkeypatch.setattr("semicraft_core.snippets.registry._REGISTRY", None)

    with pytest.raises(registry.DuplicateSnippetError):
        registry._discover()

    # Ensure the real registry is rebuilt cleanly afterwards (monkeypatch
    # restores iter_modules and _REGISTRY when the test exits).
    monkeypatch.setattr("semicraft_core.snippets.registry._REGISTRY", None)
