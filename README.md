# Job Hunter Toolkit

A portable, self-owned job search system built on plain Markdown files.

**Works with any AI. Works with no AI.**

---

## Quick start: the interactive mode

```bash
# 1. Clone and enter the repo
git clone https://github.com/chrisgallegos/job-hunter-toolkit.git
cd job-hunter-toolkit

# 2. Copy the example watchlist and customize it
cp scraper/watchlist.example.md private/watchlist.md
# Edit private/watchlist.md: companies, title filters, boost keywords, locations

# 3. Start the local server
python3 serve.py
# Opens http://localhost:8765 — the app is now live on your machine

# 4. Click "Jobs" → "Scan now" to pull fresh postings
# Analyze, Track, or Dismiss each one. The app reads/writes your private/ folder.
```

**What happens:**
- The scraper pulls from Greenhouse, Lever, Ashby company boards + RemoteOK, Remotive, WeWorkRemotely feeds
- Postings are filtered by your watchlist, scored by relevance, and saved to `private/jobs/`
- Each posting gets a card with Analyze (→ JD Analysis form), Track (→ application log), View (→ original), Dismiss (→ learnings)
- Dismissed reasons accumulate — periodically ask your AI to read them and suggest watchlist refinements

---

## If you have an AI: the self-training loop

The toolkit learns from itself through a three-file contract:

**1. Review queue** (scraper writes this on every scan)
```
private/jobs/review-queue.md
```
Token-lean list of new postings + extracted requirements. Designed as a handoff to your AI:
- Read it alongside `private/career-narrative.md`
- Judge each posting for fit beyond keywords
- Write verdicts.json

**2. Verdicts** (your AI writes this)
```json
{
  "https://jobs.ashbyhq.com/...": {
    "delta": 2,
    "why": "Gaming target hit dead-on. UI craft for Guild Wars 3, remote."
  },
  "https://weworkremotely.com/...": {
    "delta": -3,
    "why": "Building architecture, not product design — false positive."
  }
}
```
Delta range: +3 (strong fit, clear angle) → -3 (deal-breaker or discipline mismatch). The app displays these as color-coded adjustments to the keyword score: **9+2** means score 9, AI bump +2.

**3. Learnings** (app appends dismissals here)
```markdown
# Learnings — dismissed postings

- 2026-06-11 — Senior Gameplay Designer — Epic Games — gameplay
- 2026-06-11 — Level Designer — Bungie — gameplay
- 2026-06-10 — Sales Director — Home Depot — sales role
```
Every dismissal you make (with a one-word reason) lands here. Periodically ask your AI:
> *"Read private/jobs/learnings.md and private/watchlist.md. What patterns do you see? Suggest watchlist edits."*

The AI replies with: "5 dismissals mention 'gameplay' — add to department excludes. Add 'sales' to title excludes." You edit the watchlist, next scan is smarter.

**AI coding assistant: the zero-copy-paste path**

Any AI coding assistant that runs in your project directory — Claude Code, Cursor, Windsurf, GitHub Copilot, Zed AI, or similar — can close the verdict loop without copy-paste. Because it already has file access, you just ask:

```
"Read private/jobs/review-queue.md and private/career-narrative.md,
judge each posting for fit beyond keywords, and write verdicts to
private/jobs/verdicts.json."
```

The assistant reads your narrative, evaluates each posting, and writes the file directly — no separate chat window, no API key, no manual JSON. The toolkit is designed around this: files are the interface, and any tool that can read and write files works.

**Why files, not APIs?**
- Portable: fork the repo, run on your machine, zero cloud dependency
- Transparent: read/edit/understand every file with a text editor
- AI-agnostic: works with any assistant that has local file access, or via copy-paste in a chat window — same file contract either way
- Auditable: git history shows how the system learned over time

---

## The three rungs of the ladder

Use whichever fits your workflow:

### Rung 1: No AI — templates only
Fill out the Markdown templates yourself. The structure forces the thinking.
```
templates/career-narrative.md        → who you are, stories, metrics
templates/jd-analysis.md             → decode a posting, reach a verdict
templates/application-tracker.md     → log everything, find patterns
```
See `docs/facilitator-guide.md` for step-by-step instructions.

### Rung 2: With your AI (chat-based)
Drop a template + your career narrative into Claude, ChatGPT, or Gemini:
```
1. Copy templates/career-narrative.md to private/career-narrative.md
2. Fill it out (or have your AI interview you first)
3. For each posting: copy templates/jd-analysis.md, paste the job description
4. Ask your AI: "Read my narrative and analyze this posting."
5. Copy the verdict back to your file
```
Works anywhere. No setup. No code.

### Rung 3: With the scraper + interactive app
```bash
python3 serve.py  # Local server, http://localhost:8765
```
- Scraper pulls fresh postings from 6 sources every day (or on demand)
- App shows a live digest, scored and filtered by your watchlist
- One-click Analyze/Track/Dismiss

