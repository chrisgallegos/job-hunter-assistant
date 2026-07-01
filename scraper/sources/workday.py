# Workday CXS (candidate experience site) public job board API.
# https://{tenant}.{pod}.myworkdayjobs.com/wday/cxs/{tenant}/{site}/jobs
#
# Unlike Greenhouse/Lever/Ashby, there is no guessable company slug —
# each tenant needs its Workday tenant id, "pod" (wd1, wd5, wd501, ...),
# and site name, found by hand from the company's real careers page
# (open it, watch the network tab for the /wday/cxs/... call). See
# ideas/workday-adapter-scoping.md for how these four were found and
# the quirks below.
#
# Strategy: filter SERVER-SIDE with searchText, one design term at a
# time (see DESIGN_SEARCH_TERMS in sources/__init__.py), rather than
# pulling the whole board and filtering locally. Big boards make
# whole-board fetching both slow and unsafe — T-Mobile alone is 2400+
# jobs — so we ask Workday for what we want instead. searchText is
# full-text (matches description, not just title), so it returns some
# noise; scrape.py's title filter handles that downstream.
#
# Known quirks:
#   - `limit` > 20 in the request body silently 400s on at least one
#     tenant (Adobe) — page size is capped at 20 here.
#   - The list endpoint does NOT include the job description, only a
#     per-posting detail call does. So this adapter only fetches detail
#     (and therefore a real description) for postings whose title looks
#     design-relevant. Everything else still comes back with title and
#     location — passes_filters() in scrape.py doesn't need a
#     description, only score()'s keyword boost does.
#   - Workday's per-posting data carries no department field, so
#     department stays empty and scrape.py's department_excludes are
#     inert for Workday postings — title filters do the gating.

import re
from datetime import datetime, timedelta, timezone

from . import get_json, post_json, DESIGN_SEARCH_TERMS

PAGE_SIZE = 20
MAX_PAGES_PER_TERM = 15  # 300 relevance-ranked results/term. Workday's search
                         # is loose, so a common term fills this — but design
                         # titles rank to the top, so 300 captures them and the
                         # cap just bounds the noisy full-text tail.

# slug -> (workday tenant id, pod, site name, display name)
TENANTS = {
    "adobe":     ("adobe", "wd5", "external_experienced", "Adobe"),
    "nordstrom": ("nordstrom", "wd501", "nordstrom_careers", "Nordstrom"),
    "boeing":    ("boeing", "wd1", "EXTERNAL_CAREERS", "Boeing"),
    "tmobile":   ("tmobile", "wd1", "External", "T-Mobile"),
}

_DESIGN_HINT_RE = re.compile(
    r"\bdesign|\bcreative|art\s+director|\bbrand|\bvisual|\bux\b|\bui\b", re.I
)
_RELATIVE_DATE_RE = re.compile(r"posted\s+(today|yesterday|(\d+)\+?\s*days?\s+ago)", re.I)


def _strip_html(value):
    text = re.sub(r"<[^>]+>", " ", value or "")
    for entity, char in [("&amp;", "&"), ("&lt;", "<"), ("&gt;", ">"),
                          ("&nbsp;", " "), ("&#39;", "'"), ("&quot;", '"')]:
        text = text.replace(entity, char)
    text = re.sub(r"&#\d+;", "", text)
    return re.sub(r"\s+", " ", text).strip()


def _parse_relative_date(text, now=None):
    """Workday's list endpoint gives 'Posted Today' / 'Posted 5 Days
    Ago' / 'Posted 30+ Days Ago' instead of a real date. Approximate it
    relative to now — good enough for the freshness-window cutoff in
    scrape.py, not meant to be exact."""
    match = _RELATIVE_DATE_RE.search(text or "")
    if not match:
        return None
    now = now or datetime.now(timezone.utc)
    if match.group(1).lower() == "today":
        return now
    if match.group(1).lower() == "yesterday":
        return now - timedelta(days=1)
    days = match.group(2)
    return now - timedelta(days=int(days)) if days else None


def _base_url(tenant, pod, site):
    return f"https://{tenant}.{pod}.myworkdayjobs.com/wday/cxs/{tenant}/{site}"


def _fetch_detail(tenant, pod, site, external_path):
    url = f"{_base_url(tenant, pod, site)}{external_path}"
    data = get_json(url)
    info = (data or {}).get("jobPostingInfo") or {}
    return info


def fetch(slug):
    tenant_info = TENANTS.get(slug)
    if not tenant_info:
        return []
    tenant, pod, site, display = tenant_info
    jobs_url = f"{_base_url(tenant, pod, site)}/jobs"
    apply_base = f"https://{tenant}.{pod}.myworkdayjobs.com/{site}"

    # Query one design term at a time and dedup by req id, so overlap
    # between terms (a "Brand Designer" matches both "design" and
    # "brand") collapses to one posting.
    #
    # Workday's searchText is LOOSE full-text matching (any job whose
    # description mentions the term), so a common word like "design"
    # matches a big chunk of a large tech board — every term tends to
    # fill its page budget. That's expected, not a problem: results come
    # back relevance-ranked, so real design *titles* cluster at the top
    # and the per-term cap truncates the irrelevant tail, not the roles
    # we want. (Contrast Eightfold, whose search is genuinely tight.)
    raw_jobs = {}
    for term in DESIGN_SEARCH_TERMS:
        offset = 0
        for _ in range(MAX_PAGES_PER_TERM):
            data = post_json(jobs_url, {
                "appliedFacets": {}, "limit": PAGE_SIZE, "offset": offset,
                "searchText": term,
            })
            page = (data or {}).get("jobPostings") or []
            if not page:
                break
            for job in page:
                key = (job.get("bulletFields") or [""])[0] or job.get("externalPath")
                raw_jobs[key] = job
            offset += PAGE_SIZE

    postings = []
    for job in raw_jobs.values():
        title = (job.get("title") or "").strip()
        req_id = (job.get("bulletFields") or [""])[0]
        external_path = job.get("externalPath") or ""
        location = job.get("locationsText") or ""
        description = ""
        department = ""  # not exposed per-posting; see module docstring
        if _DESIGN_HINT_RE.search(title) and external_path:
            detail = _fetch_detail(tenant, pod, site, external_path)
            description = _strip_html(detail.get("jobDescription") or "")
            location = detail.get("location") or location
            additional = detail.get("additionalLocations") or []
            if additional:
                location = ", ".join([location] + additional) if location else ", ".join(additional)
        posted_dt = _parse_relative_date(job.get("postedOn") or "")
        postings.append({
            "department": department,
            "company": display,
            "source": "workday",
            "id": str(req_id),
            "title": title,
            "location": location.strip(),
            "remote": "remote" in location.lower() or None,
            "url": f"{apply_base}{external_path}",
            "posted": posted_dt.isoformat() if posted_dt else None,
            "description": description,
        })
    return postings
