---
id: TASK-21
title: Add project-scoped journal filtering for Cortex panel consumption
status: To Do
assignee: []
created_date: '2026-06-12 21:21'
labels:
  - feature
  - journal
  - cortex
dependencies: []
modified_files:
  - src/agentic_journal/storage.py
  - src/agentic_journal/web.py
  - src/agentic_journal/cli.py
  - src/agentic_journal/report.py
  - tests/test_storage.py
  - tests/test_web.py
  - tests/test_cli.py
  - tests/test_report.py
  - docs/event-schema.md
  - README.md
priority: medium
ordinal: 21000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Users need to view Agentic Journal entries by project, especially for `/Users/varienos/Landing/Repo/cortex`, so Cortex Deck can show only the relevant agent work. Current events already carry `cwd` and `repo`; the missing behavior is a stable project-path filter and consumer contract. The first target is local/dev usage against the central `~/.agentic-journal` store; production/container mounting or sync can be documented as an operational follow-up rather than duplicating journal data into each project.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 A date-scoped journal read can be filtered by a project path and includes events whose `repo` or `cwd` exactly matches that path or is beneath that path.
- [ ] #2 Filtering works for Cortex-style split roots, so a filter for `/Users/varienos/Landing/Repo/cortex` includes both `Agentbase` events with no git repo and `Codebase/Cortex` events with git repo metadata.
- [ ] #3 The existing unfiltered daily report/dashboard/status behavior remains unchanged when no project filter is supplied.
- [ ] #4 A JSON/API payload suitable for a panel consumer exposes the same summary, sessions, provider coverage, and latest-events shape after project filtering.
- [ ] #5 CLI or documentation shows how Cortex Deck should request the Cortex-only journal view in local/dev, including the project path and any runtime path assumptions.
- [ ] #6 Tests cover exact-path, child-path, non-matching-path, and unfiltered behavior.
<!-- AC:END -->
