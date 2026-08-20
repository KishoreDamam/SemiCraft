"""Fixtures for the P4-01 IP-contract tests.

The reference IP is deliberately not a catalog file (see
``reference_ip.py``), so tests that need to reach it through
``generate_files`` register it into the catalog for the duration of one test.
That is the whole point: it exercises the *registry* path, not a private
back door, so anything that would break a real IP breaks here too.
"""

from __future__ import annotations

import pytest
from semicraft_core.snippets import registry

from .reference_ip import REFERENCE_IP


@pytest.fixture
def registered_ip(monkeypatch):
    """Register the reference IP into the catalog for one test.

    ``monkeypatch`` restores the module-level cache afterwards, so no other
    test ever sees an ``ip``-kind item in the catalog.
    """
    catalog = dict(registry._registry())
    catalog[REFERENCE_IP.id] = REFERENCE_IP
    monkeypatch.setattr(registry, "_REGISTRY", catalog)
    return REFERENCE_IP
