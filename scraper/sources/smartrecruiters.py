# SmartRecruiters public postings API.
# https://api.smartrecruiters.com/v1/companies/{companyId}/postings
#
# No auth. `companyId` is NOT always the lowercased company name — some
# tenants disambiguate with a trailing digit (Ubisoft's is "ubisoft2";
# bare "ubisoft" 404s/empties). Confirm the id with one curl before
# adding it, same as every other platform in this file's siblings.
#
# List response: {offset, limit, totalFound, content:[{id, name,
# location:{city, country, remote, hybrid, fullLocation}, function:
# {label}, department:{label}, releasedDate, ...}]}. `totalFound` is a
# trustworthy total (unlike Workday's) — paginate with offset until
# content comes back empty or offset >= totalFound. `limit` is capped
# at 100 server-side regardless of what's requested.
#
# `department.label` is frequently just the company/org name (not a
# useful discipline signal) — `function.label` ("Design", "Marketing",
# "Information Technology") is the more useful bucket, so it's what
# gets passed through as `department` for scrape.py's filtering.
#
# List entries have no description — same two-tier pattern as
# Workday/Eightfold: only fetch the per-posting detail (and therefore
# a real description) for postings whose title already looks
# design-relevant, to keep total requests reasonable on large boards.
#
# Detail: https://api.smartrecruiters.com/v1/companies/{companyId}/postings/{postingId}
# Returns jobAd.sections: companyDescription, jobDescription,
# qualifications, additionalInformation — each {title, text} with HTML.
# Concatenate jobDescription + qualifications for the description; the
# company boilerplate doesn't help score() and additionalInformation is
# usually EEO/benefits filler. `postingUrl` is the human-facing apply
# link (`applyUrl` appends a `?oga=true` tracking param — postingUrl is
# the cleaner canonical link).

import re

from . import get_json

PAGE_SIZE = 100
MAX_PAGES = 10  # 1000 postings/company — generous; boards this large are rare

_DESIGN_HINT_RE = re.compile(
    r"\bdesign|\bcreative|art\s+director|\bbrand|\bvisual|\bux\b|\bui\b", re.I
)


def _fetch_detail(company_id, posting_id):
    data = get_json(
        f"https://api.smartrecruiters.com/v1/companies/{company_id}/postings/{posting_id}"
    )
    return data or {}


def _description(detail):
    sections = (detail.get("jobAd") or {}).get("sections") or {}
    parts = []
    for key in ("jobDescription", "qualifications"):
        text = (sections.get(key) or {}).get("text") or ""
        if text:
            parts.append(text)
    return "\n".join(parts)


def fetch(slug):
    company_id = slug
    postings = []
    offset = 0
    total = None
    for _ in range(MAX_PAGES):
        data = get_json(
            f"https://api.smartrecruiters.com/v1/companies/{company_id}"
            f"/postings?limit={PAGE_SIZE}&offset={offset}"
        )
        content = (data or {}).get("content") or []
        if not content:
            break
        total = (data or {}).get("totalFound")
        for job in content:
            title = (job.get("name") or "").strip()
            posting_id = str(job.get("id", ""))
            location = job.get("location") or {}
            loc_text = location.get("fullLocation") or ""
            description = ""
            posting_url = (
                f"https://jobs.smartrecruiters.com/{company_id}/{posting_id}"
            )
            if _DESIGN_HINT_RE.search(title) and posting_id:
                detail = _fetch_detail(company_id, posting_id)
                description = _description(detail)
                posting_url = detail.get("postingUrl") or posting_url
            postings.append({
                "department": (job.get("function") or {}).get("label", ""),
                "company": (job.get("company") or {}).get("name") or slug,
                "source": "smartrecruiters",
                "id": posting_id,
                "title": title,
                "location": loc_text.strip(", "),
                "remote": bool(location.get("remote")) or None,
                "url": posting_url,
                "posted": job.get("releasedDate"),
                "description": description,
            })
        offset += PAGE_SIZE
        if total is not None and offset >= total:
            break
    return postings
