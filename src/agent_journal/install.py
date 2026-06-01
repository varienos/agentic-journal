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
AGENT_JOURNAL_SESSION_ID="$SESSION_ID"
export AGENT_JOURNAL_SESSION_ID
START_TS="$(date +%s)"
AGENT_JOURNAL_WARNED=0

run_agent_journal() {{
  if command -v agent-journal >/dev/null 2>&1; then
    agent-journal "$@" >/dev/null 2>&1 || true
  elif [ "$AGENT_JOURNAL_WARNED" -eq 0 ]; then
    echo "agent-journal command not found; skipping journal command. Add the package bin directory to PATH." >&2
    AGENT_JOURNAL_WARNED=1
  fi
}}

journal_event() {{
  run_agent_journal event "$@"
}}

journal_event --type agent_start --agent "$AGENT" --session-id "$SESSION_ID" --command "$AGENT"
"$AGENT_JOURNAL_REAL_BIN" "$@"
STATUS=$?
END_TS="$(date +%s)"
DURATION_MS=$(( (END_TS - START_TS) * 1000 ))
journal_event --type agent_end --agent "$AGENT" --session-id "$SESSION_ID" --command "$AGENT" --exit-code "$STATUS" --duration-ms "$DURATION_MS"
run_agent_journal guard session-end --agent "$AGENT" --session-id "$SESSION_ID"
exit "$STATUS"
"""

GIT_HOOK_BODY = """#!/usr/bin/env sh
STATUS=0
BACKUP="$(dirname "$0")/post-commit.agent-journal.bak"
if [ -x "$BACKUP" ]; then
  "$BACKUP" "$@" || STATUS=$?
elif [ -f "$BACKUP" ]; then
  /usr/bin/env sh "$BACKUP" "$@" || STATUS=$?
fi
agent-journal event --type git_commit --agent "${AGENT_JOURNAL_AGENT:-git}" >/dev/null 2>&1 || true
exit "$STATUS"
"""


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def generate_wrapper_script(agent: str, real_bin: str) -> str:
    return WRAPPER_BODY.format(agent=agent, real_bin=real_bin)


def install_wrappers(root: str | Path, real_bins: dict[str, str] | None = None) -> dict[str, Path]:
    root_path = Path(root).expanduser()
    bin_dir = root_path / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    resolved = real_bins or {}
    if not resolved:
        bin_dir_resolved = bin_dir.resolve()
        for agent in ("codex", "claude", "gemini"):
            found = shutil.which(agent)
            if found and not Path(found).resolve().is_relative_to(bin_dir_resolved):
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
            backup.write_bytes(target.read_bytes())
            backup.chmod(target.stat().st_mode)
    target.write_text(GIT_HOOK_BODY, encoding="utf-8")
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
