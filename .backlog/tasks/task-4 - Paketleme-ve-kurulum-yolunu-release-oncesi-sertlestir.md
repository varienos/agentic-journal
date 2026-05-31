---
id: TASK-4
title: Paketleme ve kurulum yolunu release oncesi sertlestir
status: Done
assignee: []
created_date: '2026-05-31 17:29'
updated_date: '2026-05-31 17:47'
labels:
  - stabilization
  - packaging
dependencies: []
references:
  - pyproject.toml
  - src/agent_journal/install.py
  - src/agent_journal/mcp_server.py
  - docs/operations.md
priority: medium
ordinal: 4000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Problem
Agent Journal kaynak repoda calisiyor, ancak global kullanimin hedefi wrapper, console script ve MCP serverin paket kurulumundan sonra da ayni sekilde calismasi.

Is etkisi
Kullanici agent-journal install wrappers veya agent-journal-mcp komutlarini paketli kurulumda calistirdiginda path/package farklari yuzunden gunluk kaydi sessizce durabilir.

Baglam
Inspected: pyproject.toml, src/agent_journal/install.py, src/agent_journal/mcp_server.py, docs/operations.md, uv.lock.

Kapsam
Wheel/editable install davranisini dogrula; console scriptler, generated wrapper ve MCP startup icin paketlenmis ortam smoke testi ekle; operasyon dokumanini netlestir.

Kapsam disi
Homebrew/pipx/uv tool yayinlama otomasyonu zorunlu degil.

Varsayimlar
uv project workflow birincil lokal kurulum yolu olarak kullanilacak.

Riskler / bagimliliklar
MCP SDK surum degisimleri startup davranisini etkileyebilir; tool registration smoke testi surdurulmeli.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Paket kurulumundan sonra agent-journal --help ve agent-journal-mcp entrypointleri import/startup seviyesinde dogrulanir.
- [x] #2 agent-journal install wrappers ile uretilen wrapper kaynak repo scripts dizinine bagimli olmaz.
- [x] #3 Generated wrapper PATH uzerinden agent-journal bulamadiginda anlasilir hata veya dokumante edilmis davranis verir.
- [x] #4 docs/operations.md uv run, editable install ve global install icin net komutlari icerir.
- [x] #5 Release oncesi kontrol listesi pyproject/uv.lock/test komutlariyla birlikte belgelenir.
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. pyproject console script ve package include davranisini incele.
2. Temporary environment ile wheel veya editable install smoke testi tasarla.
3. Generated wrapper'in paket disi dosya bagimliligi olmadigini testle.
4. MCP entrypoint startup/import smoke testini ekle.
5. Kurulum dokumanini global ve local senaryolarla guncelle.
6. uv run pytest -q ve packaging smoke komutlarini calistir.
<!-- SECTION:PLAN:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Added package-smoke.sh to build a wheel, install it into a temporary venv, verify packaged agent-journal and agent-journal-mcp entrypoints, install generated wrappers from the packaged CLI, assert wrappers do not depend on scripts/wrappers, and confirm wrapper event capture plus missing-PATH warning behavior. Hardened generated wrappers to warn when agent-journal is unavailable while preserving the real agent exit code. Documented uv run, editable install, uv tool global install, PATH behavior, and a release checklist in docs/operations.md. Verified package-smoke.sh and the full pytest suite.
<!-- SECTION:FINAL_SUMMARY:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [x] #1 Paketleme smoke testi yesil.
- [x] #2 Wrapper ve MCP entrypoint paketli ortamda dogrulandi.
- [x] #3 Kurulum dokumani yeni kullanici icin uygulanabilir.
<!-- DOD:END -->
