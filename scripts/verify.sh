#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP_ROOT="$(mktemp -d)"
trap 'rm -rf "$TMP_ROOT"' EXIT

export AGENT_JOURNAL_HOME="$TMP_ROOT/journal"
export PATH="$ROOT/.venv/bin:$PATH"

cd "$ROOT"

uv run pytest -q
uv run python -m compileall -q src

uv run agent-journal event --type agent_start --agent codex --task VERIFY-SMOKE --note "verify smoke"
uv run agent-journal event --type task_completed_claim --agent codex --task VERIFY-SMOKE --note "verify smoke completed"
uv run agent-journal report --today --print >/dev/null
uv run agent-journal status --today >/dev/null

mkdir -p "$TMP_ROOT/real"
cat > "$TMP_ROOT/real/codex" <<'SH'
#!/usr/bin/env sh
exit 7
SH
chmod +x "$TMP_ROOT/real/codex"

uv run python - <<PY
from agent_journal.install import install_wrappers
install_wrappers("$TMP_ROOT/wrapper-journal", {"codex": "$TMP_ROOT/real/codex"})
PY

set +e
AGENT_JOURNAL_HOME="$TMP_ROOT/wrapper-journal" "$TMP_ROOT/wrapper-journal/bin/codex"
WRAPPER_STATUS=$?
set -e
test "$WRAPPER_STATUS" -eq 7

uv run python - <<PY
from pathlib import Path
import glob
import json

paths = glob.glob("$TMP_ROOT/wrapper-journal/events/*.jsonl")
assert paths, "wrapper smoke did not write JSONL events"
events = [json.loads(line) for line in Path(paths[0]).read_text().splitlines()]
assert [event["event_type"] for event in events] == ["agent_start", "agent_end"]
assert events[-1]["exit_code"] == 7
PY

mkdir -p "$TMP_ROOT/repo"
git -C "$TMP_ROOT/repo" init >/dev/null
git -C "$TMP_ROOT/repo" config user.email test@example.com
git -C "$TMP_ROOT/repo" config user.name "Test User"
printf 'hello\n' > "$TMP_ROOT/repo/tracked.txt"
git -C "$TMP_ROOT/repo" add tracked.txt
git -C "$TMP_ROOT/repo" commit -m "add tracked" >/dev/null

(cd "$TMP_ROOT/repo" && AGENT_JOURNAL_HOME="$TMP_ROOT/git-journal" "$ROOT/.venv/bin/agent-journal" event --type git_commit --agent git >/dev/null)

uv run python - <<PY
from pathlib import Path
import glob
import json
import subprocess

head = subprocess.check_output(["git", "-C", "$TMP_ROOT/repo", "rev-parse", "HEAD"], text=True).strip()
path = glob.glob("$TMP_ROOT/git-journal/events/*.jsonl")[0]
event = json.loads(Path(path).read_text().splitlines()[0])
assert event["commit"] == head
assert event["files_changed"] == ["tracked.txt"]
PY

uv run python - <<'PY'
from agent_journal.mcp_server import create_mcp_server

server = create_mcp_server()
expected = {
    "journal_note",
    "journal_task_completed",
    "journal_task_blocked",
    "journal_daily_report",
}
assert expected.issubset(set(server._tool_manager._tools))
PY

echo "agent-journal verification passed"
