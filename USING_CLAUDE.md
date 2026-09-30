# Using Claude to build, update, and schedule demos

`SETUP.md` gets the toolkit installed and your tokens captured. This guide is
the next step: **how to actually drive demos with Claude Code** — build content
in plain English, package the flows you repeat into a reusable *skill*, and then
have that skill run **automatically on a schedule** (e.g. every Monday morning)
so your demo org is always fresh without you touching it.

Read it in order the first time. Later, jump to the part you need:

1. [Set up your Claude instance](#1-set-up-your-claude-instance)
2. [Build & update demos interactively](#2-build--update-demos-interactively)
3. [Package a repeatable flow into a skill](#3-package-a-repeatable-flow-into-a-skill)
4. [Run a skill on a schedule (the Monday refresh)](#4-run-a-skill-on-a-schedule-the-monday-refresh)

---

## 1. Set up your Claude instance

**Install Claude Code** (the terminal agent). See
https://docs.claude.com/en/docs/claude-code — on macOS it's typically a one-line
install, then you run `claude` inside any folder.

**Open this folder.** From a terminal:

```bash
cd path/to/slack-demo-generator
claude
```

Claude Code reads [`CLAUDE.md`](CLAUDE.md) in this folder on startup — that file
orients it to the toolkit (how to run scripts via `.venv/bin/python`, the OAuth
gotchas, never to paste tokens in chat, etc.). You don't have to do anything;
it's automatic when you open the folder.

**Finish `SETUP.md`.** If you haven't captured tokens yet, just tell Claude
*"help me set this up"* and walk through it together.

**Connect your data sources (optional but powerful).** The most convincing
demos reference real records — a real opportunity, a real ticket — so names,
amounts, and dates line up. Claude reaches that data through **MCP servers**,
which are configured in Claude Code itself (not in this repo). Common ones:

- **Salesforce** — read/query opportunities, accounts, cases.
- **Atlassian (Jira/Confluence), ServiceNow, etc.** — reference real tickets.

Add them with `claude mcp add ...` (see
https://docs.claude.com/en/docs/claude-code/mcp). Once connected, you can ask
Claude to pull a record and seed matching Slack content in one breath.

> There are **two** paths to data, and you'll use both:
> - *You asking Claude interactively* → Claude uses the **MCP server**.
> - *A committed script running on its own* (like `update_opportunities.py`) →
>   it shells out to a **vendor CLI** (e.g. `sf`). Install that CLI separately.

---

## 2. Build & update demos interactively

The core loop is: **describe what you want in plain English; Claude turns it into
the right script calls.** You don't need to remember flags or file names — but it
helps to know what's possible so you can ask for it.

### Example prompts

**Seed a persona conversation:**

> "Have our AE persona DM the customer contact to confirm tomorrow's call, then
> have the customer reply that they're looping in their VP. Keep it casual."

Claude edits a message config and runs `send_dms_as_users.py`, logging what it
sent to `sent.json` so it can be cleaned up later.

**Build a channel thread grounded in real data:**

> "Pull the open renewal opportunity for <account> from Salesforce and start a
> deal-team thread in that account's channel — opener from the AE summarizing
> where the deal stands, then two replies from the CSM and SE."

Claude queries the Salesforce MCP server, then uses `send_thread.py`. (Thread
openers start with a 🧵 by convention so they're easy to spot.)

**Post an app-style notification:**

> "Drop a PagerDuty 'incident triggered' card into #critical-incidents, then a
> follow-up 'resolved' card in the same thread 20 minutes later in the story."

Claude uses `send_app_notification.py`. The card layouts and logos ship in the
repo — no extra setup (see `SETUP.md` Step 10).

**Manage channels:**

> "Create a private #warroom-<account> channel and invite the AE, the CSM, and
> the SE personas."

Claude uses `channel_admin.py`.

**Clean up afterward:**

> "Tear down everything we posted for this demo."

Claude runs `delete_dms.py` against `sent.json` (persona messages) and deletes
any app cards it posted.

### Tips

- **Keep your scenario configs.** When Claude builds a good flow, ask it to save
  the message config (e.g. `my_demo.json`) so you can replay it. These are
  gitignored — they're yours, and they hold real channel IDs/emails.
- **Preview before blasting.** For app cards, ask for a `--dry-run` first.
- **Let Salesforce/Jira drive the narrative.** Ask Claude to read the record
  *first*, then write the Slack content from it — the story stays consistent.

---

## 3. Package a repeatable flow into a skill

Once you find yourself asking for the *same* sequence over and over ("delete last
week's messages, send this week's, bump the Salesforce dates, keep the renewal
open"), turn it into a **skill** — a saved set of instructions Claude loads on a
trigger phrase and executes step by step.

### What a skill is

A skill is a folder under `~/.claude/skills/<name>/` containing a `SKILL.md`
file with YAML frontmatter and a body of instructions:

```markdown
---
name: demo-refresh
description: One-shot reset of the Slack + Salesforce demo environment.
triggers:
  - "refresh the demo"
  - "reset the demo"
---

# Demo Refresh

Steps Claude should follow, in order, with the exact commands to run...
```

When you type a trigger phrase (or `/demo-refresh`), Claude loads the body and
follows it. Because it lives in `~/.claude/skills/` (outside this repo), it's
personal to you and can safely contain your org's real IDs.

### Start from the example

This repo ships a **sanitized template** at
[`examples/skills/demo-refresh/SKILL.md`](examples/skills/demo-refresh/SKILL.md).
It's the exact shape of a real refresh skill — delete → preflight → send →
update Salesforce — with every org-specific value replaced by a placeholder.

To adopt it:

```bash
mkdir -p ~/.claude/skills/demo-refresh
cp examples/skills/demo-refresh/SKILL.md ~/.claude/skills/demo-refresh/SKILL.md
```

Then open it and fill in your specifics — or just tell Claude:

> "Read examples/skills/demo-refresh/SKILL.md, then help me turn it into my own
> skill in ~/.claude/skills/. My Salesforce org is <alias>, the key account is
> <name>, and here are the channels I post into..."

Claude will interview you for the placeholders and write your personalized skill.

### Test it

Back in a normal Claude Code session, type one of the trigger phrases (or
`/demo-refresh`) and watch it run each step, reading the output back to you. Fix
any step that misbehaves before you automate it — a scheduled skill is only as
reliable as the manual run.

---

## 4. Run a skill on a schedule (the Monday refresh)

The payoff: have your refresh skill run **on its own, on a cadence**, so the demo
org is always current. Claude Code runs **headless** with `claude -p "<prompt>"`
(print mode) — it executes the prompt with no interactive UI and exits. Point a
scheduler at that command and you have a standing demo refresh.

> **The Monday morning refresh** — a concrete, common cadence:
> every Monday at 7am, update Salesforce close dates so the pipeline looks
> current, post fresh channel messages and a P0 incident card, and send the DMs
> that populate each persona's Slack "Today" view. All of that is exactly what
> the `demo-refresh` skill does — so scheduling it is one line.

### The headless command

```bash
cd /path/to/slack-demo-generator && \
  claude -p "refresh the demo" --permission-mode acceptEdits >> ~/demo-refresh.log 2>&1
```

- `-p "refresh the demo"` runs your skill's trigger phrase non-interactively.
- `--permission-mode acceptEdits` (or `--dangerously-skip-permissions` if your
  flow needs to run many commands unattended) keeps it from blocking on prompts.
  **Only use this for a flow you've tested by hand** and trust end to end.
- Redirecting to a log file lets you see what happened after the fact.

Run that line manually once to confirm it works headless before scheduling it.

### macOS — `launchd` (recommended, survives reboots)

Create `~/Library/LaunchAgents/com.you.demo-refresh.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>              <string>com.you.demo-refresh</string>
  <key>ProgramArguments</key>
  <array>
    <string>/bin/zsh</string>
    <string>-lc</string>
    <string>cd /path/to/slack-demo-generator && claude -p "refresh the demo" --permission-mode acceptEdits >> $HOME/demo-refresh.log 2>&1</string>
  </array>
  <!-- Every Monday at 07:00 -->
  <key>StartCalendarInterval</key>
  <dict>
    <key>Weekday</key><integer>1</integer>
    <key>Hour</key><integer>7</integer>
    <key>Minute</key><integer>0</integer>
  </dict>
</dict>
</plist>
```

Load it (once):

```bash
launchctl load ~/Library/LaunchAgents/com.you.demo-refresh.plist
```

`launchd` is preferred over `cron` on macOS because it will run a **missed** job
after the Mac wakes/boots, so a closed laptop on Monday morning still refreshes
once it's back on. Unload with `launchctl unload <plist>` to stop it.

### Linux / simple — `cron`

```bash
crontab -e
```

Add:

```cron
# Every Monday at 07:00 — refresh the Slack + Salesforce demo
0 7 * * 1 cd /path/to/slack-demo-generator && /usr/local/bin/claude -p "refresh the demo" --permission-mode acceptEdits >> $HOME/demo-refresh.log 2>&1
```

Use the **absolute path** to `claude` (find it with `which claude`) — cron has a
minimal `PATH`.

### Things that bite scheduled runs

- **`PATH` is minimal** under launchd/cron. If your skill runs the `sf` CLI, it
  needs its dependencies on `PATH` (on macOS with Homebrew,
  `export PATH="/opt/homebrew/bin:$PATH"`). The example skill already prepends
  this in its Salesforce steps; make sure yours does too.
- **Long-running steps.** `update_opportunities.py` can iterate over many
  opportunities and run for several minutes — fine headless, just don't expect
  an instant finish.
- **Test the exact scheduled command by hand first.** Most scheduling failures
  are really "the command doesn't work in a fresh, non-interactive shell" —
  wrong working directory, missing `PATH`, or a permission prompt with nobody to
  answer it. Run the literal line first; schedule it only once it's green.
- **Keep the manual run trustworthy.** A scheduled skill inherits whatever the
  skill does. Re-test it by hand whenever you change it.

---

That's the whole arc: install Claude Code → build content by asking → save the
repeatable parts as a skill → point a scheduler at `claude -p "<trigger>"`. From
there your demo org refreshes itself on whatever cadence you set.
