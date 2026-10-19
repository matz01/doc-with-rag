# backend

Python 3.12 + FastAPI service: ingestion, permission-filtered retrieval, LLM answers with citations.
Dependencies managed with `uv`.

```bash
uv sync                                # create .venv and install dependencies
uv run uvicorn app.main:app --reload   # http://localhost:8000/docs
uv run pytest
uv run ruff check . && uv run ruff format --check .
```
