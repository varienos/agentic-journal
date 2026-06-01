# Agent Journal

[![CI](https://github.com/varienos/agent-journal/actions/workflows/ci.yml/badge.svg)](https://github.com/varienos/agent-journal/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.11%2B-2f6f9f)
![Local First](https://img.shields.io/badge/local--first-agent%20journal-126b5f)

Agent Journal is a local, observer-first activity journal for AI coding agents.
It records verifiable events from Codex, Claude Code, Gemini CLI, git commits,
and semantic MCP notes, then produces daily Markdown reports and a live local
dashboard.

Repository: [varienos/agent-journal](https://github.com/varienos/agent-journal)

## Why

Multiple agents can work on the same machine during the day. Agent Journal gives
them a shared append-only journal so you can review what happened at the end of
the day in a style close to git history:

- session starts and ends from wrapped agent commands
- explicit semantic notes from MCP tools
- claimed completed tasks, blocked tasks, and verification evidence
- git commit metadata and changed files
- risky sessions that ended without a semantic journal entry

The project is intentionally local-first. Runtime data is stored under
`~/.agent-journal` by default.

## Features

- Local CLI: `agent-journal`
- MCP server: `agent-journal-mcp`
- Agent wrappers for `codex`, `claude`, and `gemini`
- Session-end guard for missing semantic journal entries
- Git post-commit hook installer
- Daily Markdown report generation
- Live web dashboard with auto-refreshing event data
- JSONL and SQLite event storage

## Install

Clone the GitHub repo:

```bash
git clone https://github.com/varienos/agent-journal.git
cd agent-journal
uv sync --dev
```

From the source checkout:

```bash
uv run agent-journal --help
uv run agent-journal-mcp
```

Install globally with `uv tool`:

```bash
uv tool install .
agent-journal --help
```

Refresh an existing global install from this checkout:

```bash
uv tool install . --force --reinstall --refresh
```

## Quick Start

Install wrappers for local agent commands:

```bash
agent-journal install wrappers
```

Put the generated wrapper directory before the real agent binaries:

```bash
export PATH="$HOME/.agent-journal/bin:$PATH"
```

Record a manual semantic note:

```bash
agent-journal event --type semantic_note --agent codex --note "Reviewed README setup"
```

Generate today's report:

```bash
agent-journal report --today --print
```

Run the live dashboard:

```bash
agent-journal web --host 127.0.0.1 --port 8765 --today
```

Open `http://127.0.0.1:8765`.

## MCP Setup

Print ready-to-copy MCP snippets for Codex, Claude Code, and Gemini CLI:

```bash
agent-journal install mcp-snippets
```

The MCP command is:

```bash
agent-journal-mcp
```

Available MCP tools:

- `journal_note`
- `journal_task_completed`
- `journal_task_blocked`
- `journal_daily_report`

## Guarding Agent Sessions

The wrapper flow exports an `AGENT_JOURNAL_SESSION_ID`, writes `agent_start` and
`agent_end`, then runs:

```bash
agent-journal guard session-end --agent claude --session-id "$AGENT_JOURNAL_SESSION_ID"
```

If the session has no `semantic_note`, `task_completed_claim`, or
`task_blocked`, the guard writes a failed verification event with
`semantic.status = "journal_missing"`. Reports and the web dashboard show that
session under risky items so silent sessions are visible.

## Git Hook

Install the post-commit hook into a repo:

```bash
agent-journal install git-hook --repo .
```

The hook records commit metadata and changed files without blocking commits.

## Storage

Agent Journal writes events to both:

- `~/.agent-journal/events/YYYY-MM-DD.jsonl`
- `~/.agent-journal/agent-journal.db`

Reports are written to:

- `~/.agent-journal/reports/YYYY-MM-DD.md`

See [docs/event-schema.md](docs/event-schema.md) for event fields, correlation
rules, and privacy expectations.

## Development

Run tests:

```bash
uv run pytest -q
```

Run stabilization smoke checks:

```bash
scripts/verify.sh
scripts/package-smoke.sh
```

Operational details live in [docs/operations.md](docs/operations.md).

## Privacy

Agent Journal is designed to avoid prompt transcript capture by default. Event
writers should not log full file contents, prompt bodies, or secrets. Known API
keys, bearer tokens, passwords, and secret-looking values are redacted by the
event normalization path.
