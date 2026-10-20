# Progress

_Last updated: 2026-10-20 · Updated with `/wrap-up` at the end of each working session._

## Status

| Phase | Status |
|---|---|
| 1. Foundations | ✅ Done (small follow-ups below) |
| 2. Fictional data | ✅ Done |
| 3. Ingestion | ⏳ Next |
| 4–10 | ⏳ To do |

## Done

### Phase 1 — Foundations

- docker-compose with **Postgres 17 + pgvector** (`pgvector/pgvector:pg17`), healthcheck, and the
  `vector` extension enabled at first start (`infra/postgres/init.sql`).
- Backend as a standalone uv project in `backend/`, Dockerfile with dependencies in a separate layer.
- `app/config.py`: settings with `pydantic-settings`; LLM provider (Mistral, Groq, Ollama) and
  fallback chosen by configuration, validated at startup; API keys as `SecretStr`.
- `GET /health`: liveness probe, does not touch the database.
- `GET /ready`: readiness probe. Checks the database connection and that pgvector is installed
  (`app/db/checks.py`, psycopg 3). Any failure returns **503**, never 500 (`DatabaseCheckError`).
- Tests split into `tests/unit/` (fakes, no database) and `tests/integration/` (real container),
  with `pythonpath = ["."]` and the `integration`, `slow`, `llm` markers registered in `pyproject.toml`.

### Phase 2 — Fictional data

- 42 documents for the fictional company Quillmoor Software (Markdown, PDF, DOCX), `manifest.yaml`
  with per-document `allowed_groups`, 8 users in `users.yaml`.
- 60 evaluation questions in `evals/questions.yaml` across six categories (single-doc, multi-doc,
  conflicting versions, permission-denied, permission-partial, unanswerable).

### Tooling

- OpenCode v2 configuration: skills `tdd`, `python-backend`, `rag-evals`; subagents `@test-writer`
  (red phase, can edit tests only) and `@reviewer` (read-only); commands `/tdd`, `/review`, `/wrap-up`.

## Decisions

| Decision | Why | Trade-off |
|---|---|---|
| OpenAI-compatible API for all LLM providers, no LiteLLM | One less dependency, full control over retry and fallback | A non-compatible provider would need an adapter |
| psycopg 3 (sync) with explicit SQL in `app/db/` | The permission filter must be easy to read and review | No ORM conveniences; sync calls run in FastAPI's thread pool |
| Separate `/health` (liveness) and `/ready` (readiness) | Standard probe split: a database outage should not restart the API | Two endpoints to maintain |
| Readiness failures always return 503 | Orchestrators and load balancers treat 503 as "not ready yet" | Unexpected errors are hidden behind 503 and must be logged |
| Superseded policies kept in the corpus | Tests that the assistant prefers the current version | Retrieval must use `status` metadata |
| httpx2 instead of httpx for tests | Starlette’s TestClient tries it first | Newer than most models’ training data: agents may mistake it for a typo |

## Open follow-ups

- **`/ready` leaks driver details.** The 503 body returns the psycopg error text, which can include
  host and user names. Return a generic message and log the details instead.
- **Integration tests hard-code the database URL** (`docrag:docrag@localhost:5432`). They fail if
  `.env` uses different credentials. Read a `TEST_DATABASE_URL` (or the settings) instead.
- **Leftover red-phase scaffolding in `tests/unit/test_ready.py`:** `getattr(main, "check_database_ready", ...)`
  is no longer needed now that the dependency exists; override `check_database_ready` directly.
- Consider `addopts = "--strict-markers"` so a misspelled marker fails the run.
- README still says "Phase 1"; update the status line and mention the dataset.

## Next step

Fix the open follow-ups (one `/tdd` cycle for the `/ready` error message), then plan **phase 3 —
Ingestion**: parse MD, PDF and DOCX from `data/manifest.yaml`, chunk, embed locally with bge-m3,
and store chunks with their `allowed_groups` in pgvector.
