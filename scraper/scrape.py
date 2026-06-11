#!/usr/bin/env python3
"""Job Hunter Toolkit — scraping layer (rung three of the ladder).

Pulls fresh postings straight from public ATS APIs (Greenhouse, Lever,
Ashby) for the companies in your watchlist, filters them against your
title/location criteria, scores relevance, and writes Markdown into
private/jobs/ — a digest of what's new, plus one file per posting ready
to drop into the JD analysis workflow.

Local only. Standard library only. No accounts, no tokens, no telemetry.

Usage:
  python3 scrape.py                      # scan the watchlist, write digest
  python3 scrape.py --days 3             # only postings from the last 3 days
  python3 scrape.py --rescan             # include postings already seen
  python3 scrape.py --probe somecompany  # which ATS hosts this company?
  python3 scrape.py --company epicgames --source greenhouse   # one-off pull

Watchlist lives at private/watchlist.md (copy scraper/watchlist.example.md).
"""

import argparse
import json
import re
import sys
from datetime import datetime, timedelta, timezone
from html.parser import HTMLParser
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sources import get_sources
from feeds import get_feeds

ROOT = Path(__file__).resolve().parent.parent
WATCHLIST = ROOT / "private" / "watchlist.md"
EXAMPLE_WATCHLIST = Path(__file__).resolve().parent / "watchlist.example.md"
JOBS_DIR = ROOT / "private" / "jobs"
POSTINGS_DIR = JOBS_DIR / "postings"
SEEN_FILE = JOBS_DIR / ".seen.json"
DISMISSED_FILE = JOBS_DIR / "dismissed.json"
VERDICTS_FILE = JOBS_DIR / "verdicts.json"
REVIEW_QUEUE = JOBS_DIR / "review-queue.md"
LEARNINGS_FILE = JOBS_DIR / "learnings.md"


# ─── HTML → text ─────────────────────────────────────────────

class _TextExtractor(HTMLParser):
    BLOCK_TAGS = {"p", "br", "li", "div", "h1", "h2", "h3", "h4", "h5",
                  "ul", "ol", "tr"}

    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag in self.BLOCK_TAGS:
            self.parts.append("\n")
        if tag == "li":
            self.parts.append("- ")

    def handle_data(self, data):
        self.parts.append(data)


def html_to_text(value):
    if "<" not in value:
        return value.strip()
    parser = _TextExtractor()
    parser.feed(value)
    text = "".join(parser.parts)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r" ?\n ?", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


# ─── Watchlist ───────────────────────────────────────────────

def parse_watchlist(path):
    """Sections are '## ' headings; entries are '- ' list items.
    Companies may pin a source: '- epicgames (greenhouse)'."""
    sections = {}
    current = None
    for line in path.read_text().splitlines():
        line = line.strip()
        if line.startswith("## "):
            current = line[3:].strip().lower()
            sections[current] = []
        elif line.startswith("- ") and current:
            entry = line[2:].split("#")[0].strip()
            if entry:
                sections[current].append(entry)

    def slug_entries(key):
        entries = []
        for entry in sections.get(key, []):
            match = re.match(r"^(\S+)(?:\s*\(([\w-]+)\))?$", entry)
            if match:
                entries.append((match.group(1), match.group(2)))
        return entries

    def lowered(key):
        return [e.lower() for e in sections.get(key, [])]

    return {
        "companies": slug_entries("companies"),
        "feeds": slug_entries("feeds"),
        "title_includes": lowered("title must match one of"),
        "strong_titles": lowered("strong titles"),
        "title_excludes": lowered("title excludes"),
        "department_excludes": lowered("department excludes"),
        "boost_keywords": lowered("boost keywords"),
        "locations": lowered("locations"),
    }


# ─── Filtering and scoring ───────────────────────────────────

def kw_match(kw, text):
    """Substring match, except short keywords ('ui', 'ux', '3d') match
    on word boundaries only — plain substring would hit 'bUIlding' or
    'gUIld'. Longer keywords keep substring semantics so 'design'
    still matches 'designer'."""
    if len(kw) <= 3:
        return re.search(
            rf"(?<![a-z0-9]){re.escape(kw)}(?![a-z0-9])", text
        ) is not None
    return kw in text


