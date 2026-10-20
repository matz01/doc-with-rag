# Evaluation set

`questions.yaml` contains 60 questions designed together with the corpus in `data/`, so every
question has a known answer, a known user and known source documents.

## Categories

| Category | Count | What it tests |
|---|---|---|
| single-doc | 23 | The answer is in one document |
| multi-doc | 9 | The answer requires combining two documents |
| conflicting-versions | 9 | A 2025 and a 2026 version disagree; the current one must win (C08 asks about the past on purpose) |
| permission-denied | 11 | The answer exists only in documents the user cannot access |
| permission-partial | 2 | Part of the answer is accessible, part is restricted |
| unanswerable | 6 | Nobody can answer from the corpus |

## Suggested scoring

**Retrieval (deterministic, no LLM needed)**

- *Source recall*: for `source_match: any`, at least one expected source is in the retrieved
  chunks; for `source_match: all`, every expected source is.
- *Permission leaks*: no chunk from `forbidden_sources` is ever retrieved. Any leak is a
  critical failure, regardless of the answer.

**Answer (deterministic)**

- Every string in `key_facts` appears in the answer (case-insensitive). Some key facts are
  computed values (for example a commission or a date derived from a notice period), so they
  also test reasoning over the retrieved text.
- No string in `must_not_contain` appears in the answer.

**Answer (LLM-as-judge, optional)**

Compare the answer with `expected_answer` for correctness and faithfulness to the sources.

For `permission-denied` and `unanswerable`, the expected behaviour is the same: say that the
information is not available, without revealing whether a restricted document exists.
