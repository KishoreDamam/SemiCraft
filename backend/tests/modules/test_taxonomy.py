"""Catalog taxonomy (Phase-2 Appendix A.2): kind/maturity defaults, by_kind,
cross-package duplicate-id detection.

Verifies that adding taxonomy to the catalog required ZERO edits to the ten
shipped snippet files: every snippet still reports kind=="snippet" and
maturity=="stable" via the registry's getattr-defaulting, and remains a valid
SnippetDef (isinstance stays true).
"""

from __future__ import annotations

import sys
import types

import pytest
from semicraft_core.modules.contract import ModuleDef
from semicraft_core.snippets import registry
from semicraft_core.snippets.contract import SnippetDef


def test_all_existing_snippets_default_to_snippet_stable() -> None:
    snippets = registry.by_kind("snippet")
    assert len(snippets) == 10  # the ten WP-05 snippet files
    for snippet in snippets:
        assert registry.item_kind(snippet) == "snippet"
        assert registry.item_maturity(snippet) == "stable"
        # Zero-edit guarantee: still structurally a SnippetDef.
        assert isinstance(snippet, SnippetDef)


def test_snippet_files_do_not_declare_kind_attribute() -> None:
    """The snippet files themselves were not edited: their defs have no ``kind``
    attribute of their own — the default comes from the registry."""
    counter = registry.get("counter")
    assert not hasattr(counter, "kind")
    assert not hasattr(counter, "maturity")


def test_module_reports_module_kind() -> None:
    module = registry.get("edge-detector")
    assert registry.item_kind(module) == "module"
    assert registry.item_maturity(module) == "stable"
    assert module.kind == "module"


def test_by_kind_module_returns_only_modules() -> None:
    modules = registry.by_kind("module")
    # Grows as later P2-0x module WPs land; sorted by id (registry.by_kind order).
    assert [m.id for m in modules] == sorted(
        ["edge-detector", "debouncer", "clock-divider", "pwm", "lfsr", "gray-counter", "rr-arbiter"]
    )
    for m in modules:
        assert registry.item_kind(m) == "module"


def test_by_kind_unknown_kind_is_empty() -> None:
    assert registry.by_kind("ip") == []


def test_all_includes_both_kinds_sorted() -> None:
    ids = [i.id for i in registry.all()]
    assert ids == sorted(ids)
    assert "counter" in ids  # snippet
    assert "edge-detector" in ids  # module
    assert len(ids) == len(registry.by_kind("snippet")) + len(registry.by_kind("module"))


def test_by_kind_snippet_matches_pre_phase2_catalog() -> None:
    """by_kind("snippet") reproduces the snippet-only catalog (no modules)."""
    snippet_ids = {s.id for s in registry.by_kind("snippet")}
    assert "edge-detector" not in snippet_ids
    assert "counter" in snippet_ids


def test_edge_detector_module_satisfies_module_protocol() -> None:
    module = registry.get("edge-detector")
    assert isinstance(module, ModuleDef)


def test_cross_package_duplicate_id_is_hard_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """A module sharing an id with an existing snippet fails at discovery
    (snippets and modules share one id namespace)."""
    from dataclasses import dataclass

    from semicraft_core.modules.contract import (
        ExplanationDoc,
        PortGroup,
        TbSpec,
    )

    @dataclass(frozen=True)
    class _DupeModule:
        id: str = "counter"  # collides with the counter snippet
        name: str = "Dupe"
        description: str = "collides across packages"
        kind: str = "module"
        maturity: str = "stable"
        options_model: type = registry.get("counter").options_model

        def generate(self, opts):  # pragma: no cover - not reached
            raise NotImplementedError

        def explain(self, opts) -> ExplanationDoc:  # pragma: no cover
            raise NotImplementedError

        def port_groups(self, opts) -> list[PortGroup]:  # pragma: no cover
            raise NotImplementedError

        def tb_spec(self, opts) -> TbSpec:  # pragma: no cover
            raise NotImplementedError

    fake_mod = types.ModuleType("semicraft_core.modules._dupe_test")
    fake_mod.MODULE = _DupeModule()
    monkeypatch.setitem(sys.modules, "semicraft_core.modules._dupe_test", fake_mod)

    import pkgutil

    real_iter = pkgutil.iter_modules

    def fake_iter(path):
        # Yield the injected module name only for the modules package walk.
        import semicraft_core.modules as modules_pkg

        results = list(real_iter(path))
        if list(path) == list(modules_pkg.__path__):
            results.append(pkgutil.ModuleInfo(None, "_dupe_test", False))
        yield from results

    monkeypatch.setattr("semicraft_core.snippets.registry.pkgutil.iter_modules", fake_iter)
    monkeypatch.setattr("semicraft_core.snippets.registry._REGISTRY", None)

    with pytest.raises(registry.DuplicateSnippetError):
        registry._discover()

    # Rebuild cleanly afterwards.
    monkeypatch.setattr("semicraft_core.snippets.registry._REGISTRY", None)
