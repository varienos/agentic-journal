# Project-Local Journal Mirrors Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build configurable project-local Agentic Journal mirrors and connect the Cortex Deck panel to the Cortex mirror at `Agentbase/.agentic-journal`.

**Architecture:** Agentic Journal continues writing the global journal, then fans matching events out to enabled project mirrors discovered through `.agentic-journal.toml`. Mirror roots use the same SQLite/JSONL layout as the global journal, so existing payload/report readers can read a mirror root directly. Cortex reads its mounted mirror through a root-only Fastify endpoint and displays the payload in a read-only Deck page.

**Tech Stack:** Python 3.11 stdlib (`tomllib`, `sqlite3`, `argparse`, `pytest`), Agentic Journal local storage, Fastify/TypeScript, React/Vite, Vitest.

---

## File Structure

Agentic Journal:

- Create `src/agentic_journal/project_config.py`: project config parsing, discovery, path matching, mirror root resolution.
- Modify `src/agentic_journal/storage.py`: split low-level persistence from mirror fan-out; add mirror sync helper and idempotent insert counts.
- Modify `src/agentic_journal/cli.py`: add `--root` to read commands where useful and add `mirror sync`.
- Modify `src/agentic_journal/web.py`: expose root-based payloads unchanged.
- Modify `src/agentic_journal/report.py`: allow report generation from mirror roots through existing root parameter.
- Modify docs (`README.md`, `docs/event-schema.md`, `docs/operations.md`) for config, sync, container mount, and privacy notes.
- Tests: `tests/test_config.py`, `tests/test_storage.py`, `tests/test_cli.py`, `tests/test_web.py`, `tests/test_report.py`.

Cortex:

- Create `src/deck/deck-agentic-journal.ts`: JSONL mirror reader, classifier/payload builder, root-only route registration.
- Modify `src/config/env.ts`: add `agenticJournal.projectHome`, defaulting to `/Agentbase/.agentic-journal`.
- Modify `src/deck/deck-routes.ts`: register the Agentic Journal route with root-only auth.
- Modify `deck/src/api/hooks.ts`: add Agentic Journal payload types and hook.
- Create `deck/src/pages/AgenticJournalPage.tsx`: read-only panel view.
- Modify `deck/src/App.tsx` and `deck/src/components/Sidebar/index.tsx`: add root-only route/nav item.
- Modify Docker docs/compose as needed to show the mirror mount.
- Tests: add/extend Vitest backend route tests and lightweight frontend tests if existing test setup supports it.

## Chunk 1: Agentic Journal Mirror Config And Fan-Out

### Task 1: Config Parser And Matcher

**Files:**
- Create: `src/agentic_journal/project_config.py`
- Test: `tests/test_config.py`

- [ ] **Step 1: Write failing config tests**

Cover:

```python
def test_project_config_resolves_relative_mirror_path(tmp_path):
    project = tmp_path / "cortex"
    project.mkdir()
    (project / ".agentic-journal.toml").write_text(
        '[project]\nid = "cortex"\npath = "."\n\n[mirror]\nenabled = true\npath = "Agentbase/.agentic-journal"\n',
        encoding="utf-8",
    )

    config = load_project_config(project / ".agentic-journal.toml")

    assert config.project_path == project.resolve()
    assert config.mirror_root == project / "Agentbase" / ".agentic-journal"
```

Also cover disabled configs, exact match, child match, non-match, discovery from `cwd`, and discovery from `repo`.

- [ ] **Step 2: Run config tests to verify RED**

Run: `uv run pytest tests/test_config.py -q`

Expected: FAIL because `agentic_journal.project_config` does not exist.

- [ ] **Step 3: Implement config module**

Implement dataclass:

```python
@dataclass(frozen=True)
class ProjectMirrorConfig:
    config_path: Path
    project_id: str | None
    project_path: Path
    mirror_enabled: bool
    mirror_root: Path
```

Use `tomllib`, resolve `project.path` relative to config directory when not absolute, and resolve `mirror.path` relative to config directory when not absolute.

- [ ] **Step 4: Run config tests to verify GREEN**

Run: `uv run pytest tests/test_config.py -q`

Expected: PASS.

### Task 2: Mirror Fan-Out On Writes

**Files:**
- Modify: `src/agentic_journal/storage.py`
- Test: `tests/test_storage.py`

