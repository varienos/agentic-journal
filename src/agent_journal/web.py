from __future__ import annotations

import json
from datetime import date
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from agent_journal.report import classify_daily_work
from agent_journal.storage import read_events_for_date

CLASSIFIED_KEYS = (
    "completed_verified",
    "completed_claimed",
    "in_progress",
    "blocked",
    "notes",
    "risky",
)


def _event_label(event: dict[str, Any]) -> str:
    semantic = event.get("semantic") or {}
    bits = []
    task_id = semantic.get("task_id") or event.get("task_id")
    note = semantic.get("note") or semantic.get("reason")
    commit = event.get("commit")
    if task_id:
        bits.append(str(task_id))
    if commit:
        bits.append(str(commit)[:12])
    if note:
        bits.append(str(note))
    bits.append(f"agent={event.get('agent') or 'unknown'}")
    bits.append(f"repo={event.get('repo') or event.get('cwd') or 'unknown'}")
    return " - ".join(bits)


def _event_view(event: dict[str, Any]) -> dict[str, Any]:
    semantic = event.get("semantic") or {}
    evidence = event.get("evidence") or {}
    return {
        "event_id": event.get("event_id"),
        "ts": event.get("ts"),
        "event_type": event.get("event_type"),
        "agent": event.get("agent"),
        "session_id": event.get("session_id"),
        "repo": event.get("repo") or event.get("cwd"),
        "branch": event.get("branch"),
        "commit": event.get("commit"),
        "exit_code": event.get("exit_code"),
        "semantic_status": semantic.get("status"),
        "note": semantic.get("note") or semantic.get("reason"),
        "verification_status": evidence.get("verification_status"),
        "label": _event_label(event),
        "semantic": semantic,
        "evidence": evidence,
    }


def build_events_payload(root: str | Path | None, report_date: str, limit: int = 200) -> dict[str, Any]:
    events = read_events_for_date(root, report_date)
    classified = classify_daily_work(events)
    latest = [_event_view(event) for event in reversed(events[-limit:])]
    return {
        "date": report_date,
        "raw_event_count": len(events),
        "summary": {key: len(classified.get(key, [])) for key in CLASSIFIED_KEYS},
        "classified": {key: classified.get(key, []) for key in CLASSIFIED_KEYS},
        "latest_events": latest,
    }


