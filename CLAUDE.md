# Guidance for AI coding assistants

You're working in the **Job Hunter Assistant** — a portable, self-owned job search
system built on plain Markdown files and a small Python scraper. Read this before
making changes. Full contributor guidance is in `CONTRIBUTING.md`; the design
rationale is in `docs/philosophy.md`.

## Hard constraints (do not violate)

- **Boring tech, on purpose.** Python is **stdlib only** — no pip installs, no
  dependencies. JavaScript is **vanilla** — no React/Vue, no bundlers, no npm.
  If a change would need a build step, it's out of scope.
- **`private/` is sacred.** It's gitignored and holds the user's real career
  data, application tracker, and search history. Never commit anything from
  `private/`. Never move personal data out of it into a tracked file.
- **PII sweep before committing.** This repo is public and gets forked. Before
  any commit, check staged content for real names, contact info, or personal
  job-search context — especially in `ideas/` docs and code comments. If in
  doubt, keep it in `private/`.
- **No telemetry, no accounts, no external APIs beyond public job boards.** The
  scraper reads public ATS/feed endpoints only. Nothing phones home.
- **Match the surrounding style.** Terse, commented-for-the-why, human- and
  AI-legible. Don't reformat files you're not changing.

## Layout

- `scraper/scrape.py` — the scan pipeline: fetch → filter → score → write MD.
- `scraper/sources/` — company-board adapters (one file per ATS platform).
- `scraper/feeds/` — job-feed adapters (Remotive, RemoteOK, WeWorkRemotely, plus optional USAJobs/NeoGov).
- `templates/`, `docs/` — the no-code and methodology layers.
- `index.html` / `app.js` / `app.css` — the local browser app (`python3 serve.py`).
- `ideas/` — design notes and engineering findings.

## Adding an ATS source adapter (the most common contribution)

Each adapter is one small module exposing:

```python
def fetch(slug) -> list[dict]
```

Every posting dict must have these keys (see any file in `scraper/sources/` and
the contract comment at the top of `scraper/sources/__init__.py`):

```
company, source, id, title, location, remote, url, posted, description
```

`posted` is an ISO date string or `None`. Adapters return `[]` on any failure —
a slug that isn't on that platform is normal, not an error. Then:

1. Register the module in `get_sources()` in `sources/__init__.py`.
2. **Add it to `SOURCE_COST` in `scrape.py`** at cost `0` if it's a canonical
   company board — otherwise it loses cross-source dedup to pay-to-play
   aggregators. This is a real, easy-to-miss bug.
3. Add the CLI `--source` choice in `scrape.py`.

**Before adding a Workday, Eightfold, or SmartRecruiters-style adapter, read
`ideas/ats-platform-notes.md`** — it has the live-tested API shapes and the
non-obvious gotchas (Workday's unguessable tenant/pod/site, `limit>20` 400s,
loose full-text search; Eightfold's gated tenants and retail leakage; the
`\bword\b` regex trap that silently blanks "Designer"). Don't re-derive them.

## Testing

No test suite — manual verification against the live APIs is the norm. Run one
source in isolation:

```
python3 scraper/scrape.py --company epicgames --source greenhouse
python3 scraper/scrape.py --probe <company>     # which ATS hosts a company
```

When adding a source, confirm the normalized output shape matches the contract
and note what you tested (e.g. "verified against Adobe/T-Mobile, got N design
postings, descriptions populated"). Workday tenants are slow (they paginate the
board per search term) — a full scan of a Workday-heavy watchlist takes minutes;
that's expected, not a hang.
