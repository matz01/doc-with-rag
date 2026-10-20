---
name: python-backend
description: Structure and Python conventions for the FastAPI backend of this repository (uv, Pydantic v2, settings in app/config.py, dependency injection, database access, provider layer, errors, logging). Load before writing or reviewing backend code.
---

# Backend conventions

The backend is a standalone uv project in `backend/` (its own `pyproject.toml` and `uv.lock`).
Run every backend command from the repository root with `uv run --directory backend ...`,
or from inside `backend/`.

## Structure

Existing modules are marked ✓; the others are added in later phases, following this layout.

```
backend/
  app/
    main.py          ✓ FastAPI app, lifespan, routes registration
    config.py        ✓ settings (pydantic-settings) and LLM provider selection
    api/             HTTP routes and request/response models, when main.py grows
    errors.py        domain exceptions
    providers/       LLM provider interface + OpenAI-compatible client + fake
    embeddings/      embedder interface + bge-m3 implementation + fake
    ingestion/       parsing (md, pdf, docx), chunking, indexing
    retrieval/       permission-aware search
    db/              connection, SQL queries, migrations
  tests/
    unit/            ✓ fast tests, no database, no network
    integration/     tests against the docker-compose Postgres
    fixtures/        small test documents
```

Dependencies point inwards: routes → domain modules (`retrieval`, `ingestion`) → interfaces
(`providers`, `embeddings`, `db`). Domain code never imports FastAPI.

## Python style

- Python 3.12. Type hints on every function signature. Use `X | None`, not `Optional[X]`.
- Prefer plain functions and small classes. Use `typing.Protocol` for interfaces (provider,
  embedder), so tests can pass fakes without inheritance.
- Use `dataclass(frozen=True)` for internal value objects and **Pydantic v2 models** for data
  crossing a boundary (HTTP, LLM structured output, config files such as `data/manifest.yaml`).
- Use `pathlib.Path`, f-strings, and comprehensions where they stay readable.
- When a Python idiom is not obvious (decorators, context managers, generators, `async`
  details), add a one-line comment explaining why it is used. `app/config.py` is the reference
  for tone and density of comments.

## Configuration

- All settings live in `app/config.py` (`Settings`, based on `pydantic-settings`), read from
  environment variables and the repo-root `.env`.
- Access settings only through `get_settings()` (cached, usable as a FastAPI dependency).
- Invalid configuration must fail at startup: validate in `Settings` with Pydantic validators.
- Secrets are `SecretStr`. Never read `.env` directly, never log secrets.
- Every new variable goes in `.env.example`, with a comment, and in the `Settings` class.
- In tests, build settings with `Settings(_env_file=None, ...)` and clear relevant environment
  variables with `monkeypatch`, as in `tests/unit/test_config.py`.

## Dependency injection

- Settings, providers, embedder and database connections are injected with FastAPI `Depends`.
- Tests replace them with `app.dependency_overrides`, never by patching module globals.

## Database

- Postgres 17 + pgvector from docker-compose. Access it with **psycopg 3** (to be added with
  `uv add --directory backend "psycopg[binary]"`).
- SQL lives only in `app/db/`, written explicitly so the permission filter is easy to review.
- The permission filter is part of the `WHERE` clause of every query that returns chunks.
  There is no function that returns chunks without a user context.
- Schema changes are plain SQL migration files in `app/db/migrations/`, applied in order.
  `infra/postgres/init.sql` only enables the `vector` extension.

## LLM provider layer

- No LiteLLM: Mistral, Groq and Ollama all expose an OpenAI-compatible API (see the technical
  decision in the README). A provider is `base_url` + `model` + optional `api_key`, built from
  `Settings.primary_provider` and `Settings.fallback_provider`.
- One interface (`providers/base.py`) with a method returning a validated Pydantic model.
- Retry HTTP 429 and 5xx with exponential backoff, then switch to the fallback provider.
- Every call records provider, model, latency and token usage for observability.

## Errors and logging

- Domain errors are custom exceptions in `app/errors.py`, mapped to HTTP responses in the routes.
- Use the standard `logging` module with structured `extra` fields. No `print`.

## Tooling

All commands from the repository root:

| Purpose | Command |
|---|---|
| Add a dependency | `uv add --directory backend <package>` (`--dev` for tools) — never `pip install` |
| Lint | `uv run --directory backend ruff check .` |
| Format | `uv run --directory backend ruff format .` |
| Run the API locally | `uv run --directory backend uvicorn app.main:app --reload` |
| Run the whole stack | `docker compose up -d --build` |
