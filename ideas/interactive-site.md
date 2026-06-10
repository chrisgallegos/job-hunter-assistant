# Interactive Site — Direction Notes

**Status:** direction set, not designed or built. Captured June 2026.

The toolkit eventually grows an interactive layer: a local site that
laypeople — regular folk who don't live in text editors — can use
without ever touching raw Markdown.

## The principle

The MD files stay the single source of truth. The site is a **view over
the files**, never a replacement for them. Everything the site reads
and writes is the same plain Markdown an AI collaborator (or a human
with a text editor) works with. Break that, and the portability story —
the whole point — dies.

## Two ways in

1. **With an AI collaborator:** download the toolkit, ask your AI to
   run it locally ("host this for me"). The AI starts the local server;
   the human works in the friendly interface; the files underneath stay
   AI-legible.
2. **Without AI:** the interactive layer must still run for someone
   with no AI and no terminal comfort. Target: the lowest possible
   friction — ideally open a file and it works, or one copy-paste
   command at most. No accounts, no hosting, no build step for the user.

This extends the ladder rather than replacing it: the no-AI rung gets
an interface, not just worksheets.

## What it probably is (to be designed)

- Forms that read/write the `private/` MD files (career narrative
  intake, JD analysis walkthrough, tracker table with status updates)
- The tracker is the most obvious win: a table UI over `tracker.md`
  with the patterns view computed live
- Stays local: no telemetry, no data leaving the machine — same
  ownership model as everything else

## Open questions

- Tech shape: single self-contained HTML file vs. tiny local server.
  Single-file is the friendliest (double-click it) but browsers
  restrict local file writes; a tiny server writes files cleanly but
  costs one terminal command. Decide when designing.
- Does the portfolio experiment page (Phase 3) demo this interface, or
  just describe the toolkit? A live sanitized demo would be the
  stronger showcase.
- How much of each template translates to a form without losing the
  thinking the structure forces? The worksheets work *because* they
  make you write. The interface must not turn reflection into
  checkbox-clicking.