def passes_filters(posting, criteria):
    title = posting["title"].lower()
    # Strong titles always satisfy the title gate; the generic includes
    # are the wider net. Tiering happens in score(), not here.
    title_gate = criteria["title_includes"] + criteria["strong_titles"]
    if title_gate and not any(kw_match(kw, title) for kw in title_gate):
        return False
    if any(kw_match(kw, title) for kw in criteria["title_excludes"]):
        return False
    department = (posting.get("department") or "").lower()
    if department and any(
        kw_match(kw, department) for kw in criteria["department_excludes"]
    ):
        return False
    if criteria["locations"]:
        location = posting["location"].lower()
        # "Multiple Locations" style values are unknowns, not mismatches —
        # they often include remote. Keep them for human judgment.
        vague = "multiple locations" in location or "flexible" in location
        if not (
            posting["remote"]
            or not location
            or vague
            or any(loc in location for loc in criteria["locations"])
        ):
            return False
    return True


def score(posting, criteria):
    points = 0
    title = posting["title"].lower()
    # Tier 1: your actual discipline ranks above generic title matches.
    if any(kw_match(kw, title) for kw in criteria["strong_titles"]):
        points += 3
    if any(level in title for level in ("senior", "lead", "principal", "staff")):
        points += 2
    haystack = " ".join([
        title,
        posting["company"].lower(),
        (posting.get("department") or "").lower(),
        posting["description"][:4000].lower(),
    ])
    points += min(5, sum(
        1 for kw in criteria["boost_keywords"] if kw_match(kw, haystack)
    ))
    if posting["remote"]:
        points += 1
    return points


# Source hierarchy: free platforms > paid feeds.
# When the same job appears on multiple sources, prefer the free version.
SOURCE_COST = {
    "greenhouse": 0,
    "lever": 0,
    "ashby": 0,
    "remotive": 1,
    "weworkremotely": 1,
    "remoteok": 2,  # pay-to-play; deprioritize
}


def posting_dedup_key(posting):
    """Normalize company + title for cross-source dedup.
    Two postings with the same key are considered the same role."""
    co = posting["company"].lower().strip()
    ti = posting["title"].lower().strip()
    # Remove common qualifiers
    ti = ti.replace("(contract)", "").replace("(part-time)", "").strip()
    return f"{co}|{ti}"


def parse_posted(posting):
    raw = posting.get("posted")
    if not raw:
        return None
    try:
        stamp = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        if stamp.tzinfo is None:
            stamp = stamp.replace(tzinfo=timezone.utc)
        return stamp
    except ValueError:
        return None


# ─── Output ──────────────────────────────────────────────────

def slugify(text, max_len=60):
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug[:max_len].rstrip("-")


def write_posting_file(posting, today):
    POSTINGS_DIR.mkdir(parents=True, exist_ok=True)
    name = f"{today}-{slugify(posting['company'])}-{slugify(posting['title'])}.md"
    path = POSTINGS_DIR / name
    posted = parse_posted(posting)
    posted_str = posted.date().isoformat() if posted else "unknown"
    path.write_text(f"""# {posting['title']} — {posting['company']}

- **Company:** {posting['company']}
- **Title:** {posting['title']}
- **Location:** {posting['location'] or 'not listed'}{' (remote)' if posting['remote'] else ''}
- **Department:** {posting.get('department') or 'not listed'}
- **Posted:** {posted_str}
- **Source:** {posting['source']}
- **URL:** {posting['url']}

> Scraped {today}. To analyze: copy templates/jd-analysis.md to
> private/jd-{slugify(posting['company'])}-{slugify(posting['title'], 30)}.md
> and paste the description below into "The posting."

---

{html_to_text(posting['description'])}
""")
    return path


def write_latest_json(results, today, days):
    """Machine-readable sidecar of the latest digest, for the local app
    (serve.py). The Markdown digest remains the canonical artifact —
    this is a view over the same data, regenerated on every scan."""
    JOBS_DIR.mkdir(parents=True, exist_ok=True)
    postings = []
    for posting, points, file_path in results:
        posted = parse_posted(posting)
        postings.append({
            "company": posting["company"],
            "title": posting["title"],
            "department": posting.get("department") or "",
            "location": posting["location"],
            "remote": bool(posting["remote"]),
            "url": posting["url"],
            "source": posting["source"],
            "posted": posted.date().isoformat() if posted else None,
            "score": points,
            "file": str(file_path.relative_to(ROOT)),
            "description": html_to_text(posting["description"]),
        })
    payload = {"generated": today, "days": days, "postings": postings}
    (JOBS_DIR / "latest.json").write_text(json.dumps(payload, indent=1))


