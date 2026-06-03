---
id: TASK-14
title: 'Tekilleştirme refactor''larını tamamla: event-tipi setleri ve label/session_key'
status: Done
assignee: []
created_date: '2026-06-02 21:46'
labels:
  - refactor
  - maintainability
dependencies: []
modified_files:
  - src/agent_journal/events.py
  - src/agent_journal/web.py
  - src/agent_journal/diagnostics.py
  - src/agent_journal/report.py
  - tests/test_events.py
priority: medium
ordinal: 14000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
İkinci tur kod review'da tespit edildi. Önceki turda başlatılan tek-kaynak (single source of truth) refactor'u tam tamamlanmadı.

- `src/agent_journal/events.py`'deki yorum, event-tipi setlerinin web ve diagnostics dâhil merkezileştiğini iddia ediyor; ancak `web.py:build_session_views` hâlâ inline `{\"agent_start\",\"agent_end\",\"session_summary\"}` literal'ini kullanıyor (üçüncü, ayrı bir set), `diagnostics.py` hâlâ bare `\"journal_missing\"` string'i ile karşılaştırıyor. Yeni bir lifecycle event tipi eklenince web filtresi sessizce sürükleniyor.
- `web.py`, `report._label`'ı private isimle import ediyor (artık üç ayrı tüketici tarafından kullanılan bir yardımcı; private statüsünü aştı).
- `web._session_key` ile `report._session_key` farklı sözleşmelere sahip (biri session yoksa None döner; diğeri event_id'ye fallback eder) — aynı isim, farklı davranış: bakım tuzağı.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 web.py ve diagnostics.py event-tipi setleri/durum string'leri için events.py sabitlerini kullanır (web'in {agent_start,agent_end,session_summary} kombinasyonu kasıtlıysa events.py'de isimlendirilmiş bir sabit olur); VEYA events.py yorumu gerçek migrasyon durumuna göre düzeltilir
- [x] #2 report._label ve _task_id public isimlere terfi edilir ve web.py bunları import eder
- [x] #3 web._session_key'in farklı sözleşmesi yeniden adlandırma (ör. _display_session_key) veya iki tarafta yorum ile netleştirilir
- [x] #4 SESSION_OUTCOME_EVENT_TYPES <= ALLOWED_EVENT_TYPES ve SESSION_EVENT_TYPES <= ALLOWED_EVENT_TYPES invariant'ını doğrulayan bir test eklenir
<!-- AC:END -->
