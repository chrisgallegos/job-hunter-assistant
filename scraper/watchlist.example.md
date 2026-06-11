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

Aggregate job boards, scanned after the company boards. The argument
in parentheses is the feed's category. Available feeds: remotive,
weworkremotely, remoteok. Remove entries you don't want.

- remotive (design)
- weworkremotely (design)
- remoteok (design)

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
