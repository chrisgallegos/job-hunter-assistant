# BambooHR public job board API.
# Listing: https://{slug}.bamboohr.com/careers/list
# Detail:  https://{slug}.bamboohr.com/careers/{id}/detail
# No API key needed for public job listings.

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
    data = get_json(f"https://{slug}.bamboohr.com/careers/list")
    if not data or not data.get("result"):
        return []
    postings = []
    for job in data["result"]:
        job_id = job.get("id", "")
        loc = job.get("location") or {}
        location = ", ".join(filter(None, [loc.get("city") or "", loc.get("state") or ""]))

        detail = get_json(f"https://{slug}.bamboohr.com/careers/{job_id}/detail")
        opening = ((detail or {}).get("result") or {}).get("jobOpening") or {}
        description = _strip_html(opening.get("description") or "")
        url = opening.get("jobOpeningShareUrl") or f"https://{slug}.bamboohr.com/careers/{job_id}"

        postings.append({
            "company":     slug,
            "source":      "bamboohr",
            "id":          str(job_id),
            "title":       (job.get("jobOpeningName") or "").strip(),
            "department":  job.get("departmentLabel") or "",
            "location":    location,
            "remote":      bool(job.get("isRemote")),
            "url":         url,
            "posted":      None,
            "description": description,
        })
    return postings
