# Jobvite (now branded "Employ") public careersite.
# https://jobs.jobvite.com/{careersite}/jobs?nl=1
#
# No auth, no JS — the board is server-rendered HTML. `nl=1` ("no
# layout") is the clean, chrome-free variant the embed iframe uses;
# fetch that, not the full-page version.
#
# CAREERSITE SLUG IS NOT THE COMPANY NAME AND NOT GUESSABLE. Many
# tenants embed the board as an iframe on their own domain and set
# `jobs.jobvite.com/{slug}` (bare, no `/jobs`) to 302 back to that
# domain, so you can't confirm the slug by hitting the bare URL. Get it
# the reliable way: curl the company's careers page and read the embed's
# `data-careersite="..."` attribute (R&R Partners = `rrpartners`). The
# `careersite-iframe/?careersite={slug}` endpoint is a red herring — it
# rejects with an `invalid=1` redirect; only the path form
# `/{slug}/jobs?nl=1` works.
#
# List page: one <table class="jv-job-list"> per category, each row:
#   <td class="jv-job-list-name"><a href="/{slug}/job/{id}">Title</a></td>
#   <td class="jv-job-list-location">Location</td>
# grouped under <h3 class="h2">Category</h3> headers (a useful
# discipline signal — passed through as `department`).
#
# Detail page (/{slug}/job/{id}?nl=1) carries a schema.org JobPosting
# in an application/ld+json block: title, datePosted (ISO), description
# (HTML), employmentType, hiringOrganization, jobLocation, baseSalary.
# That's the clean parse path for the description + posted date, so —
# same two-tier pattern as SmartRecruiters/Workday — only the detail of
# design-relevant titles gets fetched, to keep request counts polite.
#
# reCAPTCHA on the embed gates the APPLY flow only, not the listing or
# detail HTML, so scanning is unaffected.

import json
import re

from . import get_text, strip_html

BASE = "https://jobs.jobvite.com"

_DESIGN_HINT_RE = re.compile(
    r"\bdesign|\bcreative|art\s+director|\bbrand|\bvisual|\bux\b|\bui\b", re.I
)

# Section headers and job rows, matched in one pass so each row can be
# tagged with the category header that precedes it.
_SECTION_OR_ROW_RE = re.compile(
    r'<h3 class="h2">(?P<section>.*?)</h3>'
    r'|<td class="jv-job-list-name">\s*<a href="[^"]*/job/(?P<id>[^"?]+)"[^>]*>'
    r'(?P<title>.*?)</a>.*?'
    r'<td class="jv-job-list-location">(?P<location>.*?)</td>',
    re.S,
)

_LDJSON_RE = re.compile(
    r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', re.S
)


def _job_posting_ld(html_text):
    """Return the schema.org JobPosting dict from a detail page, or {}."""
    for block in _LDJSON_RE.findall(html_text or ""):
        try:
            data = json.loads(block.strip())
        except ValueError:
            continue
        if isinstance(data, dict) and data.get("@type") == "JobPosting":
            return data
    return {}


def fetch(slug):
    listing = get_text(f"{BASE}/{slug}/jobs?nl=1")
    if not listing:
        return []

    postings = []
    section = ""
    for m in _SECTION_OR_ROW_RE.finditer(listing):
        if m.group("section") is not None:
            section = strip_html(m.group("section"))
            continue

        job_id = m.group("id")
        title = strip_html(m.group("title"))
        location = strip_html(m.group("location"))
        if not job_id or not title:
            continue

        url = f"{BASE}/{slug}/job/{job_id}"
        company = slug
        description = ""
        posted = None
        remote = True if re.search(r"\bremote\b", f"{title} {location}", re.I) else None

        if _DESIGN_HINT_RE.search(title):
            ld = _job_posting_ld(get_text(f"{url}?nl=1"))
            description = ld.get("description") or ""
            posted = ld.get("datePosted") or None
            org = ld.get("hiringOrganization")
            if isinstance(org, dict):
                org = org.get("name")
            company = org or slug

        postings.append({
            "department": section,
            "company": company,
            "source": "jobvite",
            "id": job_id,
            "title": title,
            "location": location,
            "remote": remote,
            "url": url,
            "posted": posted,
            "description": description,
        })
    return postings
