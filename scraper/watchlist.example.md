# Job Scraper Watchlist

Copy this file to `private/watchlist.md` and make it yours. The scraper
reads it on every run — sections are `## ` headings, entries are `- `
list items. All matching is case-insensitive substring matching.

To find a company's slug, try its careers page URL
(boards.greenhouse.io/SLUG, jobs.lever.co/SLUG, jobs.ashbyhq.com/SLUG)
or run `python3 scraper/scrape.py --probe SLUG` and let it check all
three sources for you.

## Companies

The slug as it appears in the company's job board URL. Pin a source in
parentheses to skip auto-detection (faster, and required when the same
slug exists on two platforms).

- discord (greenhouse)
- spotify (lever)
- ramp (ashby)

## Feeds

Aggregate boards and government portals, scanned after company boards.
Format: "- feedname (argument)" where argument is a keyword or category.
Remove lines you don't want.

### Private-sector feeds

- remotive (design)          # Remote-only; JSON API, no key needed
- weworkremotely (design)    # RSS feed; categories: design, programming, etc.
- remoteok (design)          # Remote-only; pay-to-post (deprioritized vs free sources)

### US Federal government — USAJobs

Requires a free API key: https://developer.usajobs.gov/APIRequest/Index
Register with your email + intended use. No payment, no vetting.
Add to private/usajobs.env:
  USAJOBS_API_KEY=your-key
  USAJOBS_USER_AGENT=your@email.com

Then uncomment:
# - usajobs (product designer)
# - usajobs (ux designer remote)
# - usajobs (visual designer)

Notable federal employers for designers: USDS, GSA/18F, VA, NIH, NASA.
Pay is GS schedule — GS-12/13 maps roughly to $90–$130k + locality.
Remote widely available post-pandemic.

### State and local government — NeoGov

Most US cities, counties, and state agencies use NeoGov/GovernmentJobs.
A headless-browser adapter is needed to read their listings (they load
jobs client-side via JavaScript). Not yet implemented — tracked as a TODO.

In the meantime, check these boards manually:
  https://www.governmentjobs.com/careers/seattle         (City of Seattle)
  https://www.governmentjobs.com/careers/kingcounty      (King County, WA)
  https://www.governmentjobs.com/careers/washington      (WA State)
  https://www.governmentjobs.com/careers/nyc             (New York City)
  https://www.governmentjobs.com/careers/losangeles      (City of Los Angeles)
  https://www.governmentjobs.com/careers/chicago         (City of Chicago)

When implemented, the watchlist entry will be:
# - neogov (seattle)         # Seattle design roles
# - neogov (washington)      # WA State roles

## Title must match one of

A posting is kept only if its title contains at least one of these
(or one of the Strong titles below). Leave both sections empty to
keep every title.

- design
- art director
- creative director

## Strong titles

Your actual discipline. These also satisfy the title gate, and add
+3 to the relevance score so they rank above generic matches.

- product designer
- visual design
- ui
- ux

## Department excludes

A posting is dropped if the company's own department/team label for it
contains any of these. Useful where similar titles span different
disciplines (e.g. "Game Design" vs "UX" departments at game studios).

- game design

## Title excludes

A posting is dropped if its title contains any of these — prune the
adjacent roles that share your keywords.

- engineer
- recruiter
- researcher

## Boost keywords

Not filters — relevance points. Each keyword found in the title,
company, or description adds a point to the posting's digest score.

- game
- entertainment
- design system

## Locations

A posting is kept if its location contains one of these, OR it's
remote, OR the posting lists no location. Leave empty to keep all.

- remote
- seattle
