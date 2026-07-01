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
  of the assistant.
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

## Deferred: iCIMS adapter

iCIMS is the dominant ATS at large enterprises — media conglomerates,
retail, telecom, some gaming publishers (Take-Two/2K/Rockstar). It's
notably absent from the current source list because there's no clean
public JSON API: listings are JavaScript-rendered and the partner API
requires a commercial agreement.

**Approach when prioritized:**
- Use Playwright or Puppeteer (headless browser) to render
  `https://{company}.icims.com/jobs/search` and extract job JSON from
  the network requests
- Alternatively, scrape the iCIMS XML sitemap some companies expose:
  `https://{company}.icims.com/sitemap.xml` — not universal but worth
  checking per-company
- iCIMS job URLs follow a consistent pattern once known:
  `https://{company}.icims.com/jobs/{id}/job`

**Known target companies likely on iCIMS** (confirmed not on GH/Lever/Ashby/BambooHR):
- Take-Two Interactive (2K, Rockstar, Zynga)
- Warner Bros / WB Games
- NBCUniversal / Comcast
- Ubisoft North America
- Sega of America

**Slug discovery note:** the iCIMS company subdomain is usually the
company name or brand slug — same discovery problem as other ATS
platforms, same `--probe`-style variant search applies.
