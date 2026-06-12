# Project-Local Journal Mirrors Design

## Goal

Show Agentic Journal entries by project, with Cortex as the first consumer. Cortex should be able to mount and read a project-local journal from `Agentbase/.agentic-journal` instead of requiring direct access to the host-level `~/.agentic-journal` store.

This design keeps the global journal as the source for machine-wide history, then adds configurable project mirrors for panel-friendly and container-friendly project views.

Backlog task: TASK-21.

## Decisions

- Project mirrors are opt-in through a project config file.
- For Cortex, the mirror target is `Agentbase/.agentic-journal`.
- The mirror path is still configurable for other projects.
- Matching is path-prefix based: an event belongs to a project when `repo` or `cwd` equals the configured project path, or is beneath it.
- Mirrors preserve the current event shape and storage layout so existing report/web payload builders can read either the global root or a project mirror root.
- A backfill/sync command is required so existing Cortex history can populate the new mirror.

Recommended Cortex config:

```toml
# /Users/varienos/Landing/Repo/cortex/.agentic-journal.toml
[project]
id = "cortex"
path = "/Users/varienos/Landing/Repo/cortex"

[mirror]
enabled = true
path = "Agentbase/.agentic-journal"
```

Relative mirror paths resolve from the config file directory, so the example writes to:

`/Users/varienos/Landing/Repo/cortex/Agentbase/.agentic-journal`

## Architecture

Agentic Journal keeps two write targets:

- Global root: `AGENTIC_JOURNAL_HOME` or `~/.agentic-journal`
- Project mirror root: discovered from `.agentic-journal.toml` and written only when the event matches the project path

The write path becomes:

1. Normalize the event.
2. Write it to the global journal exactly as today.
3. Discover applicable project mirror configs from the event `cwd` and `repo` ancestry.
4. For each enabled config whose `project.path` matches the event, write the same normalized event to the mirror root.
5. Deduplicate by `event_id`, using the same SQLite and JSONL idempotency behavior as the global store.

Mirror writes must not recursively trigger mirror discovery. The implementation should separate the low-level event persistence function from the high-level "write global and mirrors" function, or pass an internal flag that disables mirror fan-out for mirror writes.

## Config Discovery

For a normalized event, inspect candidates from:

- `cwd`, if present
- `repo`, if present

For each candidate path, walk upward toward filesystem root and look for `.agentic-journal.toml`. Read at most one config per directory and deduplicate configs by absolute path.

This finds the Cortex config for both existing event shapes:

- `cwd = /Users/varienos/Landing/Repo/cortex/Agentbase`, `repo = null`
- `cwd = /Users/varienos/Landing/Repo/cortex/Codebase/Cortex`, `repo = /Users/varienos/Landing/Repo/cortex/Codebase/Cortex`

Config validation:

- Missing config means no mirror.
- `mirror.enabled = false` means no mirror.
- `project.path` is required and resolves to an absolute path.
- `mirror.path` is required when enabled. Relative paths resolve from the config directory.
- Invalid configs should warn to stderr for CLI writes and avoid blocking the global write.

## Mirror Reads

No special event schema is needed for reading. A panel consumer can point existing daily payload builders at the mirror root:

```bash
agentic-journal web --root /Users/varienos/Landing/Repo/cortex/Agentbase/.agentic-journal --today
```

If the CLI does not currently expose `--root` for all relevant commands, add it where needed or expose a dedicated project command. The key requirement is that Cortex Deck can read the mirror root and receive the same payload shape used by the dashboard:

- summary counts
- classified buckets
- provider coverage
- session views
- latest events

For Cortex Deck, add a root-only backend endpoint that reads:

`AGENTIC_JOURNAL_PROJECT_HOME=/Agentbase/.agentic-journal`

or an equivalent configurable path. The frontend page should consume that endpoint rather than reaching into the filesystem directly.

## Backfill

Mirrors must support historical population from the global journal. Add a command shaped like:

```bash
agentic-journal mirror sync --config /Users/varienos/Landing/Repo/cortex/.agentic-journal.toml
```

Optional filters:

```bash
agentic-journal mirror sync --config ... --date 2026-06-13
agentic-journal mirror sync --config ... --from 2026-06-01 --to 2026-06-13
```

The sync command reads global events, applies the same project path matcher, writes matching events to the mirror, and reports counts for scanned, matched, inserted, and duplicate events.

## Error Handling

- Global writes remain primary and must not fail because a project mirror is misconfigured or temporarily unavailable.
- Mirror failures should be visible through stderr for CLI/wrapper contexts and through diagnostics.
- Duplicate events are ignored by `event_id`.
- Corrupt mirror JSONL lines are skipped with the same reader behavior as global JSONL.
- Future schema versions are skipped by readers, consistent with the global store.

## Security And Privacy

Project mirrors contain the same sensitive free-text fields as the global journal. They must use the same owner-only permissions:

- directories: `0700`
- files and SQLite sidecars: `0600`

Documentation must call out that mounting `Agentbase/.agentic-journal` into a container gives that container access to project agent summaries, notes, paths, branches, commit hashes, and evidence metadata.

The mirror directory should be ignored by git. For Cortex, add or document:

```gitignore
Agentbase/.agentic-journal/
```

## Testing

Agentic Journal tests:

- config discovery from `cwd`
- config discovery from `repo`
- relative mirror path resolution from config directory
- disabled mirror does not write
- exact project path match writes
- child path match writes
- non-matching event does not write
- global write still succeeds when mirror write fails
- duplicate mirror writes are idempotent
- sync command backfills historical matching events
- unfiltered daily report/dashboard behavior remains unchanged

Cortex tests:

- backend endpoint requires Deck/root auth
- endpoint reads the configured mirror root
- endpoint returns the expected daily payload shape
- frontend page renders loading, empty, error, and populated states

## Open Implementation Notes

- The config file can be created manually for Cortex first; a later installer command can scaffold it.
- Keep the first Cortex panel read-only.
- Do not store prompt transcripts or file contents in the mirror beyond what Agentic Journal already records.
- Avoid hardcoding `Agentbase`; only the Cortex example should use that path.
