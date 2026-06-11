# USAJobs public API — https://developer.usajobs.gov/
#
# Requires a free API key from https://developer.usajobs.gov/APIRequest/Index
# Registration is quick (email + intended use). No payment, no vetting.
#
# Configure your key in one of two ways:
#
#   Option 1 — environment variable (recommended):
#     export USAJOBS_API_KEY="your-key-here"
#     export USAJOBS_USER_AGENT="your@email.com"
#
#   Option 2 — private/usajobs.env file in the toolkit root:
#     USAJOBS_API_KEY=your-key-here
#     USAJOBS_USER_AGENT=your@email.com
#
# Watchlist entry:
#   - usajobs (design)        # "design" is a keyword, not a category
#   - usajobs (ux designer)   # more specific — whatever you'd type in a search
#   - usajobs (visual designer remote)
#
# Notable federal employers for designers:
#   USDS (United States Digital Service), GSA (18F / TTS), VA, NIH, NASA,
#   DHS, DOL, CFPB. Pay is GS schedule — GS-12/13 maps to ~$90–$130k
#   depending on locality. Remote has expanded significantly post-pandemic.

import os
import re
import urllib.parse
from pathlib import Path

from sources import get_json

_CONFIG_FILE = Path(__file__).resolve().parent.parent.parent / "private" / "usajobs.env"


def _load_config():
    key = os.environ.get("USAJOBS_API_KEY", "")
    agent = os.environ.get("USAJOBS_USER_AGENT", "")
    if not key and _CONFIG_FILE.exists():
        for line in _CONFIG_FILE.read_text().splitlines():
            line = line.strip()
            if line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            k, v = k.strip(), v.strip()
            if k == "USAJOBS_API_KEY":
                key = v
            elif k == "USAJOBS_USER_AGENT":
                agent = v
    return key.strip(), agent.strip()


def fetch(arg=None):
    api_key, user_agent = _load_config()
    if not api_key:
        # Return a sentinel posting that tells the user what to do — better
        # than a silent empty list that looks like "no federal jobs today."
        return [{
            "company": "USAJobs (setup needed)",
            "source": "usajobs",
            "id": "setup",
            "title": "Add your free USAJobs API key to get federal job listings",
            "location": "",
            "remote": False,
            "url": "https://developer.usajobs.gov/APIRequest/Index",
            "posted": None,
            "description": (
                "USAJobs requires a free API key. Register at "
                "https://developer.usajobs.gov/APIRequest/Index — "
                "email + intended use, no payment. Then add to "
                "private/usajobs.env:\n\n"
                "  USAJOBS_API_KEY=your-key\n"
                "  USAJOBS_USER_AGENT=your@email.com\n\n"
                "Notable employers: USDS, GSA/18F, VA, NIH, NASA, CFPB. "
                "GS-12/13 pay (~$90–$130k); remote widely available."
            ),
            "department": "setup",
        }]

    keyword = arg or "designer"
    params = urllib.parse.urlencode({
        "Keyword": keyword,
        "ResultsPerPage": 50,
        "SortField": "OpenDate",
        "SortDirection": "Desc",
    })
    url = f"https://data.usajobs.gov/api/search?{params}"

    import urllib.request
    import json
    import time

    req = urllib.request.Request(url, headers={
        "User-Agent": user_agent or "job-hunter-toolkit",
        "Authorization-Key": api_key,
        "Host": "data.usajobs.gov",
    })
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.load(resp)
    except Exception:
        return []

    items = (
        data.get("SearchResult", {})
            .get("SearchResultItems", [])
    )
    postings = []
    for item in items:
        pos = item.get("MatchedObjectDescriptor", {})
        title = (pos.get("PositionTitle") or "").strip()
        org = pos.get("OrganizationName") or pos.get("DepartmentName") or "Federal"
        locations = pos.get("PositionLocation") or []
        location = "; ".join(
            loc.get("LocationName", "") for loc in locations
            if loc.get("LocationName")
        )
        remote = bool(pos.get("RemoteIndicator"))
        apply_uris = pos.get("ApplyURI") or []
        url_out = apply_uris[0] if apply_uris else pos.get("PositionURI", "")
        posted = pos.get("PublicationStartDate")
        description = (
            pos.get("QualificationSummary") or
            (pos.get("UserArea") or {}).get("Details", {}).get("JobSummary") or ""
        )
        salary_parts = pos.get("PositionRemuneration") or []
        salary_str = ""
        if salary_parts:
            s = salary_parts[0]
            lo = s.get("MinimumRange", "")
            hi = s.get("MaximumRange", "")
            unit = s.get("RateIntervalCode", "")
            if lo or hi:
                salary_str = f"${lo}–${hi} {unit}".strip()
        if salary_str:
            description = f"Salary: {salary_str}\n\n{description}"
        dept = pos.get("DepartmentName") or org

        postings.append({
            "company": org,
            "source": "usajobs",
            "id": pos.get("PositionID", ""),
            "title": title,
            "location": location,
            "remote": remote,
            "url": url_out,
            "posted": posted,
            "description": description,
            "department": dept,
        })
    return postings
