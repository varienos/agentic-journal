from pathlib import Path


def test_verify_script_declares_ci_smoke_checks():
    script = Path("scripts/verify.sh")

    assert script.exists()
    text = script.read_text()
    assert "uv run pytest -q" in text
    assert "python -m compileall -q src" in text
    assert "AGENT_JOURNAL_HOME" in text
    assert "agent-journal report" in text
    assert "agent-journal web --help" in text
    assert "guard session-end" in text
    assert "install_wrappers" in text
    assert "create_mcp_server" in text
