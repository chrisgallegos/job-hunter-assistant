#!/usr/bin/env python3
"""Job Hunter Toolkit — thin local server.

Serves the interactive app (index.html) and gives it hands: the scraper
runs on demand and the watchlist is editable from the browser. The MD
files in private/ stay the single source of truth — this server is a
view over them, never a replacement.

Local only: binds 127.0.0.1, serves nothing to your network, sends
nothing anywhere. Standard library only.

Usage:
  python3 serve.py            # http://localhost:8765
  python3 serve.py --port N
"""

import argparse
import json
import os
import sys
import webbrowser
from datetime import date
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "scraper"))
import scrape  # noqa: E402  (scraper/scrape.py)


def with_verdicts(latest):
    """Fold AI verdicts (private/jobs/verdicts.json — written by your
    AI collaborator from the review queue) into the postings payload."""
    if not scrape.VERDICTS_FILE.exists():
        return latest
    try:
        verdicts = json.loads(scrape.VERDICTS_FILE.read_text())
    except json.JSONDecodeError:
        return latest
    for posting in latest.get("postings", []):
        verdict = verdicts.get(posting.get("url"))
        if isinstance(verdict, dict) and "delta" in verdict:
            posting["verdict"] = {
                "delta": max(-3, min(3, int(verdict["delta"]))),
                "why": str(verdict.get("why", ""))[:200],
            }
    return latest


def _shares_long_token(a, b):
    """True if normalized strings a and b share a token of length >= 4."""
    return bool({t for t in a.split() if len(t) >= 4}
                & {t for t in b.split() if len(t) >= 4})


def with_applied(payload):
    """Annotate each posting with tracker provenance — mirrors with_verdicts().

    For every posting that matches a row in private/tracker.md (active or
    closed), set posting["applied"] = {date, status, section}. No match
    leaves the key absent (absent = not applied).

    Matching is deliberately conservative: we prefer FALSE NEGATIVES over
    false positives. A wrong "Applied" mark misleads worse than a missed
    one, so the title test stays strict (equality or containment, never
    mere token overlap), while the company test tolerates aliasing."""
    tracker = parse_tracker()
    index = []  # (nc, nt, info)
    for row in tracker.get("active", []):
        index.append((
            scrape._norm(row.get("company", "")),
            scrape._norm(row.get("role", "")),
            {"date": row.get("applied", ""),
             "status": row.get("status") or "Applied",
             "section": "active"},
        ))
    for row in tracker.get("closed", []):
        index.append((
            scrape._norm(row.get("company", "")),
            scrape._norm(row.get("role", "")),
            {"date": row.get("applied", ""),
             "status": row.get("outcome") or "Applied",
             "section": "closed"},
        ))

    for posting in payload.get("postings", []):
        pc = scrape._norm(posting.get("company", ""))
        pt = scrape._norm(posting.get("title", ""))
        best = None
        for nc, nt, info in index:
            company_ok = pc and nc and (
                pc in nc or nc in pc or _shares_long_token(pc, nc))
            # Equality only — NO containment. _norm collapses some titles to
            # short generic stems (e.g. "Designer Freelance" -> "designer"),
            # and containment let those falsely match longer roles at a
            # company sharing one token. Equality keeps us in the
            # false-negatives-over-false-positives lane we want.
            title_ok = pt and nt and pt == nt
            if not (company_ok and title_ok):
                continue
            if best is None:
                best = info
            elif best["section"] != "active" and info["section"] == "active":
                best = info  # prefer an active row over a closed one
        if best is not None:
            posting["applied"] = best
    return payload


TRACKER = scrape.ROOT / "private" / "tracker.md"

# Column orders match the file; values pass through verbatim (markdown,
# emoji, links, dashes all preserved). See ideas/tracker-wiring.md.
ACTIVE_KEYS = ("company", "role", "channel", "applied", "status", "next", "notes")
CLOSED_KEYS = ("company", "role", "channel", "applied", "outcome", "learned")


def _split_row(line):
    """Split a markdown table row on `|` and trim each cell. Drops the
    empty leading/trailing cells produced by the bordering pipes."""
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def _parse_table(lines, keys):
    """Turn the data rows of one MD table into a list of dicts.

    Skips the header row, the `|---|` separator, and any non-table line
    (e.g. the HTML comment inside the Closed table). All-blank rows are
    omitted. Cell text is passed through verbatim."""
    rows = []
    seen_header = False
    for line in lines:
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue  # not a table row (blank line, comment, prose, ---)
        if not seen_header:
            seen_header = True  # first table row is the header — skip it
            continue
        if set(stripped) <= set("|-: "):
            continue  # separator row like |---|---|
        cells = _split_row(stripped)
        if not any(cells):
            continue  # all-blank placeholder row
        rows.append({key: (cells[i] if i < len(cells) else "")
                     for i, key in enumerate(keys)})
    return rows


