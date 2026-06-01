import os
import subprocess

from agent_journal.install import (
    codex_mcp_snippet,
    generate_wrapper_script,
    install_agent_instructions,
    install_git_hook,
    install_shell_profile,
    install_wrappers,
)


def test_generate_wrapper_script_points_to_real_binary():
    script = generate_wrapper_script("codex", "/usr/local/bin/codex")

    assert "AGENT_JOURNAL_AGENT=\"codex\"" in script
    assert "AGENT_JOURNAL_REAL_BIN=\"/usr/local/bin/codex\"" in script
    assert "AGENT_JOURNAL_SESSION_ID" in script
    assert "scripts/wrappers" not in script
    assert "run_agent_journal event" in script
    assert "guard session-end" in script


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


def test_install_wrappers_skips_existing_wrapper_when_resolving_real_binary(tmp_path, monkeypatch):
    journal = tmp_path / "journal"
    wrapper_bin = journal / "bin"
    wrapper_bin.mkdir(parents=True)
    existing_wrapper = wrapper_bin / "codex"
    existing_wrapper.write_text("#!/usr/bin/env sh\nexit 0\n", encoding="utf-8")
    existing_wrapper.chmod(0o755)
    real_bin = tmp_path / "real" / "codex"
    real_bin.parent.mkdir()
    real_bin.write_text("#!/usr/bin/env sh\nexit 0\n", encoding="utf-8")
    real_bin.chmod(0o755)
    monkeypatch.setenv("PATH", f"{wrapper_bin}{os.pathsep}{real_bin.parent}")

    installed = install_wrappers(journal)

    assert installed == {"codex": wrapper_bin / "codex"}
    assert f'AGENT_JOURNAL_REAL_BIN="{real_bin}"' in installed["codex"].read_text(encoding="utf-8")


def test_install_shell_profile_adds_wrapper_path_to_login_and_interactive_profiles(tmp_path):
    home = tmp_path / "home"
    home.mkdir()
    journal_root = tmp_path / "journal"
    (home / ".zprofile").write_text('eval "$(/opt/homebrew/bin/brew shellenv)"\n', encoding="utf-8")
    (home / ".zshrc").write_text("# existing interactive config\n", encoding="utf-8")

    installed = install_shell_profile(journal_root, home=home)
    install_shell_profile(journal_root, home=home)

    assert installed == [home / ".zprofile", home / ".zshrc"]
    for profile in installed:
        text = profile.read_text(encoding="utf-8")
        assert text.count(">>> agent-journal wrappers >>>") == 1
        assert f'export PATH="{journal_root / "bin"}:$PATH"' in text


def test_install_agent_instructions_requires_session_summary_for_each_agent(tmp_path):
    instruction_files = {
        "codex": tmp_path / "AGENTS.md",
        "claude": tmp_path / "CLAUDE.md",
        "gemini": tmp_path / "GEMINI.md",
    }
    instruction_files["codex"].write_text("@existing\n", encoding="utf-8")

    installed = install_agent_instructions(instruction_files)
    install_agent_instructions(instruction_files)

    assert installed == instruction_files
    for path in instruction_files.values():
        text = path.read_text(encoding="utf-8")
        assert text.count("Agent Journal Session Reporting") == 1
        assert "journal_session_summary" in text
        assert "session_summary" in text
        assert "journal_note" in text


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


def test_install_git_hook_chains_existing_hook(tmp_path):
    repo = tmp_path / "repo"
    hooks = repo / ".git" / "hooks"
    hooks.mkdir(parents=True)
    existing = hooks / "post-commit"
    marker = tmp_path / "existing-ran"
    existing.write_text(f"#!/usr/bin/env sh\nprintf ran > {marker}\n", encoding="utf-8")
    existing.chmod(0o755)
    shim = tmp_path / "bin"
    shim.mkdir()
    agent_journal = shim / "agent-journal"
    agent_journal.write_text("#!/usr/bin/env sh\nexit 0\n", encoding="utf-8")
    agent_journal.chmod(0o755)

    installed = install_git_hook(repo)

    env = os.environ.copy()
    env["PATH"] = f"{shim}:{env['PATH']}"
    result = subprocess.run([str(installed)], cwd=repo, env=env, check=False)
    assert result.returncode == 0
    assert marker.read_text(encoding="utf-8") == "ran"


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
