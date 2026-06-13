---
id: TASK-25
title: Add Agentic Journal model operation events
status: Done
assignee:
  - codex
created_date: '2026-06-13 18:35'
updated_date: '2026-06-13 18:45'
labels:
  - agentic-journal
  - model-activity
dependencies: []
modified_files:
  - src/agentic_journal/events.py
  - src/agentic_journal/cli.py
  - src/agentic_journal/mcp_server.py
  - src/agentic_journal/report.py
  - src/agentic_journal/web.py
  - src/agentic_journal/security.py
  - docs/event-schema.md
  - docs/operations.md
  - README.md
  - scripts/verify.sh
  - scripts/package-smoke.sh
  - tests/test_events.py
  - tests/test_cli.py
  - tests/test_mcp_server.py
  - tests/test_report.py
  - tests/test_web.py
  - tests/test_security.py
  - tests/test_docs.py
  - tests/test_verify_script.py
  - tests/test_package_smoke_script.py
priority: medium
ordinal: 25000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Add first-class Agentic Journal support for model-operation activity emitted by external runtimes such as Cortex. The journal should accept structured metadata about a model call without storing prompts, completions, transcripts, or file contents. This is the Agentic Journal-side foundation only; Cortex instrumentation will be planned separately.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 A new supported event type records model operation activity with sanitized metadata for provider, model, operation/source, status/outcome, duration, token usage, and error code when supplied.
- [x] #2 The CLI can write a model operation event using explicit flags without requiring prompt or response text.
- [x] #3 The MCP server exposes a tool for writing model operation events and rejects blank/metadata-free calls consistently with existing semantic tools.
- [x] #4 Daily reports and status classify model operation events under a dedicated model activity bucket instead of lumping them into generic in-progress work.
- [x] #5 The local web dashboard API and rendered dashboard include the model activity bucket in summary metrics and latest-event data.
- [x] #6 Documentation describes the model operation event contract and explicitly states that prompts, completions, transcripts, and file contents must not be logged.
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Add tests first for the model_operation event contract in events, CLI, MCP, report, and web payload/rendering. Verify the initial focused tests fail because the event type/tool/classification do not exist yet.
2. Add MODEL_OPERATION_EVENT_TYPE and allow it through normalization without expanding the persisted top-level schema beyond existing fields; store model-call metadata in semantic/evidence so prompts and completions are not part of the contract.
3. Extend CLI event flags for model-operation metadata: provider, model, operation/source, status/outcome, input/output/cached/reasoning tokens, and error code. Keep prompt/response/body unsupported.
4. Extend MCP with journal_model_operation using the same metadata contract and a metadata-required guard.
5. Extend report/status/web classification with a dedicated model_activity bucket and update labels/rendering so model operations are visible separately from in-progress work.
6. Update docs/README to document the model_operation contract and privacy boundary.
7. Run focused tests, then full test suite if feasible; update TASK-25 acceptance criteria and final summary based on verified output.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Implemented with TDD. Red phase produced expected failures for unsupported `model_operation`, missing CLI flags, missing MCP tool, absent `model_activity` classification, dashboard visibility, and docs. Added a narrow redaction exception so numeric `evidence.token_usage` survives while secret-looking token keys still redact.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Added first-class Agentic Journal `model_operation` support as the AJ-side foundation for future Cortex runtime instrumentation.

Changes:
- Added `model_operation` to the supported event schema and allowed structured model-call metadata through normalization.
- Added CLI flags for model activity metadata: provider, model, operation, source, status, duration, token usage, and error code.
- Added MCP tool `journal_model_operation` with a metadata-required guard.
- Added report/status/web `model_activity` classification and dashboard rendering so model operations are separate from in-progress agent sessions.
- Preserved numeric `evidence.token_usage` through redaction while continuing to redact secret-looking token keys.
- Documented the metadata-only contract and the explicit privacy boundary: no prompts, completions, transcripts, or file contents.
- Updated verify/package smoke scripts to include the new MCP tool.

Verification:
- `uv run pytest -q` -> 163 passed.
- `scripts/verify.sh` via `rtk proxy bash scripts/verify.sh` -> passed, including release check, pytest, compileall, CLI/wrapper/git/MCP/web token smoke.
- `scripts/package-smoke.sh` via `rtk proxy bash scripts/package-smoke.sh` -> passed.
<!-- SECTION:FINAL_SUMMARY:END -->
