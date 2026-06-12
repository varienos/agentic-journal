---
id: TASK-21
title: Add configurable project-local journal mirrors for Cortex panel consumption
status: Done
assignee:
  - codex
created_date: '2026-06-12 21:25'
updated_date: '2026-06-12 21:49'
labels:
  - feature
  - journal
  - cortex
  - mirror
dependencies: []
documentation:
  - docs/superpowers/specs/2026-06-13-project-local-journal-mirrors-design.md
  - >-
    docs/superpowers/plans/2026-06-13-project-local-journal-mirrors-implementation-plan.md
modified_files:
  - src/agentic_journal/project_config.py
  - src/agentic_journal/storage.py
  - src/agentic_journal/cli.py
  - tests/test_config.py
  - tests/test_storage.py
  - tests/test_cli.py
  - README.md
  - docs/event-schema.md
  - docs/operations.md
  - >-
    docs/superpowers/plans/2026-06-13-project-local-journal-mirrors-implementation-plan.md
  - /Users/varienos/Landing/Repo/cortex/Codebase/Cortex/src/config/env.ts
  - >-
    /Users/varienos/Landing/Repo/cortex/Codebase/Cortex/src/deck/deck-agentic-journal.ts
  - /Users/varienos/Landing/Repo/cortex/Codebase/Cortex/src/deck/deck-routes.ts
  - >-
    /Users/varienos/Landing/Repo/cortex/Codebase/Cortex/test/deck-agentic-journal.test.ts
  - /Users/varienos/Landing/Repo/cortex/Codebase/Cortex/deck/src/api/hooks.ts
  - >-
    /Users/varienos/Landing/Repo/cortex/Codebase/Cortex/deck/src/pages/AgenticJournalPage.tsx
  - /Users/varienos/Landing/Repo/cortex/Codebase/Cortex/deck/src/App.tsx
  - >-
    /Users/varienos/Landing/Repo/cortex/Codebase/Cortex/deck/src/components/Sidebar/index.tsx
  - /Users/varienos/Landing/Repo/cortex/Codebase/Cortex/docker-compose.yml
  - >-
    /Users/varienos/Landing/Repo/cortex/Codebase/Cortex/docker-compose.coolify.yml
  - /Users/varienos/Landing/Repo/cortex/Codebase/Cortex/.env.example
  - /Users/varienos/Landing/Repo/cortex/Codebase/Cortex/README.md
  - >-
    /Users/varienos/Landing/Repo/cortex/Codebase/Cortex/test/docker.files.test.ts
priority: medium
ordinal: 21000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Users need to view Agentic Journal entries by project, especially for `/Users/varienos/Landing/Repo/cortex`, and want a project-local mirror journal that is easy to mount into containers and read from project panels. Agentic Journal should keep global writes, but add project-level mirror configuration. For Cortex, the intended mirror target is `Agentbase/.agentic-journal` under the project, while the path remains configurable for other projects. A recommended Cortex config would live at `/Users/varienos/Landing/Repo/cortex/.agentic-journal.toml`, match `/Users/varienos/Landing/Repo/cortex`, and mirror to `Agentbase/.agentic-journal`. Cortex Deck can then read or mount the Agentbase-local mirror without direct access to host-level `~/.agentic-journal`.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 A project can opt into a local Agentic Journal mirror through project-level configuration rather than hardcoded paths.
- [x] #2 The mirror path is configurable per project and supports relative paths resolved from the config/project root.
- [x] #3 The documented Cortex example uses project path `/Users/varienos/Landing/Repo/cortex` and mirror path `Agentbase/.agentic-journal`.
- [x] #4 When an event is written, Agentic Journal mirrors it into the configured project-local journal if the event `repo` or `cwd` matches the configured project path exactly or is beneath it.
- [x] #5 The mirror preserves the existing event shape and enough derived/indexed data for daily project views, while global journal writes continue to work unchanged.
- [x] #6 The Cortex mirror includes both `Agentbase` events with no git repo and `Codebase/Cortex` events with git repo metadata.
- [x] #7 The project-local mirror is suitable for container mounting or direct panel reads, and documentation explains the local/dev and container usage model.
- [x] #8 A panel consumer can read the mirrored project journal and get the same daily summary/session/latest-events payload shape expected by the dashboard.
- [x] #9 Tests cover config discovery, relative mirror-path resolution, enabled/disabled mirror behavior, exact-path and child-path matching, non-matching events, duplicate/idempotent writes, and preservation of global journal behavior.
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
Implement configurable project-local Agentic Journal mirrors and connect Cortex Deck to the Cortex mirror.

1. Agentic Journal config/discovery: add `.agentic-journal.toml` parsing, project path matching, relative mirror path resolution, and discovery from event `cwd`/`repo` ancestry.
2. Agentic Journal write fan-out: keep global writes unchanged, then mirror matching events to configured project-local journal roots using the existing SQLite/JSONL layout and idempotent event ids.
3. Agentic Journal CLI/read support: add `mirror sync` for historical backfill and `--root` support for read commands so mirror roots can produce status/report/web payloads.
4. Agentic Journal docs/tests: document Cortex config with `path = "Agentbase/.agentic-journal"`, privacy/mounting notes, and cover config, matching, idempotency, sync, and unchanged global behavior.
5. Cortex backend: add `AGENTIC_JOURNAL_PROJECT_HOME` config defaulting to `/Agentbase/.agentic-journal`, implement a root-only `/deck/api/agentic-journal/events` route that reads mirror JSONL and returns daily summary/session/latest-events payload.
6. Cortex frontend: add a root-only Deck page and sidebar route named `Ajan Günlüğü` that consumes the backend payload.
7. Cortex docs/container: document/mount `Agentbase/.agentic-journal` for local/dev and container usage.
8. Verification: run focused Agentic Journal tests, Cortex route/build tests, backfill Cortex history into the mirror, verify the mirror status payload, then finalize TASK-21.
<!-- SECTION:PLAN:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Implemented configurable project-local Agentic Journal mirrors with `.agentic-journal.toml` discovery, idempotent write fan-out, `mirror sync` backfill, and `--root` read support. Added Cortex Deck root-only Agentic Journal API/page wiring against `AGENTIC_JOURNAL_PROJECT_HOME`, documented Docker/Coolify mirror mounts, created the local Cortex mirror config, backfilled 638 matching events into `/Users/varienos/Landing/Repo/cortex/Agentbase/.agentic-journal`, and verified the mirror status payload. Verification: `uv run pytest -q` (151 passed), `npm test -- test/deck-agentic-journal.test.ts test/docker.files.test.ts` (14 passed), `npm run build`, and `npm run build --prefix deck`.
<!-- SECTION:FINAL_SUMMARY:END -->
