# Workable public job board widget API.
# https://apply.workable.com/api/v1/widget/accounts/{slug}?details=true
# Returns the account + all jobs WITH full descriptions in one call — no
# per-job detail request needed, and no API key. Slug is the company's
# Workable subdomain (apply.workable.com/{slug} or .../api/.../{slug}).

import re
from . import get_json


def _strip_html(html):
    text = re.sub(r"<[^>]+>", " ", html or "")
    for entity, char in [("&amp;", "&"), ("&lt;", "<"), ("&gt;", ">"),
                          ("&nbsp;", " "), ("&#39;", "'"), ("&quot;", '"')]:
        text = text.replace(entity, char)
    text = re.sub(r"&#\d+;", "", text)
    return re.sub(r"\s+", " ", text).strip()


def fetch(slug):
    data = get_json(
        f"https://apply.workable.com/api/v1/widget/accounts/{slug}?details=true"
    )
    if not data or not data.get("jobs"):
        return []
    company = data.get("name") or slug
    postings = []
    for job in data["jobs"]:
        shortcode = job.get("shortcode") or ""
        location = ", ".join(filter(None, [
            job.get("city") or "", job.get("state") or "", job.get("country") or "",
        ]))
        url = job.get("shortlink") or job.get("url") or (
            f"https://apply.workable.com/j/{shortcode}" if shortcode else ""
        )
        postings.append({
            "company":     company,
            "source":      "workable",
            "id":          str(shortcode),
            "title":       (job.get("title") or "").strip(),
            "department":  job.get("department") or "",
            "location":    location,
            "remote":      bool(job.get("telecommuting")),
            "url":         url,
            "posted":      job.get("published_on") or job.get("created_at"),
            "description": _strip_html(job.get("description") or ""),
        })
    return postings
