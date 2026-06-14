# Agentic Journal Operations

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
- the affected command or module, for example `agentic-journal-mcp`

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

The smoke suite also checks MCP session context propagation, JSON API token
enforcement, wrapper guard fallback behavior, and packaged dashboard rendering.

Use the doctor command when setup behavior is unclear:

```bash
agentic-journal doctor --today
```

It reports wrapper PATH status, MCP configuration hints, global instruction
presence, daily session summary coverage, `journal_missing` counts, git hook
status, and dashboard/API token mode.

## Local And Global Install

Run from the source checkout without installing:

```bash
uv run agentic-journal --help
uv run agentic-journal report --today
uv run agentic-journal-mcp
```

Use editable install while developing the package:

```bash
uv pip install -e .
agentic-journal --help
agentic-journal install wrappers
```

Install globally with `uv tool` when the package is ready to use outside the
repo:

```bash
uv tool install .
agentic-journal --help
agentic-journal install wrappers
agentic-journal install shell-profile
agentic-journal install agent-instructions
```

Generated wrappers call `agentic-journal` through `PATH`. `install shell-profile`
adds the package bin directory to both `.zprofile` and `.zshrc` before the real
agent binaries. For one-off shells, the equivalent manual setup is:

```bash
export PATH="$HOME/.agentic-journal/bin:$PATH"
```

If `agentic-journal` is missing from `PATH`, a generated wrapper still runs the
real agent and preserves its exit code, but prints a warning and skips journal
event writes for that invocation.

## Session Summary Requirement

End-of-day reports depend on explicit session outcome records. A generic
`journal_note` is useful context, but it is not enough to explain what an agent
did in a session. Before final response or session end, agents should write:

```bash
agentic-journal event --type session_summary --agent codex \
  --session-id "$AGENTIC_JOURNAL_SESSION_ID" \
  --task TASK-8 \
  --summary "Added session summary logging and dashboard grouping" \
  --outcome completed
```

MCP clients should prefer `journal_session_summary` with the same semantic
fields. Supported outcomes are `completed`, `in_progress`, `blocked`, `no_work`,
and `unknown`.

MCP tools inherit `AGENTIC_JOURNAL_SESSION_ID` when present. They also attach the
current `cwd` and git repo, branch, and commit context from the MCP server
process. This is important: `journal_task_completed` and `journal_task_blocked`
only satisfy the guard for a wrapper session when they carry the same
`session_id` as that wrapper session.

## Journal Guard

Use the guard command at agent session end to make journaling auditable even when
the model does not voluntarily call an MCP tool:

```bash
agentic-journal guard session-end --agent claude --session-id "$AGENTIC_JOURNAL_SESSION_ID"
```

If the session already has a `session_summary`, `task_completed_claim`, or
`task_blocked` event, the guard is a no-op. If not, it writes one failed
verification event with `semantic.status = "journal_missing"`, which appears in
the Risky / Needs Review section of the daily report. The fallback event also
includes the current git `files_changed` list when available, giving objective
context without capturing transcripts or inventing summaries. Running the guard
multiple times for the same session is idempotent.

Generated wrappers export `AGENTIC_JOURNAL_SESSION_ID` and call the guard after
`agent_end`, so wrapped Codex, Claude, and Gemini sessions are automatically
flagged when they finish without a semantic journal entry.

For native agent hook systems, wire the same command into the stop/session-end
hook and pass the agent name used by that runtime. Keep MCP instructions in
place so models can still write richer semantic entries during or before final
responses.

See [native-hooks.md](native-hooks.md) for Claude SessionEnd, Gemini hook, and
Codex automation examples. Hooks should never invent completed work; they should
write a real `session_summary` only when a real outcome is available, otherwise
they should let the guard record `journal_missing`.

## Wrapper Setup

Install wrappers:

```bash
agentic-journal install wrappers
```

Install wrapper PATH setup for both login and interactive zsh sessions:

```bash
agentic-journal install shell-profile
```

This updates `.zprofile` and `.zshrc`. The `.zprofile` entry matters for
non-interactive login shells and scheduled automations; `.zshrc` covers normal
interactive terminals.

Install the global instruction block that tells each model to write a semantic
session summary before final response/session exit:

```bash
agentic-journal install agent-instructions
```

For one-off shells, put the generated bin directory before the real agent
binaries manually:

```bash
export PATH="$HOME/.agentic-journal/bin:$PATH"
```

## Git Hook Setup

Install into the current repo:

```bash
agentic-journal install git-hook --repo .
```

The hook records commit metadata without blocking commits. If an existing hook
is present, the installer writes a `post-commit.agentic-journal.bak` backup before
replacing it. The generated hook runs that backup first and preserves the
backup hook's exit code, while the Agentic Journal write remains best-effort.

## MCP Setup

Print Codex, Claude Code, and Gemini CLI config snippets:

```bash
agentic-journal install mcp-snippets
```

The MCP command is:

