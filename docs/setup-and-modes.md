# Setup and Modes — How to Run the Assistant

The assistant works in three distinct modes. Each one is fully functional.
The difference is how much friction exists between the conversation and
your files.

---

## Mode 1: Claude Code (recommended — highest fidelity)

**What it is:** Claude Code is Anthropic's CLI tool that runs locally
alongside your files. When you start a session from the assistant
directory, the AI has direct read/write access to everything in the
project — including your `private/` folder.

**Why it matters:** The AI doesn't just suggest what to write. It writes
it. Your career narrative, tracker, JD analyses — they update in
real-time during the conversation. The session IS the file update.
No copy-paste loop. No "take this output and put it in your doc."
The files are always current.

**How to set it up:**

1. Install Claude Code:
   ```
   npm install -g @anthropic-ai/claude-code
   ```
2. Open your terminal and navigate to this folder:
   ```
   cd ~/Sites/job-hunter-assistant
   ```
3. Start a session:
   ```
   claude
   ```
4. Open the session with this prompt:
   ```
   Read docs/facilitator-guide.md and private/career-narrative.md,
   then help me work through the [CHRIS] markers / run a JD analysis /
   update my tracker. Write changes to the files as we go.
   ```

That last instruction — "write changes to the files as we go" — is the
key. It tells the AI to work as a collaborator with file access, not
just a chat assistant generating text you have to manually paste.

**The session rhythm in this mode:**
- You talk, the AI asks questions
- When something's decided, the AI writes it to the file immediately
- You can open the file in a separate editor window and watch it update
- At the end of the session, your files are current — no cleanup needed

**Starting fresh vs. continuing:**
Every new Claude Code session reads the current state of your files.
The files are the memory. You never need to re-explain your situation —
just say "read my career narrative and let's work on X" and the context
is already there.

---

## Mode 2: Chat-based AI (Claude.ai, ChatGPT, Gemini, etc.)

**What it is:** You paste content into the chat, the AI responds, you
copy output back into your files manually.

**Works fine. More friction.** The human becomes the file system.

**How to run it:**

1. Open `private/career-narrative.md` in a text editor.
2. Open your AI chat in a browser tab.
3. Start the session by pasting:
   - The contents of `docs/facilitator-guide.md` (tells the AI how to run the session)
   - The current state of `private/career-narrative.md`
4. Work through the session. When the AI produces updated content,
   copy it back into the file manually.

**For JD analysis:**
Paste `docs/facilitator-guide.md` (the JD analysis section) +
your career narrative + the full job posting text. Ask for the
analysis. Copy the verdict and angle somewhere useful.

**Tip:** Keep your text editor and the chat tab side by side. Update
the file as you go rather than trying to reconcile everything at the
end of a long session.

---

## Mode 3: No AI — self-guided

**What it is:** You fill out the templates yourself, using the
facilitator guide as your own interviewer.

**How to run it:**

1. Copy `templates/career-narrative.md` to `private/career-narrative.md`
2. Open `docs/facilitator-guide.md` in one window, the narrative in another
3. Follow the facilitator guide sequence — it tells you what to write
   in each section and why the order matters
4. For JD analysis: open `templates/jd-analysis.md`, copy it to
   `private/jd-[company]-[role].md`, paste the job posting, work
   through each section yourself

**The honest caveat:** The facilitator guide tells you to "name the
patterns." That's the one thing this mode can't do — an outside
perspective, human or AI, sees things you don't see about your own
story. If you're going this alone, consider sharing your completed
narrative with a trusted colleague for a read-through before you
use it in applications.

---

## Which mode to use when

| Situation | Mode |
|---|---|
| First time building your narrative | Claude Code — the excavation interview benefits most from real-time file updates |
| Analyzing a batch of job postings | Claude Code or Chat — both work, Code is faster |
| Updating tracker after an application | Claude Code — one command, file updates immediately |
| Traveling, no dev environment | Chat-based — paste and go |
| Sharing the assistant with someone non-technical | No AI or Chat — lower barrier to entry |
| Running the assistant on someone else's machine | Chat-based or No AI |

---

## A note on the `private/` folder

Everything in `private/` is gitignored. It cannot be accidentally
committed or published. Your career narrative, tracker, JD analyses,
cover letter drafts — they stay on your machine only.

The `templates/` folder is the public system. Copy templates to
`private/` before filling them in. Never fill in the templates
directly — if you fork this repo and contribute improvements, you
don't want your personal data in the diff.

---

## Suggested first session prompt (Claude Code)

```
Read the following files in order:
1. docs/facilitator-guide.md
2. docs/methodology.md
3. private/career-narrative.md (if it exists — if not, we're starting fresh)

Then run a career narrative session with me. Follow the facilitator
guide sequence. Ask one question at a time. Write my answers to
private/career-narrative.md as we go. Start with what I'm looking for.
```

Save this somewhere you'll find it. It's the ignition key for the
whole system.
