# Extending the scraper: ATS platform notes

Hard-won, live-tested notes on adding new ATS (applicant tracking
system) platforms to `scraper/sources/`. Written so you — or your AI
agent — don't have to rediscover the same quirks by trial and error.

Each adapter is one small module exposing `fetch(slug) -> list[dict]`
of normalized postings (see `sources/__init__.py` for the exact shape).
Two platforms beyond the originals (Greenhouse/Lever/Ashby/BambooHR/
Workable) are documented here: **Workday** and **Eightfold**.

---

## General method: how to identify a company's ATS

**Don't guess the subdomain from the company name.** It works for
Greenhouse/Lever/Ashby (slug ≈ company name) but fails badly for
Workday and others. The reliable method:

1. `curl` the company's real careers page with a browser User-Agent.
2. Grep the HTML for platform signatures:
   `myworkdayjobs.com`, `eightfold.ai`, `greenhouse.io`,
   `lever.co`, `ashbyhq`, `icims`, `avature`, `smartrecruiters`,
   `successfactors`, `workdaysite.com`.
3. If the page is a JS app with no static signature, open it in a
   browser and watch the Network tab for the XHR that loads jobs — the
   API URL is right there in the request.

Blind subdomain guessing missed two real Workday tenants (Boeing,
T-Mobile) whose coordinates aren't derivable from the company name.
Checking the real page caught them in one pass.

**Also:** register any new source in `SOURCE_COST` in `scrape.py`.
Sources not listed there default to a high cost and *lose* cross-source
dedup ties to pay-to-play aggregators — so a canonical company-board
posting would get replaced by the same role's RemoteOK listing. Add
new canonical company ATSs at cost `0`.

---

## Workday (CXS API)

Every Workday-hosted careers site exposes a public JSON "candidate
experience site" (CXS) API. No auth, no cookies:

```
POST https://{tenant}.{pod}.myworkdayjobs.com/wday/cxs/{tenant}/{site}/jobs
Content-Type: application/json

{"appliedFacets":{}, "limit":20, "offset":0, "searchText":"design"}
```

Returns `{total, jobPostings:[{title, externalPath, locationsText,
postedOn, bulletFields:[reqId]}], facets:[...]}`.

Per-posting detail (needed for the description — the list omits it):

```
GET https://{tenant}.{pod}.myworkdayjobs.com/wday/cxs/{tenant}/{site}/job{externalPath}
```

Returns `jobPostingInfo` with `title`, `location`, `additionalLocations`
(non-primary cities hide here), `jobDescription` (HTML), `startDate`.
Comp, when present, is inline in the description HTML — no structured
field.

Human-facing apply URL = same path minus `/wday/cxs/{tenant}`:
`https://{tenant}.{pod}.myworkdayjobs.com/{site}/job{externalPath}`

### The catch: no guessable slug

A Workday tenant needs **three** values, and they are NOT derivable
from the company name:

1. **tenant** — usually the company name, but not always.
2. **pod** — `wd1`, `wd5`, `wd501`, … regional shards. Not guessable.
3. **site** — e.g. `external_experienced`, `External`,
   `EXTERNAL_CAREERS`, `{company}_careers`. No convention.

Find all three by opening the real careers page and reading the
`/wday/cxs/...` request URL from the Network tab. Onboarding a Workday
company is a ~5-minute manual lookup, every time — it does not amortize.
Worked examples (see `TENANTS` in `sources/workday.py`):

| tenant | pod | site |
|---|---|---|
| adobe | wd5 | external_experienced |
| nordstrom | wd501 | nordstrom_careers |
| boeing | wd1 | EXTERNAL_CAREERS |
| tmobile | wd1 | External |

### Gotchas

- **`limit` > 20 silently 400s** on some tenants (bare `HTTP_400`, no
  message). Cap page size at 20.
- **`total` is unreliable** — it does not reflect `searchText`
  filtering, and has been observed *undercounting* the real board
  (reported 1906 for a board that returned 2400+). Don't use it to
  decide when to stop paginating; stop on an empty `jobPostings` page.
- **`searchText` is loose full-text matching**, not title-only — it
  matches any job whose description mentions the term, so a common word
  like "design" returns a big chunk of a large board (engineers who
  "design systems," etc.). BUT results are **relevance-ranked**, so
  real design *titles* cluster at the top. Query per-term, cap pages
  per term, and let a downstream title filter cut the noise. The cap
  then trims the irrelevant tail, not the roles you want.
- **No per-posting department field.** The list has a board-level
  `jobFamilyGroup` facet, but individual postings carry no department,
  and that facet has no clean "Design/Creative" bucket anyway. So
  department-based excludes are inert for Workday — rely on title
  filtering.
- **Relative dates only.** The list gives "Posted Today" / "Posted 5
  Days Ago" / "Posted 30+ Days Ago" — no real timestamp. Anything older
  than 30 days reads as exactly 30 days. Fine for a ≤30-day freshness
  window; approximate beyond that.
