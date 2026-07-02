# We Work Remotely RSS.
# https://weworkremotely.com/categories/remote-design-jobs.rss
# Item titles are "Company: Role". The category slug comes from the
# watchlist arg: "- weworkremotely (design)" -> remote-design-jobs.rss.

import time
import urllib.request
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from urllib.parse import quote

from sources import USER_AGENT


def fetch(arg=None):
    if arg:
        url = f"https://weworkremotely.com/categories/remote-{quote(arg)}-jobs.rss"
    else:
        url = "https://weworkremotely.com/remote-jobs.rss"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            root = ET.fromstring(resp.read())
    except Exception:
        return []

    postings = []
    for item in root.iter("item"):
        def text(tag):
            el = item.find(tag)
            return (el.text or "").strip() if el is not None else ""

        raw_title = text("title")
        company, _, title = raw_title.partition(": ")
        if not title:
            company, title = "unknown", raw_title

        posted = None
        if text("pubDate"):
            try:
                posted = parsedate_to_datetime(text("pubDate")).isoformat()
            except (ValueError, TypeError):
                pass

        postings.append({
            "company": company.strip(),
            "source": "weworkremotely",
            "id": text("guid") or text("link"),
            "title": title.strip(),
            "location": text("region"),
            "remote": True,
            "url": text("link"),
            "posted": posted,
            "description": text("description"),
            "department": arg or "",
        })
    return postings
