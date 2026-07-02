# Lever public postings API.
# https://api.lever.co/v0/postings/{slug}?mode=json
# Returns [] (valid JSON) for unknown slugs and for boards with no postings.

from datetime import datetime, timezone

from . import get_json


def fetch(slug):
    data = get_json(f"https://api.lever.co/v0/postings/{slug}?mode=json")
    if not isinstance(data, list) or not data:
        return []
    postings = []
    for job in data:
        cats = job.get("categories") or {}
        location = cats.get("location") or ""
        workplace = (job.get("workplaceType") or "").lower()
        created = job.get("createdAt")
        posted = None
        if isinstance(created, (int, float)):
            posted = datetime.fromtimestamp(
                created / 1000, tz=timezone.utc
            ).isoformat()
        postings.append({
            "department": cats.get("department") or cats.get("team") or "",
            "company": slug,
            "source": "lever",
            "id": str(job.get("id", "")),
            "title": (job.get("text") or "").strip(),
            "location": location.strip(),
            "remote": workplace == "remote" or "remote" in location.lower() or None,
            "url": job.get("hostedUrl", ""),
            "posted": posted,
            "description": job.get("descriptionPlain")
                or job.get("description") or "",
        })
    return postings
