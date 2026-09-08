"""CORS/config surface (launch blocker B4).

Through v0.4.0 the allowed origin was hardcoded to ``http://localhost:3000``,
so the product ran under exactly one origin and failed under every other one
the way CORS failures always fail: silently in the browser, with the server
logging a normal 200. This pins the configurable replacement, and pins the two
properties that keep it from becoming a footgun — an unset variable behaves
exactly as the hardcoded version did, and credentials stay off so the wildcard
is legal for self-hosters.
"""

from __future__ import annotations

from api.config import ALLOW_CREDENTIALS, DEFAULT_CORS_ORIGINS, cors_origins


def test_unset_matches_the_hardcoded_default_this_replaced() -> None:
    assert cors_origins({}) == ["http://localhost:3000"]
    assert list(DEFAULT_CORS_ORIGINS) == ["http://localhost:3000"]


def test_a_single_origin_is_read() -> None:
    assert cors_origins({"SEMICRAFT_CORS_ORIGINS": "https://rtl.example.com"}) == [
        "https://rtl.example.com"
    ]


def test_multiple_origins_are_split_and_stripped() -> None:
    env = {"SEMICRAFT_CORS_ORIGINS": " https://a.example.com , https://b.example.com "}
    assert cors_origins(env) == ["https://a.example.com", "https://b.example.com"]


def test_trailing_and_repeated_separators_do_not_produce_empty_origins() -> None:
    """An empty-string origin matches nothing and is pure confusion in a config."""
    env = {"SEMICRAFT_CORS_ORIGINS": "https://a.example.com,,https://b.example.com,"}
    assert cors_origins(env) == ["https://a.example.com", "https://b.example.com"]


def test_an_empty_value_falls_back_rather_than_locking_everyone_out() -> None:
    """A typo that empties the variable must not silently reject every browser."""
    for value in ("", "   ", ",", " , "):
        assert cors_origins({"SEMICRAFT_CORS_ORIGINS": value}) == list(DEFAULT_CORS_ORIGINS)


def test_wildcard_is_passed_through() -> None:
    assert cors_origins({"SEMICRAFT_CORS_ORIGINS": "*"}) == ["*"]


def test_credentials_are_off_so_the_wildcard_is_actually_usable() -> None:
    """The CORS spec forbids ``Allow-Origin: *`` together with credentials.

    The app declared ``allow_credentials=True`` through v0.4.0 while sending no
    cookies, no sessions and no auth headers from anywhere in the frontend — it
    bought nothing and made the wildcard unusable. If auth is ever added this
    test should fail and be re-argued, not deleted.
    """
    assert ALLOW_CREDENTIALS is False


def test_the_app_actually_uses_the_configured_origins() -> None:
    """Guards the wiring, not just the helper: a config nobody reads is worse than none."""
    from api.main import app

    cors = [m for m in app.user_middleware if "CORS" in str(m)]
    assert cors, "the CORS middleware is no longer installed on the app"
    options = cors[0].kwargs
    assert options["allow_origins"] == cors_origins()
    assert options["allow_credentials"] is ALLOW_CREDENTIALS
