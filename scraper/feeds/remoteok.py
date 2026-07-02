# RemoteOK public API. https://remoteok.com/api?tag=design
# First element of the response is a legal/attribution notice, not a
# job. RemoteOK asks that the `url` link back to them — it does.

from urllib.parse import quote

from sources import get_json


def fetch(arg=None):
    url = "https://remoteok.com/api"
    if arg:
        url += f"?tag={quote(arg)}"
    data = get_json(url)
    if not isinstance(data, list):
        return []
    postings = []
    for job in data:
        if not job.get("position"):
            continue
        postings.append({
            "company": job.get("company") or "unknown",
            "source": "remoteok",
            "id": str(job.get("id", "")),
            "title": (job.get("position") or "").strip(),
            "location": (job.get("location") or "").strip(),
            "remote": True,
            "url": job.get("url", ""),
            "posted": job.get("date"),
            "description": job.get("description") or "",
            "department": "",
        })
    return postings
