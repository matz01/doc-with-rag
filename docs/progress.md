# Progress

_Last updated: 2026-10-23 · Updated with `/wrap-up` at the end of each working session._

## Status

| Phase | Status |
|---|---|
| 1. Foundations | ✅ Done (small follow-ups below) |
| 2. Fictional data | ✅ Done |
| 3. Ingestion | 🔄 In progress (schema migrations done, pipeline next) |
| 4–10 | ⏳ To do |

## Done

### Phase 3 — Ingestion (in progress)

- Migration runner in plain SQL (`app/db/migrations.py`): numbered `.sql` files in
  `app/db/migrations/`, applied in order and tracked in `schema_migrations`, each in its
  own transaction with its tracking row. Not wired into app startup yet.
- `0001_corpus_schema.sql`: `documents` (with `allowed_groups`, `status`, `supersedes`,
  `content_hash`) and `chunks` (document reference, ordinal, 1024-dim `vector` pinned to
  bge-m3, HNSW cosine index). **Permissions live only on documents** — chunks carry
  no permission copy of their own; every chunk-returning query joins `documents` in the
  WHERE clause (see Decisions).
- Integration tests run against the dedicated `docrag_test` database (commit `bd7c76c`),
  with a guard on `reset_test_database`: it refuses any URL that is not a `*_test`
  database or that equals the app's `DATABASE_URL` (URL logic unit-tested):
  `tests/unit/test_database_reset_guard.py`, `tests/integration/_database.py`.

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
| Permissions stored only on `documents.allowed_groups`, chunk queries join documents in the WHERE clause | Single source of truth: a stale or diverging per-chunk copy could grant access and there would be no schema-level guarantee of consistency | One primary-key join per chunk query; chunks are always queried with their document |
| OpenAI-compatible API for all LLM providers, no LiteLLM | One less dependency, full control over retry and fallback | A non-compatible provider would need an adapter |
| psycopg 3 (sync) with explicit SQL in `app/db/` | The permission filter must be easy to read and review | No ORM conveniences; sync calls run in FastAPI's thread pool |
| Separate `/health` (liveness) and `/ready` (readiness) | Standard probe split: a database outage should not restart the API | Two endpoints to maintain |
| Readiness failures always return 503 | Orchestrators and load balancers treat 503 as "not ready yet" | Unexpected errors are hidden behind 503 and must be logged |
| Superseded policies kept in the corpus | Tests that the assistant prefers the current version | Retrieval must use `status` metadata |
| httpx2 instead of httpx for tests | Starlette’s TestClient tries it first | Newer than most models’ training data: agents may mistake it for a typo |

## Open follow-ups

- Integration tests duplicate the default database URL (also the `Settings` default in
  `app/config.py`): could reference `Settings.model_fields["database_url"].default` instead.
- `TEST_DATABASE_URL` precedence is read with raw `os.environ.get` in the integration helpers,
  not through pydantic-settings: acceptable for test helpers, revisit if it grows.
- The migration runner does not detect edited files (a `.sql` changed after being applied is
  silently skipped): track a checksum when the first need appears; also no advisory lock, so
  two concurrent starts could race on `schema_migrations`.
- Add a chunk write-path test with the pgvector adapter (write an embedding as adapted numpy
  data, not only as a `::vector` cast string) when the real embedder lands.
- Verify the Dockerfile copies `app/db/migrations/` (apply_migrations reads the `.sql` files
  at runtime) at the first container build that runs it.

## Design notes for later phases

- **Phase 4 — question routing with tool calling.** Semantic search answers questions about document
  *content*, but fails on questions about document *metadata* (e.g. "list the documents whose title
  starts with A": embeddings compare meaning, not letters). The LLM therefore receives two tools and
  chooses one per question:
  - `search_documents(query)` — semantic search on chunks;
  - `list_documents(title_prefix, department, status, ...)` — SQL filter on document metadata.

  Both tools read the user from the request session, never from a tool argument the LLM can set, and
  apply the permission filter inside the SQL query.
- **Phase 6 — `metadata` evaluation category.** Add questions such as "List the documents whose title
  starts with A" for at least two users with different groups. The expected list is computed from
  `data/manifest.yaml` (title prefix + `allowed_groups`), so the check is deterministic and also
  verifies permissions.

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

Continue **phase 3 — Ingestion TDD cycles** (test DB and schema migrations are done):
parse MD, PDF and DOCX from `data/manifest.yaml`, chunk with a deterministic splitter,
embed locally with bge-m3 (fake embedder in unit tests), and insert documents and chunks
(permission filter reads `documents.allowed_groups` via join).
