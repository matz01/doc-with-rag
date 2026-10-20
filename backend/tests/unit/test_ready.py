import logging

from fastapi.testclient import TestClient

from app import main
from app.errors import DatabaseCheckError
from app.main import app

client = TestClient(app)


def _passing_database_checker() -> dict[str, str]:
    """Fake the database checker the /ready route will depend on: both checks pass."""
    return {"database": "ok", "pgvector": "ok"}


def _failing_database_checker() -> dict[str, str]:
    """Fake the database checker the /ready route depends on: the database is down."""
    return {"database": "unavailable", "pgvector": "ok"}


def _pgvector_missing_checker() -> dict[str, str]:
    """Fake the database checker the /ready route depends on: the database is up
    but pgvector is missing.

    A failed check is signalled with a status value other than "ok" plus an extra
    "error" entry carrying a human-readable message; the route passes entries through verbatim.
    """
    return {
        "database": "ok",
        "pgvector": "missing",
        "error": "pgvector extension is not installed on the database",
    }


def _raising_database_checker() -> dict[str, str]:
    """Fake the database checker the /ready route depends on: it cannot produce any result.

    When the checker cannot produce a status dict at all (connection failed,
    unexpected error), it raises the domain exception DatabaseCheckError instead
    of returning entries. The message mimics what psycopg would report, because
    driver messages can include host and user names and must never reach the body.
    """
    raise DatabaseCheckError("connection failed: host localhost, user docrag")


def test_ready_returns_503_when_database_is_unreachable():
    app.dependency_overrides[main.check_database_ready] = _failing_database_checker
    try:
        response = client.get("/ready")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 503
    assert response.json() == {
        "status": "unavailable",
        "database": "unavailable",
        "pgvector": "ok",
    }


def test_ready_returns_503_with_error_when_pgvector_is_missing():
    app.dependency_overrides[main.check_database_ready] = _pgvector_missing_checker
    try:
        response = client.get("/ready")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 503
    assert response.json() == {
        "status": "unavailable",
        "database": "ok",
        "pgvector": "missing",
        "error": "pgvector extension is not installed on the database",
    }


def test_ready_returns_503_with_generic_error_when_the_check_raises(caplog):
    app.dependency_overrides[main.check_database_ready] = _raising_database_checker
    try:
        with caplog.at_level(logging.ERROR):
            response = client.get("/ready")
    finally:
        app.dependency_overrides.clear()

    body = response.json()
    assert response.status_code == 503
    # The body speaks for the app, not for the driver: psycopg messages can include
    # host and user names, so the exception text must never be echoed back.
    assert body == {"status": "unavailable", "error": "database is not available"}
    assert "host localhost, user docrag" not in response.text
    # Operators still need the cause: the detail goes to the log, not to the client.
    assert "connection failed: host localhost, user docrag" in caplog.text


def test_ready_returns_200_with_all_checks_ok():
    app.dependency_overrides[main.check_database_ready] = _passing_database_checker
    try:
        response = client.get("/ready")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok", "pgvector": "ok"}
