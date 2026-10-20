---
name: python-backend
description: Structure and Python conventions for the FastAPI backend of this repository (uv, Pydantic v2, settings, dependency injection, database access, provider layer, errors, logging). Load before writing or reviewing backend code.
---

# Backend conventions

## Structure

```
backend/
  app/
    main.py          # FastAPI app factory, router registration
    api/             # HTTP layer only: routes, request/response models
    core/            # settings, logging, errors
    providers/       # LLM provider interface + implementations (Mistral, Groq, Ollama, fake)
    embeddings/      # embedder interface + bge-m3 implementation + fake
    ingestion/       # parsing (md, pdf, docx), chunking, indexing
    retrieval/       # permission-aware search
    db/              # connection, SQL queries, migrations
  tests/
    unit/
    integration/
    fixtures/
```

Dependencies point inwards: `api` → domain modules (`retrieval`, `ingestion`) → interfaces
(`providers`, `embeddings`, `db`). Domain code never imports FastAPI.

## Python style

- Python 3.12. Type hints on every function signature. Prefer `X | None` over `Optional[X]`.
- Prefer plain functions and small classes. Use `Protocol` for interfaces (provider, embedder),
  so tests can pass fakes without inheritance.
- Use `dataclass(frozen=True)` for internal value objects and **Pydantic v2 models** for data
  crossing a boundary (HTTP, LLM structured output, config files).
- Use `pathlib.Path`, f-strings, comprehensions where they stay readable.
- When a Python idiom is not obvious (decorators, context managers, generators, `async`
  details), add a one-line comment explaining why it is used.

## Configuration

- All settings come from environment variables via `pydantic-settings` (`core/settings.py`).
- Never read `.env` directly and never log secrets. Every new variable goes in `.env.example`.

## Dependency injection

- Providers, embedder and database connections are created once and injected with FastAPI
  `Depends`. Tests override them with `app.dependency_overrides`.

## Database

- Postgres + pgvector, accessed with **psycopg 3**. SQL lives only in `app/db/`, written
  explicitly so the permission filter is easy to review.
- The permission filter is part of the `WHERE` clause of every query that returns chunks.
  There is no function that returns chunks without a user context.
- Schema changes are plain SQL migration files in `app/db/migrations/`, applied in order.

## LLM provider layer

- One interface (`providers/base.py`) with a method returning a validated Pydantic model.
- Implementations use the OpenAI-compatible API (or LiteLLM). The active provider and the
  fallback come from settings.
- Retry HTTP 429 and 5xx with exponential backoff, then switch to the fallback provider.
- Every call records provider, model, latency and token usage for observability.

## Errors and logging

- Domain errors are custom exceptions in `core/errors.py`, mapped to HTTP responses in `api/`.
- Use the standard `logging` module with structured `extra` fields. No `print`.

## Tooling

| Purpose | Command |
|---|---|
| Add a dependency | `uv add <package>` (`uv add --dev <package>` for tools) — never `pip install` |
| Lint / format | `uv run ruff check --fix` and `uv run ruff format` |
| Run the API | `uv run fastapi dev backend/app/main.py` |
