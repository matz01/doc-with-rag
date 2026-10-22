from urllib.parse import urlsplit, urlunsplit

import pytest
from fastapi.testclient import TestClient

from app.config import Settings, get_settings
from app.main import app

from ._database import _test_database_url

client = TestClient(app)

DETERMINISTICALLY_WRONG_PASSWORD = "definitely-wrong-password"


def _url_with_wrong_password(url: str) -> str:
    """Same user and host as `url`, but a wrong password.

    psycopg fails authentication deterministically that way: no network flakiness,
    no timeout. The username is kept; when the URL carries no user info, the compose
    default username is used so there is always a user password to miss.
    """
    parts = urlsplit(url)
    userinfo, _, hostname = parts.netloc.rpartition("@")  # hosts never contain "@"
    if userinfo:
        user, _, _ = userinfo.partition(":")
    else:
        user = "docrag"
    wrong_netloc = f"{user}:{DETERMINISTICALLY_WRONG_PASSWORD}@{hostname}"
    return urlunsplit(parts._replace(netloc=wrong_netloc))


def _settings_with_running_database() -> Settings:
    """Settings pointing at the dedicated test database (`_test_database_url`).
    `mistral_api_key` is a dummy value so the settings validator passes without the
    developer's API keys (same convention as tests/unit/test_config.py).
    """
    return Settings(_env_file=None, database_url=_test_database_url(), mistral_api_key="test-key")


def _settings_with_unreachable_database() -> Settings:
    """Settings pointing at the test database but with a wrong password."""
    return Settings(
        _env_file=None,
        database_url=_url_with_wrong_password(_test_database_url()),
        mistral_api_key="test-key",
    )


@pytest.mark.integration
def test_ready_returns_503_when_the_database_is_unreachable():
    """The real checker must run against the database URL from settings: when the
    database cannot be reached, /ready fails with 503, the body stays generic and the
    driver detail (URL with host and user) is kept out of the response."""
    settings = _settings_with_unreachable_database()
    app.dependency_overrides[get_settings] = lambda: settings
    try:
        response = client.get("/ready")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 503

    body = response.json()
    assert body["status"] == "unavailable"
    assert body["error"]
    assert DETERMINISTICALLY_WRONG_PASSWORD not in response.text


@pytest.mark.integration
def test_ready_returns_200_against_the_running_database():
    """The real checker must run against the running container: when the database is
    reachable and pgvector is installed, /ready reports every check as ok."""
    settings = _settings_with_running_database()
    app.dependency_overrides[get_settings] = lambda: settings
    try:
        response = client.get("/ready")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok", "pgvector": "ok"}
