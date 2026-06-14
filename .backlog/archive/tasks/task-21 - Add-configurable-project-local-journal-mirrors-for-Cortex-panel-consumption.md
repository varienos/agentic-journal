---
id: TASK-21
title: Add configurable project-local journal mirrors for Cortex panel consumption
status: To Do
assignee: []
created_date: '2026-06-12 21:23'
labels:
  - feature
  - journal
  - cortex
  - mirror
dependencies: []
modified_files:
  - src/agentic_journal/config.py
  - src/agentic_journal/storage.py
  - src/agentic_journal/events.py
  - src/agentic_journal/web.py
  - src/agentic_journal/cli.py
  - src/agentic_journal/report.py
  - tests/test_config.py
  - tests/test_storage.py
  - tests/test_web.py
  - tests/test_cli.py
  - tests/test_report.py
  - docs/event-schema.md
  - docs/operations.md
  - README.md
priority: medium
ordinal: 21000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Users need to view Agentic Journal entries by project, especially for `/Users/varienos/Landing/Repo/cortex`, and prefer each project to have its own mirror journal that can be mounted into containers and read by project panels. Agentic Journal should keep its global journal if useful, but add a project-level configuration that mirrors matching events into a project-local journal directory. Cortex Deck should then be able to consume the project-local mirror without needing direct access to the host-level `~/.agentic-journal` store. The mirror target should be configurable per project so projects can choose location, enabled/disabled state, and project path matching behavior.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 A project can opt into a local Agentic Journal mirror through project-level configuration rather than hardcoded paths.
- [ ] #2 When an event is written, Agentic Journal mirrors it into the configured project-local journal if the event `repo` or `cwd` matches the configured project path exactly or is beneath it.
- [ ] #3 The mirror preserves the existing event shape and enough derived/indexed data for daily project views, while global journal writes continue to work unchanged.
- [ ] #4 A mirror for `/Users/varienos/Landing/Repo/cortex` can include both `Agentbase` events with no git repo and `Codebase/Cortex` events with git repo metadata.
- [ ] #5 The project-local mirror location is suitable for container mounting or direct panel reads, and documentation explains the local/dev and container usage model.
- [ ] #6 A panel consumer can read the mirrored project journal and get the same daily summary/session/latest-events payload shape expected by the dashboard.
- [ ] #7 Tests cover config discovery, enabled/disabled mirror behavior, exact-path and child-path matching, non-matching events, duplicate/idempotent writes, and preservation of global journal behavior.
<!-- AC:END -->
