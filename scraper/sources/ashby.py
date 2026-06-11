# Ashby public job board API.
# https://api.ashbyhq.com/posting-api/job-board/{slug}

from . import get_json


def fetch(slug):
    data = get_json(f"https://api.ashbyhq.com/posting-api/job-board/{slug}")
    if not data or not data.get("jobs"):
        return []
    postings = []
    for job in data["jobs"]:
        if job.get("isListed") is False:
            continue
        location = job.get("location") or ""
        postings.append({
            "department": job.get("department") or job.get("team") or "",
            "company": slug,
            "source": "ashby",
            "id": str(job.get("id", "")),
            "title": (job.get("title") or "").strip(),
            "location": location.strip(),
            "remote": job.get("isRemote"),
            "url": job.get("jobUrl", ""),
            "posted": job.get("publishedAt"),
            "description": job.get("descriptionPlain")
                or job.get("descriptionHtml") or "",
        })
    return postings
