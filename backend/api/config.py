"""Runtime configuration for the HTTP API — the only environment surface.

Until v0.4.0 the backend read **no** environment variables at all: a grep for
``environ``/``getenv`` across ``backend/`` returned one hit, and it was a
comment in ``tb/scripts.py`` about deliberately *not* probing the environment.
That is right for the generator — determinism is a ground rule, and a generator
whose output depends on the environment cannot be byte-reproducible. It is
wrong for the *server*, which had its allowed CORS origin hardcoded to
``http://localhost:3000``. Anyone self-hosting the frontend on any other host
or port got silently browser-blocked API calls and no diagnostic.

So the rule this module encodes: **the server may be configured; the generator
may not.** Nothing here reaches ``semicraft_core``.

Configuration is read once at import. Nothing is secret, nothing has a
security-sensitive default, and an unset variable always yields the previous
hardcoded behaviour — upgrading changes nothing for an existing local setup.

``SEMICRAFT_CORS_ORIGINS``
    Comma-separated list of browser origins allowed to call the API.
    Default ``http://localhost:3000`` (the frontend's ``npm run dev`` origin).
    The single value ``*`` allows any origin — reasonable for a self-hosted
    instance on a private network, and **safe here only because the API sends
    no credentials**: there are no cookies, no sessions, no auth headers and
    nothing user-specific to steal. See :data:`ALLOW_CREDENTIALS`.
"""

from __future__ import annotations

import os

__all__ = ["ALLOW_CREDENTIALS", "DEFAULT_CORS_ORIGINS", "cors_origins"]

DEFAULT_CORS_ORIGINS = ("http://localhost:3000",)

#: The API has no authentication, no cookies and no sessions, so a credentialed
#: cross-origin request has nothing to carry. Declaring ``True`` (as this app
#: did through v0.4.0) bought nothing and cost something real: the CORS spec
#: forbids ``Access-Control-Allow-Origin: *`` alongside credentials, so it made
#: the wildcard unusable for self-hosters — and "credentials plus a permissive
#: origin list" is the classic CORS misconfiguration. Flip this only if the API
#: ever grows auth, and re-read the wildcard note above when you do.
ALLOW_CREDENTIALS = False


def cors_origins(env: dict[str, str] | None = None) -> list[str]:
    """Browser origins allowed to call the API.

    Reads ``SEMICRAFT_CORS_ORIGINS`` (comma-separated). Blank entries are
    dropped and surrounding whitespace stripped, so ``"a, b,"`` is two origins.
    An unset *or empty* variable falls back to :data:`DEFAULT_CORS_ORIGINS`
    rather than to "no origins at all": a typo that empties the list should
    leave a working local setup, not a server that rejects every browser with
    an error the browser reports as a network failure.

    *env* is injectable so tests need not mutate the process environment.
    """
    source = os.environ if env is None else env
    raw = source.get("SEMICRAFT_CORS_ORIGINS", "")
    origins = [item.strip() for item in raw.split(",") if item.strip()]
    return origins or list(DEFAULT_CORS_ORIGINS)
