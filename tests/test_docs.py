from pathlib import Path


def test_native_hooks_doc_keeps_scope_and_links_guard_command():
    doc = Path("docs/native-hooks.md")
    readme = Path("README.md")

    assert doc.exists()
    text = doc.read_text(encoding="utf-8")
    assert "agentic-journal guard session-end" in text
    assert "Claude SessionEnd" in text
    assert "Gemini hook" in text
    assert "Codex" in text
    assert "Do not invent summaries" in text
    assert "transcript archive" in text
    assert "docs/native-hooks.md" in readme.read_text(encoding="utf-8")


def test_event_schema_docs_match_current_storage_and_privacy_contracts():
    text = Path("docs/event-schema.md").read_text(encoding="utf-8")

    assert "matching `session_id` is accepted only when task ids do not conflict" in text
    assert "`raw_json` is the source of truth" in text
    assert "denormalized index columns" in text
    assert "owner-only" in text
    assert "0600" in text
    assert "0700" in text
    assert "MAX_SEMANTIC_TEXT" in text
    assert "…[truncated]" in text
