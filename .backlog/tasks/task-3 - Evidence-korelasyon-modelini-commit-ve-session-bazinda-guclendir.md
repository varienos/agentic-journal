---
id: TASK-3
title: Evidence korelasyon modelini commit ve session bazinda guclendir
status: Done
assignee: []
created_date: '2026-05-31 17:29'
updated_date: '2026-05-31 17:44'
labels:
  - stabilization
  - evidence
dependencies: []
references:
  - src/agent_journal/events.py
  - src/agent_journal/report.py
  - src/agent_journal/storage.py
  - docs/event-schema.md
  - tests/test_report.py
priority: medium
ordinal: 3000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Problem
Mevcut raporlama commit bazli verification eslestirmesine iyilestirildi, ancak task/session/verification arasindaki iliski hala basit event alanlarina dayaniyor.

Is etkisi
Gun sonu raporunda hangi ajan oturumunun hangi commiti veya task claimini dogruladigi yeterince acik olmazsa completed_verified guveni zayiflar.

Baglam
Inspected: src/agent_journal/events.py, report.py, storage.py, git_context.py, tests/test_report.py, tests/test_events.py.

Kapsam
Event schema ve report classification icin session_id, task_id, commit ve verification iliskisini netlestir; backward-compatible kal; mevcut JSONL/SQLite kayitlarini okumaya devam et.

Kapsam disi
Tam task inference veya LLM tabanli otomatik ozetleme yok.

Varsayimlar
Verification eventleri komut veya MCP yoluyla explicit yazilacak; prompt transcript loglanmayacak.

Riskler / bagimliliklar
Fazla kati eslestirme verified sayisini gereksiz dusurebilir; fallback kategorileri acik olmali.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 verification eventleri commit alanina ek olarak session_id ve task_id kullanabiliyorsa report bunu dikkate alir.
- [x] #2 completed_verified sadece matching evidence oldugunda uretilir; matching yoksa completed_claimed veya in_progress olarak kalir.
- [x] #3 Ayni repo icindeki baska commitler tek verification ile otomatik verified olmaz.
- [x] #4 Event schema dokumani correlation alanlarini ve fallback davranisini aciklar.
- [x] #5 Backward-compatible eski eventler rapor uretimini kirmadan siniflandirilir.
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Event schema dokumanindaki correlation alanlarini netlestir.
2. Report classification icin commit/session/task eslestirme kurallarini test-first yaz.
3. Eski eventlerde commit veya task_id yoksa guvenli fallback davranisini uygula.
4. SQLite raw_json okumasi ile compatibility testini koru.
5. uv run pytest -q ile dogrula.
<!-- SECTION:PLAN:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Strengthened report correlation so task completion claims can be promoted to completed_verified only when a passed verification matches by commit, session_id, or semantic.task_id with compatible repo metadata. Commit rows remain verified only by exact commit hash, preserving same-repo non-matching commits as in_progress. Added regression tests for session/task/repo mismatch behavior and documented correlation/fallback rules in docs/event-schema.md. Verified with tests/test_report.py and the full pytest suite.
<!-- SECTION:FINAL_SUMMARY:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [x] #1 Correlation kurallari testlerle kilitlendi.
- [x] #2 Raporlama verified/claimed/in_progress ayrimini yaniltici yapmiyor.
- [x] #3 docs/event-schema.md yeni kurallari anlatiyor.
<!-- DOD:END -->
