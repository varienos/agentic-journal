---
id: TASK-17
title: schema_version migration yolunu tasarla
status: Done
assignee: []
created_date: '2026-06-02 21:46'
labels:
  - architecture
  - storage
dependencies: []
modified_files:
  - src/agent_journal/storage.py
  - src/agent_journal/events.py
  - src/agent_journal/config.py
  - docs/event-schema.md
priority: low
ordinal: 17000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
İkinci tur kod review'da açık (ertelenmiş) olarak işaretlendi. `events.py`'de `SCHEMA_VERSION = 1` hard-coded; SQLite tablosu `CREATE TABLE IF NOT EXISTS` ile sabit kolon kümesiyle oluşturuluyor, `PRAGMA user_version` izleme veya migration iskelesi yok, ve read-path `schema_version`'a göre dallanmıyor (`raw_json` okunup olduğu gibi tüketiliyor). Ayrıca `config.py` `DEFAULT_CONFIG`'deki `schema_version = 1`, kod sabitinden bağımsız ikinci bir kaynak.

v0.1.0'da tek şema sürümü olduğu için ertelenebilir; ancak ikinci bir event şekli geldiğinde forward/backward uyumluluk stratejisi gerekir.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 init_db'de PRAGMA user_version izleme ve user_version'a göre sıralı migration listesi eklenir
- [x] #2 Read-path, schema_version > SCHEMA_VERSION olan event'leri güvenli ele alır (skip veya uyarı; sessiz yanlış sınıflandırma yok)
- [x] #3 config DEFAULT_CONFIG'deki schema_version ile kod sabiti tek kaynağa bağlanır veya senkronizasyonu test edilir
- [x] #4 docs/event-schema.md, 'raw_json kaynak, denormalize kolonlar yeniden üretilebilir index' sözleşmesini belgeler
<!-- AC:END -->
