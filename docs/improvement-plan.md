# Agentic Journal Improvement Plan

## Scope

Agentic Journal should stay local-first and observer-first. The project should not
capture full prompt transcripts by default, should not become a general task
manager, and should avoid pretending that an agent completed work without a
semantic journal entry or verification evidence.

The near-term goal is simple: make end-of-day reporting trustworthy for Codex,
Claude, and Gemini sessions on the same machine.

## Current Baseline

- Wrapper lifecycle events capture `agent_start`, `agent_end`, and missing
  semantic-summary risks.
- MCP tools provide semantic entries, with `journal_session_summary` as the
  preferred end-of-session event.
- Global setup can install shell profile PATH blocks and model instructions.
- Reports and the live dashboard separate verified work, claimed work, session
  summaries, notes, blocked items, and risky sessions.

## Review Findings

- The system is reliable at detecting silent sessions, but it still depends on
  each model following the global instruction to produce meaningful summaries.
- The wrapper guard should remain conservative. A missing summary is a risk
  signal, not something the system should auto-fill with invented content.
- Native provider hooks are the next enforcement layer. They can call the same
  guard command and, where a transcript is available, optionally ask the model
  to summarize the session before exit.
- The README should continue to describe the happy path, while operational docs
  should document failure modes and recovery steps.

## Prioritized Plan

1. Provider hook hardening
   - Add documented Claude, Gemini, and Codex stop/session-end hook examples.
   - Keep the hook output as `session_summary` when a real summary is available
     and `journal_missing` when it is not.
   - Add smoke tests for generated hook snippets where the provider format is
     stable enough to test locally.

2. Daily report quality
   - Add a `doctor` or `audit` command that reports wrapper PATH status, MCP
     status hints, global instruction presence, and recent missing-summary
     sessions.
   - Show provider-level summary coverage percentages for the selected day.
   - Keep raw event counts visible so generated summaries cannot hide weak data.

3. Dashboard usability
   - Add provider filters and session outcome filters.
   - Highlight sessions that have `agent_end` plus `journal_missing`.
   - Keep the dashboard local-only by default, with token protection documented
     for exposed deployments.

4. Installation clarity
   - Keep `install wrappers`, `install shell-profile`, and
     `install agent-instructions` as separate commands for transparency.
   - Consider an `install doctor` command before adding any one-shot installer.
   - Avoid mutating MCP client configs automatically until each provider's
     config behavior is stable and reversible.

5. Verification and evidence
   - Preserve the distinction between `completed_claimed` and
     `completed_verified`.
   - Add more correlation tests for session id, task id, repo, and commit
     evidence.
   - Keep privacy tests around redaction and avoid transcript capture in default
     flows.

## Non-Goals

- No remote SaaS dashboard in the core project.
- No default transcript capture.
- No automatic invention of summaries for old sessions.
- No broad task-management replacement for Backlog, git history, or provider
  native histories.
