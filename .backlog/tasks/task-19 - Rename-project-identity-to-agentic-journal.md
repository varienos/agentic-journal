---
id: TASK-19
title: Rename project identity to agentic-journal
status: Done
assignee:
  - codex
created_date: '2026-06-07 06:09'
updated_date: '2026-06-07 06:17'
labels:
  - rename
  - project-identity
dependencies: []
priority: medium
ordinal: 19000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Rename the repository and project identity from agent-journal to agentic-journal across package metadata, user-facing commands, MCP naming, generated snippets, runtime storage naming, documentation, scripts, and tests. Keep the implementation focused on the rename and avoid unrelated behavioral changes.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Project metadata and repository URLs use agentic-journal instead of agent-journal.
- [x] #2 User-facing CLI, MCP command, generated snippets, installer text, and hook/script references use agentic-journal naming consistently.
- [x] #3 Default local storage naming is updated from .agent-journal/agent-journal.db to the agentic-journal equivalent while preserving the existing environment override behavior.
- [x] #4 Documentation, tests, smoke scripts, and lock/build metadata reflect the new project and command names.
- [x] #5 Relevant automated tests or verification scripts pass after the rename.
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
Approved implementation plan:
1. Update package and repository identity in pyproject.toml, uv.lock, README.md, CHANGELOG.md, and docs so the project slug is agentic-journal, the displayed product name is Agentic Journal, and GitHub URLs point to varienos/agentic-journal.
2. Rename user-facing command strings from agent-journal to agentic-journal and agent-journal-mcp to agentic-journal-mcp in CLI parser metadata, installer templates, MCP snippets, shell hooks, scripts, and tests.
3. Rename the Python import package from agent_journal to agentic_journal so source imports, package build paths, release tooling, tests, and script snippets match the new project identity.
4. Update new generated environment variables and defaults from AGENT_JOURNAL_* / ~/.agent-journal / agent-journal.db to AGENTIC_JOURNAL_* / ~/.agentic-journal / agentic-journal.db, while preserving reads of legacy AGENT_JOURNAL_* variables as compatibility fallbacks where existing installs may still supply them.
5. Update generated marker names/backups such as post-commit.agent-journal.bak and instruction wrapper markers to agentic-journal equivalents, plus diagnostics that detect installed configuration.
6. Run targeted red/green tests around the rename first, then the repo verification command that is practical in this workspace, and update TASK-19 acceptance criteria/final summary based on evidence.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Continuation message accepted as approval to proceed with the recorded plan. Scope refined to include the Python import package and new AGENTIC_JOURNAL_* environment variable names while preserving legacy AGENT_JOURNAL_* fallback reads for existing installations.

Verified after local repo rename to /Users/varienos/Landing/Repo/agentic-journal. Git remote now points to https://github.com/varienos/agentic-journal.git. Old hyphen/snake/title names no longer appear in tracked project files outside Backlog task history; legacy AGENT_JOURNAL_* environment variables remain only as compatibility fallback reads.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Renamed the project identity from agent-journal to agentic-journal across package metadata, GitHub URLs, README/docs, scripts, tests, CLI/MCP commands, generated installer snippets, hook backup names, runtime storage defaults, and the Python import package (agentic_journal). Updated generated env vars/defaults to AGENTIC_JOURNAL_*, ~/.agentic-journal, and agentic-journal.db while preserving legacy AGENT_JOURNAL_* fallback reads for existing installs. Renamed the local repository directory to /Users/varienos/Landing/Repo/agentic-journal and updated origin to https://github.com/varienos/agentic-journal.git. Verification: targeted rename tests passed, uv run pytest -q passed with 136 tests, scripts/verify.sh passed, and scripts/package-smoke.sh passed after rebuilding the moved virtualenv.
<!-- SECTION:FINAL_SUMMARY:END -->
