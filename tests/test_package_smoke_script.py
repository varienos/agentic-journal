from pathlib import Path


def test_package_smoke_script_declares_packaged_entrypoint_checks():
    script = Path("scripts/package-smoke.sh")

    assert script.exists()
    text = script.read_text()
    assert "uv build" in text
    assert "agent-journal\" --help" in text
    assert "agent-journal\" web --help" in text
    assert "agent-journal\" doctor" in text
    assert "session_summary" in text
    assert "journal_session_summary" in text
    assert "journal_task_completed" in text
    assert "PACKAGE-MCP-SESSION" in text
    assert "X-Agent-Journal-Token" in text
    assert "api_token=\"secret\"" in text
    assert "build_events_payload" in text
    assert "agent-journal-mcp" in text
    assert "guard session-end" in text
    assert "install wrappers" in text
    assert "install shell-profile" in text
    assert "install agent-instructions" in text
    assert "install git-hook" in text
    assert "AGENT_JOURNAL_HOME" in text
    assert "scripts/wrappers" in text