def extract_requirements(text, limit=600):
    """Token-lean excerpt of a posting for AI review: the lines that
    read like requirements, capped. The full text stays in the posting
    file — this is just enough to judge fit without burning context."""
    signals = ("experience", "design", "portfolio", "you will", "you have",
               "years", "skills", "proficien", "responsib")
    keep = []
    total = 0
    for line in text.splitlines():
        line = line.strip(" -•*\t")
        if not line or not any(s in line.lower() for s in signals):
            continue
        if total + len(line) > limit:
            break
        keep.append(f"- {line}")
        total += len(line)
    return "\n".join(keep) or text[:limit].strip()


def write_review_queue(results, today):
    """The AI handoff file. An AI collaborator reads this plus the
    career narrative and writes verdicts.json; the app folds the
    verdicts into the ranking. Any AI works — the contract is just
    these two files."""
    JOBS_DIR.mkdir(parents=True, exist_ok=True)
    lines = [
        f"# Review queue — {today}",
        "",
        "> **For an AI collaborator.** Read `private/career-narrative.md`",
        "> first — targets, salary floors, deal-breakers, the honest",
        "> skills split. Then judge each posting below for *fit beyond",
        "> keywords* and write `private/jobs/verdicts.json` shaped as:",
        ">",
        '> `{"<posting url>": {"delta": <-3..3>, "why": "<one sentence>"}}`',
        ">",
        "> delta +2/+3: strong narrative fit, clear angle. +1: lean apply.",
        "> 0: keywords already tell the story. -1: lean skip.",
        "> -2/-3: wrong discipline, deal-breaker, or location/comp mismatch.",
        "> Keep `why` short — it appears as a tooltip in the app.",
        "",
    ]
    for posting, points, _file_path in results:
        department = posting.get("department")
        lines += [
            f"## [{points}] {posting['title']} — {posting['company']}"
            + (f" ({department})" if department else ""),
            f"- {posting['location'] or 'location not listed'}"
            f"{' · remote' if posting['remote'] else ''} · {posting['url']}",
            extract_requirements(html_to_text(posting["description"])),
            "",
        ]
    REVIEW_QUEUE.write_text("\n".join(lines))


def write_digest(postings, today, days):
    JOBS_DIR.mkdir(parents=True, exist_ok=True)
    path = JOBS_DIR / f"digest-{today}.md"
    lines = [
        f"# Fresh postings — {today}",
        "",
        f"{len(postings)} new posting(s) in the last {days} day(s), "
        "sorted by relevance score.",
        "",
    ]
    for posting, points, file_path in postings:
        posted = parse_posted(posting)
        posted_str = posted.date().isoformat() if posted else "undated"
        department = posting.get("department")
        lines += [
            f"## [{points}] {posting['title']} — {posting['company']}"
            + (f" ({department})" if department else ""),
            f"- **Location:** {posting['location'] or 'not listed'}"
            f"{' (remote)' if posting['remote'] else ''}",
            f"- **Posted:** {posted_str} via {posting['source']}",
            f"- **Apply:** {posting['url']}",
            f"- **Saved:** {file_path.relative_to(ROOT)}",
            "",
        ]
    path.write_text("\n".join(lines))
    return path


# ─── Seen state ──────────────────────────────────────────────

def load_seen():
    if SEEN_FILE.exists():
        return json.loads(SEEN_FILE.read_text())
    return {}


def save_seen(seen):
    JOBS_DIR.mkdir(parents=True, exist_ok=True)
    SEEN_FILE.write_text(json.dumps(seen, indent=1, sort_keys=True))


# ─── Commands ────────────────────────────────────────────────

def probe(slug):
    print(f"Probing '{slug}' across sources...")
    for name, module in get_sources().items():
        postings = module.fetch(slug)
        status = f"{len(postings)} postings" if postings else "no board found"
        print(f"  {name:12} {status}")


class WatchlistError(Exception):
    pass


