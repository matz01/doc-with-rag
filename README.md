# doc-with-rag

A **permission-aware enterprise document assistant**. A fictional company keeps its documents
split by department (HR, Sales, Finance, Engineering). Each user asks questions in natural language
and gets answers with cited sources, built **only from the documents they are allowed to see**.

> Status: phases 1 (foundations) and 2 (fictional dataset) are done. Database, minimal API and
> evaluation questions are in place; next is Phase 3 (ingestion: parsing, chunking, embeddings).

## Key idea

Access control happens **inside the database search query**: chunks a user cannot see are never
retrieved, so they can never reach the LLM. No post-generation filtering.

## Planned stack

| Layer | Choice |
|---|---|
| Backend | Python 3.12, FastAPI, Pydantic v2, `uv` |
| Storage | Postgres + pgvector (documents, chunks, embeddings, permissions) |
| Embeddings | Local, sentence-transformers `BAAI/bge-m3` |
| LLM | Provider-agnostic layer: Mistral (primary), Groq (fallback), Ollama (optional, local) |
| Frontend | React + TypeScript + Vite |
| Quality | pytest, ruff, Vitest + React Testing Library |
| Observability | Langfuse (latency, tokens, cost per question) |
| Runtime | Docker + docker-compose |

## Quick start

```bash
cp .env.example .env      # then set real values
docker compose up -d --build   # API on localhost:8000, Postgres 17 + pgvector on localhost:5432
```

- API docs: http://localhost:8000/docs
- Health check: http://localhost:8000/health

Backend development without Docker:

```bash
cd backend
uv sync
uv run uvicorn app.main:app --reload   # dev server
uv run pytest                          # tests
uv run ruff check . && uv run ruff format --check .
```

## Repository layout

```
backend/   Python API: ingestion, retrieval, Q&A
frontend/  React UI
data/      Fictional company documents, users and permissions
evals/     Evaluation suite and results
infra/     Infrastructure config (Postgres init scripts)
```

## Roadmap

1. Foundations — repo structure, docker-compose, minimal FastAPI app, provider config
2. Fictional data — company, 30–50 documents, users and groups
3. Ingestion — parsing, chunking, local embeddings, pgvector
4. Q&A — permission-filtered search, cited and validated answers
5. Frontend — chat, clickable citations, user switcher
6. Evaluation — retrieval metrics, answer grading, provider comparison
7. Observability and reliability — tracing, costs, retry/fallback
8. MCP server — permission-aware document search
9. Structured extraction — contracts/invoices to validated JSON
10. Polish — architecture diagram, demo, deployment

## Technical decisions

**LLM provider config — plain OpenAI-compatible settings, no LiteLLM (for now).**
Mistral, Groq and Ollama all expose an OpenAI-compatible API, so a provider is just
`base_url` + `model` + optional `api_key`, chosen with `LLM_PROVIDER` / `LLM_FALLBACK_PROVIDER`
(see `backend/app/config.py`). Trade-off: one less dependency and full control over
retry/fallback, but adding a non-compatible provider later would need an adapter.
Invalid configuration (unknown provider, missing key) stops the API at startup.

## Data

All documents are fictional and generated for this project. No real or personal data.
The corpus: **42 documents** for the fictional company *Quillmoor Software*
(Markdown, PDF, DOCX) with per-document permissions in `data/manifest.yaml`,
**8 users** in `data/users.yaml`, and **60 evaluation questions** in
`evals/questions.yaml` (single-doc, multi-doc, conflicting versions,
permission-denied, permission-partial, unanswerable).

## License

[MIT](LICENSE)
