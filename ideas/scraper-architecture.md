# Scraping Layer — Architecture Notes

**Status:** built June 2026 — see `scraper/`. This doc is the original
design sketch, kept for the reasoning. Differences from the sketch:
output lands in `private/jobs/` (with the rest of your instance) rather
than `scraper/output/`; a `private/watchlist.md` file drives which
companies are scraped and what counts as relevant; postings get a
keyword relevance score in a daily digest. Workday deferred as planned.

A simple local Python script that pulls job postings from the major ATS
platforms — Greenhouse, Lever, Workday, Ashby — plus individual company
career pages, and writes them to structured Markdown or CSV that the
templates (and any AI collaborator) can read.

## Principles

- **Local only.** The user runs it on their machine. No hosted service,
  no accounts, no data sent anywhere — same ownership model as the rest
  of the toolkit.
- **Optional.** Rung three of the ladder. Nothing in the templates
  depends on it; it just feeds the JD analysis pipeline at volume.
- **Boring tech.** One script, standard library where possible, output
  a human can read without the AI. Greenhouse and Lever have public
  JSON endpoints per company board, which covers a surprising share of
  tech postings; Ashby similar. Workday is the hard one — defer it.

## Sketch

```
scraper/
├── scrape.py          # CLI: python scrape.py --company stripe --source greenhouse
├── sources/           # one small adapter per ATS
└── output/            # gitignored — postings land here as MD/CSV
```

Output per posting: company, title, location, posted date, source URL,
full description text — i.e., exactly the fields the JD analysis
template's "The posting" section asks for, so a scraped posting drops
straight into the workflow.

## Open questions

- Respect robots.txt and rate limits — design this in from the start
- Dedup across sources when the same role appears on multiple boards
- Staleness: postings vanish; keep the scraped copy (the JD analysis
  template already says to paste and keep the original for this reason)