- [ ] **Step 1: Write failing storage tests**

Add tests for:

- global write still writes global root
- matching event writes mirror root
- non-matching event does not write mirror root
- duplicate writes remain idempotent
- mirror append failure does not fail the global write

- [ ] **Step 2: Run storage tests to verify RED**

Run: `uv run pytest tests/test_storage.py -q`

Expected: FAIL because write fan-out does not exist.

- [ ] **Step 3: Implement low-level persist helper and mirror fan-out**

Add an internal `_persist_event(root, event) -> tuple[Path, bool]` that performs the current SQLite+JSONL write and returns whether a new row was inserted. Keep public `write_event(root, event) -> Path` stable.

After a successful global insert, discover matching mirror configs and call `_persist_event(mirror_root, event)` for each, catching mirror exceptions and warning without failing the global write.

- [ ] **Step 4: Run storage tests to verify GREEN**

Run: `uv run pytest tests/test_storage.py -q`

Expected: PASS.

### Task 3: Mirror Sync CLI

**Files:**
- Modify: `src/agentic_journal/cli.py`
- Modify: `src/agentic_journal/storage.py`
- Test: `tests/test_cli.py`

- [ ] **Step 1: Write failing CLI tests**

Cover:

```python
exit_code = main([
    "mirror", "sync",
    "--root", str(global_root),
    "--config", str(project / ".agentic-journal.toml"),
])
```

Assert matching historical events land in `Agentbase/.agentic-journal`, non-matching events do not, and output includes scanned/matched/inserted/duplicate counts.

- [ ] **Step 2: Run CLI tests to verify RED**

Run: `uv run pytest tests/test_cli.py -q`

Expected: FAIL because `mirror sync` is not registered.

- [ ] **Step 3: Implement `mirror sync`**

Read global events with `read_events_for_date(root, None)` or the date filter, apply the same project matcher, persist to mirror root without fan-out, and print counts.

- [ ] **Step 4: Run CLI tests to verify GREEN**

Run: `uv run pytest tests/test_cli.py -q`

Expected: PASS.

### Task 4: Root-Selectable Read Commands And Docs

**Files:**
- Modify: `src/agentic_journal/cli.py`
- Modify: `README.md`
- Modify: `docs/event-schema.md`
- Modify: `docs/operations.md`
- Tests: `tests/test_cli.py`, `tests/test_web.py`, `tests/test_report.py`

- [ ] **Step 1: Write failing tests for `--root` reads**

Add tests that `status --root`, `report --root`, and `web --root` use the mirror root.

- [ ] **Step 2: Run tests to verify RED**

Run: `uv run pytest tests/test_cli.py tests/test_web.py tests/test_report.py -q`

Expected: FAIL until `--root` exists.

- [ ] **Step 3: Implement root selection**

Add optional `--root` to read commands and pass `Path(args.root).expanduser()` instead of `journal_root()` where supplied.

- [ ] **Step 4: Update docs**

Document Cortex config:

```toml
[project]
id = "cortex"
path = "/Users/varienos/Landing/Repo/cortex"

[mirror]
enabled = true
path = "Agentbase/.agentic-journal"
```

Document sync:

```bash
agentic-journal mirror sync --config /Users/varienos/Landing/Repo/cortex/.agentic-journal.toml
```

- [ ] **Step 5: Run focused Agentic Journal tests**

Run: `uv run pytest tests/test_config.py tests/test_storage.py tests/test_cli.py tests/test_web.py tests/test_report.py -q`

Expected: PASS.

## Chunk 2: Cortex Deck Mirror Reader

### Task 5: Backend Payload Reader And Route

**Files:**
- Create: `/Users/varienos/Landing/Repo/cortex/Codebase/Cortex/src/deck/deck-agentic-journal.ts`
- Modify: `/Users/varienos/Landing/Repo/cortex/Codebase/Cortex/src/config/env.ts`
- Modify: `/Users/varienos/Landing/Repo/cortex/Codebase/Cortex/src/deck/deck-routes.ts`
- Test: `/Users/varienos/Landing/Repo/cortex/Codebase/Cortex/test/deck-agentic-journal.test.ts`

- [ ] **Step 1: Write failing route tests**

Use a temp mirror root with `events/2026-06-13.jsonl`, login as root, and assert:

