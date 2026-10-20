---
description: Build a feature test-first (red → green → refactor)
agent: build
---

Load the `tdd` skill (and `python-backend` for backend work).

Feature: $ARGUMENTS

1. **Test list.** Propose the list of behaviours to test, from simplest to most complex,
   including edge cases and failure cases. **Stop and wait for my confirmation.**
2. For each behaviour, in order:
   - **Red:** ask `@test-writer` to write one failing test for that behaviour.
     If it reports a required stub, add only that stub and confirm the test now fails on behaviour.
   - **Green:** write the minimal production code to make it pass. Do not edit test files.
     Run the test file, then the unit suite.
   - **Refactor:** clean up with all tests green and run the suite again.
   - Report in two lines: behaviour covered, tests passing.
3. If a test cannot pass without changing it, stop and explain the problem instead of
   changing the test.
4. When the list is complete, run the full suite and ruff, then ask `@reviewer` to review the changes.
