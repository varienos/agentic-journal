from pathlib import Path


def test_native_hooks_doc_keeps_scope_and_links_guard_command():
    doc = Path("docs/native-hooks.md")
    readme = Path("README.md")

    assert doc.exists()
    text = doc.read_text(encoding="utf-8")
    assert "agent-journal guard session-end" in text
    assert "Claude SessionEnd" in text
    assert "Gemini hook" in text
    assert "Codex" in text
    assert "Do not invent summaries" in text
    assert "transcript archive" in text
    assert "docs/native-hooks.md" in readme.read_text(encoding="utf-8")
