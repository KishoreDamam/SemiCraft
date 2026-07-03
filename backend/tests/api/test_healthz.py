"""Trivial smoke test for the placeholder API app (WP-00).

WP-06 will add full coverage of the frozen API contract.
"""

from api.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def test_healthz_returns_ok() -> None:
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
