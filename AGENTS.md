# AGENTS.md

## Project goal

A **permission-aware enterprise document assistant**:
a fictional company has documents split by department (HR, Sales, Finance, Engineering);
each user asks questions in natural language and gets answers with cited sources,
built **only from the documents they are allowed to see**.

Scope: RAG, embeddings, semantic search, access control, structured outputs, tool calling,
quality evaluation, latency and cost monitoring, Docker, deployment.
Code should be readable and technical decisions documented with their trade-offs.

## Repository layout

| Path | Content |
|---|---|
| `backend/` | Python API (FastAPI). Tests in `backend/tests/unit/` and `backend/tests/integration/` |
| `frontend/` | React + TypeScript app. Tests next to the code as `*.test.ts` / `*.test.tsx` |
| `data/` | Fictional corpus: `documents/`, `manifest.yaml` (permissions), `users.yaml` |
| `evals/` | Evaluation questions and runner |

## Stack

- **Backend:** Python 3.12, FastAPI, Pydantic v2, dependency management with `uv`
- **Database:** Postgres + pgvector (documents, chunks, embeddings and permissions in the same DB)
- **Embeddings:** run locally with sentence-transformers, model `BAAI/bge-m3`.
  No external API for embeddings.
- **LLM:** all calls go through a single provider-agnostic layer (OpenAI-compatible format or LiteLLM).
  The provider is switched via configuration, never in code.
  - Primary: **Mistral** (free Experiment plan)
  - Fallback: **Groq** (free tier)
  - Optional, local: **Ollama**
- **Frontend:** React + TypeScript + Vite, polished UI (clickable citations, user switcher to demonstrate permissions)
- **Quality:** pytest, ruff; frontend tests with Vitest + React Testing Library
- **Observability:** Langfuse (or equivalent) for latency, tokens and estimated cost per question
- **Containers:** Docker + docker-compose, local startup with a single command

## Rules

- **Test-driven development:** all production code is written test-first. Load the `tdd` skill
  before changing any production code. Never modify a test to make it pass.
- **Python conventions:** load the `python-backend` skill before writing backend code.
- **Language:** everything in English — code, comments, commits, README, documentation and data.
- **Secrets:** API keys only in `.env` (never committed, never read by agents). Keep `.env.example`
  up to date, with no real values.
- **Data:** only the fictional corpus in `data/`. No real or personal data.
  (The Mistral Experiment plan may use requests for model training: acceptable only because the data is fictional.)
- **Permissions:** the permission filter must be applied **inside the database search query**, before any chunk
  is passed to the LLM — never by filtering after generation.
- **Free-tier limits:** handle HTTP 429 with retry and exponential backoff, then automatic switch to the fallback provider.
- **Caching:** cache LLM responses during evaluation runs, so re-running the suite does not consume requests.
- Work one phase at a time. Before writing code for a phase, propose a plan and wait for confirmation.
- Small, descriptive commits (Conventional Commits: `feat:`, `fix:`, `test:`, `refactor:`, `docs:`, `chore:`).
  No features beyond the current phase.

## Agents, skills and commands

| Type | Name | Purpose |
|---|---|---|
| Skill | `tdd` | Red → green → refactor rules and testing conventions |
| Skill | `python-backend` | Backend structure and Python conventions |
| Skill | `rag-evals` | How to run and interpret the evaluation suite |
| Subagent | `@test-writer` | Writes failing tests (red phase). Can edit test files only |
| Subagent | `@reviewer` | Read-only review of uncommitted changes |
| Command | `/tdd <feature>` | Guided TDD cycle for one feature |
| Command | `/review` | Review before committing |

In the green phase, the Build agent must not edit test files; `opencode.json` asks for
confirmation whenever it tries.

## Phased plan

1. **Foundations:** repo structure, docker-compose with Postgres + pgvector, minimal FastAPI app, provider config, `.env.example`
2. **Fictional data:** done — see `data/README.md` and `evals/README.md`
3. **Ingestion:** parsing (MD, PDF, DOCX), chunking, local embeddings, storage in pgvector with metadata and permissions from `data/manifest.yaml`
4. **Q&A:** question endpoint → permission-filtered search → LLM answer with citations (structured, validated output)
5. **Frontend:** chat, clickable citations, user switcher
6. **Evaluation:** runner for `evals/questions.yaml`; deterministic retrieval and answer checks, optional LLM-as-judge;
   provider comparison; results table in the README
7. **Observability and reliability:** tracing, costs, retry/fallback
8. **MCP server** exposing document search (permission-aware)
9. **Extra structured outputs:** field extraction from contracts/invoices into validated JSON
10. **Polish:** README with architecture diagram, demo GIF, technical decisions and known limitations; deploy the demo
    with cached example questions and a per-visitor request limit
