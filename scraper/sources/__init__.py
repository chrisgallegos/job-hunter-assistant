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


def get_sources():
    from . import greenhouse, lever, ashby, bamboohr, workable
    return {
        "greenhouse": greenhouse,
        "lever":      lever,
        "ashby":      ashby,
        "bamboohr":   bamboohr,
        "workable":   workable,
    }
