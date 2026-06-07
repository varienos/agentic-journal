from __future__ import annotations

import os
from pathlib import Path

from agentic_journal.git_hooks import resolve_git_hook_path


SHELL_PROFILE_BEGIN = "# >>> agentic-journal wrappers >>>"
SHELL_PROFILE_END = "# <<< agentic-journal wrappers <<<"
AGENT_INSTRUCTIONS_BEGIN = "<!-- >>> agentic-journal instructions >>> -->"
AGENT_INSTRUCTIONS_END = "<!-- <<< agentic-journal instructions <<< -->"

WRAPPER_BODY = """#!/usr/bin/env sh
set -u
AGENTIC_JOURNAL_AGENT="{agent}"
AGENTIC_JOURNAL_REAL_BIN="{real_bin}"
export AGENTIC_JOURNAL_AGENT
export AGENTIC_JOURNAL_REAL_BIN
AGENT="$AGENTIC_JOURNAL_AGENT"
SESSION_ID="$(date +%s)-$$"
AGENTIC_JOURNAL_SESSION_ID="$SESSION_ID"
export AGENTIC_JOURNAL_SESSION_ID
START_TS="$(date +%s)"
AGENTIC_JOURNAL_WARNED=0

run_agentic_journal() {{
  if command -v agentic-journal >/dev/null 2>&1; then
    agentic-journal "$@" >/dev/null 2>&1 || true
  elif [ "$AGENTIC_JOURNAL_WARNED" -eq 0 ]; then
    echo "agentic-journal command not found; skipping journal command. Add the package bin directory to PATH." >&2
    AGENTIC_JOURNAL_WARNED=1
  fi
}}

journal_event() {{
  run_agentic_journal event "$@"
}}

journal_event --type agent_start --agent "$AGENT" --session-id "$SESSION_ID" --command "$AGENT"
"$AGENTIC_JOURNAL_REAL_BIN" "$@"
STATUS=$?
END_TS="$(date +%s)"
DURATION_MS=$(( (END_TS - START_TS) * 1000 ))
journal_event --type agent_end --agent "$AGENT" --session-id "$SESSION_ID" --command "$AGENT" --exit-code "$STATUS" --duration-ms "$DURATION_MS"
run_agentic_journal guard session-end --agent "$AGENT" --session-id "$SESSION_ID"
exit "$STATUS"
"""

GIT_HOOK_BODY = """#!/usr/bin/env sh
STATUS=0
BACKUP="$(dirname "$0")/post-commit.agentic-journal.bak"
if [ -x "$BACKUP" ]; then
  "$BACKUP" "$@" || STATUS=$?
elif [ -f "$BACKUP" ]; then
  /usr/bin/env sh "$BACKUP" "$@" || STATUS=$?
fi
agentic-journal event --type git_commit --agent "${AGENTIC_JOURNAL_AGENT:-git}" >/dev/null 2>&1 || true
exit "$STATUS"
"""


def _upsert_marked_block(path: Path, begin: str, end: str, block: str) -> None:
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    normalized_block = block.strip() + "\n"
    if begin in text and end in text and text.index(begin) < text.index(end):
        start = text.rfind("\n", 0, text.index(begin)) + 1
        end_index = text.index(end, text.index(begin)) + len(end)
        next_newline = text.find("\n", end_index)
        if next_newline != -1:
            end_index = next_newline + 1
        prefix = text[:start].rstrip()
        suffix = text[end_index:].lstrip("\n").rstrip()
        parts = [part for part in (prefix, normalized_block.strip(), suffix) if part]
        updated = "\n\n".join(parts) + "\n"
    else:
        updated = (text.rstrip() + "\n\n" if text.strip() else "") + normalized_block
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(updated, encoding="utf-8")


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def generate_wrapper_script(agent: str, real_bin: str) -> str:
    return WRAPPER_BODY.format(agent=agent, real_bin=real_bin)


def _which_outside_dir(command: str, excluded_dir: Path) -> str | None:
    excluded = excluded_dir.resolve()
    for entry in os.environ.get("PATH", "").split(os.pathsep):
        directory = Path(entry or ".").expanduser()
        candidate = directory / command
        if not candidate.is_file() or not os.access(candidate, os.X_OK):
            continue
        if candidate.resolve().is_relative_to(excluded):
            continue
        return str(candidate)
    return None


