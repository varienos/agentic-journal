---
id: TASK-21
title: Add configurable project-local journal mirrors for Cortex panel consumption
status: To Do
assignee: []
created_date: '2026-06-12 21:25'
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
Users need to view Agentic Journal entries by project, especially for `/Users/varienos/Landing/Repo/cortex`, and want a project-local mirror journal that is easy to mount into containers and read from project panels. Agentic Journal should keep global writes, but add project-level mirror configuration. For Cortex, the intended mirror target is `Agentbase/.agentic-journal` under the project, while the path remains configurable for other projects. A recommended Cortex config would live at `/Users/varienos/Landing/Repo/cortex/.agentic-journal.toml`, match `/Users/varienos/Landing/Repo/cortex`, and mirror to `Agentbase/.agentic-journal`. Cortex Deck can then read or mount the Agentbase-local mirror without direct access to host-level `~/.agentic-journal`.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 A project can opt into a local Agentic Journal mirror through project-level configuration rather than hardcoded paths.
- [ ] #2 The mirror path is configurable per project and supports relative paths resolved from the config/project root.
- [ ] #3 The documented Cortex example uses project path `/Users/varienos/Landing/Repo/cortex` and mirror path `Agentbase/.agentic-journal`.
- [ ] #4 When an event is written, Agentic Journal mirrors it into the configured project-local journal if the event `repo` or `cwd` matches the configured project path exactly or is beneath it.
- [ ] #5 The mirror preserves the existing event shape and enough derived/indexed data for daily project views, while global journal writes continue to work unchanged.
- [ ] #6 The Cortex mirror includes both `Agentbase` events with no git repo and `Codebase/Cortex` events with git repo metadata.
- [ ] #7 The project-local mirror is suitable for container mounting or direct panel reads, and documentation explains the local/dev and container usage model.
- [ ] #8 A panel consumer can read the mirrored project journal and get the same daily summary/session/latest-events payload shape expected by the dashboard.
- [ ] #9 Tests cover config discovery, relative mirror-path resolution, enabled/disabled mirror behavior, exact-path and child-path matching, non-matching events, duplicate/idempotent writes, and preservation of global journal behavior.
<!-- AC:END -->
