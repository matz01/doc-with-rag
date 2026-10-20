import pytest
from fastapi.testclient import TestClient

from app.config import Settings, get_settings
from app.main import app

client = TestClient(app)


def _settings_with_running_database() -> Settings:
    """Settings pointing at the running docker-compose container.

    The URL is explicit so the test never reads the developer's .env mid-run;
    `mistral_api_key` is a dummy value so the settings validator passes without it
    (same convention as tests/unit/test_config.py).
    """
    return Settings(
        _env_file=None,
        database_url="postgresql://docrag:docrag@localhost:5432/docrag",
        mistral_api_key="test-key",
    )


def _settings_with_unreachable_database() -> Settings:
    """Settings pointing at the running container but with a wrong password.

    psycopg fails to authenticate deterministically: no network flakiness, no timeout.
    `mistral_api_key` is a dummy value so the settings validator passes without the
    developer's .env (same convention as tests/unit/test_config.py).
    """
    return Settings(
        _env_file=None,
        database_url="postgresql://docrag:definitely-wrong-password@localhost:5432/docrag",
        mistral_api_key="test-key",
    )


@pytest.mark.integration
def test_ready_returns_503_when_the_database_is_unreachable():
    """The real checker must run against the database URL from settings: when the
    database cannot be reached, /ready fails with 503 and a human-readable reason."""
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
