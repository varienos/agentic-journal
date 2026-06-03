---
id: TASK-16
title: >-
  Eksik test kapsamını ekle: günlük rapor paylaşımı, web bind çıkış kodu, izin
  bitleri
status: Done
assignee: []
created_date: '2026-06-02 21:46'
labels:
  - testing
dependencies: []
modified_files:
  - tests/test_cli.py
  - tests/test_mcp_server.py
  - tests/test_storage.py
  - tests/test_security.py
  - tests/test_report.py
priority: medium
ordinal: 16000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
İkinci tur kod review'da tespit edildi. Bu dalda eklenen/değişen birkaç kod yolu producer üzerinden test edilmiyor; bir regresyon mevcut testleri geçirir.

- `report.render_daily_report`/`resolve_report_date` doğrudan test edilmiyor; CLI report testi \"Provider Coverage\" iddiası içermiyor ve MCP `journal_daily_report` aracının hiç testi yok (yalnızca kaydı kontrol ediliyor). Düzeltilen \"today.md\" + eksik provider coverage hatası şu an yakalanmazdı.
- `web.py` fail-closed bind'in CLI bağlantısı (`run_web_server`'daki `ensure_safe_binding` çağrısı ve `_handle_web`'deki try/except ValueError → return 2) test edilmiyor.
- `config.secure_dir`/`secure_file` gerçek izin bitleri (0700/0600) hiçbir yerde doğrulanmıyor (güvenlik özelliği).
- `storage._date_from_ts` path-traversal guard'ı ve `SECRET_KEY_RE`'nin yeni alternatifleri (passwd, private_key) ile bare Bearer value-pattern'i test edilmiyor.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 render_daily_report(tmp_path, None) gerçek ISO tarih döndürür ve markdown 'Provider Coverage' içerir; MCP journal_daily_report yazılan dosya gerçek-tarihli (today.md değil) ve 'Provider Coverage' içerir
- [x] #2 main(['web','--host','0.0.0.0']) token yokken 2 döner ve stderr 'non-loopback' içerir
- [x] #3 secure_dir 0o700, secure_file 0o600 bitlerini doğrulayan test (Windows'ta skip edilebilir)
- [x] #4 _date_from_ts('../../x') ValueError yükseltir testi
- [x] #5 SECRET_KEY_RE'nin passwd/private_key anahtar eşleşmesi ve bare 'Bearer <token>' value-pattern'i için testler
<!-- AC:END -->
