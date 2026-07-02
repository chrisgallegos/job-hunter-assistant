# Job Scraper Watchlist

Copy this file to `private/watchlist.md` and make it yours. The scraper
reads it on every run — sections are `## ` headings, entries are `- `
list items. All matching is case-insensitive substring matching.

To find a company's slug, try its careers page URL
(boards.greenhouse.io/SLUG, jobs.lever.co/SLUG, jobs.ashbyhq.com/SLUG)
or run `python3 scraper/scrape.py --probe SLUG` and let it check all
three sources for you.

## Expanding your watchlist with AI

Once you have a `private/career-narrative.md`, ask your AI to suggest
companies based on your actual targets — not generic lists:

```
Read private/career-narrative.md and suggest 10–15 companies to add
to my scraper watchlist. For each one: why it fits my targets, which
ATS platform it uses (greenhouse / lever / ashby), and the likely slug.
Mark any you're uncertain about so I can run --probe to verify.
```

The AI uses your stated industries, salary expectations, and
deal-breakers to weight suggestions — not just your job title. Run this
prompt again any time you hear about a company worth watching. The
watchlist is designed to grow over time.

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

NOTE: the department field is often blank — aggregator feeds (RemoteOK,
WeWorkRemotely) don't provide one, and some ATSes leave it empty. When
it's blank this rule can't fire, so anything you truly want gone should
ALSO go in Title excludes below.

- game design

## Title excludes

A posting is dropped if its title contains any of these — prune the
adjacent roles that share your keywords. Matching is case-insensitive
substring (words of 3 letters or fewer match on word boundaries only).

- engineer
- programmer
- recruiter
- researcher

### How to tune this section (a worked example)

You'll keep seeing roles that match your keywords but aren't your craft.
The fix is to add the *discipline word* here, but two rules keep it safe:

1. Catch it on the TITLE, not just the department. Example: searching
   game studios surfaces "Senior Level Designer" and "Narrative Designer".
   They pass the title gate because they contain "design", and the
   Department excludes miss them whenever the feed left the department
   blank. Adding "level design" and "narrative design" here closes the
   leak. (This filters by DISCIPLINE, not industry — you keep the game
   studios, you just drop the crafts you don't practice. Their visual /
   UI / UX / product roles still come through.)

2. Prefer the two-word discipline form over a bare word, because
   substring matching over-fires. "game design" also catches
   "Game Designer" — good. But a bare "quest" would also nuke any title
   containing "reQUESTed", and a bare "level" would hit "C-Level". When
   in doubt, use the longer phrase and test with a rescan.

# Example game-studio discipline excludes (uncomment if you're a designer
# fishing in gaming and tired of game-design/engineering false positives):
# - game design        # also catches "Game Designer"
# - gameplay
# - level design       # also catches "Level Designer"
# - narrative design   # also catches "Narrative Designer"

## Boost keywords

Not filters — relevance points. Each keyword found in the title,
company, or description adds a point to the posting's digest score.

- game
- entertainment
- design system

## Company tier boosts

Optional. Group the companies under `## Companies` with `### ` sub-headers
(e.g. `### Gaming studios`, `### Agencies & consultancies`) — those
sub-headers become each company's "tier." This section matches keywords
(case-insensitive substring) against those tier labels and adds points to
the relevance score, so postings from your priority tiers rank higher.

Title remains the fundamental filter and strong-title/seniority remain the
fundamental score components — this is only a thumb on the scale. Only the
single LARGEST matching value is added (no stacking), and feeds/aggregators
get no tier, so they're never boosted here. Omit the section entirely for
no boost (fully backward compatible).

Format: "- keyword: points". Worked example (matches the sub-headers a
gaming-leaning designer might use):

- gaming: 3
- entertainment: 2
- design systems: 2
- agencies: 1

Note: deduplication is automatic and needs no config. When the same role
shows up on a canonical company board AND an aggregator (RemoteOK, etc.),
the canonical posting wins and the aggregator copies ride along on it as
`also_on` — nothing is lost, the canonical one is just the primary.

Also automatic, no config needed: postings from less-canonical sources
(RemoteOK, free aggregator feeds) get a small automatic score penalty vs.
company boards, so aggregator noise sinks in the ranking on its own —
`## Score penalties` below is for tuning your OWN false positives, not
source quality.

## Score penalties

The inverse of Boost keywords — a hit SUBTRACTS from the relevance score
instead of adding to it. Same matching as boost keywords (title +
company + department + description, case-insensitive substring/word-
boundary per `kw_match`). Use this to downweight terms that correlate
with "wrong discipline" or "wrong seniority" for you, WITHOUT hard-
excluding the posting the way Title excludes would — useful for
foot-in-door plays you still want to eyeball, just ranked lower.

Format: "- keyword: points" (points is written positive, subtracted
under the hood). Worked example for a mid-career product designer who
keeps seeing junior titles and copywriting-adjacent noise:

- junior: 2
- associate: 2
- intern: 4
- copywriter: 3

Penalties sum (unlike Company tier boosts, which only takes the largest
match) — a posting that trips two penalty keywords sinks by both. If a
term is disqualifying rather than just noisy, it belongs in Title
excludes or Department excludes instead — penalties are for "still
worth a glance, just not at the top."

## Salary floor

Optional, single line, digits only (no `$` or commas). When a posting's
extracted salary max falls below this, the app flags it — never filters
it out, since salary extraction is a best-effort regex over free text
and plenty of real postings just don't state a number. Comp figures with
an hourly rate skip the floor check entirely (an hourly rate isn't
comparable to an annual floor without knowing hours/year).

- 120000

## Locations

A posting is kept if its location contains one of these, OR it's
remote, OR the posting lists no location. Leave empty to keep all.

- remote
- seattle
