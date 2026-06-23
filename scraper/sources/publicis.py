# Publicis Groupe careers — Jibe/iCIMS multi-brand board.
# https://careers.publicisgroupe.com/api/jobs?tags1=Creative&page=N&limit=100
#
# Unlike the other adapters, Publicis is ONE giant board spanning every
# Groupe agency (Razorfish, Heartbeat, Leo Burnett, Saatchi, etc.). There
# is no per-company slug to probe — so this adapter ignores `slug` and
# instead pulls the "Creative" department facet (tags1=Creative), which is
# the designer-relevant slice (~270 roles vs. ~2,700 total). The watchlist
# title/location filters then narrow it the rest of the way.
#
# Per-job JSON is rich: title, full_location, posted_date, description +
# responsibilities + qualifications, plus tag facets:
#   tags1 = department   tags2 = brand/agency   tags6 = work type (Hybrid/Remote/On-site)

import re
from . import get_json

DEPARTMENT = "Creative"          # the facet we care about
PAGE_SIZE = 100                  # API rejects limits much above this
MAX_PAGES = 6                    # safety cap (~600 roles); Creative is ~270
BASE = "https://careers.publicisgroupe.com/api/jobs"
VIEW = "https://careers.publicisgroupe.com/jobs/{}?lang=en-us"


def _strip_html(html):
    text = re.sub(r"<[^>]+>", " ", html or "")
    for entity, char in [("&amp;", "&"), ("&lt;", "<"), ("&gt;", ">"),
                          ("&nbsp;", " "), ("&#39;", "'"), ("&quot;", '"')]:
        text = text.replace(entity, char)
    text = re.sub(r"&#\d+;", "", text)
    return re.sub(r"\s+", " ", text).strip()


def _first(tag):
    """Tag facets come back as lists; take the first value."""
    if isinstance(tag, list):
        return tag[0] if tag else ""
    return tag or ""


def fetch(slug):
    # slug is ignored — Publicis is a single multi-brand board, queried by
    # department facet rather than company subdomain.
    postings = []
    for page in range(1, MAX_PAGES + 1):
        data = get_json(
            f"{BASE}?tags1={DEPARTMENT}&page={page}&limit={PAGE_SIZE}"
        )
        jobs = (data or {}).get("jobs") or []
        if not jobs:
            break
        for entry in jobs:
            job = entry.get("data") or {}
            req_id = str(job.get("req_id") or job.get("slug") or "")
            if not req_id:
                continue
            brand = _first(job.get("tags2")) or "Publicis Groupe"
            work_type = _first(job.get("tags6")).lower()
            location = (job.get("full_location")
                        or job.get("short_location") or "").strip()
            body = " ".join(filter(None, [
                _strip_html(job.get("description") or ""),
                _strip_html(job.get("responsibilities") or ""),
                _strip_html(job.get("qualifications") or ""),
            ]))
            postings.append({
                "company":     brand,
                "source":      "publicis",
                "id":          req_id,
                "title":       (job.get("title") or "").strip(),
                "department":  _first(job.get("tags1")),
                "location":    location,
                "remote":      "remote" in work_type
                               or "remote" in location.lower() or None,
                "url":         VIEW.format(req_id),
                "posted":      job.get("posted_date") or job.get("create_date"),
                "description": body,
            })
        if len(jobs) < PAGE_SIZE:
            break
    return postings
