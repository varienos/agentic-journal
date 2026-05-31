from agent_journal.install import (
    codex_mcp_snippet,
    generate_wrapper_script,
    install_git_hook,
    install_wrappers,
)


def test_generate_wrapper_script_points_to_real_binary():
    script = generate_wrapper_script("codex", "/usr/local/bin/codex")

    assert "AGENT_JOURNAL_AGENT=\"codex\"" in script
    assert "AGENT_JOURNAL_REAL_BIN=\"/usr/local/bin/codex\"" in script
    assert "scripts/wrappers" not in script
    assert "agent-journal event" in script


def test_install_wrappers_creates_agent_bins(tmp_path):
    real_bin = tmp_path / "real" / "codex"
    real_bin.parent.mkdir()
    real_bin.write_text("#!/usr/bin/env sh\nexit 0\n")
    real_bin.chmod(0o755)

    installed = install_wrappers(tmp_path / "journal", {"codex": str(real_bin)})

    assert installed == {"codex": tmp_path / "journal" / "bin" / "codex"}
    assert installed["codex"].exists()
    assert installed["codex"].stat().st_mode & 0o111


def test_install_git_hook_backs_up_existing_hook(tmp_path):
    repo = tmp_path / "repo"
    hooks = repo / ".git" / "hooks"
    hooks.mkdir(parents=True)
    existing = hooks / "post-commit"
    existing.write_text("existing\n")

    installed = install_git_hook(repo)

    assert installed == existing
    assert existing.read_text().startswith("#!/usr/bin/env sh")
    assert (hooks / "post-commit.agent-journal.bak").read_text() == "existing\n"


def test_codex_mcp_snippet_mentions_agent_journal_mcp():
    snippet = codex_mcp_snippet("/repo")

    assert "agent-journal-mcp" in snippet
    assert "/repo" in snippet
