---
id: TASK-15
title: >-
  docs/event-schema.md'yi doğrulama düzeltmesi ve yeni gizlilik korumalarıyla
  hizala
status: Done
assignee: []
created_date: '2026-06-02 21:46'
labels:
  - docs
dependencies: []
modified_files:
  - docs/event-schema.md
priority: medium
ordinal: 15000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
İkinci tur kod review'da tespit edildi. README ve operations.md bu dalda güncellendi ama `docs/event-schema.md` (README'nin gizlilik beklentileri için işaret ettiği kanonik referans) sürüklendi.

(a) Korelasyon kuralı bölümü hâlâ şöyle diyor: \"A task_completed_claim can become completed_verified when a passed verification event has the same session_id and a compatible repo.\" Bu, bu dalın doğrulama düzeltmesinin (report.py `_matches_passed_verification`) bilerek KALDIRDIĞI eski/hatalı davranış. İki taraf da task_id taşıdığında paylaşılan session_id artık tek başına yeterli değil.

(b) \"Privacy rules\" bölümü yalnızca eski üç maddeyi listeliyor; bu dalda eklenen value-tabanlı redaction formatlarını (AWS/GitHub/GitLab/Slack/Google/JWT/Stripe/PEM/URL-credential), owner-only dosya izinlerini (0600/0700) ve `MAX_SEMANTIC_TEXT=4000` serbest-metin sınırını (`…[truncated]`) yansıtmıyor.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Korelasyon kuralı, iki taraf da task_id taşıdığında session_id eşleşmesinin task_id uyumuyla kapılandığını yansıtacak şekilde güncellenir (mevcut task_id kuralıyla çelişki giderilir)
- [x] #2 Privacy bölümü value-tabanlı sır tespitini, owner-only dosya/dizin izinlerini ve serbest-metin uzunluk sınırı + truncation davranışını belgeler
- [x] #3 Doküman koddaki güncel davranışla tutarlıdır; gerekirse test_docs.py invariant'ı güncellenir/eklenir
<!-- AC:END -->
