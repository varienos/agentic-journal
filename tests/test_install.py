import os
import subprocess

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


def test_generated_wrapper_warns_when_agent_journal_is_missing(tmp_path):
    real_bin = tmp_path / "real" / "codex"
    real_bin.parent.mkdir()
    real_bin.write_text("#!/usr/bin/env sh\nexit 7\n")
    real_bin.chmod(0o755)
    wrapper = tmp_path / "codex"
    wrapper.write_text(generate_wrapper_script("codex", str(real_bin)), encoding="utf-8")
    wrapper.chmod(0o755)
    env = os.environ.copy()
    env["AGENT_JOURNAL_HOME"] = str(tmp_path / "journal")
    env["PATH"] = "/usr/bin:/bin"

    result = subprocess.run([str(wrapper)], env=env, capture_output=True, text=True, check=False)

    assert result.returncode == 7
    assert "agent-journal command not found" in result.stderr


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


def test_install_git_hook_does_not_depend_on_source_tree(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    monkeypatch.setattr("agent_journal.install.project_root", lambda: tmp_path / "missing-source")

    installed = install_git_hook(repo)

    assert installed == repo / ".git" / "hooks" / "post-commit"
    assert "agent-journal event --type git_commit" in installed.read_text()


def test_codex_mcp_snippet_mentions_agent_journal_mcp():
    snippet = codex_mcp_snippet("/repo")

    assert "agent-journal-mcp" in snippet
    assert "/repo" in snippet
