# slack-demo-generator

A demo-preparation toolkit for Slack Solutions Engineers. Use it to stage a
realistic, "lived-in" Slack org before a customer demo — then clean it all up
in one step afterward. You drive it in plain English through your AI coding
agent (Claude Code); it turns each request into the right API calls.

## Why use this

- **Full automation:** Refresh an entire demo story in one shot: send DMs,
  post channel messages, trigger app notifications, and update Salesforce. It
  can run on a set schedule (mine runs a skill every Monday at 8am, as long as
  my computer is on), so your demo org is always fresh.
- **Real messages from real users:** Messages, threads, and DMs are sent as the
  actual users, with their real name and photo and no `APP` badge. They look
  real, and because they're genuine user messages they also make Slack search
  and Slackbot answers better.
- **Real system connections:** Claude can read and update the tools you
  connect, like creating Salesforce cases and opportunities or pushing out
  close dates. Those changes can trigger your org's real Salesforce-to-Slack
  workflow notifications, and Jira notifications can link to real tickets.
- **App notifications for any app:** For systems you don't have access to,
  post realistic notifications from apps like PagerDuty, Datadog, ServiceNow,
  and Jira, using the [app notification library](blockkit/) I maintain in
  this repo. Each one mimics the real app's layout and logo.
- **Channel management:** Create channels, add users, set topics, and rename or
  archive channels, so you can build out a full demo org, not just a few
  messages.
- **Document creation:** Generate PDFs and other documents from your
  third-party data, and have users share them in channels and DMs.
- **Salesforce page layout design:** Update Salesforce field names and page
  structure to match a customer's layout. (Works well for field renames and
  small changes; full object redesigns can be buggy.)
- **One-step cleanup:** Everything sent as a user is tracked, so you can delete
  it all with a single request.

> **New to Vibe Coding or Terminal commands?** No problem. You can ask your
> agent for clarification or step-by-step instructions at any point. This
> project was built with beginner coders in mind.

## Get started

Read [SETUP.md](SETUP.md). Core setup is ~15–20 minutes; you can do the minimum
(personas + messages) first and add the optional pieces (app notifications,
channel admin, MCP-grounded data) whenever you need them. You'll need:

- Admin access to your demo Slack org
- Python 3.12
- A willingness to click through one self-signed cert warning
- *(optional)* a GitHub PAT — only if you want to post app-notification cards
- *(optional)* MCP servers configured in your agent — only to ground content
  in real data

## Using Claude Code?

Open this folder in Claude Code and ask: *"help me set this up."*
[CLAUDE.md](CLAUDE.md) tells Claude how to handle the gotchas (incognito for
OAuth, never paste tokens in chat, what to do if verification fails, etc.).

Once you're set up, [USING_CLAUDE.md](USING_CLAUDE.md) is the end-to-end guide to
actually *driving* demos with Claude: building content in plain English,
packaging the flows you repeat into a reusable **skill**, and running that skill
**on a schedule** (e.g. a Monday-morning refresh that bumps Salesforce dates and
reseeds channels/DMs on its own).

## What's in here

```
├── README.md            ← you are here
├── SETUP.md             ← one-time install & token capture
├── USING_CLAUDE.md      ← build demos, author skills, schedule them
├── CLAUDE.md            ← orientation Claude Code reads automatically
├── requirements.txt     ← Python dependencies
├── tokens.example.json  ← copy to tokens.json and fill in
├── scripts/             ← all the Python (run these)
│   ├── config.py                  shared helpers (token loading, clients)
│   ├── auth_user.py · save_bot_token.py · check_bot_token.py · verify_setup.py
│   ├── send_dms_as_users.py · send_thread.py · delete_dms.py
│   ├── channel_admin.py · preflight.py · archive_channel.py
│   ├── send_app_notification.py · push_logos.py · push_blockkit.py
│   └── update_opportunities.py · update_profile.py · run_demo.py
├── blockkit/            ← app-notification card layouts (*.json)
├── logos/               ← app-notification icons (*.png)
├── skills/              ← reusable Claude skill templates (demo-refresh)
└── examples/            ← configs you copy & edit for a demo
```

Run any script from the repo root as `.venv/bin/python scripts/<name>.py`
(config.py and your `tokens.json` are found automatically). See the
**File reference** and **How it fits together** sections in
[SETUP.md](SETUP.md) for the full picture.

---

*Originally forked from
[scastaneda-eng/slack-dm-generator](https://github.com/scastaneda-eng/slack-dm-generator)
and broadened from a DM-seeding script into a general demo-asset builder.*
