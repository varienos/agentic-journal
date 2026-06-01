---
id: TASK-8
title: Session summary event modelini ve MCP aracini ekle
status: Done
assignee: []
created_date: '2026-06-01 15:51'
updated_date: '2026-06-01 15:58'
labels:
  - journal
  - semantic
  - mcp
dependencies: []
modified_files:
  - src/agent_journal/events.py
  - src/agent_journal/cli.py
  - src/agent_journal/mcp_server.py
  - tests/test_events.py
  - tests/test_cli.py
  - tests/test_mcp_server.py
priority: high
ordinal: 8000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Problem: Agent Journal bugunku kayitlarda agent_start yakaliyor ama oturumda ne yapildigini aciklayan semantic summary uretmiyor. Kapsam: session_summary event type, CLI semantic alanlari, journal_session_summary MCP tool'u, guard'in summary yoklugunu yakalamasi ve testleri. Kapsam disi: provider transcript parserlari.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 session_summary event type normalize edilir ve JSONL/SQLite'a yazilabilir.
- [x] #2 agent-journal event ile summary/outcome/task/session bilgisi yazilabilir.
- [x] #3 MCP server journal_session_summary tool'u ile agent, session_id, summary, outcome ve task bilgisi kaydedebilir.
- [x] #4 guard session-end artik yalnizca session_summary/task_completed/task_blocked gibi outcome kayitlarini yeterli sayar; sadece generic note summary yerine gecmez.
- [x] #5 Ilgili CLI/MCP/guard testleri red-green ile gecer.
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
session_summary event type, CLI --summary/--outcome alanlari, journal_session_summary MCP tool'u ve guard'in generic note'u outcome saymamasi eklendi. Dogrulama: hedefli TDD testleri, uv run pytest -q, scripts/verify.sh ve scripts/package-smoke.sh.
<!-- SECTION:FINAL_SUMMARY:END -->
