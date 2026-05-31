from __future__ import annotations

import shutil
from pathlib import Path


WRAPPER_BODY = """#!/usr/bin/env sh
set -u
AGENT_JOURNAL_AGENT="{agent}"
AGENT_JOURNAL_REAL_BIN="{real_bin}"
export AGENT_JOURNAL_AGENT
export AGENT_JOURNAL_REAL_BIN
AGENT="$AGENT_JOURNAL_AGENT"
SESSION_ID="$(date +%s)-$$"
START_TS="$(date +%s)"

journal_event() {{
  agent-journal event "$@" >/dev/null 2>&1 || true
}}

journal_event --type agent_start --agent "$AGENT" --session-id "$SESSION_ID" --command "$AGENT"
"$AGENT_JOURNAL_REAL_BIN" "$@"
STATUS=$?
END_TS="$(date +%s)"
DURATION_MS=$(( (END_TS - START_TS) * 1000 ))
journal_event --type agent_end --agent "$AGENT" --session-id "$SESSION_ID" --command "$AGENT" --exit-code "$STATUS" --duration-ms "$DURATION_MS"
exit "$STATUS"
"""


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def wrapper_source() -> Path:
    return project_root() / "scripts" / "wrappers" / "agent-journal-wrapper.sh"


def generate_wrapper_script(agent: str, real_bin: str, wrapper: str | None = None) -> str:
    return WRAPPER_BODY.format(agent=agent, real_bin=real_bin)


def install_wrappers(root: str | Path, real_bins: dict[str, str] | None = None) -> dict[str, Path]:
    root_path = Path(root).expanduser()
    bin_dir = root_path / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    resolved = real_bins or {}
    if not resolved:
        for agent in ("codex", "claude", "gemini"):
            found = shutil.which(agent)
            if found and not str(found).startswith(str(bin_dir)):
                resolved[agent] = found

    installed: dict[str, Path] = {}
    for agent, real_bin in resolved.items():
        target = bin_dir / agent
        target.write_text(generate_wrapper_script(agent, real_bin), encoding="utf-8")
        target.chmod(0o755)
        installed[agent] = target
    return installed


def install_git_hook(repo: str | Path) -> Path:
    repo_path = Path(repo).expanduser()
    hooks_dir = repo_path / ".git" / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)
    target = hooks_dir / "post-commit"
    if target.exists():
        backup = hooks_dir / "post-commit.agent-journal.bak"
        if not backup.exists():
            backup.write_text(target.read_text(encoding="utf-8"), encoding="utf-8")
    source = project_root() / "scripts" / "hooks" / "post-commit"
    target.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
    target.chmod(0o755)
    return target


def codex_mcp_snippet(project_path: str | Path | None = None) -> str:
    cwd = Path(project_path).expanduser() if project_path else project_root()
    return f"""[mcp_servers.agent_journal]
command = "agent-journal-mcp"
args = []
cwd = "{cwd}"
startup_timeout_sec = 30
tool_timeout_sec = 120
"""


def claude_mcp_snippet(project_path: str | Path | None = None) -> str:
    cwd = Path(project_path).expanduser() if project_path else project_root()
    return f"""{{
  "mcpServers": {{
    "agent-journal": {{
      "command": "agent-journal-mcp",
      "args": [],
      "cwd": "{cwd}"
    }}
  }}
}}
"""


def gemini_mcp_snippet(project_path: str | Path | None = None) -> str:
    cwd = Path(project_path).expanduser() if project_path else project_root()
    return f"""{{
  "mcpServers": {{
    "agent-journal": {{
      "command": "agent-journal-mcp",
      "args": [],
      "cwd": "{cwd}"
    }}
  }}
}}
"""
