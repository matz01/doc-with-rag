# CLAUDE.md

## Project goal

A **permission-aware enterprise document assistant**:
a fictional company has documents split by department (HR, Sales, Finance, Engineering);
each user asks questions in natural language and gets answers with cited sources,
built **only from the documents they are allowed to see**.

Scope: RAG, embeddings, semantic search, access control, structured outputs, tool calling,
quality evaluation, latency and cost monitoring, Docker, deployment.
Code should be readable and technical decisions documented with their trade-offs.

When writing Python, prefer idiomatic but simple code and briefly explain non-obvious choices.

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

- **Language:** everything in English — code, comments, commits, README, documentation and the fictional company documents.
- **Secrets:** API keys only in `.env` (never committed). Keep `.env.example` up to date, with no real values.
- **Data:** only fictional company documents generated for this project. No real or personal data.
  (The Mistral Experiment plan may use requests for model training: acceptable only because the data is fictional.)
- **Permissions:** the permission filter must be applied **inside the database search query**, before any chunk
  is passed to the LLM — never by filtering after generation.
- **Free-tier limits:** handle HTTP 429 with retry and exponential backoff, then automatic switch to the fallback provider.
- **Caching:** cache LLM responses during evaluation runs, so re-running the suite does not consume requests.
- Small, descriptive commits. No features beyond the current phase.

## Phased plan

1. **Foundations:** repo structure, docker-compose with Postgres + pgvector, minimal FastAPI app, provider config, `.env.example`
2. **Fictional data:** an invented company, 30–50 documents across 4 departments, users and groups with different permissions
3. **Ingestion:** parsing, chunking, local embeddings, storage in pgvector with metadata and permissions
4. **Q&A:** question endpoint → permission-filtered search → LLM answer with citations (structured, validated output)
5. **Frontend:** chat, clickable citations, user switcher
6. **Evaluation:** 30+ questions with expected answers and expected source documents; deterministic retrieval metrics
   plus answer grading; provider comparison; results table in the README
7. **Observability and reliability:** tracing, costs, retry/fallback
8. **MCP server** exposing document search (permission-aware)
9. **Extra structured outputs:** field extraction from contracts/invoices into validated JSON
10. **Polish:** README with architecture diagram, demo GIF, technical decisions and known limitations; deploy the demo
    with cached example questions and a per-visitor request limit

## Working with agents

- Work one phase at a time. Before writing code for a phase, propose the plan and wait for confirmation.
- Never read, print or modify `.env`.
- Project subagents live in `./.opencode/agents`:
  - `@reviewer` — read-only code review before each commit
  - `@test-writer` — writes and runs tests for existing code
  - `@code-writer` — writes code to make tests pass