- **Possible Cloudflare cooldown.** Bursts of rapid requests
  occasionally tripped a blanket `400` across all requests for a short
  window, self-recovering. Use real pacing/backoff if automating hard.
- **A `422` on `/jobs` is NOT proof of a real public careers board.**
  Workday hosts thousands of tenants including internal-only/HR
  instances that have nothing to do with a public careers site. Probing
  plausible tenant names against generic site guesses (`External`,
  `EXTERNAL_CAREERS`, ...) reliably turns up `422` ("tenant exists,
  site name wrong") for large companies even when their *real* public
  careers flow runs on a totally different platform (confirmed on
  `disney` — see Platform sightings below). A `422` only means "keep
  looking," not "this is close." The only reliable signal is still the
  real careers page itself: if it has no `myworkdayjobs.com` anywhere
  in its HTML or JS bundles, it's not Workday, no matter what generic
  tenant probing turns up.

Retail-heavy Workday tenants (e.g. T-Mobile) need no special store
filtering: because the search is vocabulary-based, store/sales job
descriptions that lack design words simply never come back.

---

## Eightfold (PCSX API)

Public JSON search API, no auth. Tenant slug is **just the lowercased
company name** (`{company}.eightfold.ai`) — no pod/site lookup, so it's
cheaper to onboard than Workday. Verify a guess with one curl.

```
GET https://{tenant}.eightfold.ai/api/pcsx/search
    ?domain={tenant}.com
    &query={term}
    &start=0
    &sort_by=relevance
    &filter_include_remote=1
```

Returns `{data:{positions:[...], count, filterDef:{...}}}`. Each
position: `id` (internal), `displayJobId`/`atsJobId` (the company's own
req ID), `name` (title), `standardizedLocations`, `postedTs` (unix —
real timestamps, unlike Workday), `department` (populated, usable for
excludes), `workLocationOption`.

Detail (for the description):

```
GET https://{tenant}.eightfold.ai/api/apply/v2/jobs/{id}?domain={tenant}.com
```

### Gotchas

- **Not every tenant is open.** Some real Eightfold tenants return
  `403 "PCSX is not enabled for this user"` (search gated for anonymous
  users) or `"Group ID not found"` (misconfigured/aliased domain).
  Confirm each slug with a curl before adding it.
- **Fixed page size of 10**, regardless of any `limit`/`num` param.
  Paginate with `start`; `data.count` is a *trustworthy* total (unlike
  Workday), so stop when `start >= count`.
- **Per-query result cap.** Combined with page size, capping at N pages
  bounds each query. A broad term on a huge board can exceed the cap
  (e.g. Microsoft's "design" query returns ~980 hits) — relevance sort
  probably keeps real titles in the top window, but verify if a known
  role goes missing.
- **`location` param is geo-anchored.** Omit it and results default to
  the requesting IP's region. Pass explicit location + `filter_include_remote=1`.
- **Retail leakage.** Retail-heavy tenants (e.g. Starbucks) put every
  store on the board, and Eightfold's relevance is fuzzy/semantic — a
  barista ranked #9 in a "design" query, and store *addresses* carry
  design words (a store at "...& BRAND" street matched a "brand"
  query). These get filtered out downstream by a title gate, but they
  waste description detail-fetches and eat the page cap. Fix: skip by
  `department` before the detail-fetch (see `RETAIL_DEPARTMENTS` in
  `sources/eightfold.py`: `barista`, `shift supervisor`, `coffeehouse`,
  `baker`). Deliberately do NOT gate bare "store" — that would also
  drop legitimate "Store Design"/"Store Development" roles.

---

## SmartRecruiters

Public JSON postings API, no auth. **Company id is NOT reliably the
lowercased company name** — some tenants disambiguate with a trailing
digit or different casing (Ubisoft's id is `ubisoft2`; bare `ubisoft`
returns `totalFound: 0`, not an error, so it silently looks like "no
postings" rather than "wrong id"). Confirm the id with one curl before
adding it, same discipline as Eightfold's tenant slug.

```
GET https://api.smartrecruiters.com/v1/companies/{companyId}/postings?limit=100&offset=0
```

Returns `{offset, limit, totalFound, content:[{id, name, location:
{city, country, remote, hybrid, fullLocation}, function:{label},
department:{label}, releasedDate, ...}]}`. `totalFound` is a
**trustworthy total** (like Eightfold, unlike Workday) — paginate on
`offset` and stop when `offset >= totalFound` or a page comes back
empty.

Per-posting detail (needed for the description — the list omits it):

```
GET https://api.smartrecruiters.com/v1/companies/{companyId}/postings/{postingId}
```

Returns `jobAd.sections`: `companyDescription`, `jobDescription`,
`qualifications`, `additionalInformation` — each `{title, text}` with
real (not entity-escaped) HTML. Also carries `postingUrl` (clean
human-facing apply link) and `applyUrl` (same link + an `?oga=true`
tracking param — prefer `postingUrl`).

### Gotchas

- **`limit` is capped at 100** server-side regardless of what's
  requested — the response echoes back whatever it actually used, so
  trust the echoed `limit`, not the one you sent.
- **`department.label` is often just the company/org name**, not a
  discipline — e.g. Ubisoft's `department` came back `"Ubisoft"` for
  every posting checked. `function.label` (`"Design"`, `"Marketing"`,
  `"Information Technology"`) is the actually-useful bucket; the
  adapter passes that through as `department` for scrape.py's
  filtering instead of the literal `department` field.
- **A wrong company id doesn't error** — it returns a normal 200 with
  `totalFound: 0`, indistinguishable at a glance from "real tenant,
  just no open roles right now." Always sanity-check a nonzero count
  before concluding a company isn't on the platform.
- Same two-tier fetch pattern as Workday/Eightfold: list is cheap and
  covers every posting, but only postings whose title already looks
  design-relevant get the per-posting detail call (and therefore a
  real description) — everything else still has title/location for
  `passes_filters()`.

---

## Server-side vs whole-board fetch

Big employers have thousands of postings (Adobe ~1000, T-Mobile 2400+,
Starbucks hundreds of thousands incl. retail). Fetching the whole board
to find a handful of relevant roles is slow and risks blind truncation.
Both adapters instead query a shared list of design-relevant terms
(`DESIGN_SEARCH_TERMS` in `sources/__init__.py`) server-side, dedup by
req id, and let `scrape.py`'s title/location filters do the final
narrowing. Tune that term list over time: add a term, watch a few
scans, keep it if it surfaces real roles, drop it if it only adds
noise.

Note this leaves one small coverage seam: a role whose title qualifies
on a term NOT in the search list (and whose body also lacks the search
terms) won't be returned. In practice nearly everything a design title
filter accepts also contains a search term in its full text — but if a
known role goes missing, adding its keyword to the term list closes it.

---

## Cross-cutting bug to avoid: word-boundary regex

A design-relevance pre-filter using `\bdesign\b` will **never match
"Designer"** — `\b` requires a boundary on both sides, and there's none
between "design" and "er". Use prefix-only `\bdesign` so "Designer,"
"Design Director," "Design Systems" all match. This one silently
produced empty descriptions for real design postings until caught by
checking a known match's description length. Same trap applies to any
`\bword\b` filter over job titles.

---

## Platform sightings (factual reference)

Companies checked while scoping, for anyone chasing the same targets.
A company being on a platform says nothing about whether its public API
is open — verify per the method above.

| Company | Platform | Notes |
|---|---|---|
| Adobe, Nordstrom, Boeing, T-Mobile | Workday CXS | open, adapter-ready |
| Starbucks, Microsoft | Eightfold PCSX | open |
| Netflix | Eightfold | tenant exists but search API gated (403) — re-confirmed still gated |
| Hulu / Disney | not Workday | real careers site (`jobs.disneycareers.com`) is TalentBrew/Radancy, no `myworkdayjobs.com` anywhere in the page or its JS bundles. A `disney` tenant DOES exist on Workday's infrastructure (probing returns `422`, i.e. "tenant found, site name wrong") but that's a false-positive signal — see the Workday gotcha below about `422` vs a real public board. No way to find a real site name because the public careers flow doesn't go through Workday at all. Commented out in the watchlist. |
| EA | Avature | not yet adapted |
| Snap | Workday "Recruiting" (`workdaysite.com`) | different product than CXS; API shape not yet found |
| Nintendo (of America) | Greenhouse | slug is `nintendo` (NOT `nintendoofamerica`/`noa`) — found by pulling the real careers page's Next.js JS chunks and grepping for `boards-api.greenhouse.io`. Careers page itself (`careers.nintendo.com`) is a JS SPA with no static ATS signature; the API call only showed up inside a compiled `.js` chunk. |
| Sony Interactive Entertainment (PlayStation) | Greenhouse | main board slug `sonyinteractiveentertainmentglobal` (208 postings, real UX/Design Director/UI-UX roles). Studio-specific sub-boards also exist on the same platform: `siei`, `teamlfg`, `haven` (Haven Studios). Found via `careers.playstation.com`'s HTML, which embeds literal `job-boards.greenhouse.io/...` apply URLs. |
| Activision Blizzard | Eightfold | tenant `activision` is real (`activision.eightfold.ai`) but PCSX search is gated (403 "PCSX is not enabled for this user") — same as Netflix. `activisionblizzard`, `blizzard`, `king` don't resolve as separate tenants. |
| Ubisoft | SmartRecruiters | company id is `ubisoft2`, not `ubisoft` (which returns `totalFound: 0`) — see the SmartRecruiters gotchas above. 199 postings, ~26 design-hint titles. |
| Wise (fintech, ex-TransferWise) | SmartRecruiters | id `wise`, 368 postings — used as the second verification target for the SmartRecruiters adapter (non-gaming, confirms the adapter generalizes). |

Retail company career sites also index product-category words into
search results, so a query for "design" can return "Designer Handbags"
or "Designated Selling Associate" (substring match on "**Design**ated").
Expect that noise and gate it by title/department downstream.
