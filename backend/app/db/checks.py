"""Database checks used by the /ready endpoint.

All SQL lives in `app/db/`, so permission filters and health queries stay easy to
review. Any failure is translated into `DatabaseCheckError` (from `app.errors`),
matching the checker contract: either a status dict, or a domain error the app maps
to HTTP 503.
"""

import psycopg

from app.errors import DatabaseCheckError

# A readiness probe must not hang on a half-open connection; 3s is generous for a LAN.
CONNECT_TIMEOUT_SECONDS = 3


def database_ready_checks(database_url: str) -> dict[str, str]:
    """Check the connection and that pgvector is installed.

    Returns one entry per check, plus an `error` message when a check fails
    without being an error of the checker itself (e.g. extension missing).
    """
    try:
        # `with` releases the connection even when the cursor raises; psycopg is a
        # sync driver, FastAPI serves the route from its thread pool.
        with psycopg.connect(database_url, connect_timeout=CONNECT_TIMEOUT_SECONDS) as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1 FROM pg_extension WHERE extname = 'vector'")
                if cursor.fetchone() is None:
                    return {
                        "database": "ok",
                        "pgvector": "missing",
                        "error": "the pgvector extension is not installed on the database",
                    }
    except Exception as exc:
        # The bottom of readiness: the app maps DatabaseCheckError to 503, never 500.
        message = str(exc).strip() or "could not connect to the database"
        raise DatabaseCheckError(message) from exc
    return {"database": "ok", "pgvector": "ok"}
