"""API contract tests for POST /api/v2/simulate (P3-03).

``run_smoke`` is mocked throughout so the suite never needs a real verilator
(graceful degradation is mandatory — the endpoint and its tests must pass on a
Windows dev host with no verilator). We assert the response shape, the status
folding, the unavailable / no-TB / timeout paths, and that error mapping
(404 / 422) matches the other v2 routes.
"""

from __future__ import annotations

from unittest.mock import patch

from api.main import app
from fastapi.testclient import TestClient
from semicraft_core.sim import SimResult

client = TestClient(app)

_EXPECTED_KEYS = {
    "status",
    "exit_code",
    "stdout_tail",
    "stderr_tail",
    "duration_s",
    "marker_seen",
}


def _fake_run(status, *, exit_code=None, stdout="", stderr=""):
    def _run(tb_path, rtl_paths, **kwargs):
        return SimResult(status, exit_code, stdout, stderr, 0.42)

    return _run


def test_simulate_module_pass_shape() -> None:
    with patch(
        "semicraft_core.sim.service.run_smoke",
        side_effect=_fake_run("pass", exit_code=0, stdout="SMOKE PASS: edge_detector"),
    ):
        response = client.post(
            "/api/v2/simulate",
            json={"item_id": "edge-detector", "options": {"language": "sv"}},
        )
    assert response.status_code == 200
    body = response.json()
    assert set(body.keys()) == _EXPECTED_KEYS
    assert body["status"] == "pass"
    assert body["exit_code"] == 0
    assert body["marker_seen"] is True
    assert isinstance(body["duration_s"], (int, float))


def test_simulate_module_fail() -> None:
    with patch(
        "semicraft_core.sim.service.run_smoke",
        side_effect=_fake_run("fail", exit_code=1, stdout="mismatch at cycle 3"),
    ):
        response = client.post(
            "/api/v2/simulate",
            json={"item_id": "edge-detector", "options": {"language": "sv"}},
        )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "fail"
    assert body["marker_seen"] is False


def test_simulate_unavailable_when_verilator_missing() -> None:
    """No verilator must yield 200 + status='unavailable', never a 500."""
    with patch(
        "semicraft_core.sim.service.run_smoke",
        side_effect=_fake_run("unavailable", stderr="verilator binary not found on PATH"),
    ):
        response = client.post(
            "/api/v2/simulate",
            json={"item_id": "edge-detector", "options": {"language": "sv"}},
        )
    assert response.status_code == 200
    assert response.json()["status"] == "unavailable"


def test_simulate_timeout_surfaced_as_error() -> None:
    with patch(
        "semicraft_core.sim.service.run_smoke",
        side_effect=_fake_run("timeout", stderr="simulation binary timed out after 30s"),
    ):
        response = client.post(
            "/api/v2/simulate",
            json={"item_id": "edge-detector", "options": {"language": "sv"}},
        )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "error"
    assert "timed out" in body["stderr_tail"]


def test_simulate_snippet_has_no_tb() -> None:
    """A snippet (counter) generates no testbench -> status='no_tb', no run."""
    with patch("semicraft_core.sim.service.run_smoke") as mock_run:
        response = client.post(
            "/api/v2/simulate",
            json={"item_id": "counter", "options": {"language": "sv"}},
        )
    mock_run.assert_not_called()
    assert response.status_code == 200
    assert response.json()["status"] == "no_tb"


def test_simulate_unknown_item_id_404() -> None:
    response = client.post(
        "/api/v2/simulate",
        json={"item_id": "does-not-exist", "options": {}},
    )
    assert response.status_code == 404


def test_simulate_invalid_options_422_shape() -> None:
    response = client.post(
        "/api/v2/simulate",
        json={"item_id": "counter", "options": {"width": 0}},
    )
    assert response.status_code == 422
    body = response.json()
    assert isinstance(body["detail"], list) and len(body["detail"]) >= 1
    assert body["detail"][0]["loc"][:2] == ["body", "options"]
