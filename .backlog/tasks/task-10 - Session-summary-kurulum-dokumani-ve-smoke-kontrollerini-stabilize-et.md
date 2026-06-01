---
id: TASK-10
title: Session summary kurulum dokumani ve smoke kontrollerini stabilize et
status: Done
assignee: []
created_date: '2026-06-01 15:51'
updated_date: '2026-06-01 15:58'
labels:
  - docs
  - smoke
  - github
dependencies:
  - TASK-8
  - TASK-9
modified_files:
  - README.md
  - docs/event-schema.md
  - docs/operations.md
  - scripts/verify.sh
  - scripts/package-smoke.sh
  - tests/test_verify_script.py
  - tests/test_package_smoke_script.py
priority: high
ordinal: 10000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Problem: Kullanici ajanlarin oturum sonunda aciklayici olay kaydi yazmasini bekliyor; kurulum dokumani ve smoke kontrolleri yeni session_summary akisini garanti etmeli. Kapsam: README/docs/event-schema/operations guncellemeleri, verify/package-smoke kontrolleri, global install yenileme ve GitHub push. Kapsam disi: provider-specific transcript otomatik ozetleme.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Dokumantasyon ajanlarin final/session-end oncesi journal_session_summary yazmasi gerektigini aciklar.
- [x] #2 event schema session_summary alanlarini ve privacy sinirlarini tarif eder.
- [x] #3 verify/package-smoke yeni MCP tool ve report/API davranisini kontrol eder.
- [x] #4 Degisiklikler commitlenir, global kurulum yenilenir ve origin/main'e push edilir.
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
README, operations ve event schema session_summary gerekliligini acikliyor. verify/package-smoke yeni event type, MCP tool, web API ve report davranisini kontrol ediyor. Degisiklikler commitlenip global kuruluma ve origin/main push akisine alinacak.
<!-- SECTION:FINAL_SUMMARY:END -->
