---
id: TASK-20
title: Update global agentic-journal install and wrappers
status: Done
assignee:
  - codex
created_date: '2026-06-07 07:08'
updated_date: '2026-06-07 07:12'
labels:
  - global-install
  - rename-followup
dependencies: []
priority: medium
ordinal: 20000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Audit and fix the machine-wide Agentic Journal installation after the project rename. Ensure global CLI/MCP commands, wrapper PATH entries, agent instruction blocks, and MCP snippets point to agentic-journal instead of agent-journal, and verify codex/claude/gemini wrapper scripts can invoke the new CLI.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Global agentic-journal and agentic-journal-mcp commands are available and the old agent-journal command is not the preferred active command.
- [x] #2 Global wrapper directory and shell profile PATH block reference agentic-journal naming and usable command paths.
- [x] #3 Global Codex, Claude, and Gemini instruction/config files use the new Agentic Journal command/snippet names without stale agent-journal references.
- [x] #4 Generated codex, claude, and gemini wrapper scripts have valid real-binary targets and can call agentic-journal lifecycle commands.
- [x] #5 A doctor or equivalent verification command reports the setup as healthy after fixes.
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Inspect command resolution for agentic-journal/agentic-journal-mcp and any stale agent-journal binaries. 2. Inspect global wrapper root, shell profile PATH blocks, MCP config snippets, and agent instruction files. 3. Reinstall the package globally from the renamed checkout and regenerate wrappers/shell profile/instructions/snippets as needed. 4. Verify command availability, wrapper script targets, doctor output, and absence of stale agent-journal references in generated global files.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Global setup audited after the project rename. Root cause was stale uv tool install, shell profile PATH blocks, global agent instruction blocks, MCP config entries, and wrappers still pointing at agent-journal and /Users/varienos/Landing/Repo/agent-journal.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Installed agentic-journal globally from /Users/varienos/Landing/Repo/agentic-journal and uninstalled the old agent-journal uv tool. Migrated journal data into ~/.agentic-journal, including JSONL/reports and a SQLite backup from agent-journal.db to agentic-journal.db. Regenerated ~/.agentic-journal/bin wrappers for codex/claude/gemini, updated ~/.zprofile and ~/.zshrc PATH blocks, refreshed Codex/Claude/Gemini global instruction blocks, updated Codex/Claude/Gemini MCP config references, added Gemini's agentic-journal MCP server, and installed the repo post-commit hook with agentic-journal. Verification: agentic-journal doctor --today reports wrappers ok, MCP configured, instructions ok, and git hook ok; wrapper scripts pass sh -n; real binary targets are executable; global checked files contain no stale agent-journal/agent_journal/Agent Journal/AGENT_JOURNAL references; which -a shows agentic-journal commands and no old agent-journal commands.
<!-- SECTION:FINAL_SUMMARY:END -->
