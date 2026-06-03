---
id: TASK-18
title: write_event rollback'ını çift I/O hatasına karşı sertleştir
status: Done
assignee: []
created_date: '2026-06-02 21:46'
labels:
  - storage
  - robustness
dependencies: []
modified_files:
  - src/agent_journal/storage.py
  - tests/test_storage.py
priority: low
ordinal: 18000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
İkinci tur kod review'da tespit edildi (Low). `storage.write_event`, JSONL mirror append'i OSError verirse `delete_event` çağırıp re-raise ederek SQLite ile mirror'ı tutarlı tutuyor (tek-hata yolu doğru, test edildi). Ancak `delete_event`'in kendisi de başarısız olursa (ör. DB kilitli/disk dolu her ikisini de etkiler), orijinal append hatası maskelenir ve SQLite satırı sızar; sonraki retry `INSERT OR IGNORE` ile satırı duplicate görüp mirror append'i atlar, boşluk iyileşmez.

SQLite birincil okuma yolu olduğundan veri kaybedilmez (daha güvenli başarısızlık yönü); yalnızca dar çift-hata kenar durumu.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 delete_event başarısızlığı orijinal append OSError'ını maskelemez; kullanıcıya yükseltilen hata orijinal append hatasıdır
- [x] #2 Çift-hata durumunda davranış kodda yorumla belgelenir (SQLite birincil; mirror boşluğu kabul edilir)
- [x] #3 Mümkünse delete_event de başarısız olduğunda orijinal hatanın korunduğunu doğrulayan bir test eklenir
<!-- AC:END -->
