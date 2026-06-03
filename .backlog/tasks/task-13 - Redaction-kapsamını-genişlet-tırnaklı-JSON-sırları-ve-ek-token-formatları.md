---
id: TASK-13
title: 'Redaction kapsamını genişlet: tırnaklı JSON sırları ve ek token formatları'
status: Done
assignee: []
created_date: '2026-06-02 21:46'
labels:
  - security
  - redaction
dependencies: []
modified_files:
  - src/agent_journal/security.py
  - tests/test_security.py
priority: medium
ordinal: 13000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
İkinci tur kod review'da tespit edildi. `src/agent_journal/security.py` bazı yaygın sır biçimlerini kaçırıyor.

Doğrulanan under-reach: serileştirilmiş JSON bir string alanına (ör. bir `command` veya `evidence` satırı) geldiğinde anahtar tırnaklıdır (`\"password\":\"...\"`), bu yüzden `ASSIGNMENT_SECRET_RE`'nin gerektirdiği `\\s*[:=]\\s*` ayracı keyword'ün hemen ardından gelmez ve eşleşme başarısız olur. Örnek: `redact_value({\"command\": 'curl -d {\"password\":\"hunter2plaintext\"}'})` → sır sızar.

Bilinen-eksik diğer formatlar (kabul edilir ama belgelenmeli/eklenmeli): Azure `AccountKey=`, `ssh-rsa AAAA...` (PEM başlıksız), hex/40-karakter genel API anahtarları, Twilio `AC...` SID, `npm_...` token.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Tırnaklı anahtar biçimleri redakte edilir: redact_value('{"password":"hunter2"}') ve '{"api_key": "..."}' (key ile ayraç arasında opsiyonel tırnak; quoted value desteği)
- [x] #2 En az şu ek formatlar için kalıp + test eklenir veya bilinçli kapsam-dışı olarak belgelenir: Azure AccountKey, ssh-rsa anahtarları, npm_ token, Twilio AC SID, uzun hex anahtarlar
- [x] #3 Eklenen her format için tests/test_security.py'de pozitif bir test bulunur
- [x] #4 ReDoS riski olmadan: eklenen kalıplar uzun girdilerde lineer kalır
<!-- AC:END -->
