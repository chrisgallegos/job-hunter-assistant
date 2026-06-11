# Job Hunter Toolkit

A portable, self-owned job search system built on plain Markdown files.

**Works with any AI. Works with no AI.**

---

## If you have an AI: hand it this repo

Drop this folder into a conversation with Claude, ChatGPT, Gemini, or
any capable model and say:

> *"Read the docs/ folder and help me run a job search session."*

That's it. The AI absorbs the instructions and knows what to do — how
to interview you, how to analyze a job posting, how to update your
tracker. The docs are written for both you and the AI to read. Nothing
is hidden in a prompt you can't see.

**Using Claude Code** (Anthropic's local CLI tool)? Even better. Start
a session from this folder and the AI reads and writes your files
directly — your career narrative, tracker, and JD analyses update in
real-time during the conversation. No copy-paste, no cleanup. See
`docs/setup-and-modes.md` for the exact first-session prompt.

---

## If you don't have an AI: the docs guide you directly

Every template is a human-readable worksheet with clear instructions.
The `docs/facilitator-guide.md` walks you through each section in
order — what to write, why it matters, and what to watch out for.
The structure does the thinking you'd otherwise be doing alone.

---

## What this is

A structured methodology for running a job search — analysis worksheets,
drafting guides, research checklists, and a tracker — written as plain
Markdown templates you fill out and own.

It is **not** an AI tool. The methodology does the thinking. But every
template is written to be equally legible to you and to an AI collaborator
of your choice, so you can delegate the laborious parts — parsing job
descriptions, drafting cover letters, pattern-matching across postings —
while you bring the judgment and career context only you have.

## The ladder

Use it at whatever rung suits you. Each one works without the rung above it:

1. **No AI** — fill out the templates yourself. The structure forces the
   thinking: keyword gaps, story preparation, channel tracking.
2. **With your AI collaborator** — point any AI at a template plus your
   career narrative. The "If working with an AI collaborator" section in
   each template tells it how to participate.
3. **With the scraper** *(optional — see `scraper/`)* — a local Python
   script that pulls fresh postings straight from public ATS APIs
   (Greenhouse, Lever, Ashby) for the companies you watch, filters them
   against your criteria, and writes a relevance-scored digest your AI
   can read. Standard library only. Runs on your machine. No data sent
   anywhere. Copy `scraper/watchlist.example.md` to
   `private/watchlist.md`, then `python3 scraper/scrape.py`.

## What you own

Everything. There is no service, no account, no credits, no telemetry.
Fork it, change it, share it. Your personal data lives in `private/`,
which is gitignored — the system is public, your search is yours.

## Getting started

**Choose how you want to run it — see `docs/setup-and-modes.md` for
the full guide.**

The short version:

- **Claude Code (CLI):** Start a session from this folder. The AI reads
  and writes your files directly during the conversation — no
  copy-paste, no cleanup. Highest fidelity. First-session prompt is
  in the setup guide.
- **Chat-based AI (Claude.ai, ChatGPT, Gemini):** Paste your files in,
  work through the session, copy output back manually. Works anywhere.
- **No AI:** Follow `docs/facilitator-guide.md` as a self-guided
  worksheet. The structure does the work.

Then:

1. Build your career narrative first — copy `templates/career-narrative.md`
   to `private/` and run a session with `docs/facilitator-guide.md` as
   the guide. This is the foundation everything else draws from.
2. Found a posting? Copy `templates/jd-analysis.md` to `private/jd-[company]-[role].md`,
   paste the job description, work through it. Verdict plus angle comes
   out the other end.
3. Log everything in `private/tracker.md` — the patterns section is
   where the search learns from itself.

## The templates

| Template | Job |
|---|---|
| `career-narrative.md` | The foundation — who you are, your stories, your voice |
| `jd-analysis.md` | Decode a posting; reach an apply/skip/stretch verdict |
| `cover-letter.md` | Turn the verdict's angle into a letter in your voice |
| `company-research.md` | One page that makes you the candidate who did the homework |
| `interview-prep.md` | Angles, stories, and out-loud rehearsal per interview |
| `application-tracker.md` | The pulse of the search, and its feedback loop |

## Structure

```
templates/   The system — generic, publishable, yours to adapt
docs/        Philosophy and methodology — why it works this way
ideas/       Future components, designed but not built
private/     Your instance — gitignored, never leaves your machine
```

## Philosophy

The "we" model: the human brings judgment and career context, the AI
handles parsing, drafting, and pattern matching. Most AI job-search tools
invert this — the AI does the thinking and falls over without it. Here,
well-structured context is the product, and AI is an amplifier you can
optionally plug in.

## License

MIT — free for anyone to own and run.