**Verdict loop — three options, same output:**

**a) AI coding assistant (zero friction)**
Open this project in any AI coding assistant with local file access (Claude Code, Cursor, Windsurf, Copilot, etc.) and say:
> *"Read private/jobs/review-queue.md and private/career-narrative.md, judge each posting for fit, and write verdicts to private/jobs/verdicts.json."*
The assistant reads both files, reasons against your narrative, and writes the verdicts directly. No copy-paste, no extra chat window, no API key.

**b) Chat-based (Claude, GPT, Gemini, or any)**
1. Copy the contents of `private/jobs/review-queue.md`
2. Paste into a chat session alongside your career narrative
3. Ask the AI to produce a verdicts JSON block
4. Save the output as `private/jobs/verdicts.json`

**c) Skip verdicts entirely**
The keyword score alone is useful. Verdicts are an optional layer, not a requirement.

---

## How the scraper works

**Sources:** Greenhouse, Lever, Ashby (company job boards); Remotive, RemoteOK, WeWorkRemotely (job feeds).

**Watchlist** (`private/watchlist.md` — you customize this):
```markdown
## Companies
- epicgames (greenhouse)
- spotify (lever)
- arenanet (ashby)

## Feeds
- remotive (design)
- weworkremotely (design)

## Strong titles
- product designer
- visual design
- ui
- ux

## Title excludes
- engineer
- recruiter

## Department excludes
- game design
- gameplay
- level design

## Boost keywords
- gaming
- studio
- design system
```

