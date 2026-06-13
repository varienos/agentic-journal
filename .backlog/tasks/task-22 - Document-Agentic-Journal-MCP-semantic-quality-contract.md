---
id: TASK-22
title: Document Agentic Journal MCP semantic quality contract
status: To Do
assignee: []
created_date: '2026-06-13 14:52'
labels:
  - agentic-journal
  - mcp
  - quality
dependencies: []
references:
  - src/agentic_journal/mcp_server.py
  - tests/test_mcp_server.py
priority: medium
ordinal: 22000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Agentic Journal MCP tools now avoid writing empty semantic records. Future maintainers and client integrators need an explicit contract for which fields are required, what skip responses mean, and how this protects daily/project journals from low-value noise.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Documentation states that journal_note requires a non-empty note, journal_session_summary requires a non-empty summary, journal_task_completed requires task_id or note, and journal_task_blocked requires a non-empty reason.
- [ ] #2 Documentation explains that skipped MCP calls do not write SQLite or JSONL events and return a stable skipped:* message for client visibility.
- [ ] #3 Tests cover the documented skip behavior at the public MCP helper boundary and prove no event is persisted for skipped calls.
- [ ] #4 Release or integration notes mention the skip contract so Cortex and other MCP clients can surface it without treating it as a transport failure.
<!-- AC:END -->
