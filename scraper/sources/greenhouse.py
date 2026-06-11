# Greenhouse public board API.
# https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true
# `content` comes back as entity-escaped HTML; scrape.py converts to text.

import html

from . import get_json


def fetch(slug):
    data = get_json(
        f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true"
    )
    if not data or not data.get("jobs"):
        return []
    postings = []
    for job in data["jobs"]:
        location = (job.get("location") or {}).get("name", "") or ""
        # Some boards (e.g. Epic) pad locations with literal BLANK segments:
        # "BLANK,BLANK,Multiple Locations"
        location = ", ".join(
            part.strip() for part in location.split(",")
            if part.strip() and part.strip().upper() != "BLANK"
        )
        departments = [
            d.get("name", "") for d in (job.get("departments") or []) if d
        ]
        postings.append({
            "department": ", ".join(d for d in departments if d),
            "company": job.get("company_name") or slug,
            "source": "greenhouse",
            "id": str(job.get("id", "")),
            "title": (job.get("title") or "").strip(),
            "location": location.strip(),
            "remote": "remote" in location.lower() or None,
            "url": job.get("absolute_url", ""),
            "posted": job.get("first_published") or job.get("updated_at"),
            "description": html.unescape(job.get("content") or ""),
        })
    return postings