**Scoring:**
- Base: title match (strong titles +3, includes +0, excludes drop to 0), seniority level (+2), boost keywords (up to +5), remote (+1)
- AI layer: verdicts delta overrides or amplifies the base score
- Dedup: when the same job appears on multiple sources, keeps the free platform version (Greenhouse/Lever/Ashby over RemoteOK's pay-to-play)

**Output:**
- `private/jobs/digest-YYYY-MM-DD.md` — human-readable ranked list, Markdown export
- `private/jobs/latest.json` — machine-readable for the app
- `private/jobs/postings/` — one MD file per posting, ready to drop into JD Analysis template
- `private/jobs/review-queue.md` — token-lean handoff to your AI
- `private/jobs/verdicts.json` — where your AI writes back
- `private/jobs/dismissed.json` — what you rejected and why
- `private/jobs/learnings.md` — pattern accumulation for watchlist refinement

---

## Security & privacy

**What stays on your machine:**
- Everything in `private/` — your narrative, tracker, search history, verdicts, dismissals
- Gitignored entirely. Never committed. Never published.

**What's public in the repo:**
- Templates (generic, no personal data)
- Docs (methodology, how to use the system)
- Scraper code (reads public APIs only)
- Server code (binds localhost only, serves only what you need)
- Example watchlist (no real companies yet — you customize it)

**Data flow:**
1. Scraper → pulls from public job boards (Greenhouse, Lever, Ashby, Remotive, RemoteOK, WeWorkRemotely)
2. Server → local only, binds 127.0.0.1, never broadcasts
3. App → reads/writes your private/ folder via the server
4. Your AI → reads/writes `private/` directly (AI coding assistant) or via copy-paste (chat) — same file contract either way, no API account required

**LinkedIn deliberately excluded:**
- No public job API available; unofficial scraping violates ToS and is technically fragile
- Most LinkedIn postings are republished from Greenhouse/Lever/Ashby anyway — we catch them there first
- Alternative: save LinkedIn job searches as email alerts, paste interesting ones into JD Analysis

**No telemetry, no accounts, no tracking.** The entire toolkit is yours.

---

## Structure

```
templates/          Reusable MD templates — copy these into private/ and fill them out
  career-narrative.md       Your foundation: stories, metrics, voice, targets, deal-breakers
  jd-analysis.md            Decode a posting, reach apply/skip/stretch verdict
  cover-letter.md           Draft from your narrative + the posting's angle
  company-research.md       Background before an interview
  interview-prep.md         Stories and rehearsal prompts
  application-tracker.md    Log every application, track the funnel

docs/               Philosophy, methodology, setup guides
  philosophy.md             Why the "we" model works
  methodology.md            How the templates fit together
  facilitator-guide.md      Step-by-step for no-AI mode
  setup-and-modes.md        First-session prompts for Claude Code, chat, self-guided

scraper/            Job board scraper — pulls from public APIs, local only
  scrape.py                 CLI: python3 scraper/scrape.py [--days 7] [--rescan] ...
  serve.py                  Local server: python3 serve.py [--port 8765]
  sources/                  Adapters: greenhouse.py, lever.py, ashby.py
  feeds/                    Feed adapters: remotive.py, remoteok.py, weworkremotely.py
  watchlist.example.md      Template for your custom watchlist

index.html, app.js, app.css, tokens.css
                    Interactive app: run serve.py, opens at http://localhost:8765
                    Sections: Home, Narrative (wizard + portrait), JD Analysis, Jobs (scraper UI), Tracker

ideas/              Designs for future layers
  career-coin.md            Portable career identity object (human + machine readable)
  interactive-site.md       Direction notes for the browser app
  scraper-architecture.md   Design sketch and deferred decisions

private/            YOUR instance — gitignored, never published
  career-narrative.md       Filled-out version (you write this)
  tracker.md                Application log and patterns
  watchlist.md              Custom company list, filters, keywords
  jobs/                     Scraper outputs
    digest-YYYY-MM-DD.md    Ranked postings from that day's scan
    latest.json             Machine-readable version (for the app)
    review-queue.md         Token-lean handoff for your AI
    verdicts.json           Your AI's judgment layer
    dismissed.json          What you rejected + reason
    learnings.md            Accumulated dismissal patterns
    postings/               One MD file per posting (drop into JD Analysis)

.gitignore          Ensures private/ stays private
LICENSE             MIT — fork it, own it
```

---

## Philosophy

**The "we" model:** The human brings judgment, career context, and the ability to say "no." The AI (optional) handles parsing, drafting, and pattern-matching — the parts that are tedious and scale.

Most AI job-search tools flip this: the AI thinks, you confirm. Here, the structure does the thinking (the templates force you to answer hard questions), and AI is an optional amplifier. This means:

- The system works without any AI (rung 1 and 2 don't require one)
- Your narrative becomes the real asset — you own it, can port it anywhere, use any AI
- Verdicts aren't black-box scores; you see the reasoning and can disagree
- The feedback loop is explicit — dismissals → learnings → watchlist edits

**Why Markdown?** It's human-readable, portable, version-controllable, and every tool understands it. You can read and edit everything with a text editor or your AI or both.

---

## For forkers: make it yours

1. **Customize templates** — change the career narrative structure if your industry works differently, adapt the JD analysis for your targets
2. **Extend the scraper** — add a new ATS adapter, a new feed source, or a dedup strategy that works better for your search
3. **Tweak the watchlist** — company list, title filters, and boost keywords are all user-configurable
4. **Share learnings patterns** — if you find a pattern (e.g., "game design roles are 60% false positives for product designers"), document it for others

The toolkit is not a platform; it's a starting point. Fork it, break it, rebuild it to fit your search.

---

## Getting started (detailed)

### Prerequisites
- Python 3.6+
- A text editor (any will do)
- (Optional) An AI collaborator — two modes, same file contract:
  - **AI coding assistant** — any tool that runs in your project directory (Claude Code, Cursor, Windsurf, GitHub Copilot, Zed AI, etc.) reads and writes `private/` directly. Zero copy-paste.
  - **Chat-based** — Claude, ChatGPT, Gemini, or any chat UI. Copy `review-queue.md`, paste in the AI's response as `verdicts.json`. Takes an extra step but works anywhere.

### Step 1: Set up your narrative
```bash
cp templates/career-narrative.md private/career-narrative.md
# Edit private/career-narrative.md — fill in your story
```
Or, ask your AI:
> "Read templates/career-narrative.md, then interview me. Fill it out based on my answers."

This is the foundation. Everything else references it.

### Step 2: Start analyzing postings
Found a job posting? Create a file:
```bash
cp templates/jd-analysis.md private/jd-[company]-[role].md
# Paste the job description
# Work through the sections
```
Or ask your AI:
> "Read my career narrative and this JD. Analyze it."

### Step 3 (optional): Use the scraper
```bash
cp scraper/watchlist.example.md private/watchlist.md
# Edit: add your target companies, refine filters
python3 serve.py
# Go to http://localhost:8765, click "Jobs", hit "Scan now"
```

### Step 4: Log and learn
```bash
cp templates/application-tracker.md private/tracker.md
# Log every application as you submit
# Periodically: "What patterns do I see? What needs to change?"
```

---

## Troubleshooting

**"No scans yet"** → Click "Scan now" (first scan takes ~30s as it checks 6 sources across dozens of companies)

**"Watchlist has no companies"** → Edit `private/watchlist.md`, add companies under `## Companies`

**"No matching postings"** → Watchlist filters might be too tight. Lower `## Title excludes`, or try `--days 60` to widen the window

**"Server not responding"** → Make sure `python3 serve.py` is running. It binds `127.0.0.1:8765` by default. Check `--port` if 8765 is in use.

**"Verdicts not showing up"** → Check that `private/jobs/verdicts.json` exists. Your AI needs to write it in the shape described above.

---

## License

MIT. Free for anyone to own and run. No conditions, no tracking.

---

## Questions?

Check `docs/philosophy.md` for why the system is designed this way, or `docs/setup-and-modes.md` for first-session walkthroughs with Claude Code / chat / solo.

The entire system is intentionally transparent. Read the code. Change it. Break it. Make it yours.
