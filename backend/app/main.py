import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.config import Settings, get_settings
from app.db.checks import database_ready_checks
from app.errors import DatabaseCheckError

HTTP_503 = status.HTTP_503_SERVICE_UNAVAILABLE

logger = logging.getLogger(__name__)

# Ready means "usable or not", nothing more: driver messages (psycopg included) can
# carry host and user names, so the body stays generic and the cause goes to the log.
READY_FAILURE_MESSAGE = "database is not available"


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load settings eagerly so a bad .env stops the server at boot, not on the first request.
    get_settings()
    yield


app = FastAPI(
    title="doc-with-rag",
    description="Permission-aware enterprise document assistant.",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health")
def health() -> dict[str, str]:
    """Liveness probe: the process is up. It does not check the database."""
    return {"status": "ok"}


def check_database_ready(settings: Settings = Depends(get_settings)) -> dict[str, str]:  # noqa: B008 - FastAPI's DI idiom
    """Report the state of the database dependencies, one entry per check.

    The checks live in `app/db`; `Depends` lets unit tests inject a fake instead.
    """
    return database_ready_checks(settings.database_url)


@app.exception_handler(DatabaseCheckError)
def database_check_error(request: Request, exc: DatabaseCheckError) -> JSONResponse:
    """The checker could not produce any result: readiness fails with 503, never 500."""
    # The detail belongs in the log only; clients see the fixed generic message.
    logger.error("database readiness check failed: %s", exc)
    return JSONResponse(
        {"status": "unavailable", "error": READY_FAILURE_MESSAGE}, status_code=HTTP_503
    )


@app.get("/ready")
def ready(
    checks: dict[str, str] = Depends(check_database_ready),  # noqa: B008 - FastAPI's DI idiom
) -> JSONResponse:
    """Readiness probe: the database is reachable and pgvector is installed."""
    if all(value == "ok" for value in checks.values()):
        return JSONResponse({"status": "ok", **checks})
    return JSONResponse(
        {"status": "unavailable", **checks}, status_code=status.HTTP_503_SERVICE_UNAVAILABLE
    )
