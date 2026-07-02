# NeoGov / GovernmentJobs.com — state and local government jobs
#
# NeoGov is the dominant platform for US state and local government hiring:
# city, county, transit, courts, school districts, port authorities.
# Most large US municipalities are on it — Seattle, King County, WA State,
# NYC, LA, Chicago, etc.
#
# CURRENT STATUS: read-only HTML only (no public API)
#
# NeoGov's job board is a React SPA — job listings are loaded client-side
# via authenticated XHR after page load. The initial HTML render contains
# no job data, so stdlib urllib can't reach it without a headless browser.
#
# A headless-browser adapter (Playwright, Selenium) is a tracked TODO but
# would add a non-trivial dependency. The stub below is intentionally
# transparent: it tells users which agencies to check manually and what
# the URL patterns are, rather than silently returning nothing.
#
# When the headless adapter is ready, it will live here and accept the
# same `arg` interface as every other feed: "- neogov (seattle)" in the
# watchlist will trigger fetch("seattle").
#
# AGENCY SLUGS — governmentjobs.com/careers/{slug}:
#   Federal/national:  usds, gsa, dol, va, nasa, nih, cdc
#   West Coast:        seattle, kingcounty, washington, portland,
#                      oregon, losangeles, sanfrancisco, sandiego
#   Midwest/East:      chicago, nyc, boston, dc, md, virginia
#   Tech agencies:     gsa (18F/TTS), digitalservice (USDS)
#
# For now, use these for manual checks or copy the URL into JD Analysis.

_AGENCY_BASE = "https://www.governmentjobs.com/careers"

# Populated in get_neogov_url() for users who want a direct link.
_KNOWN_SLUGS = {
    # WA / Pacific NW
    "seattle": "City of Seattle",
    "kingcounty": "King County",
    "washington": "Washington State",
    "portland": "City of Portland",
    "oregon": "State of Oregon",
    # CA
    "losangeles": "City of LA",
    "sanfrancisco": "City of San Francisco",
    "sandiego": "City of San Diego",
    # IL/NY
    "chicago": "City of Chicago",
    "nyc": "New York City",
    # Federal-ish (USDS / GSA are on USAJobs, but some orgs are here)
    "dc": "District of Columbia",
}


def get_neogov_url(slug, keyword=""):
    """Returns the URL to check manually for a given agency slug."""
    params = f"?keyword={keyword}" if keyword else ""
    return f"{_AGENCY_BASE}/{slug}/jobs{params}"


def fetch(arg=None):
    """NeoGov adapter — not yet implemented (requires headless browser).

    Returns a single informational posting so the user knows it's
    configured but waiting on the adapter, rather than silently skipping.
    """
    slug = arg or "washington"
    label = _KNOWN_SLUGS.get(slug, slug)
    url = get_neogov_url(slug)
    desc_lines = [
        f"NeoGov adapter for '{slug}' ({label}) is not yet implemented.",
        "",
        "NeoGov loads jobs client-side via JavaScript — a headless browser",
        "adapter is needed to read them. This is a tracked TODO.",
        "",
        "To check this board manually:",
        f"  {url}",
        "",
        "Other common NeoGov agency slugs:",
    ]
    for s, name in _KNOWN_SLUGS.items():
        desc_lines.append(f"  {s:20} {_AGENCY_BASE}/{s}/jobs")
    desc_lines += [
        "",
        "For federal roles, use 'usajobs' in ## Feeds — it has a real API.",
    ]

    return [{
        "company": f"NeoGov — {label}",
        "source": "neogov",
        "id": f"neogov-stub-{slug}",
        "title": f"[NeoGov adapter not yet implemented — see {url}]",
        "location": "",
        "remote": False,
        "url": url,
        "posted": None,
        "description": "\n".join(desc_lines),
        "department": "setup",
    }]