def render_dashboard_html(default_date: date | None = None, refresh_ms: int = 2000) -> str:
    selected_date = (default_date or date.today()).isoformat()
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Agent Journal Live</title>
  <style>
    :root {{
      --bg: #f6f7f9;
      --panel: #ffffff;
      --text: #17202a;
      --muted: #697386;
      --line: #d8dee8;
      --accent: #126b5f;
      --warn: #a6421c;
      --ok: #236b2e;
      --shadow: 0 1px 2px rgba(16, 24, 40, 0.08);
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: var(--bg);
      color: var(--text);
      letter-spacing: 0;
    }}
    header {{
      background: var(--panel);
      border-bottom: 1px solid var(--line);
      padding: 18px 24px;
      position: sticky;
      top: 0;
      z-index: 5;
    }}
    .topbar {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      max-width: 1280px;
      margin: 0 auto;
    }}
    h1 {{
      font-size: 22px;
      line-height: 1.2;
      margin: 0;
      font-weight: 700;
    }}
    .controls {{
      display: flex;
      align-items: center;
      gap: 10px;
      flex-wrap: wrap;
    }}
    input, button {{
      height: 36px;
      border: 1px solid var(--line);
      border-radius: 6px;
      background: var(--panel);
      color: var(--text);
      padding: 0 10px;
      font: inherit;
    }}
    button {{
      cursor: pointer;
      background: var(--accent);
      border-color: var(--accent);
      color: white;
      font-weight: 650;
    }}
    main {{
      max-width: 1280px;
      margin: 0 auto;
      padding: 20px 24px 36px;
    }}
    .status {{
      display: flex;
      align-items: center;
      gap: 8px;
      color: var(--muted);
      font-size: 13px;
      min-height: 20px;
    }}
    .dot {{
      width: 9px;
      height: 9px;
      border-radius: 50%;
      background: var(--ok);
      display: inline-block;
    }}
    .summary {{
      display: grid;
      grid-template-columns: repeat(6, minmax(130px, 1fr));
      gap: 10px;
      margin: 18px 0;
    }}
    .metric {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 13px;
      box-shadow: var(--shadow);
      min-height: 78px;
    }}
    .metric span {{
      display: block;
      color: var(--muted);
      font-size: 12px;
      line-height: 1.3;
      text-transform: uppercase;
    }}
    .metric strong {{
      display: block;
      font-size: 28px;
      line-height: 1;
      margin-top: 9px;
    }}
    .layout {{
      display: grid;
      grid-template-columns: minmax(0, 1fr) 360px;
      gap: 16px;
      align-items: start;
    }}
    section {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      box-shadow: var(--shadow);
      overflow: hidden;
    }}
    section h2 {{
      margin: 0;
      padding: 13px 14px;
      border-bottom: 1px solid var(--line);
      font-size: 15px;
      line-height: 1.3;
    }}
    .event-list, .bucket-list {{
      display: grid;
      gap: 0;
    }}
    .event {{
      display: grid;
      grid-template-columns: 170px 120px minmax(0, 1fr);
      gap: 12px;
      padding: 11px 14px;
      border-bottom: 1px solid var(--line);
      min-height: 58px;
    }}
    .event:last-child, .bucket-item:last-child {{ border-bottom: 0; }}
    .time, .kind, .bucket-meta {{
      color: var(--muted);
      font-size: 12px;
      line-height: 1.4;
    }}
    .kind {{
      font-weight: 700;
      color: var(--accent);
      overflow-wrap: anywhere;
    }}
    .kind.risky {{ color: var(--warn); }}
    .label {{
      font-size: 13px;
      line-height: 1.45;
      overflow-wrap: anywhere;
    }}
    .side {{
      display: grid;
      gap: 16px;
    }}
    .bucket-item {{
      padding: 11px 14px;
      border-bottom: 1px solid var(--line);
      font-size: 13px;
      line-height: 1.45;
      overflow-wrap: anywhere;
    }}
    .empty {{
      padding: 16px 14px;
      color: var(--muted);
      font-size: 13px;
    }}
    @media (max-width: 920px) {{
      .topbar, .controls {{ align-items: stretch; }}
      .topbar {{ flex-direction: column; }}
      .summary {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
      .layout {{ grid-template-columns: 1fr; }}
      .event {{ grid-template-columns: 1fr; gap: 4px; }}
    }}
  </style>
</head>
<body>
  <header>
    <div class="topbar">
      <div>
        <h1>Agent Journal Live</h1>
        <div class="status"><span class="dot"></span><span id="status">Waiting for events</span></div>
      </div>
      <div class="controls">
        <input id="date" type="date" value="{selected_date}" aria-label="Report date">
        <button id="refresh" type="button">Refresh</button>
      </div>
    </div>
  </header>
  <main>
    <div class="summary">
      <div class="metric"><span>Verified</span><strong id="m-completed_verified">0</strong></div>
      <div class="metric"><span>Claimed</span><strong id="m-completed_claimed">0</strong></div>
      <div class="metric"><span>In Progress</span><strong id="m-in_progress">0</strong></div>
      <div class="metric"><span>Blocked</span><strong id="m-blocked">0</strong></div>
      <div class="metric"><span>Notes</span><strong id="m-notes">0</strong></div>
      <div class="metric"><span>Risky</span><strong id="m-risky">0</strong></div>
    </div>
    <div class="layout">
      <section>
        <h2>Latest Events</h2>
        <div id="events" class="event-list"></div>
      </section>
      <div class="side">
        <section data-section="notes">
          <h2>Notes</h2>
          <div id="notes" class="bucket-list"></div>
        </section>
        <section data-section="risky">
          <h2>Risky / Needs Review</h2>
          <div id="risky" class="bucket-list"></div>
        </section>
      </div>
    </div>
  </main>
  <script>
    const refreshMs = {int(refresh_ms)};
    const keys = ["completed_verified", "completed_claimed", "in_progress", "blocked", "notes", "risky"];
    const statusEl = document.getElementById("status");
    const dateEl = document.getElementById("date");
    const eventsEl = document.getElementById("events");

    function text(value) {{
      return value === null || value === undefined || value === "" ? "-" : String(value);
    }}

    function renderBucket(id, items) {{
      const root = document.getElementById(id);
      root.innerHTML = "";
      if (!items || items.length === 0) {{
        const empty = document.createElement("div");
        empty.className = "empty";
        empty.textContent = "No entries";
        root.appendChild(empty);
        return;
      }}
      items.forEach((item) => {{
        const row = document.createElement("div");
        row.className = "bucket-item";
        row.textContent = item;
        root.appendChild(row);
      }});
    }}

    function renderEvents(events) {{
      eventsEl.innerHTML = "";
      if (!events || events.length === 0) {{
        const empty = document.createElement("div");
        empty.className = "empty";
        empty.textContent = "No events for this date";
        eventsEl.appendChild(empty);
        return;
      }}
      events.forEach((event) => {{
        const row = document.createElement("div");
        row.className = "event";
        const time = document.createElement("div");
        time.className = "time";
        time.textContent = text(event.ts);
        const kind = document.createElement("div");
        kind.className = "kind" + (event.event_type === "verification" && event.verification_status === "failed" ? " risky" : "");
        kind.textContent = text(event.event_type);
        const label = document.createElement("div");
        label.className = "label";
        label.textContent = text(event.label);
        row.append(time, kind, label);
        eventsEl.appendChild(row);
      }});
    }}

    async function loadEvents() {{
      const date = dateEl.value;
      const response = await fetch(`/api/events?date=${{encodeURIComponent(date)}}`, {{ cache: "no-store" }});
      if (!response.ok) throw new Error(`HTTP ${{response.status}}`);
      const payload = await response.json();
      keys.forEach((key) => {{
        document.getElementById(`m-${{key}}`).textContent = payload.summary[key] || 0;
      }});
      renderEvents(payload.latest_events);
      renderBucket("notes", payload.classified.notes);
      renderBucket("risky", payload.classified.risky);
      statusEl.textContent = `${{payload.raw_event_count}} raw events · updated ${{new Date().toLocaleTimeString()}}`;
    }}

    document.getElementById("refresh").addEventListener("click", () => loadEvents().catch((error) => {{
      statusEl.textContent = `Refresh failed: ${{error.message}}`;
    }}));
    loadEvents().catch((error) => {{ statusEl.textContent = `Refresh failed: ${{error.message}}`; }});
    setInterval(() => loadEvents().catch(() => {{}}), refreshMs);
  </script>
</body>
</html>"""


def _write_response(handler: BaseHTTPRequestHandler, status: HTTPStatus, body: bytes, content_type: str) -> None:
    handler.send_response(status)
    handler.send_header("Content-Type", content_type)
    handler.send_header("Content-Length", str(len(body)))
    handler.send_header("Cache-Control", "no-store")
    handler.end_headers()
    handler.wfile.write(body)


def create_web_handler(root: str | Path | None, default_date: str, refresh_ms: int = 2000):
    class AgentJournalHandler(BaseHTTPRequestHandler):
        def log_message(self, format: str, *args: Any) -> None:
            return

        def do_GET(self) -> None:
            parsed = urlparse(self.path)
            if parsed.path in ("/", "/index.html"):
                html = render_dashboard_html(date.fromisoformat(default_date), refresh_ms=refresh_ms)
                _write_response(self, HTTPStatus.OK, html.encode("utf-8"), "text/html; charset=utf-8")
                return
            if parsed.path == "/api/events":
                params = parse_qs(parsed.query)
                report_date = params.get("date", [default_date])[0] or default_date
                payload = build_events_payload(root, report_date)
                body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
                _write_response(self, HTTPStatus.OK, body, "application/json; charset=utf-8")
                return
            _write_response(self, HTTPStatus.NOT_FOUND, b'{"error":"not found"}', "application/json; charset=utf-8")

    return AgentJournalHandler


def run_web_server(
    root: str | Path | None,
    host: str,
    port: int,
    default_date: str,
    refresh_ms: int = 2000,
) -> None:
    server = ThreadingHTTPServer((host, port), create_web_handler(root, default_date, refresh_ms))
    actual_host, actual_port = server.server_address
    print(f"Agent Journal web: http://{actual_host}:{actual_port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Stopping Agent Journal web")
