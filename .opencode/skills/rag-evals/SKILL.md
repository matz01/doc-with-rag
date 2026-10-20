---
name: rag-evals
description: How to run the evaluation suite in evals/, how scoring works and how to interpret and report results (retrieval recall, permission leaks, key facts, forbidden content, provider comparison). Load when running, changing or reporting on evaluations.
slash: false
---

# RAG evaluations

The evaluation set is `evals/questions.yaml`; the scoring rules are in `evals/README.md`.
Read both before changing the runner or the questions.

## Principles

- **Permission leaks are critical failures.** A single retrieved chunk from a
  `forbidden_sources` document fails the run, whatever the answer says.
- Retrieval metrics and deterministic answer checks need no LLM. Run them first and often.
- LLM-as-judge is optional and always cached.
- LLM responses are cached by (provider, model, prompt hash), so re-runs cost nothing.
  Bypass the cache only when explicitly asked.
- Compare runs only on the same corpus and question set version.

## Metrics to report

| Metric | Definition |
|---|---|
| Source recall | Share of questions whose expected sources were retrieved (`any` / `all` per question) |
| Permission leaks | Number of retrieved chunks from forbidden sources (must be 0) |
| Key-fact accuracy | Share of answers containing every `key_facts` string (case-insensitive) |
| Forbidden content | Answers containing a `must_not_contain` string |
| Abstention | For `permission-denied` and `unanswerable`: share of answers that correctly say the information is not available |
| Latency | p50 and p95 per question |
| Cost | Estimated cost per question and per run, per provider |

Report results per category (single-doc, multi-doc, conflicting-versions, permission-denied,
permission-partial, unanswerable) as a Markdown table, then list every failed question with
its id, the expected answer and the actual answer.

## Changing the question set

- Never change a question or its expected answer to make the system pass.
- A new question must be verifiable against the corpus: its expected sources must be
  readable by its user, and its forbidden sources must not be.
