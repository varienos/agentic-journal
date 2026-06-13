---
id: TASK-23
title: Add container-level smoke for Cortex Agentic Journal MCP integration
status: To Do
assignee: []
created_date: '2026-06-13 14:52'
labels:
  - cortex
  - agentic-journal
  - mcp
  - docker
dependencies: []
references:
  - /Users/varienos/Landing/Repo/cortex/Codebase/Cortex/Dockerfile
  - >-
    /Users/varienos/Landing/Repo/cortex/Codebase/Cortex/src/mcp/registry-installer.ts
  - >-
    /Users/varienos/Landing/Repo/cortex/Codebase/Cortex/src/deck/deck-agentic-journal.ts
priority: medium
ordinal: 23000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Cortex depends on the agentic-journal-mcp command inside the runtime container and on registry install options matching the panel's project journal path. Add an end-to-end smoke so Docker/Coolify regressions are caught beyond static file assertions.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 A smoke check verifies the runtime image exposes agentic-journal-mcp to the non-root appuser process, not only to root during build.
- [ ] #2 The smoke verifies a non-default AGENTIC_JOURNAL_PROJECT_HOME value is propagated into the Agentic Journal MCP server registration path.
- [ ] #3 The smoke writes or simulates a semantic event and confirms the Cortex panel read path and MCP write path point at the same project-local journal root.
- [ ] #4 README or deployment docs describe how to run the smoke before Coolify rollout.
<!-- AC:END -->
