import subprocess

from agent_journal.git_context import get_git_context


def test_get_git_context_returns_none_outside_repo(tmp_path):
    ctx = get_git_context(tmp_path)

    assert ctx["repo"] is None
    assert ctx["branch"] is None
    assert ctx["commit"] is None
    assert ctx["dirty"] is False
    assert ctx["changed_files"] == []


def test_get_git_context_reads_repo_details(tmp_path):
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, stdout=subprocess.DEVNULL)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=tmp_path, check=True)
    (tmp_path / "README.md").write_text("hello\n")
    subprocess.run(["git", "add", "README.md"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-m", "initial"], cwd=tmp_path, check=True, stdout=subprocess.DEVNULL)
    (tmp_path / "changed.txt").write_text("changed\n")

    ctx = get_git_context(tmp_path)

    assert ctx["repo"] == str(tmp_path)
    assert ctx["commit"]
    assert ctx["dirty"] is True
    assert "changed.txt" in ctx["changed_files"]


def test_get_git_context_preserves_first_character_for_modified_tracked_file(tmp_path):
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, stdout=subprocess.DEVNULL)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=tmp_path, check=True)
    (tmp_path / "README.md").write_text("hello\n")
    subprocess.run(["git", "add", "README.md"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-m", "initial"], cwd=tmp_path, check=True, stdout=subprocess.DEVNULL)
    (tmp_path / "README.md").write_text("changed\n")

    ctx = get_git_context(tmp_path)

    assert "README.md" in ctx["changed_files"]
    assert "EADME.md" not in ctx["changed_files"]
