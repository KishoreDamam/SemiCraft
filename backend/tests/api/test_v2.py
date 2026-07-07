"""API v2 contract tests (Phase-2 Appendix A.1, P2-05a).

Mirrors the structure of ``test_generate.py`` for v1. Deliberately does NOT
hardcode the total catalog count for the same reason as v1: sibling module WPs
(P2-06..12) add more modules in parallel. We do assert a floor (11+: 10
snippets + edge-detector) and specific known ids/kinds.
"""

from __future__ import annotations

import io
import zipfile

from api.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


# ---------------------------------------------------------------------------
# GET /api/v2/catalog
# ---------------------------------------------------------------------------


def test_v2_catalog_has_required_shape_and_floor_count() -> None:
    response = client.get("/api/v2/catalog")
    assert response.status_code == 200
    body = response.json()
    assert "items" in body
    items = body["items"]
    assert len(items) >= 11  # 10 snippets + edge-detector, more modules land later

    ids = [i["id"] for i in items]
    assert len(ids) == len(set(ids)), "duplicate ids in v2 catalog"

    for entry in items:
        for key in ("id", "name", "description", "kind", "maturity", "json_schema", "defaults"):
            assert key in entry, f"item {entry.get('id')} missing key {key!r}"
        assert entry["kind"] in {"snippet", "module"}
        assert entry["maturity"] in {"stable", "beta"}


def test_v2_catalog_includes_edge_detector_as_module() -> None:
    response = client.get("/api/v2/catalog")
    items = response.json()["items"]
    edge = next(i for i in items if i["id"] == "edge-detector")
    assert edge["kind"] == "module"


def test_v2_catalog_includes_counter_as_snippet() -> None:
    response = client.get("/api/v2/catalog")
    items = response.json()["items"]
    counter = next(i for i in items if i["id"] == "counter")
    assert counter["kind"] == "snippet"


def test_v1_snippets_endpoint_unaffected_by_v2_catalog() -> None:
    """v1 /api/v1/snippets must still serve exactly the snippet-kind items,
    with no `kind`/`maturity` keys added to its entries (byte-compat)."""
    response = client.get("/api/v1/snippets")
    assert response.status_code == 200
    body = response.json()
    snippets = body["snippets"]

    # No modules leak into v1.
    ids = [s["id"] for s in snippets]
    assert "edge-detector" not in ids
    assert "counter" in ids

    for entry in snippets:
        assert "kind" not in entry
        assert "maturity" not in entry
        for key in ("id", "name", "description", "json_schema", "defaults"):
            assert key in entry


# ---------------------------------------------------------------------------
# POST /api/v2/generate — snippet (single rtl file)
# ---------------------------------------------------------------------------


def test_v2_generate_counter_single_rtl_file() -> None:
    response = client.post(
        "/api/v2/generate",
        json={"item_id": "counter", "options": {"language": "sv"}},
    )
    assert response.status_code == 200
    body = response.json()

    for key in ("files", "explanation", "lint", "config_hash", "language"):
        assert key in body

    assert body["language"] == "sv"
    files = body["files"]
    assert len(files) == 1
    assert files[0]["path"] == "counter.sv"
    assert files[0]["kind"] == "rtl"
    assert "module counter" in files[0]["text"]

    lint = body["lint"]
    assert isinstance(lint, list)
    assert len(lint) == 1
    assert lint[0]["path"] == "counter.sv"
    assert lint[0]["status"] in {"clean", "warnings", "unavailable"}
    assert isinstance(lint[0]["messages"], list)

    assert isinstance(body["config_hash"], str) and len(body["config_hash"]) == 12


# ---------------------------------------------------------------------------
# POST /api/v2/generate — module (rtl + doc files)
# ---------------------------------------------------------------------------


