# Eightfold AI public job-search API.
# https://{tenant}.eightfold.ai/api/pcsx/search?domain={tenant}.com&query=...&start=N
#
# Tenant slug = company name lowercased; `domain` is the tenant's own
# corporate domain (usually {tenant}.com). Confirmed working for
# Starbucks and Microsoft — NOT universal: some real tenants (Netflix
# confirmed) have this endpoint gated for anonymous users with a 403
# "PCSX is not enabled" error even though the tenant itself is real.
# See ideas/eightfold-adapter-scoping.md for how this was found.
#
# Unlike Greenhouse/Lever, this isn't a "fetch the whole board" API —
# a company like Starbucks has hundreds of thousands of retail
# postings, far too many to paginate in full. So this adapter runs a
# small set of design-relevant search queries instead and lets
# scrape.py's own title/department filters do the real narrowing,
# same as every other adapter's downstream behavior.
#
# Page size is fixed at 10 regardless of any limit/num param tried;
# the response's data.count IS a trustworthy total (unlike Workday's),
# so pagination stops there rather than on an empty-page guess.
#
# Job descriptions require a separate detail call
# (/api/apply/v2/jobs/{id}?domain=...) — same constraint as Workday.
# Detail is only fetched for postings whose title already looks
# design-relevant, to keep total requests reasonable.

import re
from datetime import datetime, timezone

from . import get_json, DESIGN_SEARCH_TERMS

PAGE_SIZE = 10
MAX_PAGES = 10  # safety cap regardless of `count`

# slug -> display name (the API only knows the lowercase tenant slug)
DISPLAY_NAMES = {
    "starbucks": "Starbucks",
    "microsoft": "Microsoft",
}

_DESIGN_HINT_RE = re.compile(
    r"\bdesign|\bcreative|art\s+director|\bbrand|\bvisual|\bux\b|\bui\b", re.I
)

# Retail-heavy tenants put every store on the same board, and frontline
# store roles leak into design searches via fuzzy relevance and street
# names ("...& BRAND" makes a barista match the 'brand' query). Eightfold
# tags them with a clear department, so drop them up front — before the
# wasted description detail-fetch. Substring match, case-folded; this is
# a tunable knob (Starbucks-flavored today since it's the only retail
# Eightfold tenant). Deliberately NOT gating bare "store" — that would
# also catch legit "Store Design"/"Store Development" roles, which are
# real retail-environment design work. Corporate design departments
# (Creative Studio, Brand & Category, etc.) never contain these tokens.
RETAIL_DEPARTMENTS = ("barista", "shift supervisor", "coffeehouse", "baker")


def _strip_html(value):
    text = re.sub(r"<[^>]+>", " ", value or "")
    for entity, char in [("&amp;", "&"), ("&lt;", "<"), ("&gt;", ">"),
                          ("&nbsp;", " "), ("&#39;", "'"), ("&quot;", '"')]:
        text = text.replace(entity, char)
    text = re.sub(r"&#\d+;", "", text)
    return re.sub(r"\s+", " ", text).strip()


def _fetch_detail(tenant, position_id):
    url = (f"https://{tenant}.eightfold.ai/api/apply/v2/jobs/{position_id}"
           f"?domain={tenant}.com")
    return get_json(url) or {}


def fetch(slug):
    tenant = slug
    found = {}
    for query in DESIGN_SEARCH_TERMS:
        query = query.replace(" ", "+")  # URL-encode multi-word terms
        start = 0
        count = None
        for _ in range(MAX_PAGES):
            url = (f"https://{tenant}.eightfold.ai/api/pcsx/search"
                   f"?domain={tenant}.com&query={query}&start={start}"
                   f"&sort_by=relevance&filter_include_remote=1")
            data = get_json(url)
            payload = (data or {}).get("data") or {}
            positions = payload.get("positions") or []
            if not positions:
                break
            for pos in positions:
                pos_id = pos.get("id")
                if pos_id is not None:
                    found[pos_id] = pos
            count = payload.get("count")
            start += PAGE_SIZE
            if count is not None and start >= count:
                break

    postings = []
    for pos in found.values():
        dept = (pos.get("department") or "").lower()
        if any(retail in dept for retail in RETAIL_DEPARTMENTS):
            continue  # store/retail role — skip before the detail fetch
        title = (pos.get("name") or "").strip()
        position_id = pos.get("id")
        req_id = pos.get("displayJobId") or str(position_id)
        locations = pos.get("standardizedLocations") or pos.get("locations") or []
        location = ", ".join(locations)
        posted_ts = pos.get("postedTs")
        posted = (
            datetime.fromtimestamp(posted_ts, tz=timezone.utc).isoformat()
            if posted_ts else None
        )
        description = ""
        url = f"https://{tenant}.eightfold.ai/careers/job/{position_id}"
        if _DESIGN_HINT_RE.search(title):
            detail = _fetch_detail(tenant, position_id)
            description = _strip_html(detail.get("job_description") or "")
            url = detail.get("canonicalPositionUrl") or url
        postings.append({
            "department": pos.get("department") or "",
            "company": DISPLAY_NAMES.get(tenant, tenant),
            "source": "eightfold",
            "id": str(req_id),
            "title": title,
            "location": location,
            "remote": (pos.get("workLocationOption") or "").lower() == "remote" or None,
            "url": url,
            "posted": posted,
            "description": description,
        })
    return postings
