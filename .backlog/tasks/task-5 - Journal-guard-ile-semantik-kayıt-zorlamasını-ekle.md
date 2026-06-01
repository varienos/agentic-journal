---
id: TASK-5
title: Journal guard ile semantik kayıt zorlamasını ekle
status: Done
assignee: []
created_date: '2026-06-01 04:44'
updated_date: '2026-06-01 04:51'
labels:
  - stabilization
  - guard
dependencies: []
priority: high
ordinal: 5000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Problem: MCP journal_note gönüllü çağrılıyor; ajan oturumu semantik kayıt bırakmadan bitebilir. Kapsam: session guard CLI ekle; aynı session içinde semantic_note/task_completed_claim/task_blocked yoksa risky fallback event yaz; raporda semantic notes görünür olsun; docs ve smoke kapsamını güncelle. Kapsam dışı: gerçek ajan hook configlerini tüm projelere otomatik yazmak.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 agent-journal guard session-end aynı session için semantik kayıt varsa yeni fallback yazmaz.
- [x] #2 Semantik kayıt yoksa guard session-end risky fallback event yazar ve idempotent çalışır.
- [x] #3 Daily report semantic_note kayıtlarını okunabilir Notes bölümünde gösterir.
- [x] #4 Operations dokümanı Claude/Gemini/Codex hook kullanımını açıklar.
- [x] #5 verify/package smoke ve pytest yeşil kalır.
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Added agent-journal guard session-end to enforce auditable journaling when a model omits semantic MCP output. The guard is idempotent, skips sessions that already have semantic_note/task_completed_claim/task_blocked, and writes a failed verification with semantic.status=journal_missing otherwise. Generated wrappers now export AGENT_JOURNAL_SESSION_ID and invoke the guard after agent_end, making wrapped agent sessions automatically risky when they finish without semantic journal data. Daily reports now include Notes, docs explain guard wiring, and verify/package smoke cover the new behavior.
<!-- SECTION:FINAL_SUMMARY:END -->
