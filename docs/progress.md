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

- **Separate test database before phase 3.** Integration tests currently use the same database as
  the app (`DATABASE_URL`). That is fine while they only read (`/ready`), but from phase 3 they will
  insert and delete documents. Create a `docrag_test` database in the same container (in
  `infra/postgres/init.sql`, with the `vector` extension), point `TEST_DATABASE_URL` at it, and
  reset its tables at the start of each integration run.
- Integration tests duplicate the default database URL (also the `Settings` default in
  `app/config.py`): could reference `Settings.model_fields["database_url"].default` instead.
- `TEST_DATABASE_URL` precedence is read with raw `os.environ.get` in the integration helpers,
  not through pydantic-settings: acceptable for test helpers, revisit if it grows.

## Session log

2026-10-20 (follow-up session, before phase 3):

- `/ready` no longer leaks driver details: the 503 body returns the fixed generic message
  "database is not available"; the checker error text is logged instead (unit test pins both
  the hiding and the logging; the integration test pins it end-to-end against a real wrong password).
- Integration tests no longer hard-code the database URL: `TEST_DATABASE_URL` when set,
  otherwise the same `database_url` the app reads from `.env`. Documented in `.env.example`.
- Red-phase scaffolding removed from `tests/unit/test_ready.py` (direct `check_database_ready`
  override keys instead of `getattr` fallbacks).
- `addopts = "--strict-markers"` in `backend/pyproject.toml`.
- README status line updated; Data section now describes the dataset.

## Next step

Plan **phase 3 — Ingestion**, starting with the separate test database: parse MD, PDF and DOCX
from `data/manifest.yaml`, chunk, embed locally with bge-m3, and store chunks with their
`allowed_groups` in pgvector.