def test_v2_generate_edge_detector_rtl_and_doc_files() -> None:
    response = client.post(
        "/api/v2/generate",
        json={"item_id": "edge-detector", "options": {"language": "sv"}},
    )
    assert response.status_code == 200
    body = response.json()

    files = body["files"]
    kinds = [f["kind"] for f in files]
    assert "rtl" in kinds
    assert "doc" in kinds

    rtl_file = next(f for f in files if f["kind"] == "rtl")
    doc_file = next(f for f in files if f["kind"] == "doc")

    assert rtl_file["path"].endswith(".sv")
    assert "module edge_detector" in rtl_file["text"]

    assert doc_file["path"].endswith(".md")
    # port table present
    assert "| Port | Direction | Description |" in doc_file["text"]

    # lint only covers rtl files, not doc
    lint_paths = [entry["path"] for entry in body["lint"]]
    assert rtl_file["path"] in lint_paths
    assert doc_file["path"] not in lint_paths
    assert len(lint_paths) == 1


# ---------------------------------------------------------------------------
# POST /api/v2/generate — errors (mirror v1 mapping)
# ---------------------------------------------------------------------------


def test_v2_generate_invalid_options_422_shape() -> None:
    response = client.post(
        "/api/v2/generate",
        json={"item_id": "counter", "options": {"width": 0}},
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


def test_v2_generate_unknown_item_id_404() -> None:
    response = client.post(
        "/api/v2/generate",
        json={"item_id": "does-not-exist", "options": {}},
    )
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# POST /api/v2/generate/zip
# ---------------------------------------------------------------------------


def test_v2_generate_zip_is_valid_and_matches_files_order() -> None:
    response = client.post(
        "/api/v2/generate/zip",
        json={"item_id": "edge-detector", "options": {"language": "sv"}},
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/zip"

    content_disposition = response.headers["content-disposition"]
    assert "attachment" in content_disposition
    assert "semicraft_edge-detector_" in content_disposition
    assert ".zip" in content_disposition

    # Cross-check entry names/order against the JSON files[] for the same request.
    json_response = client.post(
        "/api/v2/generate",
        json={"item_id": "edge-detector", "options": {"language": "sv"}},
    )
    expected_paths = [f["path"] for f in json_response.json()["files"]]

    zf = zipfile.ZipFile(io.BytesIO(response.content))
    assert zf.namelist() == expected_paths

    for f in json_response.json()["files"]:
        assert zf.read(f["path"]).decode("utf-8") == f["text"]


def test_v2_generate_zip_bytes_are_deterministic() -> None:
    payload = {"item_id": "counter", "options": {"width": 16, "direction": "down"}}
    r1 = client.post("/api/v2/generate/zip", json=payload)
    r2 = client.post("/api/v2/generate/zip", json=payload)
    assert r1.status_code == 200
    assert r2.status_code == 200
    assert r1.content == r2.content


def test_v2_generate_zip_unknown_item_id_404() -> None:
    response = client.post(
        "/api/v2/generate/zip",
        json={"item_id": "does-not-exist", "options": {}},
    )
    assert response.status_code == 404


def test_v2_generate_zip_invalid_options_422() -> None:
    response = client.post(
        "/api/v2/generate/zip",
        json={"item_id": "counter", "options": {"width": 0}},
    )
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Hardening — oversized request body applies to v2 routes too
# ---------------------------------------------------------------------------


def test_v2_generate_oversized_request_body_rejected() -> None:
    huge_prefix = "x" * (70 * 1024)
    payload = {"item_id": "counter", "options": {"naming": {"prefix": huge_prefix}}}
    import json as _json

    body_bytes = _json.dumps(payload).encode("utf-8")
    assert len(body_bytes) > 64 * 1024

    response = client.post(
        "/api/v2/generate",
        content=body_bytes,
        headers={"content-type": "application/json"},
    )
    assert response.status_code == 413


# ---------------------------------------------------------------------------
# Regression guard: v1 /api/v1/generate response unchanged for counter
# ---------------------------------------------------------------------------


def test_v1_generate_response_shape_unchanged_for_counter() -> None:
    response = client.post(
        "/api/v1/generate",
        json={"snippet_id": "counter", "options": {"language": "sv"}},
    )
    assert response.status_code == 200
    body = response.json()

    # Same top-level keys as before v2 landed — no `files` key on v1.
    assert set(body.keys()) == {
        "code",
        "filename",
        "language",
        "explanation",
        "lint",
        "config_hash",
    }
    assert body["filename"] == "counter.sv"
    assert "module counter" in body["code"]
    assert isinstance(body["lint"], dict)  # v1 lint stays a single dict, not a list