def scan(days=7, rescan=False, company=None, source=None, log=None):
    """Run a full scan: fetch boards, filter, score, write artifacts
    (per-posting MD, digest MD, latest.json, seen state). Returns the
    list of (posting, points, file_path). Used by the CLI below and by
    serve.py."""
    log = log or (lambda msg: None)
    if not WATCHLIST.exists():
        raise WatchlistError(
            f"No watchlist at {WATCHLIST}. "
            f"Copy {EXAMPLE_WATCHLIST} there and edit it."
        )

    criteria = parse_watchlist(WATCHLIST)
    if company:
        criteria["companies"] = [(company, source)]
    if not criteria["companies"]:
        raise WatchlistError(
            "Watchlist has no companies. Add some under '## Companies'."
        )

    sources = get_sources()
    seen = load_seen()
    dismissed = (
        json.loads(DISMISSED_FILE.read_text())
        if DISMISSED_FILE.exists() else {}
    )
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    today = datetime.now().date().isoformat()
    fresh = []
    seen_urls_this_run = set()

    def consider(postings):
        for posting in postings:
            url = posting["url"]
            if not url or url in seen_urls_this_run or url in dismissed:
                continue
            if not passes_filters(posting, criteria):
                continue
            posted = parse_posted(posting)
            if posted and posted < cutoff:
                continue
            seen_urls_this_run.add(url)
            if url in seen and not rescan:
                continue
            seen.setdefault(url, today)
            fresh.append((posting, score(posting, criteria)))

    for slug, pinned in criteria["companies"]:
        modules = (
            {pinned: sources[pinned]} if pinned in sources else sources
        )
        postings = []
        for name, module in modules.items():
            postings = module.fetch(slug)
            if postings:
                log(f"{slug}: {len(postings)} postings via {name}")
                break
        else:
            log(f"{slug}: no board found on any source")
            continue
        consider(postings)

    feed_modules = get_feeds()
    for name, arg in criteria["feeds"]:
        module = feed_modules.get(name)
        if not module:
            log(f"{name}: unknown feed (have: {', '.join(feed_modules)})")
            continue
        postings = module.fetch(arg)
        label = f"{name} ({arg})" if arg else name
        log(f"{label}: {len(postings)} postings")
        consider(postings)

    # Dedup across sources: keep the free version when the same job
    # surfaces on multiple platforms.
    deduped = {}  # key -> (posting, points)
    for posting, points in fresh:
        key = posting_dedup_key(posting)
        if key in deduped:
            existing_posting, existing_points = deduped[key]
            existing_cost = SOURCE_COST.get(existing_posting["source"], 99)
            new_cost = SOURCE_COST.get(posting["source"], 99)
            # Prefer lower cost (free > remotive > remoteok)
            # Tiebreak: keep higher score
            if new_cost < existing_cost or (
                new_cost == existing_cost and points > existing_points
            ):
                deduped[key] = (posting, points)
        else:
            deduped[key] = (posting, points)

    fresh = list(deduped.values())
    fresh.sort(key=lambda pair: (-pair[1], pair[0]["title"]))
    results = []
    for posting, points in fresh:
        file_path = write_posting_file(posting, today)
        results.append((posting, points, file_path))

    if results:
        digest = write_digest(results, today, days)
        write_review_queue(results, today)
        log(f"Digest: {digest.relative_to(ROOT)}")
        log(f"AI review queue: {REVIEW_QUEUE.relative_to(ROOT)}")
    write_latest_json(results, today, days)
    save_seen(seen)
    return results


def run(args):
    try:
        results = scan(days=args.days, rescan=args.rescan,
                       company=args.company, source=args.source, log=print)
    except WatchlistError as err:
        print(err)
        return 1
    if results:
        print(f"\n{len(results)} new matching posting(s).")
    else:
        print(f"\nNo new matching postings in the last {args.days} day(s).")
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--days", type=int, default=7,
                        help="freshness window in days (default 7)")
    parser.add_argument("--rescan", action="store_true",
                        help="include postings already seen in past runs")
    parser.add_argument("--probe", metavar="SLUG",
                        help="check which ATS hosts a company, then exit")
    parser.add_argument("--company", metavar="SLUG",
                        help="scrape a single company instead of the watchlist")
    parser.add_argument("--source", choices=["greenhouse", "lever", "ashby"],
                        help="pin the ATS for --company")
    args = parser.parse_args()

    if args.probe:
        probe(args.probe)
        return 0
    return run(args)


if __name__ == "__main__":
    sys.exit(main())
