---
description: End of session — update docs/progress.md and the phase status in AGENTS.md
agent: build
---

Update the project progress log at the end of this working session.

Recent commits:
!`git log --oneline -20`

Uncommitted changes:
!`git status --short`

1. Read `docs/progress.md` and the "Phased plan" section of `AGENTS.md`.
2. Find what changed since the "Last updated" date in `docs/progress.md`, using the commits above,
   `git diff` and this session's conversation. Read the changed files when needed.
3. Update `docs/progress.md`:
   - set "Last updated" to today's date;
   - update the status table;
   - add completed work under "Done", in the phase it belongs to;
   - add new technical decisions to "Decisions", with why and trade-off;
   - remove follow-ups that are resolved, add new ones (bugs, shortcuts, TODOs found in the code);
   - rewrite "Next step" as one concrete action someone could start tomorrow.
4. If a phase started or finished, update its marker (✅ / 🔄 / ⏳) in the "Phased plan" of `AGENTS.md`.
5. Only write facts you can verify in the code, the commits or this session. Keep it short: this is
   a log for the next session, not a report.
6. Show me the changes and propose a commit message (`docs: update progress log`). Do not commit.
