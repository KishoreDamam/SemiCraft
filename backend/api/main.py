"""SemiCraft HTTP API (WP-06, IMPLEMENTATION_PLAN.md §4 — frozen contract;
Phase-2 Appendix A.1 — API v2 multi-file contract, P2-05a).

Implements:

- ``GET  /healthz``           — liveness check (kept from the WP-00 placeholder).
- ``GET  /api/v1/snippets``   — catalog built from the snippet registry
  (``kind == "snippet"`` only — backcompat, byte-identical to pre-Phase-2).
- ``POST /api/v1/generate``  — validate options, generate code, lint, respond.
- ``GET  /api/v2/catalog``          — full catalog (snippets + modules).
- ``POST /api/v2/generate``         — multi-file generation (Appendix A.1).
- ``POST /api/v2/generate/zip``     — same body, zip download.

Error mapping (§4, unchanged in v2):

- unknown ``snippet_id``/``item_id``  -> :class:`UnknownSnippetError` -> 404.
- invalid ``options``     -> ``pydantic.ValidationError`` -> HTTP 422, in
  FastAPI's standard ``{"detail": [...]}`` envelope with ``loc`` prefixed by
  ``["body", "options"]`` so the frontend's ``fieldErrorsFrom()`` (lib/api.ts)
  can find the offending field.
- generator bug producing invalid IR -> :class:`IRValidationError` -> HTTP 500
  with a generic message; the real error is logged server-side only.

Lint (WP-04) is imported lazily inside the request path because it is being
built in parallel — if the module or the ``verilator`` binary is unavailable,
the endpoint still responds, with ``{"status": "unavailable", "messages": []}``.
"""

from __future__ import annotations

import io
import logging
import zipfile

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, ValidationError
from semicraft_core.generate import generate as core_generate
from semicraft_core.generate import generate_files as core_generate_files
from semicraft_core.ir.validate import IRValidationError
from semicraft_core.snippets import registry

logger = logging.getLogger("semicraft.api")

app = FastAPI(title="SemiCraft API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- hardening: reject oversized request bodies -----------------------------

MAX_BODY_BYTES = 64 * 1024


@app.middleware("http")
async def limit_body_size(request: Request, call_next):
    content_length = request.headers.get("content-length")
    if content_length is not None:
        try:
            if int(content_length) > MAX_BODY_BYTES:
                return JSONResponse(
                    status_code=413,
                    content={"detail": "Request body too large (max 64 KB)."},
                )
        except ValueError:
            pass  # malformed header; let downstream parsing handle/reject it

    # Content-Length may be absent (chunked transfer); guard on the actual
    # body size too so a streamed oversized body is still rejected.
    body = await request.body()
    if len(body) > MAX_BODY_BYTES:
        return JSONResponse(
            status_code=413,
            content={"detail": "Request body too large (max 64 KB)."},
        )

    # Starlette caches ``request.body()``, so downstream handlers that call
    # ``await request.json()`` / re-read the body still see the same bytes.
    return await call_next(request)


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


# --- GET /api/v1/snippets ----------------------------------------------------


@app.get("/api/v1/snippets")
def list_snippets() -> dict:
    snippets = []
    for snippet in registry.by_kind("snippet"):
        defaults_model = snippet.options_model()
        snippets.append(
            {
                "id": snippet.id,
                "name": snippet.name,
                "description": snippet.description,
                "json_schema": snippet.options_model.model_json_schema(),
                "defaults": defaults_model.model_dump(mode="json"),
            }
        )
    return {"snippets": snippets}


# --- GET /api/v2/catalog ------------------------------------------------------


@app.get("/api/v2/catalog")
def list_catalog() -> dict:
    """Full catalog (snippets + modules), Appendix A.1.

    Uses ``registry.all()`` (all kinds) rather than the v1 helper's
    snippet-only filter — the whole point of v2 is one catalog covering every
    registered ``kind``.
    """
    items = []
    for item in registry.all():
        defaults_model = item.options_model()
        items.append(
            {
                "id": item.id,
                "name": item.name,
                "description": item.description,
                "kind": registry.item_kind(item),
                "maturity": registry.item_maturity(item),
                "json_schema": item.options_model.model_json_schema(),
                "defaults": defaults_model.model_dump(mode="json"),
            }
        )
    return {"items": items}


# --- POST /api/v1/generate ---------------------------------------------------


class GenerateRequest(BaseModel):
    snippet_id: str
    options: dict = {}


def _lint_report(code: str, language: str) -> dict:
    """Run WP-04's lint if available; degrade gracefully otherwise.

    Imported lazily so the API works regardless of whether WP-04 has landed
    yet, and regardless of whether the ``verilator`` binary is installed.
    """
    try:
        from semicraft_core.lint.verilator import lint
    except Exception:  # noqa: BLE001 - module missing/broken -> unavailable
        return {"status": "unavailable", "messages": []}

    try:
        report = lint(code, language=language, top="counter")
    except Exception:  # noqa: BLE001 - any lint runtime failure -> unavailable
        logger.exception("lint execution failed")
        return {"status": "unavailable", "messages": []}

    if isinstance(report, dict):
        return report
    # LintReport-like object: adapt to the response shape.
    messages = [
        {
            "severity": m.severity,
            "code": m.code,
            "line": m.line,
            "text": m.text,
        }
        for m in getattr(report, "messages", [])
    ]
    return {"status": getattr(report, "status", "unavailable"), "messages": messages}


@app.post("/api/v1/generate")
def generate(body: GenerateRequest) -> dict:
    try:
        result = core_generate(body.snippet_id, body.options)
    except registry.UnknownSnippetError as exc:
        return JSONResponse(status_code=404, content={"detail": str(exc)})
    except ValidationError as exc:
        # Re-map to FastAPI's standard 422 envelope with loc prefixed by
        # ["body", "options"] so the frontend's fieldErrorsFrom() (which
        # expects exactly this shape) can locate the offending field.
        errors = []
        for err in exc.errors():
            loc = ["body", "options", *err["loc"]]
            errors.append({"loc": loc, "msg": err["msg"], "type": err["type"]})
        return JSONResponse(status_code=422, content={"detail": errors})
    except IRValidationError:
        logger.exception("IR validation failed for snippet_id=%s (generator bug)", body.snippet_id)
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal error generating code."},
        )

    language = body.options.get("language", "sv")

    # Lint always runs against the wrapped version, even for fragment
    # requests, so fragments are still checked (IMPLEMENTATION_PLAN §5 WP-04
    # task 3 / WP-06 lint field note).
    lint_options = dict(body.options)
    lint_options["include_wrapper"] = True
    try:
        lint_result = core_generate(body.snippet_id, lint_options)
        lint_code = lint_result.code
        lint_language = language
    except Exception:  # noqa: BLE001 - fall back to the primary result's code
        lint_code = result.code
        lint_language = language

    explanation = result.explanation
    explanation_payload = (
        explanation.model_dump(mode="json") if isinstance(explanation, BaseModel) else explanation
    )

    return {
        "code": result.code,
        "filename": result.filename,
        "language": language,
        "explanation": explanation_payload,
        "lint": _lint_report(lint_code, lint_language),
        "config_hash": result.config_hash,
    }


