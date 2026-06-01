---
id: TASK-11
title: Self-review bulgularini stabilize et
status: Done
assignee: []
created_date: '2026-06-01 16:17'
updated_date: '2026-06-01 16:24'
labels:
  - review
  - stabilization
  - security
  - mcp
dependencies: []
modified_files:
  - src/agent_journal/mcp_server.py
  - src/agent_journal/install.py
  - src/agent_journal/storage.py
  - src/agent_journal/web.py
  - README.md
  - docs/operations.md
  - docs/event-schema.md
  - tests/test_mcp_server.py
  - tests/test_cli.py
  - tests/test_install.py
  - tests/test_storage.py
  - tests/test_web.py
priority: high
ordinal: 11000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Problem: Self-review Agent Journal'da MCP context/session korelasyonu, git hook chaining, storage idempotency ve web API exposure riskleri buldu. Kapsam: review bulgularini regression testleriyle kapatmak; MCP outcome tool'larini session/repo context ile yazmak; git hook'u mevcut hook'u zincirleyecek hale getirmek; SQLite/JSONL mirror duplicate davranisini tutarli yapmak; web API icin local token guard ve dokumantasyon eklemek. Kapsam disi: hosted/multi-user dashboard ve provider transcript parserlari.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 MCP journal_note/session_summary/task_completed/task_blocked eventleri cwd/repo/branch/commit ve AGENT_JOURNAL_SESSION_ID context'i ile yazilir.
- [x] #2 Guard session-end, MCP journal_task_completed veya journal_task_blocked ayni session icinde yazildiginda risky journal_missing uretmez.
- [x] #3 Git hook installer mevcut post-commit hook'u yedekler ve yeni hook icinden calistirir.
- [x] #4 Ayni event_id tekrar yazildiginda SQLite ve JSONL mirror duplicate uretmeden tutarli kalir.
- [x] #5 Web API default local-only kalir; token ayarlandiginda /api/events token olmadan 401 doner ve GUI tokenli fetch yapabilir.
- [x] #6 README/operations/event-schema yeni davranislari aciklar ve full verify/package smoke/CI gecer.
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Self-review bulgulari regression testleriyle kapatildi. MCP tool'lari session ve git context tasiyor; guard MCP task_completed/task_blocked eventlerini ayni session icinde outcome sayiyor; git hook mevcut post-commit backup'ini zincirliyor; write_event duplicate event_id icin JSONL/SQLite'i hizali tutuyor; web API token ayarlandiginda 401/200 davranisi ve GUI tokenli fetch dogrulandi. Lokal dogrulama: uv run pytest -q, scripts/verify.sh, scripts/package-smoke.sh, uv lock --check, git diff --check ve Browser token render smoke.
<!-- SECTION:FINAL_SUMMARY:END -->
