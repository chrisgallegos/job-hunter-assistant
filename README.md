# Job Hunter Toolkit

A portable, self-owned job search system built on plain Markdown files.

**Works with any AI. Works with no AI.**

## What this is

A structured methodology for running a job search — analysis worksheets,
drafting guides, research checklists, and a tracker — written as plain
Markdown templates you fill out and own.

It is **not** an AI tool. The methodology does the thinking. But every
template is written to be equally legible to you and to an AI collaborator
of your choice (Claude, Gemini, GPT, or any capable model), so you can
delegate the laborious parts — parsing job descriptions, drafting cover
letters, pattern-matching across postings — while you bring the judgment
and career context only you have.

## The ladder

Use it at whatever rung suits you. Each one works without the rung above it:

1. **No AI** — fill out the templates yourself. The structure forces the
   thinking: keyword gaps, story preparation, channel tracking.
2. **With your AI collaborator** — point any AI at a template plus your
   career narrative. The "If working with an AI collaborator" section in
   each template tells it how to participate.
3. **With the scraper** *(optional, not yet built — see
   `ideas/scraper-architecture.md`)* — a local Python script that pulls
   postings from job boards into Markdown your AI can read. Runs on
   your machine. No data sent anywhere.

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
