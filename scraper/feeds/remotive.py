# Remotive public API. https://remotive.com/api/remote-jobs?category=design
# All postings are remote by definition; candidate_required_location
# narrows the region ("USA", "Worldwide", ...).

from urllib.parse import quote

from sources import get_json


def fetch(arg=None):
    url = "https://remotive.com/api/remote-jobs"
    if arg:
        url += f"?category={quote(arg)}"
    data = get_json(url)
    if not data or not data.get("jobs"):
        return []
    postings = []
    for job in data["jobs"]:
        postings.append({
            "company": job.get("company_name") or "unknown",
            "source": "remotive",
            "id": str(job.get("id", "")),
            "title": (job.get("title") or "").strip(),
            "location": (job.get("candidate_required_location") or "").strip(),
            "remote": True,
            "url": job.get("url", ""),
            "posted": job.get("publication_date"),
            "description": job.get("description") or "",
            "department": job.get("category") or "",
        })
    return postings
