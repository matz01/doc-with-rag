# Progress

_Last updated: 2026-10-23 · Updated with `/wrap-up` at the end of each working session._

## Status

| Phase | Status |
|---|---|
| 1. Foundations | ✅ Done (small follow-ups below) |
| 2. Fictional data | ✅ Done |
| 3. Ingestion | 🔄 In progress (manifest, parsing, chunking, embedder, persistence done; pipeline+CLI next) |
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
- TDD cycle: manifest loader (`app/ingestion/manifest.py`, commit `92b874b`) — validated
  Pydantic models, unique ids, paths that must stay inside the corpus root, and
  `superseded_by` derived from the inverse `supersedes` links (the YAML field is ignored).
  Verified against the real manifest: 42 documents parse, derived links match the YAML's,
  all referenced files exist.
- TDD cycle: parsing (commit `0433747`) — `parse_document` turns md (headings open sections,
  fenced code verbatim), pdf (one block per page) and docx (Heading styles) into
  `ParsedBlock(text, section)`; mini fixtures in `tests/fixtures/`. All 42 corpus files parse.
- TDD cycle: chunking (commit `9edacdd`) — `chunk_blocks` merges consecutive blocks of the
  same section with `\n\n` up to 1400 chars, cuts larger blocks into overlapping character
  windows (200 overlap), never mixes sections, emits no empty chunks (schema CHECK). Real
  corpus → 198 chunks, max 1118 chars.
- TDD cycle: embedder (commits `105375f`, `34301cf`) — `Embedder` Protocol;
  `FakeEmbedder` (md5 hash → fixed dims, offline, deterministic) for tests;
  `BgeM3Embedder` (sentence-transformers, local, rejects != 1024 dims at construction);
  `Settings.embedding_model = "BAAI/bge-m3"` + `.env.example`. Slow integration test pins
  1024-dim output and stability; first run downloads the model (~2–3 GB, HF cache).
- TDD cycle: corpus persistence (commit `da91a0a`) — `app/db/corpus.py`:
  `upsert_document` (ON CONFLICT update), `replace_chunks` (delete-all-then-insert per
  document, idempotent re-ingestion, embeddings as plain floats cast `::vector`,
  executemany on the cursor, NOT on the connection in psycopg 3), `document_hashes` for the
  unchanged-skip; integration tests pin all fields, updates, replacement, FK cascade.
- Cycle 6 STARTED (uncommitted): `app/ingestion/pipeline.py` stub only —
  `content_hash_of` and `ingest_corpus` raise `NotImplementedError`, tests not written yet.

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
| `superseded_by` derived in code from the inverse `supersedes` links | One declared relation; no risk of the YAML's two fields disagreeing | The YAML's own `superseded_by` field is silently ignored |
| Chunking is a pure deterministic function of the parsed blocks (sections kept, `content_hash` skip depends on it) | Re-ingesting an unchanged document must not re-embed: cost and stability of the test suite | Cosmetic rules (word-boundary cuts) are traded for exact window overlap |
| bge-m3 dimension checked at embedder construction (1024) | A wrong model would corrupt stored vectors silently | Construction fails loudly instead of adapting |
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
- Unit tests resolve fixture paths from `__file__` (pytest cwd is `backend/`):
  `uv run --directory backend pytest <path>` runs from the backend directory, never the repo root.
- The migration runner does not detect edited files (a `.sql` changed after being applied is
  silently skipped): track a checksum when the first need appears; also no advisory lock, so
  two concurrent starts could race on `schema_migrations`.
- Chunk write-path test with the pgvector adapter: resolved differently — `replace_chunks`
  writes plain float lists via a `::vector` cast (pinned in integration tests), the read
  path uses `register_vector`. Revisit with the adapter only if a COPY-based bulk insert
  is ever needed for performance.
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

2026-10-23 (phase 3 ingestion, cycles 1–5 committed):

- Phase 3 groundwork committed: plain-SQL migration runner + corpus schema (`ce3a192`),
  `reset_test_database` guard with unit-tested URL logic (`b87bc35`; review-driven), and the
  reviewed decision to keep permissions only on `documents` (chunk join in the search query).
- Five TDD cycles landed as one commit each: manifest loader (`92b874b`), parsing MD/PDF/DOCX
  (`0433747`), chunking (`9edacdd`), embedder Protocol + fake + bge-m3 with
  `Settings.embedding_model` (`105375f`, `34301cf` — the slow test downloaded bge-m3 to the
  HF cache), corpus persistence (`da91a0a`).
- Red phases via `@test-writer`; two pre-green test corrections were needed (fixture path
  resolved from `__file__` because pytest cwd is `backend/`; embedding roundtrip read
  requires `register_vector` while the write path stays adapter-free) — assertions kept.
- Sanity checks against the real corpus pass: manifest parses fully coherent (42 docs,
  derived links match), all 42 files parse to 251 blocks → 198 chunks (max 1118 chars).
- Cycle 6 (pipeline + CLI) started red: `app/ingestion/pipeline.py` stub is in the
  working tree UNCOMMITTED, tests not yet written.

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

Cycle 6 — ingestion pipeline (red phase first, tests are missing): integration tests with
`FakeEmbedder` for `ingest_corpus` (ingests a tmp corpus end to end; re-running an unchanged
corpus skips everything via `content_hash`, zero embed calls; a changed document re-embeds
alone; the real corpus ingest with the fake embedder pins report counts), then implement the
core green, add the `python -m app.ingestion` CLI glue (`Settings` → `BgeM3Embedder`), and a
`slow` end-to-end test on the real corpus. (The permission-filter join belongs to phase 4
retrieval, not to ingestion.)
