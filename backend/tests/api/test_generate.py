"""Full coverage of the frozen HTTP API contract (IMPLEMENTATION_PLAN.md §4).

Deliberately does NOT hardcode the snippet count in the catalog test — sibling
WP-05x agents are adding snippet files in parallel, so only structural
invariants (every entry has the required keys; the counter entry's schema
carries enums/bounds/descriptions) are asserted.
"""

from __future__ import annotations

import json

from api.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


# ---------------------------------------------------------------------------
# healthz
# ---------------------------------------------------------------------------


def test_healthz_returns_ok() -> None:
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


# ---------------------------------------------------------------------------
# GET /api/v1/snippets
# ---------------------------------------------------------------------------


def test_catalog_entries_have_required_shape() -> None:
    response = client.get("/api/v1/snippets")
    assert response.status_code == 200
    body = response.json()
    assert "snippets" in body
    snippets = body["snippets"]
    assert len(snippets) >= 1  # do not hardcode count; siblings add snippets

    ids = [s["id"] for s in snippets]
    assert "counter" in ids
    assert len(ids) == len(set(ids)), "duplicate snippet ids in catalog"

    for entry in snippets:
        for key in ("id", "name", "description", "json_schema", "defaults"):
            assert key in entry, f"snippet {entry.get('id')} missing key {key!r}"
        assert isinstance(entry["json_schema"], dict)
        assert isinstance(entry["defaults"], dict)
        assert entry["json_schema"].get("properties"), "schema must have properties"


def test_counter_schema_carries_enums_bounds_and_descriptions() -> None:
    """Frontend form dependency (IMPLEMENTATION_PLAN §8 JSON Schema fidelity)."""
    response = client.get("/api/v1/snippets")
    snippets = response.json()["snippets"]
    counter = next(s for s in snippets if s["id"] == "counter")

    schema = counter["json_schema"]
    props = schema["properties"]

    # bounds on width
    width = props["width"]
    assert width["minimum"] == 1
    assert width["maximum"] == 1024
    assert "description" in width and width["description"]

    # enum on direction (may be direct enum or via $defs/$ref/allOf)
    direction = props["direction"]
    direction_enum = direction.get("enum")
    if direction_enum is None and "$ref" in direction:
        ref_name = direction["$ref"].split("/")[-1]
        direction_enum = schema["$defs"][ref_name].get("enum")
    assert direction_enum is not None
    assert set(direction_enum) == {"up", "down", "updown"}
    assert "description" in direction and direction["description"]

    # descriptions present on a boolean field too
    assert props["enable"].get("description")

    # defaults dict actually has the model defaults
    defaults = counter["defaults"]
    assert defaults["width"] == 8
    assert defaults["direction"] == "up"
    assert defaults["enable"] is True


# ---------------------------------------------------------------------------
# POST /api/v1/generate — happy path
# ---------------------------------------------------------------------------


def test_generate_counter_sv_happy_path() -> None:
    response = client.post(
        "/api/v1/generate",
        json={"snippet_id": "counter", "options": {"language": "sv"}},
    )
    assert response.status_code == 200
    body = response.json()

    for key in ("code", "filename", "language", "explanation", "lint", "config_hash"):
        assert key in body

    assert body["language"] == "sv"
    assert body["filename"] == "counter.sv"
    assert "module counter" in body["code"]
    assert isinstance(body["config_hash"], str) and len(body["config_hash"]) == 12

    explanation = body["explanation"]
    for key in (
        "purpose",
        "configuration",
        "signals",
        "reset_behavior",
        "enable_behavior",
        "assumptions",
        "limitations",
    ):
        assert key in explanation

    lint = body["lint"]
    assert lint["status"] in {"clean", "warnings", "unavailable"}
    assert isinstance(lint["messages"], list)


def test_generate_counter_verilog_happy_path() -> None:
    response = client.post(
        "/api/v1/generate",
        json={"snippet_id": "counter", "options": {"language": "verilog"}},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["language"] == "verilog"
    assert body["filename"] == "counter.v"
    assert "module counter" in body["code"]


# ---------------------------------------------------------------------------
# POST /api/v1/generate — fragment mode
# ---------------------------------------------------------------------------


def test_generate_fragment_mode_filename() -> None:
    response = client.post(
        "/api/v1/generate",
        json={
            "snippet_id": "counter",
            "options": {"language": "sv", "include_wrapper": False},
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["filename"] == "counter_fragment.sv"
    # fragment mode never emits the module wrapper
    assert "module counter" not in body["code"]
    # lint still ran (against a wrapper-forced variant) and produced a report
    assert body["lint"]["status"] in {"clean", "warnings", "unavailable"}


# ---------------------------------------------------------------------------
# POST /api/v1/generate — errors
# ---------------------------------------------------------------------------


def test_generate_invalid_options_422_shape() -> None:
    response = client.post(
        "/api/v1/generate",
        json={"snippet_id": "counter", "options": {"width": 0}},
    )
    assert response.status_code == 422
    body = response.json()
    assert "detail" in body
    assert isinstance(body["detail"], list) and len(body["detail"]) >= 1

    item = body["detail"][0]
    assert item["loc"][:2] == ["body", "options"]
    assert "width" in item["loc"]
    assert "msg" in item
    assert "type" in item


def test_generate_unknown_snippet_id_404() -> None:
    response = client.post(
        "/api/v1/generate",
        json={"snippet_id": "does-not-exist", "options": {}},
    )
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# POST /api/v1/generate — config_hash stability
# ---------------------------------------------------------------------------


def test_config_hash_stable_across_identical_calls() -> None:
    payload = {"snippet_id": "counter", "options": {"width": 16, "direction": "down"}}
    r1 = client.post("/api/v1/generate", json=payload)
    r2 = client.post("/api/v1/generate", json=payload)
    assert r1.status_code == 200
    assert r2.status_code == 200
    assert r1.json()["config_hash"] == r2.json()["config_hash"]
    assert r1.json()["code"] == r2.json()["code"]


def test_config_hash_stable_across_option_key_order() -> None:
    opts_a = {"width": 16, "direction": "down", "enable": True}
    opts_b = {"enable": True, "direction": "down", "width": 16}

    r1 = client.post("/api/v1/generate", json={"snippet_id": "counter", "options": opts_a})
    r2 = client.post("/api/v1/generate", json={"snippet_id": "counter", "options": opts_b})
    assert r1.status_code == 200
    assert r2.status_code == 200
    assert r1.json()["config_hash"] == r2.json()["config_hash"]


# ---------------------------------------------------------------------------
# Hardening — oversized request body
# ---------------------------------------------------------------------------


def test_oversized_request_body_rejected() -> None:
    huge_prefix = "x" * (70 * 1024)  # > 64 KB
    payload = {"snippet_id": "counter", "options": {"naming": {"prefix": huge_prefix}}}
    body_bytes = json.dumps(payload).encode("utf-8")
    assert len(body_bytes) > 64 * 1024

    response = client.post(
        "/api/v1/generate",
        content=body_bytes,
        headers={"content-type": "application/json"},
    )
    assert response.status_code == 413