# --- POST /api/v2/generate & /api/v2/generate/zip ----------------------------


class GenerateV2Request(BaseModel):
    item_id: str
    options: dict = {}


def _generate_files_or_error(item_id: str, options: dict):
    """Shared body for the v2 generate/zip endpoints.

    Returns either a ``GenerateFilesResult`` or a :class:`JSONResponse` holding
    the appropriate error envelope (404 / 422 / 500) — callers check which by
    type before proceeding.
    """
    try:
        return core_generate_files(item_id, options)
    except registry.UnknownSnippetError as exc:
        return JSONResponse(status_code=404, content={"detail": str(exc)})
    except ValidationError as exc:
        errors = []
        for err in exc.errors():
            loc = ["body", "options", *err["loc"]]
            errors.append({"loc": loc, "msg": err["msg"], "type": err["type"]})
        return JSONResponse(status_code=422, content={"detail": errors})
    except IRValidationError:
        logger.exception("IR validation failed for item_id=%s (generator bug)", item_id)
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal error generating code."},
        )


def _v2_response_payload(result) -> dict:
    """Build the JSON body for ``POST /api/v2/generate`` (Appendix A.1)."""
    explanation = result.explanation
    explanation_payload = (
        explanation.model_dump(mode="json") if isinstance(explanation, BaseModel) else explanation
    )

    lint_reports = []
    for f in result.files:
        if f.kind != "rtl":
            continue
        lint_reports.append({"path": f.path, **_lint_report(f.text, result.language)})

    return {
        "files": [{"path": f.path, "kind": f.kind, "text": f.text} for f in result.files],
        "explanation": explanation_payload,
        "lint": lint_reports,
        "config_hash": result.config_hash,
        "language": result.language,
    }


@app.post("/api/v2/generate")
def generate_v2(body: GenerateV2Request) -> dict:
    result = _generate_files_or_error(body.item_id, body.options)
    if isinstance(result, JSONResponse):
        return result
    return _v2_response_payload(result)


# Fixed zip entry timestamp (1980-01-01, the DOS epoch and zipfile's floor) so
# that two identical requests produce byte-identical zip bytes (ground rule
# §1: determinism) — real wall-clock timestamps would break that guarantee.
_FIXED_ZIP_DATE_TIME = (1980, 1, 1, 0, 0, 0)


@app.post("/api/v2/generate/zip")
def generate_v2_zip(body: GenerateV2Request):
    result = _generate_files_or_error(body.item_id, body.options)
    if isinstance(result, JSONResponse):
        return result

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        for f in result.files:
            info = zipfile.ZipInfo(filename=f.path, date_time=_FIXED_ZIP_DATE_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            zf.writestr(info, f.text)

    zip_bytes = buffer.getvalue()
    filename = f"semicraft_{body.item_id}_{result.config_hash}.zip"
    return Response(
        content=zip_bytes,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# Ensure our own request-body model surfaces the same envelope shape as the
# rest of the app for any *other* validation errors FastAPI raises (e.g. a
# malformed top-level body that never reaches the try/except above).
@app.exception_handler(RequestValidationError)
async def _validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(status_code=422, content={"detail": exc.errors()})
