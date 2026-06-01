# Native Agent Hooks

Agent Journal should stay local-first and observer-first. Native hooks are an
enforcement layer for sessions that do not go through the generated wrappers,
not a transcript archive and not a way to invent completed work.

## Rule

Do not invent summaries. A hook may write a `session_summary` only when the
agent or runtime provides a real session outcome. If no semantic outcome exists,
call the guard and let Agent Journal record `journal_missing`.

The common guard command is:

```bash
agent-journal guard session-end --agent "$AGENT" --session-id "$AGENT_JOURNAL_SESSION_ID"
```

The guard is idempotent. If the session already has a `session_summary`,
`task_completed_claim`, or `task_blocked`, it does nothing. Otherwise it writes
a failed verification event with `semantic.status = "journal_missing"`.

## Claude SessionEnd

For Claude Code, wire the guard into a `SessionEnd` hook only when the
environment carries the same `AGENT_JOURNAL_SESSION_ID` used by the wrapper or
MCP process.

Example command:

```bash
agent-journal guard session-end \
  --agent claude \
  --session-id "${AGENT_JOURNAL_SESSION_ID:-claude-native-session}"
```

If Claude has already called `journal_session_summary`, this stays quiet. If it
has not, the session appears in Risky / Needs Review with a missing semantic
summary diagnosis.

## Gemini hook

For Gemini CLI hook systems, use the same guard shape and keep the agent name
stable:

```bash
agent-journal guard session-end \
  --agent gemini \
  --session-id "${AGENT_JOURNAL_SESSION_ID:-gemini-native-session}"
```

Prefer the wrapper-provided `AGENT_JOURNAL_SESSION_ID`. A synthetic fallback
session id is useful only as a last-resort signal that the hook ran; it cannot
correlate with wrapper lifecycle events.

## Codex

Codex sessions should prefer the generated wrapper:

```bash
agent-journal install wrappers
agent-journal install shell-profile
```

If an automation starts Codex without the wrapper, add a final step that writes
a real `session_summary` when the automation knows the outcome, then call the
guard:

```bash
agent-journal event --type session_summary \
  --agent codex \
  --session-id "$AGENT_JOURNAL_SESSION_ID" \
  --summary "Implemented provider coverage and doctor diagnostics" \
  --outcome completed

agent-journal guard session-end \
  --agent codex \
  --session-id "$AGENT_JOURNAL_SESSION_ID"
```

Do not use this pattern to mark unknown work as completed. If the automation
cannot explain the outcome, skip the `session_summary` and let the guard record
the missing semantic entry.

## Verification

After installing hooks, run:

```bash
agent-journal doctor --today
agent-journal report --today --print
```

Look for provider coverage, missing summaries, and the hook status in the
doctor output. The daily report should keep verified, claimed, observed, and
risky work visibly separate.
