# The Career Coin

**Status:** concept, not designed or built. Captured June 2026.
**Origin:** emerged from the Design.md lineage — same move, different domain.

---

## The concept

A resume is a document optimized for human skimming, designed for 1955.
A vCard is contact data optimized for digital transfer, designed for 1995.
The career coin is career identity optimized for human-AI collaboration —
generated from honest natural language, expressed as both a readable
portrait and a structured parseable object, owned entirely by the person
it describes.

Not a resume replacement that requires companies to change behavior.
Not a new platform requiring sign-up on both sides.
A portable career object — like a business card, like a contact export,
like a resume — but different. You toss it not for luck but for trade.

---

## The two sides

**Human side** — the portrait view. Readable, narrative, honest.
A person can read it. Generated from the career narrative MD.

**Machine side** — structured, encoded, not eye-legible but perfectly
parseable. Skills as weighted categories. Projects as structured objects
with metrics. Compensation as a range. Deal-breakers encoded but not
exposed to human reviewers before the conversation warrants it.

Both sides generated from the same source: the MD files the candidate
actually wrote. Not keyword-stuffed for ATS crawlers. Derived from
honest narrative — which means it can't be gamed the way a resume can.

---

## Why it's different from "reinventing email"

Every previous resume reinvention requires the hiring side to change:
new platform, new portal, new login, upload your profile here. The
infrastructure burden lands on companies with no incentive to adopt.

The coin puts the generation burden on the candidate — where it belongs,
because the candidate has the skin in the game — and degrades gracefully
to every existing context. It's also a flat file. You can email it.
Paste it into any AI. Print the human side. It works today without
anyone adopting a new standard, while being genuinely better in
AI-native hiring contexts.

---

## The Design.md lineage

Google's Design.md solved a specific problem: design systems had no
machine-readable spec format. Information existed in human documents
but tooling couldn't validate against it. Design.md said: same
information, structured differently, now both humans and tools can use it.

The career coin is the same move for career identity. The information
already exists in the MD files. The coin is the structured parallel —
same source, dual encoding, useful to both humans and AI tools without
reformatting.

---

## The privacy layer

The machine-readable side being non-eye-legible is protective, not
just aesthetic. Compensation floor, deal-breakers, honest skills
split — present in the coin, not visible to a human scanner, but
available to a parsing tool matching against role requirements.

The candidate controls what's in the coin and what's exposed at which
stage of the process.

---

## What it implies at scale

If the format were open and standardized — a career equivalent of vCard
or RSS — any hiring tool could ingest it. Any candidate could generate
one. The ATS industry as currently constituted becomes partially
obsolete: data arrives pre-structured and honest rather than scraped
from a PDF and mangled.

That's a standards problem as much as a product problem. The assistant
is the reference implementation — the thing that proves the format
works before anyone tries to standardize it.

---

## Build sequence

This is a layer beyond the current assistant. Dependencies in order:

1. Thin local server — MD files as real nodes (next to build)
2. Structured export — career narrative as JSON/structured object
3. Encoding layer — human side + machine side from same source
4. The coin format spec — open, documented, forkable

The assistant we have now generates the human-readable narrative.
The coin is what this becomes when it grows up.
