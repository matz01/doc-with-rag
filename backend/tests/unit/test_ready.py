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
    of returning entries; the app must map it to a 503, never a 500.
    """
    raise DatabaseCheckError("unexpected failure while checking the database")


def test_ready_returns_503_when_database_is_unreachable():
    checker = getattr(main, "check_database_ready", _failing_database_checker)
    app.dependency_overrides[checker] = _failing_database_checker
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
    checker = getattr(main, "check_database_ready", _pgvector_missing_checker)
    app.dependency_overrides[checker] = _pgvector_missing_checker
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


def test_ready_returns_503_when_the_check_raises_database_check_error():
    checker = getattr(main, "check_database_ready", _raising_database_checker)
    app.dependency_overrides[checker] = _raising_database_checker
    try:
        response = client.get("/ready")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 503
    assert response.json() == {
        "status": "unavailable",
        "error": "unexpected failure while checking the database",
    }


def test_ready_returns_200_with_all_checks_ok():
    # The /ready route and its dependency do not exist yet. Key the override on the
    # real dependency (app.main.check_database_ready) so the fake is injected as
    # soon as the route lands; until then the fake doubles as a placeholder key
    # and the request fails with the expected 404 instead of an import error.
    checker = getattr(main, "check_database_ready", _passing_database_checker)
    app.dependency_overrides[checker] = _passing_database_checker
    try:
        response = client.get("/ready")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok", "pgvector": "ok"}
