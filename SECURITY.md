# Security & Privacy

This document explains how your data is protected in the Job Hunter Assistant.

## TL;DR

- **Your search data never leaves your machine** — everything in `private/` is gitignored
- **No accounts, APIs, or telemetry** — the system is entirely local
- **No cloud dependencies** — runs on Python standard library only
- **You control what's public** — fork the repo, customize it, keep the original templates generic

---

## What stays private (on your machine)

```
private/
├── career-narrative.md     Your real story, metrics, deal-breakers
├── tracker.md              Your application history
├── watchlist.md            Your target companies and filters
├── jobs/
│   ├── digest-*.md         Your daily scans
│   ├── verdicts.json       Your AI's judgments
│   ├── dismissed.json      What you rejected and why
│   ├── learnings.md        Accumulated patterns
│   └── postings/           Individual analyses
└── [anything else you add]
```

**`.gitignore` rule:**
```
private/*
!private/README.md
```

This means: "Ignore all of `private/` except for the README." So if you accidentally `git add .`, everything in `private/` is silently skipped — git never stages it. (Note: `.gitignore` only protects untracked files. If you deliberately `git add -f` something from `private/`, git will take it — don't.)

**Test this yourself:**
```bash
cd private/
echo "secret" > secret.txt
git add .
# git will ignore it; no warning, it's just silently skipped
```

---

## What's public (in the repo)

- `templates/` — Generic worksheets, no personal data
- `scraper/` — Code that reads public APIs
- `serve.py` — Local server code
- `docs/` — Philosophy and methodology
- `index.html`, `app.js`, `app.css` — App code
- `README.md`, `CONTRIBUTING.md` — Documentation

**Example watchlist** (`scraper/watchlist.example.md`) contains only a few well-known example slugs and generic worked examples — you replace them with your own targets. Nothing in it is personally identifying.

---

## How data flows

### Scraper
```
Public job boards (Greenhouse, Lever, Ashby, BambooHR, Workable, Workday,
Eightfold, SmartRecruiters, Publicis + Remotive, RemoteOK, WeWorkRemotely feeds)
    ↓
scraper/scrape.py (runs on your machine)
    ↓
private/jobs/latest.json (saved locally)
    ↓
serve.py (local server, binds 127.0.0.1)
    ↓
index.html (app in your browser)
```

**No external calls:**
- The scraper reads public APIs — no authentication required, anyone can call them
- The server binds `127.0.0.1` — unreachable from the network
- The app runs in your browser — all processing is client-side

### Verdicts (your AI)
```
private/jobs/review-queue.md (token-lean handoff)
    ↓
[Your AI — Claude, GPT, Gemini, or local model]
    ↓
private/jobs/verdicts.json (written by you, pasted into the file)
    ↓
App merges verdicts into scoring
```

**Your AI never talks to the assistant:**
- No API calls back to the system
- No server-to-API-service communication
- You manually copy the verdicts file (or paste the content) — full control

---

## Threat model

### Attack: Someone gains access to my GitHub account
**Impact:** The repo is forked. Nothing is exposed — `private/` was never committed.

**Mitigation:** It already is. The `.gitignore` prevents accidental commits. But to be extra safe:
```bash
# Before pushing, verify nothing sensitive is staged:
git status
# If you see private/career-narrative.md or private/jobs/, stop
# It should never be listed. The .gitignore overrides user mistakes.
```

### Attack: Someone hacks into my machine and reads files
**Impact:** They get your `private/` folder (same as if they stole your laptop).

**Mitigation:** This is a local system. If your machine is compromised, your files are at risk regardless. Encrypt your drive (FileVault on macOS, BitLocker on Windows, LUKS on Linux). Use strong passwords. Use SSH keys for GitHub.

### Attack: The server is compromised / exploited
**Impact:** Minimal — the server is local-only (`127.0.0.1:8765`). It's unreachable from the network. No one can exploit it remotely.

**Mitigation:** It's not exposed. But if you wanted to be paranoid:
- Never run `python3 serve.py` with `--bind 0.0.0.0` (not in the code, and won't ever be)
- Never expose the local server through a tunnel or proxy
- Use a firewall to block incoming connections to port 8765

### Attack: Job boards are hacked and my data is exposed there
**Impact:** Your postings are public (they already are — they're job listings). Nothing new is exposed.

**Mitigation:** You control what data goes into the system. Read the postings you save; they're the public JDs from the boards themselves.

### Attack: I paste my narrative into an untrusted AI
**Impact:** The AI sees your career details, targets, and deal-breakers.

**Mitigation:** Use a trusted AI provider (Claude, OpenAI, Google — your choice). Never paste your narrative into random websites or unsecured chat tools.

---

## Credential handling

**The system doesn't use API keys or credentials.**

Job boards (Greenhouse, Lever, Ashby, etc.) have public APIs for their job listings. You don't need to log in. The scraper reads them unauthenticated.

**If you extend the system to add a source that requires credentials:**
- Store them in `.env` (gitignored)
- Never commit them
- Use environment variables only, never hardcoded strings
- Document that users should set them locally

Example:
```python
# Good:
api_key = os.environ.get("SOME_API_KEY")
if not api_key:
    raise ValueError("Set SOME_API_KEY in .env")

# Bad:
api_key = "sk-1234567890..."  # NEVER DO THIS
```

---

## For forkers: privacy checklist

If you fork this and customize it:

- [ ] Check `.gitignore` before first push — make sure `private/*` is in there
- [ ] Test: `git status` should never show files from `private/`
- [ ] Before pushing, review staged files: `git diff --cached` should not have your narrative, tracker, etc.
- [ ] If you add new personal-data files, add them to `.gitignore`
- [ ] If you add a new API integration, document credential handling
- [ ] If you expose the server (via tunnel, reverse proxy, etc.), understand the security implications — the system wasn't designed for that

---

## Transparency

The entire codebase is readable. You can inspect:
- What the scraper sends to job boards (just GET requests to public endpoints)
- What the server responds with (your own data, from `private/`)
- Where files are written (always in `private/` or temporary `.json` for latest digest)
- What the app does (vanilla JavaScript, no obfuscation)

If you spot a security issue, please file it responsibly:
1. Open an issue on GitHub (private if possible)
2. Describe the vulnerability
3. Allow time for a fix before disclosure

---

## Regulatory compliance (GDPR, CCPA, etc.)

**For you:** This is a personal tool running on your machine. You're responsible for your own data.

**For forks others use:** You (the repo owner) are not processing anyone else's data — each user runs it on their own machine, owns their own `private/` folder. There's no central database, no data collection, no profiling. Each fork is entirely independent.

If you're worried about compliance:
- Document clearly that users own their data
- Remind users that `private/` stays private
- Don't modify the system to store data centrally or upload it

---

## Questions?

- **"Is my data safe?"** — Yes, if your machine is secure and you don't share it. The system has no networked components.
- **"Can I trust this code?"** — Read it. It's open source, < 2000 lines of Python, no dependencies. You can audit the entire system in an afternoon.
- **"What if I want to share my fork with others?"** — Make sure `private/` is empty before pushing (it will be, thanks to `.gitignore`). Your templates and code are shareable; your data is not.
- **"Can I run this in Docker / the cloud?"** — You can, but there's no advantage. It's a local system. Running it on a shared server means others could potentially read your files — use full-disk encryption if you do.

---

## Security is boring, which is good

The job-hunter-assistant uses no fancy crypto, no cloud APIs, no authentication. It's boring on purpose:

- Boring = auditable
- Auditable = trustworthy
- Trustworthy = you can use it for sensitive career data

Complexity is the enemy of security. We avoid it.
