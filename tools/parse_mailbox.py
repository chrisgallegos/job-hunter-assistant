#!/usr/bin/env python3
"""Parse a job-search mailbox into a tracker-ready digest — headers only.

Privacy by design: this reads ONLY the From / Subject / Date headers of each
message. It never reads, prints, or writes message bodies. Point it at an
.mbox file (Apple Mail: right-click mailbox -> Export Mailbox; or Google
Takeout -> Mail -> single label) and it emits:

  - a CSV (date, status, company, from_email, subject)
  - a short summary to stdout (counts by status, by company, date range)

Status is inferred from the subject line with conservative keyword rules;
ambiguous ones are marked "other" so you can eyeball them. Standard library
only. Local only. Nothing leaves your machine.

Usage:
  python3 tools/parse_mailbox.py "/path/to/2026.mbox/mbox"
  python3 tools/parse_mailbox.py "/path/to/mbox" --csv private/jobs/mail-digest.csv
  python3 tools/parse_mailbox.py "/path/to/mbox" --since 2026-01-01
"""

import argparse
import csv
import mailbox
import re
import sys
from collections import Counter
from email.header import decode_header, make_header
from email.utils import parseaddr, parsedate_to_datetime
from pathlib import Path

# ─── subject-line classifiers (order matters: first match wins) ───
# Rejections are checked before "applied" because some declines reuse
# "your application" phrasing ("Application Update", "regarding your
# application ... filled").
RULES = [
    ("rejected", re.compile(
        r"unfortunately|regret to inform|not (be )?moving forward|"
        r"other candidates|not selected|decided (to|not)|"
        r"filled this position|no longer (available|considering)|"
        r"application update|won.t be moving|will not be moving|"
        r"position has been filled|pursue other", re.I)),
    ("interview", re.compile(
        r"\binterview\b|next steps|schedul|availabilit|phone screen|"
        r"hiring manager|panel|meet with|recruiter (call|screen)|"
        r"set up (a )?(call|time)|confirming (your |next )", re.I)),
    ("applied", re.compile(
        r"thank you for applying|thanks for applying|application received|"
        r"received your application|successfully submitted|"
        r"thank you for your (interest|application)|we.ve received|"
        r"application (was )?(sent|submitted)|your application (to|for|with)|"
        r"thank you for taking the time", re.I)),
]


def decode(raw):
    if not raw:
        return ""
    try:
        return str(make_header(decode_header(raw))).strip()
    except Exception:
        return raw.strip()


def classify(subject):
    for status, rx in RULES:
        if rx.search(subject):
            return status
    return "other"


def company_from(name, email):
    """Best-effort company label from sender. Prefer a meaningful display
    name; fall back to the domain when the name is a generic no-reply."""
    name = name.strip()
    generic = re.compile(r"^(no[\s_-]?reply|noreply|do[\s_-]?not[\s_-]?reply|"
                         r"talent|recruiting|careers|jobs|notifications?)$", re.I)
    if name and not generic.match(name):
        return name
    domain = email.split("@")[-1] if "@" in email else email
    # strip common ATS / mail-host domains down to the org token
    domain = re.sub(r"\.(com|net|org|io|co|us)$", "", domain, flags=re.I)
    domain = domain.split(".")[-1]  # e.g. mail.greenhouse -> greenhouse
    return domain or "(unknown)"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mbox", help="path to the mbox file")
    ap.add_argument("--csv", help="write rows here (default: stdout summary only)")
    ap.add_argument("--since", help="ISO date floor, e.g. 2026-01-01")
    args = ap.parse_args()

    path = Path(args.mbox)
    if not path.exists():
        sys.exit(f"no mbox at {path}")

    since = args.since
    rows = []
    box = mailbox.mbox(str(path))
    for msg in box:
        # headers only — bodies are never accessed
        subject = decode(msg.get("subject", ""))
        name, addr = parseaddr(msg.get("from", ""))
        name, addr = decode(name), addr.lower()
        try:
            dt = parsedate_to_datetime(msg.get("date", ""))
            iso = dt.date().isoformat() if dt else ""
        except Exception:
            iso = ""
        if since and iso and iso < since:
            continue
        rows.append({
            "date": iso,
            "status": classify(subject),
            "company": company_from(name, addr),
            "from_email": addr,
            "subject": subject,
        })

    rows.sort(key=lambda r: r["date"])

    if args.csv:
        out = Path(args.csv)
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open("w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["date", "status", "company",
                                             "from_email", "subject"])
            w.writeheader()
            w.writerows(rows)
        print(f"wrote {len(rows)} rows -> {out}\n")

    # ─── summary (safe to show: counts + sender labels, no bodies) ───
    status_counts = Counter(r["status"] for r in rows)
    dates = [r["date"] for r in rows if r["date"]]
    print(f"messages parsed: {len(rows)}")
    if dates:
        print(f"date range: {dates[0]} -> {dates[-1]}")
    print("\nby status:")
    for s in ("applied", "interview", "rejected", "other"):
        print(f"  {s:10} {status_counts.get(s, 0)}")
    print("\ntop companies (by message volume):")
    for company, n in Counter(r["company"] for r in rows).most_common(25):
        print(f"  {n:3}  {company}")


if __name__ == "__main__":
    main()