def install_wrappers(root: str | Path, real_bins: dict[str, str] | None = None) -> dict[str, Path]:
    root_path = Path(root).expanduser()
    bin_dir = root_path / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    resolved = real_bins or {}
    if not resolved:
        bin_dir_resolved = bin_dir.resolve()
        for agent in ("codex", "claude", "gemini"):
            found = _which_outside_dir(agent, bin_dir_resolved)
            if found:
                resolved[agent] = found

    installed: dict[str, Path] = {}
    for agent, real_bin in resolved.items():
        target = bin_dir / agent
        target.write_text(generate_wrapper_script(agent, real_bin), encoding="utf-8")
        target.chmod(0o755)
        installed[agent] = target
    return installed


def shell_profile_block(root: str | Path) -> str:
    bin_dir = Path(root).expanduser() / "bin"
    return f"""{SHELL_PROFILE_BEGIN}
# Agentic Journal wrappers: keep before real agent binaries, including login shells used by automations.
if [ -d "{bin_dir}" ]; then
  export PATH="{bin_dir}:$PATH"
fi
{SHELL_PROFILE_END}
"""


def install_shell_profile(
    root: str | Path,
    *,
    home: str | Path | None = None,
    profiles: list[str | Path] | None = None,
) -> list[Path]:
    home_path = Path(home).expanduser() if home else Path.home()
    targets = (
        [Path(profile).expanduser() for profile in profiles]
        if profiles
        else [home_path / ".zprofile", home_path / ".zshrc"]
    )
    block = shell_profile_block(root)
    for target in targets:
        _upsert_marked_block(target, SHELL_PROFILE_BEGIN, SHELL_PROFILE_END, block)
    return targets


def agent_instructions_block() -> str:
    return f"""{AGENT_INSTRUCTIONS_BEGIN}
## Agentic Journal Session Reporting

- At the end of every meaningful work session, before the final response or session exit, write one semantic Agentic Journal entry.
- Prefer the MCP tool `journal_session_summary` when available.
- Include the current agent name, task id when known, outcome (`completed`, `in_progress`, `blocked`, `no_work`, or `unknown`), and a concise summary of what changed, what was verified, and what remains.
- `journal_note` is only for incidental notes; it does not satisfy end-of-session reporting.
- If MCP is unavailable, run `agentic-journal event --type session_summary --agent <agent> --session-id "$AGENTIC_JOURNAL_SESSION_ID" --summary "<work summary>" --outcome <outcome>`.
{AGENT_INSTRUCTIONS_END}
"""


def default_agent_instruction_files() -> dict[str, Path]:
    home = Path.home()
    return {
        "codex": home / ".codex" / "AGENTS.md",
        "claude": home / ".claude" / "CLAUDE.md",
        "gemini": home / ".gemini" / "GEMINI.md",
    }


def install_agent_instructions(
    instruction_files: dict[str, str | Path] | None = None,
) -> dict[str, Path]:
    targets = {
        agent: Path(path).expanduser()
        for agent, path in (instruction_files or default_agent_instruction_files()).items()
    }
    block = agent_instructions_block()
    for target in targets.values():
        _upsert_marked_block(target, AGENT_INSTRUCTIONS_BEGIN, AGENT_INSTRUCTIONS_END, block)
    return targets


def install_git_hook(repo: str | Path) -> Path:
    target = resolve_git_hook_path(repo)
    hooks_dir = target.parent
    hooks_dir.mkdir(parents=True, exist_ok=True)
    if target.exists():
        backup = hooks_dir / "post-commit.agentic-journal.bak"
        if not backup.exists():
            backup.write_bytes(target.read_bytes())
            backup.chmod(target.stat().st_mode)
    target.write_text(GIT_HOOK_BODY, encoding="utf-8")
    target.chmod(0o755)
    return target


def codex_mcp_snippet(project_path: str | Path | None = None) -> str:
    cwd = Path(project_path).expanduser() if project_path else project_root()
    return f"""[mcp_servers.agentic_journal]
command = "agentic-journal-mcp"
args = []
cwd = "{cwd}"
startup_timeout_sec = 30
tool_timeout_sec = 120
"""


def claude_mcp_snippet(project_path: str | Path | None = None) -> str:
    cwd = Path(project_path).expanduser() if project_path else project_root()
    return f"""{{
  "mcpServers": {{
    "agentic-journal": {{
      "command": "agentic-journal-mcp",
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
    "agentic-journal": {{
      "command": "agentic-journal-mcp",
      "args": [],
      "cwd": "{cwd}"
    }}
  }}
}}
"""
