---
id: TASK-1
title: Backlog workflow baseline ve ajan talimatlarini stabilize et
status: Done
assignee: []
created_date: '2026-05-31 17:29'
updated_date: '2026-05-31 17:39'
labels:
  - stabilization
  - backlog
dependencies: []
references:
  - AGENTS.md
  - CLAUDE.md
  - GEMINI.md
  - .backlog/config.yml
  - README.md
priority: high
ordinal: 1000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Problem
Backlog kurulumu yeni yapildi; .backlog/, AGENTS.md, CLAUDE.md ve GEMINI.md dosyalari mevcut ama proje icin kalici workflow baseline'i henuz dogrulanmis degil.

Is etkisi
Ajanlar task acma, arama ve takip akisini farkli yorumlarsa Agent Journal gelistirmesi sirasinda tekrar eden veya eksik tasklar olusabilir.

Baglam
Inspected: AGENTS.md, CLAUDE.md, GEMINI.md, .backlog/config.yml, README.md, backlog task list/overview ciktisi.

Kapsam
Backlog.md workflow'unu Agent Journal reposu icin dogrula, task lifecycle kararlarini netlestir, MCP/CLI fallback yolunu belgeleyen minimum operasyon notunu hazirla.

Kapsam disi
Agent Journal runtime kodu degistirme; mevcut tasklari yeniden kapsamlandirma.

Varsayimlar
Backlog CLI kullanilabilir ve task_prefix task olarak kalacak.

Riskler / bagimliliklar
Backlog MCP client her ortamda yuklu olmayabilir; CLI fallback akisi net olmali.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 AGENTS.md/CLAUDE.md/GEMINI.md icindeki Backlog yonlendirmeleri repo gercegiyle uyumlu oldugu dogrulanir.
- [x] #2 Backlog CLI ile search-first task creation akisi icin kisa operator notu eklenir veya mevcut docs/operations.md icinde referanslanir.
- [x] #3 Yeni task acmadan once kullanilacak duplicate search terimleri ve raporlama formati netlesir.
- [x] #4 Backlog setup dosyalari git durumunda bilincli olarak takip edilecek veya ignore edilecek sekilde kararlandirilir.
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. AGENTS.md, CLAUDE.md, GEMINI.md ve .backlog/config.yml dosyalarini oku.
2. Backlog CLI ve varsa MCP kullanimi icin repo-ozel minimum workflow notunu belirle.
3. Duplicate search ve task creation pratiklerini docs/operations.md veya uygun backlog dokumaninda belgelemek icin hazirla.
4. Backlog setup dosyalarinin git tracking kararini netlestir.
5. backlog overview ve task list ile sonucu dogrula.
<!-- SECTION:PLAN:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Backlog baseline stabilized in docs/operations.md. Confirmed AGENTS/CLAUDE/GEMINI Backlog MCP guidance, .backlog/config.yml, backlog task list, and backlog overview. Documented CLI fallback, duplicate search terms, reporting expectations, and the decision to track .backlog plus agent instruction files in git.
<!-- SECTION:FINAL_SUMMARY:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [x] #1 Backlog workflow baseline'i repo icinde acik ve tekrar uygulanabilir.
- [x] #2 Duplicate search ve task creation beklentisi dokumante edildi.
- [x] #3 backlog task list/overview komutlari beklenen sekilde calisiyor.
<!-- DOD:END -->