- no cookie returns 401
- non-root returns 403 if practical with existing helpers
- root returns payload with `summary`, `sessions`, `latestEvents`, `rawEventCount`
- `AGENTIC_JOURNAL_PROJECT_HOME` config path is respected

- [ ] **Step 2: Run route tests to verify RED**

Run: `npm test -- test/deck-agentic-journal.test.ts`

Expected: FAIL because route/module does not exist.

- [ ] **Step 3: Implement JSONL reader**

Read `events/${date}.jsonl`, skip corrupt lines, classify event buckets with the same key names as Agentic Journal payload where feasible, and return a stable panel payload. Do not require SQLite in Cortex.

- [ ] **Step 4: Register root-only route**

Register:

`GET /deck/api/agentic-journal/events?date=YYYY-MM-DD`

with Deck auth and `requireRootAccess`.

- [ ] **Step 5: Run route tests to verify GREEN**

Run: `npm test -- test/deck-agentic-journal.test.ts`

Expected: PASS.

### Task 6: Deck Page And Navigation

**Files:**
- Modify: `/Users/varienos/Landing/Repo/cortex/Codebase/Cortex/deck/src/api/hooks.ts`
- Create: `/Users/varienos/Landing/Repo/cortex/Codebase/Cortex/deck/src/pages/AgenticJournalPage.tsx`
- Modify: `/Users/varienos/Landing/Repo/cortex/Codebase/Cortex/deck/src/App.tsx`
- Modify: `/Users/varienos/Landing/Repo/cortex/Codebase/Cortex/deck/src/components/Sidebar/index.tsx`

- [ ] **Step 1: Add hook types and page**

Create `useAgenticJournalEvents(date)` and a page with date picker, summary metric cards, session list, risky/notes lists, and latest events table.

- [ ] **Step 2: Add route and nav**

Add root-only route `/agentic-journal` and sidebar label `Ajan Günlüğü`.

- [ ] **Step 3: Run Deck build/test**

Run:

```bash
npm run build
npm run build:deck
```

Expected: PASS.

### Task 7: Cortex Container And Docs

**Files:**
- Modify: `/Users/varienos/Landing/Repo/cortex/Codebase/Cortex/docker-compose.coolify.yml`
- Modify: `/Users/varienos/Landing/Repo/cortex/Codebase/Cortex/README.md`

- [ ] **Step 1: Document/mount project mirror**

Add `AGENTIC_JOURNAL_PROJECT_HOME=/Agentbase/.agentic-journal` and a commented or active bind/volume note for `Agentbase/.agentic-journal`.

- [ ] **Step 2: Verify compose text**

Run the existing Docker file tests if they cover compose:

```bash
npm test -- test/docker.files.test.ts
```

Expected: PASS or update assertions if they intentionally check env/mount lists.

## Chunk 3: Verification And Finalization

### Task 8: End-To-End Local Verification

**Files:**
- Runtime only

- [ ] **Step 1: Create Cortex config locally if missing**

Create `/Users/varienos/Landing/Repo/cortex/.agentic-journal.toml` with the agreed config only if the user wants the runtime file created. If not, document the command.

- [ ] **Step 2: Backfill from global journal**

Run:

```bash
uv run agentic-journal mirror sync --config /Users/varienos/Landing/Repo/cortex/.agentic-journal.toml
```

Expected: reports matched events for Cortex and creates `/Users/varienos/Landing/Repo/cortex/Agentbase/.agentic-journal`.

- [ ] **Step 3: Confirm mirror payload**

Run:

```bash
uv run agentic-journal status --root /Users/varienos/Landing/Repo/cortex/Agentbase/.agentic-journal --date 2026-06-13
```

Expected: raw events > 0 if global history for that date has Cortex events.

- [ ] **Step 4: Run full relevant tests**

Run:

```bash
uv run pytest -q
npm test --prefix /Users/varienos/Landing/Repo/cortex/Codebase/Cortex
npm run build --prefix /Users/varienos/Landing/Repo/cortex/Codebase/Cortex
npm run build:deck --prefix /Users/varienos/Landing/Repo/cortex/Codebase/Cortex
```

Expected: PASS.

- [ ] **Step 5: Update TASK-21 and final summary**

Check acceptance criteria, add final summary, and mark the task done through Backlog MCP.
