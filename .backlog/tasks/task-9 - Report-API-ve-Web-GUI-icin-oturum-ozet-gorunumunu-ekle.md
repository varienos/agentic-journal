---
id: TASK-9
title: Report API ve Web GUI icin oturum ozet gorunumunu ekle
status: Done
assignee: []
created_date: '2026-06-01 15:51'
updated_date: '2026-06-01 15:58'
labels:
  - journal
  - web
  - report
dependencies:
  - TASK-8
modified_files:
  - src/agent_journal/report.py
  - src/agent_journal/web.py
  - tests/test_report.py
  - tests/test_web.py
priority: high
ordinal: 9000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Problem: GUI ve Markdown rapor event stream gosteriyor; kullanici gun sonu icin ajan bazli oturumda ne yapildi bilgisini gormek istiyor. Kapsam: report classifier session_summaries bolumu, web API sessions payload'i, dashboard'da Sessions gorunumu ve missing summary isaretleri. Kapsam disi: auth ve remote deploy.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Markdown report Session Summaries bolumu uretir ve session_summary eventlerini aciklayici listeler.
- [x] #2 Web API sessions dizisi dondurur; her session agent, session_id, repo, branch, commit, outcome, summary ve missing_summary bilgisini tasir.
- [x] #3 Dashboard summary/event stream yaninda oturum bazli aciklayici gorunum sunar.
- [x] #4 Summary olmayan started session'lar GUI/API'de missing summary olarak isaretlenir.
- [x] #5 Report ve web testleri red-green ile gecer.
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Markdown report Session Summaries bolumu, web API sessions payload'i ve dashboard Session Summaries paneli eklendi. Missing summary session'lar API/GUI'de isaretleniyor. Dogrulama: tests/test_report.py, tests/test_web.py, uv run pytest -q, Browser ile http://127.0.0.1:8766 uzerinde completed ve missing summary render kontrolu.
<!-- SECTION:FINAL_SUMMARY:END -->
