from pathlib import Path


def test_package_smoke_script_declares_packaged_entrypoint_checks():
    script = Path("scripts/package-smoke.sh")

    assert script.exists()
    text = script.read_text()
    assert "uv build" in text
    assert "agent-journal\" --help" in text
    assert "agent-journal\" web --help" in text
    assert "build_events_payload" in text
    assert "agent-journal-mcp" in text
    assert "guard session-end" in text
    assert "install wrappers" in text
    assert "install git-hook" in text
    assert "AGENT_JOURNAL_HOME" in text
    assert "scripts/wrappers" in text
