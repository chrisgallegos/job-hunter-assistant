# Spec: wire the app's Tracker tab to private/tracker.md (Phase 1 — read-only)

## Goal
The Tracker tab is currently localStorage-backed (`jht_tracker`) and cannot
represent the real data in `private/tracker.md` (it only models the Active
table; no Closed table, no Patterns). Phase 1 makes the app a faithful
**read-only view** of `private/tracker.md`. No write-back yet (that's Phase 2).

After Phase 1: open the app → Tracker tab → see the real Active table, the
real Closed table, and the Patterns prose, all sourced live from the MD file.

## Hard constraints (do not violate)
- **Markdown is the single source of truth.** The server is a view over the
  file. Phase 1 never writes to `tracker.md`.
- **Stdlib only**, no external deps (see serve.py imports).
- **Local only** — server binds 127.0.0.1; `/private/*` stays 403'd.
- Preserve all existing endpoints and behavior.

## The data contract: `GET /api/tracker`
Returns JSON:
```
{
  "active": [ { "company","role","channel","applied","status","next","notes" }, ... ],
  "closed": [ { "company","role","channel","applied","outcome","learned" }, ... ],
  "patterns": "<raw markdown string of the Patterns section>"
}
```
- Active table columns (in file order): Company | Role | Channel | Applied | Status | Next action | Notes  → keys company, role, channel, applied, status, next, notes
- Closed table columns: Company | Role | Channel | Applied | Outcome | What I learned → keys company, role, channel, applied, outcome, learned
- `patterns`: everything under the `## Patterns` heading, returned as raw markdown (the app renders it read-only; do not try to tabulate it).

## Server task (serve.py) — Agent A
- Add a `GET /api/tracker` route. **Mirror the existing `/api/watchlist` GET
  handler (serve.py ~91–96)** and use the existing `send_json()` helper
  (serve.py ~154–160).
- Write a small stdlib MD parser helper (like `with_verdicts()` at ~31–47 —
  parse before send_json). Rules the parser MUST handle, because the real file
  contains all of these:
  - Three sections delimited by headings `## Active`, `## Closed`, `## Patterns`
    (sections separated by `---` lines).
  - A table = a header row (`| Company | Role | ... |`), a separator row
    (`|---|---|...|`), then data rows. **Skip** the header and separator rows.
  - **Skip any line that is not a table row** inside the table region — notably
    an HTML comment line `<!-- ... -->` exists inside the Closed table; ignore it.
  - Cell values may contain markdown (bold `**x**`, links `[a](b)`, emoji,
    en/em dashes, `$` ranges). Do NOT strip or alter them — pass through verbatim.
  - Cells never contain a literal unescaped `|` (safe to split on `|`).
  - Trim surrounding whitespace per cell; an empty placeholder row (all blank
    cells) should be omitted.
- If `private/tracker.md` is missing, return `{"active":[],"closed":[],"patterns":""}`.
- Do not modify any other route.

## App task (app.js / index.html / app.css) — Agent B
- Replace the localStorage load: `loadTracker()` (app.js ~686–689) becomes an
  async fetch of `/api/tracker`. Follow the existing server-fetch pattern used
  by the Jobs scan / watchlist code (search app.js for `fetch(` and the
  `/api/watchlist` usage to copy request/response handling).
- Extend `renderTracker()` (app.js ~695–719) to render **two tables** (Active
  with its 7 columns, Closed with its 6 columns) plus a read-only Patterns
  block (render the raw markdown; a minimal markdown-to-HTML or `<pre>` is fine
  for Phase 1 — keep it simple and readable).
- Update the Tracker tab markup in index.html (the `#tracker-body` table region
  ~lines 220–266) to host both tables + a Patterns container. Match existing
  visual style (this app's Jobs cards are the design reference; app.css).
- **Phase 1 is read-only:** leave the add/edit modal in place but it does not
  need to persist anywhere yet; if simplest, hide the "Add" affordance for now
  and add a small note "Editing lands in Phase 2 — edit private/tracker.md
  directly for now." Do not wire any POST.
- Do NOT touch serve.py.

## Out of scope (Phase 2, later)
- `POST /api/tracker` with **surgical block-write** (replace only the Active
  table block between `## Active` and the next `---`; leave Closed + Patterns +
  comments byte-for-byte). Never regenerate the whole file from JSON.
- In-app add/edit of Active rows; an "Archive to Closed" affordance that opens
  the MD rather than editing inline. Closed + Patterns stay MD-edited by design
  (reflective writing shouldn't become checkbox-clicking).
- Retiring `jht_tracker` localStorage after a one-time import.

## Verification (Phase 1 done when)
- `GET /api/tracker` returns the real Active/Closed rows + Patterns text.
- App Tracker tab shows the live data from `private/tracker.md` (33 Active /
  68 Closed at time of writing), no console errors, in the preview server.
