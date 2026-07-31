# Source adapters — one small module per ATS platform.
# Each adapter exposes fetch(slug) -> list[dict] of normalized postings:
#   { company, source, id, title, location, remote, url, posted, description }
# posted is an ISO date string or None. Adapters return [] on any failure —
# a slug that isn't on that platform is normal, not an error.

import html
import json
import re
import threading
import time
import urllib.request
import urllib.error
from urllib.parse import urlsplit

USER_AGENT = "job-hunter-assistant scraper (local, personal use)"
REQUEST_GAP_SECONDS = 0.5

# Per-host rate limiting: unrelated hosts (Greenhouse vs Workday vs
# SmartRecruiters) shouldn't queue behind each other — only requests to
# the SAME host need to stay REQUEST_GAP_SECONDS apart. `_last_request`
# tracks the last request time per hostname; `_host_locks` gives each
# host its own lock so concurrent threads hitting that host serialize
# (wait-then-request happens atomically per host, never less than the
# gap between two requests to the same host). `_locks_guard` only
# protects creation of a new per-host lock, not the request itself.
_last_request = {}
_host_locks = {}
_locks_guard = threading.Lock()


def _lock_for(host):
    with _locks_guard:
        lock = _host_locks.get(host)
        if lock is None:
            lock = threading.Lock()
            _host_locks[host] = lock
        return lock


def _throttle(url):
    """Block until it's been >= REQUEST_GAP_SECONDS since the last
    request to this URL's host. Returns the lock already held so the
    caller can release it after the request completes (keeping the
    whole wait+request+stamp sequence atomic per host)."""
    host = urlsplit(url).netloc
    lock = _lock_for(host)
    lock.acquire()
    wait = REQUEST_GAP_SECONDS - (time.time() - _last_request.get(host, 0.0))
    if wait > 0:
        time.sleep(wait)
    return host, lock


def _mark_done(host, lock):
    _last_request[host] = time.time()
    lock.release()


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


def strip_html(value):
    """Tags out, entities decoded, whitespace collapsed. Shared by every
    adapter that gets HTML-flavored description text back from its API
    (Workday, Eightfold, Workable, Publicis, BambooHR) — was copy-pasted
    five times with a hand-rolled entity list before this. html.unescape
    handles the FULL entity set (named + numeric, e.g. &amp; &#39;
    &nbsp;), which the old hand-rolled version didn't."""
    text = re.sub(r"<[^>]+>", " ", value or "")
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def get_json(url):
    """Fetch a URL and parse JSON. Returns None on any failure.
    Enforces a small gap between requests to the same host — these are
    public APIs; be a polite guest. Requests to different hosts don't
    wait on each other (see _throttle)."""
    host, lock = _throttle(url)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.load(resp)
    except (urllib.error.URLError, json.JSONDecodeError, TimeoutError, OSError):
        return None
    finally:
        _mark_done(host, lock)
    return data


def get_text(url):
    """Fetch a URL and return the raw response body as text. Returns None
    on any failure. Same per-host rate limiter as get_json. For adapters
    whose board is server-rendered HTML rather than a JSON API (Jobvite),
    parsed downstream with regex + the shared strip_html."""
    host, lock = _throttle(url)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            charset = resp.headers.get_content_charset() or "utf-8"
            return resp.read().decode(charset, errors="replace")
    except (urllib.error.URLError, TimeoutError, OSError):
        return None
    finally:
        _mark_done(host, lock)


def post_json(url, payload):
    """POST a JSON body and parse the JSON response. Returns None on any
    failure. Shares the same per-host rate limiter as get_json —
    Workday's CXS API in particular has shown transient blanket 400s
    under bursty request patterns, so every adapter hitting a given host
    stays under one gap for that host."""
    host, lock = _throttle(url)
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
        _mark_done(host, lock)
    return data


def get_sources():
    from . import (
        greenhouse, lever, ashby, bamboohr, workable, publicis,
        workday, eightfold, smartrecruiters, jobvite,
    )
    return {
        "greenhouse":     greenhouse,
        "lever":          lever,
        "ashby":          ashby,
        "bamboohr":       bamboohr,
        "workable":       workable,
        "publicis":       publicis,
        "workday":        workday,
        "eightfold":      eightfold,
        "smartrecruiters": smartrecruiters,
        "jobvite":        jobvite,
    }
