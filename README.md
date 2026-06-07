# Agentic Journal

[![CI](https://github.com/varienos/agentic-journal/actions/workflows/ci.yml/badge.svg)](https://github.com/varienos/agentic-journal/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.11%2B-2f6f9f)
![License](https://img.shields.io/badge/license-MIT-2f6f9f)
![Local First](https://img.shields.io/badge/local--first-agent%20journal-126b5f)

Agentic Journal is a local, observer-first activity journal for AI coding agents.
It records verifiable events from Codex, Claude Code, Gemini CLI, git commits,
and semantic MCP notes, then produces daily Markdown reports and a live local
dashboard.

## Why

Multiple agents can work on the same machine during the day. Agentic Journal gives
them a shared append-only journal so you can review what happened at the end of
the day in a style close to git history:

- session starts and ends from wrapped agent commands
- explicit session summaries and semantic notes from MCP tools
- claimed completed tasks, blocked tasks, and verification evidence
- git commit metadata and changed files
- risky sessions that ended without a semantic journal entry

The project is intentionally local-first. Runtime data is stored under
`~/.agentic-journal` by default.

## Features

- Local CLI: `agentic-journal`
- MCP server: `agentic-journal-mcp`
- Agent wrappers for `codex`, `claude`, and `gemini`
- Session-end guard for missing semantic journal entries
- Required session summary events for useful end-of-day reports
- `doctor` setup audit for wrappers, MCP config hints, instructions, hooks, and daily coverage
- Provider-level coverage scores for Codex, Claude, and Gemini sessions
- Git post-commit hook installer
- Daily Markdown report generation with verified, claimed, observed, and risky evidence levels
- Live web dashboard with auto-refreshing event data and optional API token
- `CHANGELOG.md` plus tag-driven GitHub release automation
- JSONL and SQLite event storage

## Install

Clone the GitHub repo:

```bash
git clone https://github.com/varienos/agentic-journal.git
cd agentic-journal
uv sync --dev
```

From the source checkout:

```bash
uv run agentic-journal --help
uv run agentic-journal-mcp
```

Install globally with `uv tool`:

```bash
uv tool install .
agentic-journal --help
```

Refresh an existing global install from this checkout:

```bash
uv tool install . --force --reinstall --refresh
```

## Quick Start

Install wrappers for local agent commands:

```bash
agentic-journal install wrappers
```

Install the wrapper PATH block into both login and interactive zsh profiles:

```bash
agentic-journal install shell-profile
```

This writes the wrapper directory into `.zprofile` and `.zshrc`, so terminal
sessions and shell-based automations resolve `codex`, `claude`, and `gemini`
through Agentic Journal before the real binaries.

Install the global model instruction that requires end-of-session summaries:

```bash
agentic-journal install agent-instructions
```

This adds a marked Agentic Journal section to Codex, Claude, and Gemini global
instruction files. Agents should use the MCP `journal_session_summary` tool
before their final response or session exit.

For one-off shells, the equivalent PATH setup is:

```bash
export PATH="$HOME/.agentic-journal/bin:$PATH"
```

Record a manual semantic note:

```bash
agentic-journal event --type semantic_note --agent codex --note "Reviewed README setup"
```

Record the outcome of an agent session:

```bash
agentic-journal event --type session_summary --agent codex \
  --session-id "$AGENTIC_JOURNAL_SESSION_ID" \
  --task TASK-8 \
  --summary "Added session summary logging and dashboard grouping" \
  --outcome completed
```

Generate today's report:

```bash
agentic-journal report --today --print
```

Audit setup and provider coverage:

```bash
agentic-journal doctor --today
```

Run the live dashboard:

```bash
agentic-journal web --host 127.0.0.1 --port 8765 --today
```

Open `http://127.0.0.1:8765`.

## MCP Setup

Print ready-to-copy MCP snippets for Codex, Claude Code, and Gemini CLI:

```bash
agentic-journal install mcp-snippets
```

The MCP command is:

```bash
agentic-journal-mcp
```

Available MCP tools:

- `journal_note`
- `journal_session_summary`
- `journal_task_completed`
- `journal_task_blocked`
- `journal_daily_report`

MCP writes inherit `AGENTIC_JOURNAL_SESSION_ID` when present and attach the
current working directory plus git repo, branch, and commit context. This keeps
MCP outcome events correlated with wrapper `agent_start` / `agent_end` events
and prevents the session guard from reporting false missing-summary risks.

## Guarding Agent Sessions

The wrapper flow exports an `AGENTIC_JOURNAL_SESSION_ID`, writes `agent_start` and
`agent_end`, then runs:

```bash
agentic-journal guard session-end --agent claude --session-id "$AGENTIC_JOURNAL_SESSION_ID"
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
agentic-journal install git-hook --repo .
```

The hook records commit metadata and changed files without blocking commits. If
a `post-commit` hook already exists, the installer backs it up to
`post-commit.agentic-journal.bak` and chains it from the generated hook so the
existing hook still runs.

## Web Token

The dashboard binds to `127.0.0.1` by default. With no token, `/api/events` is
unauthenticated, so binding a non-loopback host without a token is refused. To
expose it more broadly, protect the JSON API with a token:

```bash
agentic-journal web --host 0.0.0.0 --port 8765 --today --token "$AGENTIC_JOURNAL_WEB_TOKEN"
```

Open the page with `?token=...`; the page strips the token from the URL and
sends it as the `X-Agent-Journal-Token` header for `/api/events` requests.

## Storage

Agentic Journal writes each event to both:

- `~/.agentic-journal/events/YYYY-MM-DD.jsonl`
- `~/.agentic-journal/agentic-journal.db`

Duplicate `event_id` writes are ignored in both SQLite and the JSONL mirror so
the two stores stay aligned.

Reports are written to:

- `~/.agentic-journal/reports/YYYY-MM-DD.md`

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

## Release

Releases use `CHANGELOG.md`, the project version in `pyproject.toml`, and
`vMAJOR.MINOR.PATCH` Git tags. Before tagging, run:

```bash
scripts/release-check.sh
```

Pushing a matching version tag starts the GitHub Release workflow, builds wheel
and source distributions, extracts notes from `CHANGELOG.md`, and publishes the
GitHub release.

Operational details live in [docs/operations.md](docs/operations.md).
Native hook examples live in [docs/native-hooks.md](docs/native-hooks.md).
The improvement roadmap lives in
[docs/improvement-plan.md](docs/improvement-plan.md).

## Privacy

Agentic Journal is designed to avoid prompt transcript capture by default. Event
writers should not log full file contents, prompt bodies, or secrets. Known API
keys, bearer tokens, passwords, and secret-looking values are redacted by the
event normalization path.

## License

Agentic Journal is released under the [MIT License](LICENSE).
