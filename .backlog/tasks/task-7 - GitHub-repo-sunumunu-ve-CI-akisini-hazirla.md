---
id: TASK-7
title: GitHub repo sunumunu ve CI akisini hazirla
status: Done
assignee: []
created_date: '2026-06-01 05:51'
updated_date: '2026-06-01 05:55'
labels:
  - github
  - ci
dependencies: []
modified_files:
  - README.md
  - .github/workflows/ci.yml
priority: high
ordinal: 7000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
GitHub'a push oncesi Agent Journal reposunu GitHub uzerinde okunabilir ve dogrulanabilir hale getir: README badge/clone akislarini ekle, GitHub Actions CI workflow'u ekle, remote push dogrulamasini yap.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 README GitHub uzerinde repo, CI ve clone akislarini net gosterir.
- [x] #2 GitHub Actions CI workflow'u test ve smoke komutlarini calistirir.
- [x] #3 Degisiklikler dogrulanir, commitlenir ve origin/main'e push edilir.
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
GitHub sunumu icin README badge ve clone akisi eklendi, GitHub Actions CI workflow'u test/verify/package-smoke adimlariyla eklendi, remote origin varienos/agent-journal olarak dogrulandi. Dogrulama: uv sync --dev --locked; scripts/verify.sh; scripts/package-smoke.sh; git diff --check.
<!-- SECTION:FINAL_SUMMARY:END -->
