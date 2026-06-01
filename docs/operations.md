# Agent Journal Operations

## Backlog Workflow

This repository tracks stabilization and follow-up work with Backlog.md. The
Backlog setup files are part of the repo state and should be committed:

- `.backlog/config.yml`
- `.backlog/tasks/*.md`
- `AGENTS.md`
- `CLAUDE.md`
- `GEMINI.md`

Use the Backlog MCP workflow when the client exposes it. If MCP resources or
tools are not available, use the CLI fallback:

```bash
backlog task list --plain
backlog search "agent journal wrapper" --plain
backlog search "evidence correlation" --plain
backlog task create "Concrete outcome title" --plain
backlog task edit TASK-1 --status "Done" --plain
```

Before opening a new task, run duplicate searches with at least:

- the feature or fix area, for example `wrapper`, `packaging`, `evidence`
- the user-visible symptom, for example `missing commit files`
- the affected command or module, for example `agent-journal-mcp`

When reporting task changes, include the task id, title, status, and the most
important files inspected or changed. Keep implementation work out of task
planning turns unless the user explicitly asks to execute the tasks.

## Stabilization Verification

Run the full stabilization smoke before closing backlog tasks or preparing a
release candidate:

```bash
scripts/verify.sh
scripts/package-smoke.sh
```

`scripts/verify.sh` runs the Python test suite, compiles `src`, writes a daily
report, checks session summary logging, checks wrapper event capture, verifies
git commit metadata, and confirms the MCP server exposes the expected journal
tools.

`scripts/package-smoke.sh` builds a wheel, installs it into a temporary venv,
checks packaged console scripts, verifies generated wrappers, and confirms the
MCP server can be created from the packaged environment.

## Local And Global Install

Run from the source checkout without installing:

```bash
uv run agent-journal --help
uv run agent-journal report --today
uv run agent-journal-mcp
```

Use editable install while developing the package:

```bash
uv pip install -e .
agent-journal --help
agent-journal install wrappers
```

Install globally with `uv tool` when the package is ready to use outside the
repo:

```bash
uv tool install .
agent-journal --help
agent-journal install wrappers
```

Generated wrappers call `agent-journal` through `PATH`. Add the package bin
directory to `PATH` before the real agent binaries:

```bash
export PATH="$HOME/.agent-journal/bin:$PATH"
```

If `agent-journal` is missing from `PATH`, a generated wrapper still runs the
real agent and preserves its exit code, but prints a warning and skips journal
event writes for that invocation.

## Session Summary Requirement

End-of-day reports depend on explicit session outcome records. A generic
`journal_note` is useful context, but it is not enough to explain what an agent
did in a session. Before final response or session end, agents should write:

```bash
agent-journal event --type session_summary --agent codex \
  --session-id "$AGENT_JOURNAL_SESSION_ID" \
  --task TASK-8 \
  --summary "Added session summary logging and dashboard grouping" \
  --outcome completed
```

MCP clients should prefer `journal_session_summary` with the same semantic
fields. Supported outcomes are `completed`, `in_progress`, `blocked`, `no_work`,
and `unknown`.

## Journal Guard

Use the guard command at agent session end to make journaling auditable even when
the model does not voluntarily call an MCP tool:

```bash
agent-journal guard session-end --agent claude --session-id "$AGENT_JOURNAL_SESSION_ID"
```

If the session already has a `session_summary`, `task_completed_claim`, or
`task_blocked` event, the guard is a no-op. If not, it writes one failed
verification event with `semantic.status = "journal_missing"`, which appears in
the Risky / Needs Review section of the daily report. Running the guard multiple
times for the same session is idempotent.

Generated wrappers export `AGENT_JOURNAL_SESSION_ID` and call the guard after
`agent_end`, so wrapped Codex, Claude, and Gemini sessions are automatically
flagged when they finish without a semantic journal entry.

For native agent hook systems, wire the same command into the stop/session-end
hook and pass the agent name used by that runtime. Keep MCP instructions in
place so models can still write richer semantic entries during or before final
responses.

## Wrapper Setup

Install wrappers:

```bash
agent-journal install wrappers
```

Then put the generated bin directory before the real agent binaries:

```bash
export PATH="$HOME/.agent-journal/bin:$PATH"
```

## Git Hook Setup

Install into the current repo:

```bash
agent-journal install git-hook --repo .
```

The hook records commit metadata without blocking commits. If an existing hook
is present, the installer writes a `post-commit.agent-journal.bak` backup before
replacing it.

## MCP Setup

Print Codex, Claude Code, and Gemini CLI config snippets:

```bash
agent-journal install mcp-snippets
```

The MCP command is:

```bash
agent-journal-mcp
```

The MVP semantic tools are:

- `journal_note`
- `journal_session_summary`
- `journal_task_completed`
- `journal_task_blocked`
- `journal_daily_report`

MCP responses are intentionally short to preserve model context.

## Release Checklist

Before tagging or sharing a build:

```bash
uv lock --check
uv run pytest -q
scripts/verify.sh
scripts/package-smoke.sh
```

Confirm `pyproject.toml` has the intended version and console scripts, and that
`uv.lock` is committed with dependency changes.

## Daily Report

Generate today's report:

```bash
agent-journal report --today
```

Cron example:

```bash
0 23 * * * agent-journal report --today
```

Codex automation prompt:

```text
Generate today's Agent Journal report by running `agent-journal report --today`.
Summarize completed_verified, completed_claimed, in_progress, blocked, and risky items.
Do not modify project files.
```

## Live Web Dashboard

Run the local dashboard:

```bash
agent-journal web --host 127.0.0.1 --port 8765 --today
```

Open `http://127.0.0.1:8765`. The page polls `/api/events` every two seconds
and shows summary counters, session summaries, latest raw events, notes, and
risky guard entries.

Use a fixed date when reviewing past work:

```bash
agent-journal web --date 2026-06-01 --port 8765
```

The web server is local-only by default and does not add authentication. Keep
`--host 127.0.0.1` unless you intentionally expose it on your network.
