"""SemiCraft HTTP API entry point.

This is a minimal placeholder exposing only a health check endpoint.
WP-06 replaces this with the full API implementing the frozen contract in
IMPLEMENTATION_PLAN.md section 4.
"""

from fastapi import FastAPI

app = FastAPI(title="SemiCraft API")


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}
