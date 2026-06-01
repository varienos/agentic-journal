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
- explicit session summaries and semantic notes from MCP tools
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
- Required session summary events for useful end-of-day reports
- Git post-commit hook installer
- Daily Markdown report generation
- Live web dashboard with auto-refreshing event data and optional API token
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

Install the wrapper PATH block into both login and interactive zsh profiles:

```bash
agent-journal install shell-profile
```

This writes the wrapper directory into `.zprofile` and `.zshrc`, so terminal
sessions and shell-based automations resolve `codex`, `claude`, and `gemini`
through Agent Journal before the real binaries.

Install the global model instruction that requires end-of-session summaries:

```bash
agent-journal install agent-instructions
```

This adds a marked Agent Journal section to Codex, Claude, and Gemini global
instruction files. Agents should use the MCP `journal_session_summary` tool
before their final response or session exit.

For one-off shells, the equivalent PATH setup is:

```bash
export PATH="$HOME/.agent-journal/bin:$PATH"
```

Record a manual semantic note:

```bash
agent-journal event --type semantic_note --agent codex --note "Reviewed README setup"
```

Record the outcome of an agent session:

```bash
agent-journal event --type session_summary --agent codex \
  --session-id "$AGENT_JOURNAL_SESSION_ID" \
  --task TASK-8 \
  --summary "Added session summary logging and dashboard grouping" \
  --outcome completed
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
- `journal_session_summary`
- `journal_task_completed`
- `journal_task_blocked`
- `journal_daily_report`

MCP writes inherit `AGENT_JOURNAL_SESSION_ID` when present and attach the
current working directory plus git repo, branch, and commit context. This keeps
MCP outcome events correlated with wrapper `agent_start` / `agent_end` events
and prevents the session guard from reporting false missing-summary risks.

## Guarding Agent Sessions

The wrapper flow exports an `AGENT_JOURNAL_SESSION_ID`, writes `agent_start` and
`agent_end`, then runs:

```bash
agent-journal guard session-end --agent claude --session-id "$AGENT_JOURNAL_SESSION_ID"
```

Before final response or session end, agents should call
`journal_session_summary` with a concise outcome. If the session has no
`session_summary`, `task_completed_claim`, or `task_blocked`, the guard writes a
failed verification event with
`semantic.status = "journal_missing"`. Reports and the web dashboard show that
session under risky items so silent sessions are visible.

## Git Hook

Install the post-commit hook into a repo:

```bash
agent-journal install git-hook --repo .
```

The hook records commit metadata and changed files without blocking commits. If
a `post-commit` hook already exists, the installer backs it up to
`post-commit.agent-journal.bak` and chains it from the generated hook so the
existing hook still runs.

## Web Token

The dashboard binds to `127.0.0.1` by default. If you expose it more broadly,
protect the JSON API with a token:

```bash
agent-journal web --host 0.0.0.0 --port 8765 --today --token "$AGENT_JOURNAL_WEB_TOKEN"
```

Open the page with `?token=...`; the browser sends that value as the
`X-Agent-Journal-Token` header for `/api/events` requests.

## Storage

Agent Journal writes each event to both:

- `~/.agent-journal/events/YYYY-MM-DD.jsonl`
- `~/.agent-journal/agent-journal.db`

Duplicate `event_id` writes are ignored in both SQLite and the JSONL mirror so
the two stores stay aligned.

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
The improvement roadmap lives in
[docs/improvement-plan.md](docs/improvement-plan.md).

## Privacy

Agent Journal is designed to avoid prompt transcript capture by default. Event
writers should not log full file contents, prompt bodies, or secrets. Known API
keys, bearer tokens, passwords, and secret-looking values are redacted by the
event normalization path.
