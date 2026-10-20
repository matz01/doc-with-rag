---
name: tdd
description: Test-driven development rules for this repository (red → green → refactor), test conventions for pytest and Vitest, and how to handle LLMs, embeddings and the database in tests. Load before writing or changing any production code, including bug fixes.
---

# Test-driven development

All production code in this repository is written test-first.

## The cycle

1. **Test list.** Before coding, write a short list of the behaviours the change needs,
   from the simplest to the most complex. Include edge cases and failure cases.
2. **Red.** Write **one** test for **one** behaviour. Run it. It must fail **for the expected
   reason**: an assertion failure, not a syntax or import error. If the code under test does
   not exist yet, create a minimal stub (for example a function that raises
   `NotImplementedError`) so the test fails on behaviour.
3. **Green.** Write the **minimal** production code that makes the test pass. Run the test
   file, then the whole unit suite.
4. **Refactor.** With all tests green, improve names, structure and duplication in both code
   and tests. Run the suite again after every refactoring step.
5. Repeat with the next item of the test list.

## Hard rules

- **Never change a test to make it pass.** If a test looks wrong, stop and explain why.
  Only the red phase writes or changes tests.
- Never write production code that no failing test requires.
- **Bug fixes start with a failing test that reproduces the bug.**
- Never skip, delete or mark tests as expected failures to get a green suite.
- Keep each cycle small: if the green step needs more than about 30 lines of code, the test
  is too big — split it.

## Where tests go

| Kind | Location | Runs against |
|---|---|---|
| Backend unit | `backend/tests/unit/` | Fakes only: no database, no network, no model download |
| Backend integration | `backend/tests/integration/` | The Postgres + pgvector container from docker-compose |
| Frontend | next to the code, `*.test.ts` / `*.test.tsx` | jsdom + MSW |

Test files are named `test_<module>.py` and mirror the module they test
(`app/config.py` → `tests/unit/test_config.py`).

## Writing good tests

- Structure: **Arrange – Act – Assert**, separated by a blank line.
- Names describe behaviour:
  - pytest: `test_<expected_behaviour>_when_<condition>` (for example
    `test_missing_api_key_for_selected_provider_fails`)
  - Vitest: `it("shows the sources of an answer when the user clicks a citation")`
- One behaviour per test. Several assertions are fine if they check the same behaviour.
- Tests must be deterministic: no real time, randomness or network without control.
- Test public behaviour, not private helpers or implementation details.
- Keep the developer's environment out of tests: use `monkeypatch` for environment variables
  and `Settings(_env_file=None, ...)` for settings.
- HTTP endpoints are tested with FastAPI's `TestClient`; dependencies are replaced with
  `app.dependency_overrides`.

## Dependencies in tests

| Dependency | Unit tests | Integration tests |
|---|---|---|
| LLM providers | Always a fake provider implementing the provider interface. Never a real API | Fake provider, except explicit provider smoke tests marked `llm` |
| Embedding model | Fake embedder returning fixed small vectors | Real `bge-m3`, marked `slow` |
| Postgres + pgvector | Not used: test the logic with in-memory fakes | Real database from docker-compose |
| Files in `data/` | Small fixtures in `backend/tests/fixtures/` | The real corpus |

**Permission filtering is always tested against the real database.** Every query that returns
chunks needs an integration test proving that a user cannot retrieve chunks from documents
outside their groups.

Integration tests require the database to be running (`docker compose up -d db`). They read
`DATABASE_URL` from settings and must clean up the data they create.

Custom markers (`integration`, `slow`, `llm`) must be registered under `markers` in
`[tool.pytest.ini_options]` in `backend/pyproject.toml` before they are first used.

## Frontend

- Vitest + React Testing Library. Query elements the way a user finds them
  (`getByRole`, `getByLabelText`), not by class names or test ids unless unavoidable.
- Mock the backend API with MSW, never by mocking `fetch` directly.
- Use `userEvent` for interactions.

## Commands

All commands from the repository root:

| Purpose | Command |
|---|---|
| Backend unit tests | `uv run --directory backend pytest tests/unit` |
| Backend integration tests | `uv run --directory backend pytest tests/integration` |
| One test file | `uv run --directory backend pytest tests/unit/test_config.py` |
| Exclude slow and real-LLM tests | `uv run --directory backend pytest -m "not slow and not llm"` |
| Lint and format check | `uv run --directory backend ruff check .` and `uv run --directory backend ruff format --check .` |
| Frontend tests | `npm test --prefix frontend` |

## Definition of done

- Every item of the test list has a passing test.
- The whole unit suite passes; integration tests pass for the touched area.
- Ruff check and format check pass.
- Commits are small: `test:` and `feat:`/`fix:` commits may be combined per cycle.
