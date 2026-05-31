from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any


def _git(cwd: Path, *args: str) -> str | None:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=cwd,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    return result.stdout.rstrip("\n")


def get_git_context(cwd: str | Path) -> dict[str, Any]:
    path = Path(cwd)
    repo = _git(path, "rev-parse", "--show-toplevel")
    if not repo:
        return {
            "repo": None,
            "branch": None,
            "commit": None,
            "dirty": False,
            "changed_files": [],
        }

    branch = _git(path, "branch", "--show-current")
    commit = _git(path, "rev-parse", "HEAD")
    status = _git(path, "status", "--porcelain") or ""
    changed_files = []
    for line in status.splitlines():
        if len(line) > 3:
            changed_files.append(line[3:].strip())

    return {
        "repo": repo,
        "branch": branch or None,
        "commit": commit,
        "dirty": bool(changed_files),
        "changed_files": changed_files,
    }


def get_head_commit_files(cwd: str | Path) -> list[str]:
    output = _git(Path(cwd), "show", "--pretty=", "--name-only", "HEAD")
    if not output:
        return []
    return [line.strip() for line in output.splitlines() if line.strip()]
