---
id: TASK-2
title: Agent Journal uc uca smoke ve CI stabilizasyonu ekle
status: Done
assignee: []
created_date: '2026-05-31 17:29'
updated_date: '2026-05-31 17:42'
labels:
  - stabilization
  - testing
dependencies: []
references:
  - src/agent_journal/cli.py
  - src/agent_journal/install.py
  - src/agent_journal/mcp_server.py
  - scripts/hooks/post-commit
  - scripts/wrappers/agent-journal-wrapper.sh
  - tests/test_cli.py
priority: high
ordinal: 2000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Problem
MVP testleri geciyor ama kritik operator akislari hala manuel smoke komutlarina dayaniyor: event yazma, report/status, generated wrapper, git hook ve MCP tool kaydi.

Is etkisi
Gelecek degisiklikler journaling omurgasini bozarsa ajan gunlukleri sessizce eksik veya yanlis uretilir.

Baglam
Inspected: src/agent_journal/cli.py, storage.py, install.py, mcp_server.py, scripts/hooks/post-commit, scripts/wrappers/agent-journal-wrapper.sh, tests/.

Kapsam
Tek komutla calisan stabilizasyon smoke suite veya CI-friendly test hedefi ekle; local runtime dizinini gecici tut; wrapper/git hook/MCP isimlerini dogrula.

Kapsam disi
Hosted CI saglayici entegrasyonu zorunlu degil; cloud dashboard yok.

Varsayimlar
uv run pytest mevcut dogrulama komutu olarak kalacak.

Riskler / bagimliliklar
Wrapper testleri PATH ve real binary shadowing nedeniyle kirilgan olabilir; temp dizin ve fake binary kullanilmali.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Tek bir komut Agent Journal unit testlerini ve kritik smoke kontrollerini calistirir.
- [x] #2 Generated wrapper fake binary exit code'unu aynen korudugu ve agent_start/agent_end event yazdigi dogrulanir.
- [x] #3 Git post-commit veya git_commit event smoke testi HEAD commit hash ve commit dosyalarini dogrular.
- [x] #4 MCP server olusturuldugunda journal_note, journal_task_completed, journal_task_blocked, journal_daily_report tool isimleri kayitli gorunur.
- [x] #5 Smoke calismalari kullanici ~/.agent-journal verisini kirletmez; gecici AGENT_JOURNAL_HOME kullanir.
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Mevcut tests/ kapsaminda smoke'a en yakin testleri tespit et.
2. Gerekirse scripts/ veya pytest marker ile tek komutluk smoke hedefi tanimla.
3. Fake binary ile wrapper start/end ve exit code davranisini test et.
4. Temporary git repo ile git_commit metadata davranisini test et.
5. MCP server tool registration testini smoke kapsaminda tut.
6. uv run pytest -q ve smoke hedefini calistir.
<!-- SECTION:PLAN:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Added scripts/verify.sh as the single stabilization command. It runs unit tests, compileall, report/status smoke, generated wrapper fake-binary smoke with preserved exit code and start/end events, git commit metadata smoke in a temporary repo, and MCP tool registration checks while isolating AGENT_JOURNAL_HOME under a temp directory. Documented the command in docs/operations.md and verified pytest plus scripts/verify.sh locally.
<!-- SECTION:FINAL_SUMMARY:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [x] #1 Unit testler ve smoke hedefi lokal olarak yesil.
- [x] #2 Smoke hedefi runtime artefaktlarini repo veya kullanici home altinda birakmiyor.
- [x] #3 docs/operations.md stabilizasyon dogrulama komutunu soyluyor.
<!-- DOD:END -->
