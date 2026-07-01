# Contributing

This assistant is designed to be forked and customized. Here are ways to improve it:

## For your own search (fork and own)

The most valuable contribution is using this in anger — finding what breaks, what's unclear, what you'd change.

1. **Customize your watchlist** — add companies, refine title filters, tune boost keywords. Every search is different.
2. **Share learnings patterns** — if you find a recurring reason to dismiss postings, document it. Others will hit the same wall.
3. **Extend the scraper** — add a new job board, a new source, a better dedup strategy for your region.
4. **Improve your narrative** — as you search, your narrative sharpens. Later forks can learn from yours.

## For everyone (pull requests)

The core assistant is intentionally minimal. Before opening a PR, ask: "Does this belong in the default system, or does it belong in the user's fork?"

### Small wins we'd merge:
- **Bug fixes** — if the scraper crashes on a certain board, that's ours
- **New sources** — if you add an ATS adapter or job feed (same normalized contract as the existing ones), that's useful
- **Documentation clarity** — if a section is confusing, improve it
- **Accessibility** — if the app or templates could work better for different industries / styles, suggest it

### Probably not:
- AI model integrations — the whole point is you choose your AI
- Database/hosted backends — the whole point is local files
- UI polish that breaks the "boring tech" constraint — if it requires npm/webpack/TypeScript, it's probably out of scope
- New rung of the ladder — the three rungs (templates, with AI, with scraper) are the design
- Opinionated defaults — your watchlist is yours. We ship examples, not opinions.

## Code style

- Python: stdlib only, no dependencies
- JavaScript: vanilla (no React/Vue/etc), no bundlers
- Markdown: plain, readable, both human and AI-legible
- Shell: POSIX-compatible where possible

Keep it boring. Boring is maintainable.

## Testing

- Manual testing is fine — run the scraper, see if it breaks
- Document what you tested: "Verified against Greenhouse/Lever/Ashby on 2026-06-11, got 50/120/10 postings"
- If adding a new source, test the normalized output shape matches the contract

## Security

- **No credentials in code** — the system is local and public
- **No external APIs** — we read public job boards only
- **No telemetry** — if you add a feature, it must not phone home
- **Private/ is sacred** — anything in private/ never gets committed, never gets uploaded

## Filing issues

- **Bug**: "Scraper crashes on Ashby when..." → include stack trace, exact board, watchlist excerpt
- **Enhancement**: "Add X source because..." → explain why it's different from what we have, link the API docs
- **Question**: "How do I...?" → use Discussions, not Issues

## Roadmap (not prioritized, just sketched)

These are in `ideas/` because they're designed but not built:

- **Career Coin** — dual-output resume: human portrait + machine-parseable object
- **Scheduled daily scans** — launchd/systemd integration
- **Pattern extraction from learnings** — auto-suggest watchlist edits from dismissed.json

None of these are blocked on external dependencies. None require new architecture. They're just work.

**Already built (once thought hard, turned out not to be):** Workday and
Eightfold adapters. Workday was assumed to need a headless browser — it doesn't;
both are plain public JSON APIs, same as Greenhouse/Lever. The findings that made
them tractable (API shapes, the no-guessable-slug problem, per-platform quirks)
live in `ideas/ats-platform-notes.md` — read it before adding another ATS.

## Questions?

The philosophy is in `docs/philosophy.md`. The first-use walkthrough is in `docs/setup-and-modes.md`. Read those before diving in.

---

**tl;dr:** This is intentionally a fork-and-own system. The best contribution is using it in anger, learning from it, and improving your own version. If you find a bug or build something that obviously belongs in the core, we're happy to merge it. But the default state is: customize it for your search, keep it yours.