def parse_tracker():
    """Parse private/tracker.md into the {active, closed, patterns} contract.

    Like with_verdicts(): build the payload from the MD (the source of
    truth), then hand it to send_json(). The file is never written here.
    Returns the empty structure if the file is missing."""
    if not TRACKER.exists():
        return {"active": [], "closed": [], "patterns": ""}

    sections = {}
    current = None
    buffer = []
    for line in TRACKER.read_text().splitlines():
        heading = line.strip()
        if heading.startswith("## "):
            if current is not None:
                sections[current] = buffer
            current = heading[3:].strip().lower()
            buffer = []
        elif current is not None:
            buffer.append(line)
    if current is not None:
        sections[current] = buffer

    active = _parse_table(sections.get("active", []), ACTIVE_KEYS)
    closed = _parse_table(sections.get("closed", []), CLOSED_KEYS)
    patterns = "\n".join(sections.get("patterns", [])).strip()
    return {"active": active, "closed": closed, "patterns": patterns}


def append_learning(today, body, reason):
    """Dismissals accumulate in learnings.md — the raw material the
    search learns from. Periodically hand it to your AI: 'read my
    learnings and suggest watchlist edits.'"""
    if not scrape.LEARNINGS_FILE.exists():
        scrape.LEARNINGS_FILE.write_text(
            "# Learnings — dismissed postings\n\n"
            "> Every dismissal lands here with its reason. This file is\n"
            "> the search learning from itself: when a pattern repeats,\n"
            "> it belongs in the watchlist. Periodically ask your AI to\n"
            "> read this plus private/watchlist.md and propose edits —\n"
            "> new title excludes, department excludes, or boost changes.\n\n"
        )
    entry = (
        f"- {today} — {body.get('title', '?')} — {body.get('company', '?')}"
        + (f" — \"{reason}\"" if reason else " — no reason given")
        + f"\n  {body.get('url', '')}\n"
    )
    with scrape.LEARNINGS_FILE.open("a") as handle:
        handle.write(entry)


class Handler(SimpleHTTPRequestHandler):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    # ── API ──────────────────────────────────────────────────

    def do_GET(self):
        if self.path == "/api/jobs":
            latest = scrape.JOBS_DIR / "latest.json"
            if latest.exists():
                return self.send_json(
                    with_applied(with_verdicts(json.loads(latest.read_text()))))
            return self.send_json({"generated": None, "postings": []})

        if self.path == "/api/verdicts":
            if scrape.VERDICTS_FILE.exists():
                return self.send_json(json.loads(scrape.VERDICTS_FILE.read_text()))
            return self.send_json({})

        if self.path == "/api/watchlist":
            if scrape.WATCHLIST.exists():
                return self.send_json({"text": scrape.WATCHLIST.read_text()})
            return self.send_json(
                {"text": scrape.EXAMPLE_WATCHLIST.read_text(), "example": True}
            )

        if self.path == "/api/tracker":
            return self.send_json(parse_tracker())

        # Static files — but private/ is never served over HTTP.
        # The API above exposes exactly what the app needs, nothing more.
        if self.path.startswith("/private"):
            return self.send_error(403, "private/ is not served")
        return super().do_GET()

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        try:
            body = json.loads(self.rfile.read(length) or b"{}")
        except json.JSONDecodeError:
            return self.send_error(400, "invalid JSON")

        if self.path == "/api/scrape":
            log = []
            try:
                results = scrape.scan(
                    days=int(body.get("days", 7)),
                    rescan=bool(body.get("rescan", False)),
                    log=log.append,
                )
            except scrape.WatchlistError as err:
                return self.send_json({"error": str(err), "log": log}, 400)
            latest = json.loads((scrape.JOBS_DIR / "latest.json").read_text())
            latest["log"] = log
            latest["new"] = len(results)
            return self.send_json(with_applied(with_verdicts(latest)))

        if self.path == "/api/dismiss":
            url = body.get("url", "")
            if not url:
                return self.send_json({"error": "no url"}, 400)
            dismissed = (
                json.loads(scrape.DISMISSED_FILE.read_text())
                if scrape.DISMISSED_FILE.exists() else {}
            )
            today = date.today().isoformat()
            reason = (body.get("reason") or "").strip()
            dismissed[url] = {"date": today, "reason": reason}
            scrape.JOBS_DIR.mkdir(parents=True, exist_ok=True)
            scrape.DISMISSED_FILE.write_text(json.dumps(dismissed, indent=1))
            append_learning(today, body, reason)
            return self.send_json({"dismissed": True})

        if self.path == "/api/watchlist":
            text = body.get("text", "")
            if not text.strip():
                return self.send_json({"error": "watchlist is empty"}, 400)
            scrape.WATCHLIST.parent.mkdir(parents=True, exist_ok=True)
            scrape.WATCHLIST.write_text(text)
            return self.send_json({"saved": True})

        return self.send_error(404)

    # ── plumbing ─────────────────────────────────────────────

    def send_json(self, payload, status=200):
        data = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, fmt, *args):
        if args and isinstance(args[0], str) and "/api/" in args[0]:
            super().log_message(fmt, *args)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--port", type=int,
                        default=int(os.environ.get("PORT", 8765)))
    parser.add_argument("--no-browser", action="store_true",
                        help="don't open the browser automatically")
    args = parser.parse_args()

    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    url = f"http://localhost:{args.port}"
    print(f"Job Hunter Toolkit running at {url}  (Ctrl+C to stop)")
    if not args.no_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
