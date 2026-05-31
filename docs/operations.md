# Agent Journal Operations

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

For a single repo, copy `scripts/hooks/post-commit` to `.git/hooks/post-commit`
and make it executable. The hook records commit metadata without blocking commits.
If an existing hook is present, the installer writes a
`post-commit.agent-journal.bak` backup before replacing it.

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
- `journal_task_completed`
- `journal_task_blocked`
- `journal_daily_report`

MCP responses are intentionally short to preserve model context.

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