```bash
agentic-journal-mcp
```

The MVP semantic tools are:

- `journal_note`
- `journal_session_summary`
- `journal_task_completed`
- `journal_task_blocked`
- `journal_model_operation`
- `journal_daily_report`

MCP responses are intentionally short to preserve model context.

## Project-Local Mirrors

Use project-local mirrors when a repo or container needs a scoped view of the
global Agentic Journal. The global journal still receives every event first.
Enabled mirror configs receive a copy only when the event `cwd` or `repo` is the
configured project path or one of its children.

Create a project config. For Cortex:

```toml
# /Users/varienos/Landing/Repo/cortex/.agentic-journal.toml
[project]
id = "cortex"
path = "/Users/varienos/Landing/Repo/cortex"

[mirror]
enabled = true
path = "Agentbase/.agentic-journal"
```

Backfill existing history from the global journal:

```bash
agentic-journal mirror sync --config /Users/varienos/Landing/Repo/cortex/.agentic-journal.toml
```

Useful variants:

```bash
agentic-journal mirror sync --config /Users/varienos/Landing/Repo/cortex/.agentic-journal.toml --date 2026-06-13
agentic-journal mirror sync --config /Users/varienos/Landing/Repo/cortex/.agentic-journal.toml --from 2026-06-01 --to 2026-06-13
```

Confirm the mirror can be read:

```bash
agentic-journal status --root /Users/varienos/Landing/Repo/cortex/Agentbase/.agentic-journal --today
agentic-journal report --root /Users/varienos/Landing/Repo/cortex/Agentbase/.agentic-journal --today --print
```

Serve the existing web dashboard from a mirror root:

```bash
agentic-journal web --root /Users/varienos/Landing/Repo/cortex/Agentbase/.agentic-journal --host 127.0.0.1 --port 8765 --today
```

For containers, mount only the project mirror and point the consumer at that
path. Cortex uses:

```bash
AGENTIC_JOURNAL_PROJECT_HOME=/Agentbase/.agentic-journal
```

The mirror directory should be ignored by git:

```gitignore
Agentbase/.agentic-journal/
```

Project mirrors contain the same semantic summaries, notes, paths, branches,
commit hashes, and evidence metadata as the global journal. Treat a mounted
mirror as sensitive project telemetry.

## Release Checklist

Before tagging or sharing a build:

```bash
uv lock --check
uv run pytest -q
scripts/release-check.sh
scripts/verify.sh
scripts/package-smoke.sh
```

Confirm `pyproject.toml`, `src/agentic_journal/__init__.py`, and
`CHANGELOG.md` all describe the same version. `scripts/release-check.sh`
enforces that the `pyproject.toml` and `__init__.py` versions match, and verifies
the changelog has both an `[Unreleased]` section and a non-empty section for the
current version.

For a GitHub release:

```bash
VERSION=0.1.0
scripts/release-check.sh --tag "v$VERSION"
git tag "v$VERSION"
git push origin "v$VERSION"
```

The `Release` GitHub Actions workflow runs on `v*.*.*` tags. It validates
release metadata, runs tests plus smoke checks, builds wheel and source
distributions, extracts release notes from `CHANGELOG.md`, and publishes the
release with `gh release create --verify-tag`. Use `gh release view "v$VERSION"`
after the workflow completes to confirm the GitHub release exists.

## Daily Report

Generate today's report:

```bash
agentic-journal report --today
```

Cron example:

```bash
0 23 * * * agentic-journal report --today
```

Codex automation prompt:

```text
Generate today's Agentic Journal report by running `agentic-journal report --today`.
Summarize completed_verified, completed_claimed, in_progress, blocked, and risky items.
Do not modify project files.
```

## Live Web Dashboard

Run the local dashboard:

```bash
agentic-journal web --host 127.0.0.1 --port 8765 --today
```

Open `http://127.0.0.1:8765`. The page polls `/api/events` every two seconds
and shows summary counters, session summaries, latest raw events, notes, and
risky guard entries.

Use a fixed date when reviewing past work:

```bash
agentic-journal web --date 2026-06-01 --port 8765
```

The web server is local-only by default. With no token configured, `/api/events`
is unauthenticated, so the dashboard refuses to bind a non-loopback host
(anything other than `127.0.0.1`/`localhost`/`::1`) unless a token is set. To
expose it on your network, you must pass a token:

```bash
agentic-journal web --host 0.0.0.0 --port 8765 --today --token "$AGENTIC_JOURNAL_WEB_TOKEN"
```

Then open `http://host:8765/?token=...`. The page reads the token from the URL,
immediately strips it from the address bar/history, and sends it as the
`X-Agent-Journal-Token` header for `/api/events`. Requests with no token or the
wrong token receive `401`.

You can also set `AGENTIC_JOURNAL_WEB_TOKEN` instead of passing `--token`. Binding
a non-loopback host without either fails fast with an error rather than serving
the journal openly.
