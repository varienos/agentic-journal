#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP_ROOT="$(mktemp -d)"
trap 'rm -rf "$TMP_ROOT"' EXIT

export AGENTIC_JOURNAL_HOME="$TMP_ROOT/journal"
export PATH="$ROOT/.venv/bin:$PATH"

cd "$ROOT"

scripts/release-check.sh
uv run pytest -q
uv run python -m compileall -q src

uv run agentic-journal event --type agent_start --agent codex --session-id VERIFY-SESSION --task VERIFY-SMOKE --note "verify smoke"
uv run agentic-journal event --type session_summary --agent codex --session-id VERIFY-SESSION --task VERIFY-SMOKE --summary "verify smoke session summary" --outcome completed
uv run agentic-journal event --type task_completed_claim --agent codex --session-id VERIFY-SESSION --task VERIFY-SMOKE --note "verify smoke completed"
uv run agentic-journal guard session-end --agent codex --session-id VERIFY-SESSION >/dev/null
uv run agentic-journal event --type agent_start --agent claude --session-id VERIFY-MISSING --note "missing semantic smoke"
uv run agentic-journal guard session-end --agent claude --session-id VERIFY-MISSING >/dev/null
uv run agentic-journal guard session-end --agent claude --session-id VERIFY-MISSING >/dev/null
uv run agentic-journal report --today --print >/dev/null
uv run agentic-journal status --today >/dev/null
uv run agentic-journal web --help >/dev/null

mkdir -p "$TMP_ROOT/real"
cat > "$TMP_ROOT/real/codex" <<'SH'
#!/usr/bin/env sh
exit 7
SH
chmod +x "$TMP_ROOT/real/codex"

uv run python - <<PY
from agentic_journal.install import install_wrappers
install_wrappers("$TMP_ROOT/wrapper-journal", {"codex": "$TMP_ROOT/real/codex"})
PY

set +e
AGENTIC_JOURNAL_HOME="$TMP_ROOT/wrapper-journal" "$TMP_ROOT/wrapper-journal/bin/codex"
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
assert [event["event_type"] for event in events] == ["agent_start", "agent_end", "verification"]
assert events[1]["exit_code"] == 7
assert events[-1]["semantic"]["status"] == "journal_missing"
PY

mkdir -p "$TMP_ROOT/repo"
git -C "$TMP_ROOT/repo" init >/dev/null
git -C "$TMP_ROOT/repo" config user.email test@example.com
git -C "$TMP_ROOT/repo" config user.name "Test User"
printf 'hello\n' > "$TMP_ROOT/repo/tracked.txt"
git -C "$TMP_ROOT/repo" add tracked.txt
git -C "$TMP_ROOT/repo" commit -m "add tracked" >/dev/null

(cd "$TMP_ROOT/repo" && AGENTIC_JOURNAL_HOME="$TMP_ROOT/git-journal" "$ROOT/.venv/bin/agentic-journal" event --type git_commit --agent git >/dev/null)

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
from agentic_journal.mcp_server import create_mcp_server

server = create_mcp_server()
expected = {
    "journal_note",
    "journal_session_summary",
    "journal_task_completed",
    "journal_task_blocked",
    "journal_daily_report",
}
assert expected.issubset(set(server._tool_manager._tools))
PY

uv run python - <<PY
from agentic_journal.events import normalize_event
from agentic_journal.storage import write_event
from agentic_journal.web import create_web_handler
from http.server import ThreadingHTTPServer
import http.client
import json
import threading

root = "$TMP_ROOT/token-journal"
write_event(root, normalize_event({
    "event_type": "semantic_note",
    "agent": "codex",
    "semantic": {"note": "token smoke"},
}))
server = ThreadingHTTPServer(("127.0.0.1", 0), create_web_handler(root, "$(date +%F)", api_token="secret"))
thread = threading.Thread(target=server.serve_forever, daemon=True)
thread.start()
host, port = server.server_address
conn = http.client.HTTPConnection(host, port, timeout=5)
try:
    conn.request("GET", "/api/events")
    response = conn.getresponse()
    response.read()
    assert response.status == 401
    conn.request("GET", "/api/events", headers={"X-Agent-Journal-Token": "secret"})
    response = conn.getresponse()
    body = response.read()
    assert response.status == 200
    assert json.loads(body)["raw_event_count"] == 1
finally:
    conn.close()
    server.shutdown()
    server.server_close()
PY

echo "agentic-journal verification passed"
