from __future__ import annotations

import subprocess
from pathlib import Path


def resolve_git_hook_path(repo: str | Path, hook_name: str = "post-commit") -> Path:
    repo_path = Path(repo).expanduser()
    try:
        output = subprocess.check_output(
            ["git", "rev-parse", "--git-path", f"hooks/{hook_name}"],
            cwd=repo_path,
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
    except (FileNotFoundError, subprocess.CalledProcessError):
        return repo_path / ".git" / "hooks" / hook_name

    hook_path = Path(output).expanduser()
    if hook_path.is_absolute():
        return hook_path
    return repo_path / hook_path
