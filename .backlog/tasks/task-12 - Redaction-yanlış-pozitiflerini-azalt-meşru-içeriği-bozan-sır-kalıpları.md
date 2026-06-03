---
id: TASK-12
title: 'Redaction yanlış-pozitiflerini azalt: meşru içeriği bozan sır kalıpları'
status: Done
assignee: []
created_date: '2026-06-02 21:45'
labels:
  - security
  - redaction
dependencies: []
modified_files:
  - src/agent_journal/security.py
  - tests/test_security.py
priority: medium
ordinal: 12000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
İkinci tur kod review'da tespit edildi (fix/code-review-findings, commit 1b541a5 sonrası). `src/agent_journal/security.py` içindeki yeni value-pattern redaction bazı meşru içeriği sır sanıp `[REDACTED]` ile yok ediyor; bu, gözlemci aracında journal içeriğini sessizce bozar (veri bütünlüğü sorunu).

Doğrulanan yanlış-pozitifler:
- `(sk|pk|rk)[-_][A-Za-z0-9_-]{8,}` kalıbı: `pk_test_widget_render_ok` ve `rk_unit_test_helper` gibi sıradan tanımlayıcıları tümüyle redakte ediyor (Stripe test anahtarları kasıtlı olarak gizli değildir).
- Bare `\bBearer\s+[A-Za-z0-9._~+/=-]{8,}\b` kalıbı: "Bearer responsibility matters" → "Bearer [REDACTED] matters" (Bearer kelimesinden sonraki ≥8 karakterlik herhangi bir düz metin sözcüğü yok ediliyor).

Amaç: gerçek sırları yakalamayı sürdürürken precision'ı artırmak.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 sk_/pk_/rk_ ön ekli sıradan tanımlayıcılar (ör. pk_test_widget_render_ok, rk_unit_test_helper) redaksiyona uğramaz
- [x] #2 Stripe/OpenAI kalıbı yalnızca sağlayıcı-özgü infix'lerle (sk_live_, sk_test_, pk_live_, rk_live_, sk- uzun token) veya bir entropi/karışık-charset eşiğiyle eşleşir
- [x] #3 Bare Bearer kalıbı yalnızca token-şekilli değerleri (ör. uzunluk >= 20 ve rakam içeren) redakte eder; 'Bearer <sıradan sözcük>' düz metni korunur
- [x] #4 Hem korunan (yanlış-pozitif) hem redakte edilen (doğru-pozitif) durumlar için tests/test_security.py'ye testler eklenir
<!-- AC:END -->
