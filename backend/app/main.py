from fastapi import FastAPI

app = FastAPI(
    title="doc-with-rag",
    description="Permission-aware enterprise document assistant.",
    version="0.1.0",
)


@app.get("/health")
def health() -> dict[str, str]:
    """Liveness probe: the process is up. It does not check the database."""
    return {"status": "ok"}
