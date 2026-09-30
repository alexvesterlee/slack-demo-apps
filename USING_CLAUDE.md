# Using Claude to build, update, and schedule demos

`SETUP.md` gets everything installed. This guide covers what comes next:
**asking Claude to build your demo**, saving the steps you repeat as a
**skill**, and having that skill **run on a schedule** so your demo stays fresh
on its own.

1. [Get started](#1-get-started)
2. [Build demos by asking](#2-build-demos-by-asking)
3. [Save a repeatable flow as a skill](#3-save-a-repeatable-flow-as-a-skill)
4. [Run it on a schedule](#4-run-it-on-a-schedule)

---

## 1. Get started

1. **Install Claude Code** (see https://docs.claude.com/en/docs/claude-code).
2. **Open this folder in Claude Code.** In a terminal:

   ```bash
   cd path/to/slack-demo-generator
   claude
   ```

   Claude automatically picks up its instructions for this toolkit. You don't
   need to do anything else.
3. **Not set up yet?** Tell Claude *"help me set this up"* and it will walk you
   through `SETUP.md`.

**Optional: connect Salesforce, Jira, and other tools.** The best demos use
real records, like a real opportunity or a real ticket, so the story lines up.
Claude connects to these through **MCP servers**, which you add in Claude Code
(see https://docs.claude.com/en/docs/claude-code/mcp). Once connected, you can
say "pull this opportunity and post about it in Slack" in one request.

---

## 2. Build demos by asking

Describe what you want in plain English. Claude writes the messages and runs
the right scripts. You don't need to remember any commands.

**Send DMs between personas**
> "Have our AE DM the customer to confirm tomorrow's call, then have the
> customer reply that they're bringing their VP."

Claude sends each message as that person and keeps a list of everything it
sent, so it can be cleaned up later.

**Start a thread using real data**
> "Look up the open renewal for <account> in Salesforce and start a deal-team
> thread in that account's channel. The AE summarizes the deal, then the CSM
> and SE reply."

Claude reads the opportunity from Salesforce, then uses a Python script to
create the thread in the channel.

**Post an app notification**
> "Post a PagerDuty 'incident triggered' alert in #critical-incidents, then a
> 'resolved' update in the same thread."

Claude posts it as the PagerDuty app, using card designs and logos that come
with this repo.

**Set up channels**
> "Create a private #warroom-<account> channel and add the AE, CSM, and SE."

**Clean up**
> "Delete everything we posted for this demo."

### Tips

- **Save the good ones.** When a demo comes out well, ask Claude to save it so
  you can replay it later. These files stay on your computer and never go to
  GitHub.
- **Preview first.** Ask Claude to show you a message or card before it posts.
- **Start from real data.** Ask Claude to look up the record first, then write
  the Slack messages from it so the details match.

---

## 3. Save a repeatable flow as a skill

If you keep asking for the same steps (for example "delete last week's
messages, post this week's, and update the Salesforce dates"), save them as a
**skill**. A skill is a saved set of instructions that Claude runs whenever you
say its trigger phrase, like *"refresh the demo"*.

This repo includes a ready-made example:
[`skills/demo-refresh/SKILL.md`](skills/demo-refresh/SKILL.md). To make it
yours, tell Claude:

> "Help me turn skills/demo-refresh/SKILL.md into my own skill. My Salesforce
> org is <alias>, my key account is <name>, and these are the channels I use..."

Claude asks you a few questions and saves your personal version on your
computer, not in the repo, so your org's details stay private.

**Test it.** Say *"refresh the demo"* and watch each step run. Fix anything that
goes wrong before you schedule it.

---

## 4. Run it on a schedule

Once your skill works when you run it by hand, Claude can set it to run
automatically. For example, you could have it run **every Monday at 7am** and:

- update Salesforce close dates so the pipeline looks current,
- post fresh channel messages and an incident alert,
- send the DMs that fill each persona's Slack "Today" view.

Just tell Claude:

> "Schedule my demo refresh to run every Monday at 7am."

Claude sets it up using your computer's built-in scheduler. **You don't need to
download or install anything.** Claude can also check it, change the time, or
turn it off later. Just ask.

**Good to know:**

- **Your computer needs to be on.** On a Mac, if the laptop was closed at 7am,
  the refresh runs as soon as it wakes up.
- **It runs without asking.** A scheduled run can't stop and ask your
  permission, so Claude pre-approves the commands your skill uses. Only
  schedule a skill you've tested by hand and trust.
- **Check the log.** Each run writes to a log file. Ask Claude *"did my demo
  refresh work?"* and it will read it for you.
- **Check your company's policy.** If your organization has rules about
  automated jobs on work laptops, follow them.

---

**The whole idea:** ask Claude to build your demo → save the steps you repeat
as a skill → schedule it. After that, your demo org stays fresh on its own.
