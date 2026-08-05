# Hacker News monthly "hiring" threads, via the public Algolia API.
# https://hn.algolia.com/api/v1/search_by_date  +  /items/{id}
#
# Two direct-from-source, no-middleman gig lanes, posted monthly by user
# "whoishiring":
#   - "Ask HN: Who is hiring?"                 -> employers posting roles
#   - "Ask HN: Freelancer? Seeking freelancer?"-> two kinds of top-level
#     comment: "SEEKING WORK" (freelancers advertising — NOT leads) and
#     "SEEKING FREELANCER" (clients wanting to hire — the actual leads).
#
# We always resolve the LATEST thread of each dynamically (never hardcode
# a month) because the live HN data can lag any given calendar date. Each
# top-level comment becomes one posting; the wide-net philosophy holds —
# the adapter returns broadly and the gig-lane filters narrow by
# discipline + the marketplace-exclude. Returns [] on any failure.
#
# `kind` distinguishes a real lead ("client") from a competitor ad
# ("worker") so the lane can drop the latter; feeds/__init__ documents the
# shared dict shape, plus these HN-only extras: employment, kind.

import re

from sources import get_json, strip_html

_ALGOLIA = "https://hn.algolia.com/api/v1"


def _latest_thread(title_needle):
    """objectID of the most recent whoishiring story whose title contains
    title_needle (case-insensitive), or None."""
    data = get_json(
        f"{_ALGOLIA}/search_by_date?tags=story,author_whoishiring"
        f"&query={title_needle.replace(' ', '%20')}&hitsPerPage=10"
    )
    for hit in (data or {}).get("hits", []):
        if title_needle.lower() in (hit.get("title") or "").lower():
            return hit.get("objectID")
    return None


def _first_line(text):
    for line in text.splitlines():
        line = line.strip()
        if line:
            return line
    return text[:80]


def _posting(comment, kind):
    raw = comment.get("text") or ""
    text = strip_html(raw)
    if not text:
        return None
    author = comment.get("author") or "unknown"
    oid = str(comment.get("id") or comment.get("objectID") or "")
    return {
        "company": f"HN: {author}",
        "source": "hackernews",
        "id": oid,
        "title": _first_line(text)[:140],
        "location": "remote" if re.search(r"\bremote\b", text, re.I) else "",
        "remote": True if re.search(r"\bremote\b", text, re.I) else None,
        "url": f"https://news.ycombinator.com/item?id={oid}",
        "posted": comment.get("created_at"),
        "description": text,
        "department": "",
        "employment": "gig",
        "kind": kind,
    }


def fetch(arg=None):
    postings = []

    hiring = _latest_thread("Who is hiring?")
    if hiring:
        data = get_json(f"{_ALGOLIA}/items/{hiring}")
        for c in (data or {}).get("children", []):
            # Every top-level comment in this thread is an employer role.
            p = _posting(c, kind="client")
            if p:
                postings.append(p)

    freelance = _latest_thread("Seeking freelancer?")
    if freelance:
        data = get_json(f"{_ALGOLIA}/items/{freelance}")
        for c in (data or {}).get("children", []):
            text = strip_html(c.get("text") or "")
            # Only "SEEKING FREELANCER" comments are leads (a client
            # hiring). "SEEKING WORK" comments are other freelancers
            # advertising — competitors, not leads — so tag them 'worker'
            # and let the lane drop them.
            head = text[:40].upper()
            kind = "client" if head.startswith("SEEKING FREELANCER") else "worker"
            p = _posting(c, kind=kind)
            if p:
                postings.append(p)

    return postings
