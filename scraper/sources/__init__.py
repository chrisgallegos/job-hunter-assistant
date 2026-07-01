# Source adapters — one small module per ATS platform.
# Each adapter exposes fetch(slug) -> list[dict] of normalized postings:
#   { company, source, id, title, location, remote, url, posted, description }
# posted is an ISO date string or None. Adapters return [] on any failure —
# a slug that isn't on that platform is normal, not an error.

import json
import time
import urllib.request
import urllib.error

USER_AGENT = "job-hunter-toolkit scraper (local, personal use)"
REQUEST_GAP_SECONDS = 0.5

_last_request = [0.0]

# Design-relevant search terms for adapters that filter SERVER-SIDE
# (Workday, Eightfold) instead of fetching a whole board. The polite,
# scalable move: ask the board for what we want one term at a time,
# rather than pulling thousands of jobs to find five.
#
# This list is the knob, tuned by hand over time — the same
# learn-from-the-files loop as learnings.md → watchlist, but for the
# query layer. Add a term, watch the next few scans: if it keeps
# surfacing real roles it earns its place; if it only returns noise,
# drop it. Don't try to make it exhaustive in one sitting. Results are
# deduped by req id, so overlap between terms is harmless.
DESIGN_SEARCH_TERMS = ["design", "creative", "brand", "art director"]


def get_json(url):
    """Fetch a URL and parse JSON. Returns None on any failure.
    Enforces a small gap between requests — these are public APIs;
    be a polite guest."""
    wait = REQUEST_GAP_SECONDS - (time.time() - _last_request[0])
    if wait > 0:
        time.sleep(wait)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.load(resp)
    except (urllib.error.URLError, json.JSONDecodeError, TimeoutError, OSError):
        return None
    finally:
        _last_request[0] = time.time()
    return data


def post_json(url, payload):
    """POST a JSON body and parse the JSON response. Returns None on any
    failure. Shares the same rate limiter as get_json — Workday's CXS
    API in particular has shown transient blanket 400s under bursty
    request patterns, so all adapters stay under one shared gap."""
    wait = REQUEST_GAP_SECONDS - (time.time() - _last_request[0])
    if wait > 0:
        time.sleep(wait)
    body = json.dumps(payload).encode()
    req = urllib.request.Request(
        url, data=body, method="POST",
        headers={"User-Agent": USER_AGENT, "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.load(resp)
    except (urllib.error.URLError, json.JSONDecodeError, TimeoutError, OSError):
        return None
    finally:
        _last_request[0] = time.time()
    return data


def get_sources():
    from . import (
        greenhouse, lever, ashby, bamboohr, workable, publicis,
        workday, eightfold,
    )
    return {
        "greenhouse": greenhouse,
        "lever":      lever,
        "ashby":      ashby,
        "bamboohr":   bamboohr,
        "workable":   workable,
        "publicis":   publicis,
        "workday":    workday,
        "eightfold":  eightfold,
    }
