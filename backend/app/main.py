from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import get_settings


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
