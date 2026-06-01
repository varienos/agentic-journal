---
id: TASK-6
title: Anlık Agent Journal web GUI ekle
status: Done
assignee: []
created_date: '2026-06-01 05:29'
updated_date: '2026-06-01 05:38'
labels:
  - ui
  - web
  - stabilization
dependencies: []
modified_files:
  - src/agent_journal/web.py
  - src/agent_journal/cli.py
  - tests/test_web.py
  - tests/test_cli.py
  - scripts/verify.sh
  - scripts/package-smoke.sh
  - docs/operations.md
priority: high
ordinal: 6000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Problem: Günlük kayıtları şu an CLI report ile okunuyor; kullanıcı anlık olarak ajan eventlerini, notları ve risky guard kayıtlarını web arayüzünden görmek istiyor. Kapsam: dependency eklemeden agent-journal web komutu, JSON API, auto-refresh dashboard, docs ve smoke doğrulaması. Kapsam dışı: auth, remote deploy, multi-user dashboard, full frontend build pipeline.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 agent-journal web --help CLI komutunda görünür ve host/port/date seçenekleri sağlar.
- [x] #2 Web API bugünün raw eventlerini, sınıflandırılmış summary bilgisini ve latest event listesini JSON döner.
- [x] #3 Dashboard HTML summary kartları, event akışı, notes/risky görünümü ve auto-refresh davranışı içerir.
- [x] #4 Paket smoke web entrypoint/help ve API render davranışını doğrular.
- [x] #5 pytest, verify ve package-smoke yeşil kalır.
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Agent Journal icin dependency eklemeden agent-journal web komutu, /api/events JSON endpoint'i, auto-refresh dashboard, operasyon dokumani ve paket smoke dogrulamasi eklendi. Dogrulama: uv run pytest -q; scripts/verify.sh; scripts/package-smoke.sh; git diff --check.
<!-- SECTION:FINAL_SUMMARY:END -->
