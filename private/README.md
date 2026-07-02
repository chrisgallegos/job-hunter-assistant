# Your private workspace

Everything in this folder except this README is gitignored. Your career
narrative, JD analyses, drafts, research, and tracker live here — they
never get committed, never get published.

Start by copying `../templates/career-narrative.md` here and filling
it out.

## Your files

Suggested naming as your search grows:

```
career-narrative.md           Your story, targets, deal-breakers, voice
tracker.md                    Application log and funnel analysis
watchlist.md                  Scraper: companies, filters, keywords

jd-[company]-[role].md        JD analysis per posting
cover-[company]-[role].md     Cover letter draft
research-[company].md         Pre-interview company background
interview-[company].md        Interview prep notes

jobs/                         Scraper output (created automatically)
  digest-YYYY-MM-DD.md        Ranked postings from each scan
  latest.json                 Machine-readable (used by the app)
  review-queue.md             Handoff to your AI collaborator
  verdicts.json               Your AI's judgment layer
  dismissed.json              What you rejected + reasons
  learnings.md                Accumulated patterns for watchlist tuning
  postings/                   One MD file per scraped posting
```

## Optional: API keys

Some scraper sources require a free API key. Store them here — this
folder is gitignored, so keys stay on your machine and never get pushed.

### USAJobs (US federal government jobs)

Register at https://developer.usajobs.gov/APIRequest/Index
Quick signup — email + intended use, no payment.

Create `private/usajobs.env`:
```
USAJOBS_API_KEY=your-key-here
USAJOBS_USER_AGENT=your@email.com
```

Then add to your watchlist under `## Feeds`:
```
- usajobs (product designer)
- usajobs (ux designer remote)
```

Notable federal employers: USDS, GSA (18F/TTS), VA, NIH, NASA, CFPB, DHS.
Pay is GS schedule — GS-12/13 roughly $90–$130k depending on locality.
Remote options expanded significantly post-pandemic.

## Nothing here ever leaves your machine

The `.gitignore` at the repo root ignores everything in this folder
except this README. If you're ever unsure what's tracked, run:
```bash
git status
```
Files from `private/` should never appear in the output. If they do,
something has gone wrong — do not push until you've resolved it.
