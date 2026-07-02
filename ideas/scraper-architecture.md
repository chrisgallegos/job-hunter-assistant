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
retail, telecom, some gaming publishers. It's notably absent from the
current source list because there's no clean public JSON API: listings
are JavaScript-rendered and the partner API requires a commercial
agreement.

**Recon pass (2026-07-01, ~15 min timebox):** tried the sitemap
approach against Take-Two, the most-cited iCIMS gaming target.
Findings:

- **Take-Two Interactive is NOT on iCIMS.** Its real careers site
  (`careers.take2games.com`, reached via `take2games.com/careers`) is a
  bespoke Next.js app pulling from Contentful (CDN hosts under
  `images.ctfassets.net`) with no iCIMS/Greenhouse/Workday/Eightfold/
  SmartRecruiters signature anywhere in the static HTML. The `/jobs`
  listing route is client-rendered and its data fetch isn't visible in
  the shipped JS bundles either (likely a Next.js server action/RSC
  call, not a plain client-side `fetch()` to a discoverable URL) —
  would need a real headless-browser network trace to find, which is
  out of stdlib-only scope anyway.
- **Take-Two's studios are already covered without iCIMS**: Rockstar,
  2K, and Zynga are all separately confirmed on Greenhouse (see
  `private/watchlist.md`'s gaming tier) — so the Take-Two umbrella
  itself isn't actually a coverage gap, just the parent-company page.
- **`{guessed-slug}.icims.com/sitemap.xml` was 404 for every plausible
  Take-Two variant** (`take2`, `taketwo`, `take-two`,
  `taketwointeractive`) — consistent with the Workday/Eightfold lesson:
  ATS subdomains are not guessable from the company name, and without
  a real page to read the true subdomain off of, there's no way in.
- **Ubisoft, previously listed here as a likely iCIMS target, turned
  out to be SmartRecruiters** (`ubisoft2` — see `ats-platform-notes.md`
  and `sources/smartrecruiters.py`). Removing it from the "known iCIMS
  targets" list below since it was wrong.

**Conclusion: still deferred.** No stdlib-only (sitemap or JSON
endpoint) path was found in this pass. A real adapter would need either
(a) a headless browser to render the JS app and capture the XHR that
loads jobs, which is out of scope per this repo's stdlib-only
constraint, or (b) finding a specific company that still exposes the
iCIMS sitemap — worth a retry if a real iCIMS-hosted target's actual
careers URL is found first (don't guess the subdomain; read it off the
real page per the standard method in `ats-platform-notes.md`).

**Approach when prioritized:**
- Use Playwright or Puppeteer (headless browser) to render
  `https://{company}.icims.com/jobs/search` and extract job JSON from
  the network requests
- Alternatively, scrape the iCIMS XML sitemap some companies expose:
  `https://{company}.icims.com/sitemap.xml` — not universal but worth
  checking per-company, and only findable once the real subdomain is
  known (guessing it, as tried above, doesn't work)
- iCIMS job URLs follow a consistent pattern once known:
  `https://{company}.icims.com/jobs/{id}/job`

**Known target companies believed to still be on iCIMS** (not directly
re-verified this pass — Take-Two was checked and ruled out, Ubisoft was
checked and turned out to be SmartRecruiters):
- Warner Bros / WB Games
- NBCUniversal / Comcast
- Sega of America

**Slug discovery note:** the iCIMS company subdomain is usually the
company name or brand slug, but — same lesson as Workday and this
pass's Take-Two dead end — don't trust that guess. Read the real
subdomain off the company's actual careers page (grep its HTML/JS for
`icims.com`) before probing sitemap/API paths against it.
