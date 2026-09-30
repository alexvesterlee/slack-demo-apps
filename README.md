# slack-demo-generator

A demo-preparation toolkit for Slack Solutions Engineers. Use it to stage a
realistic, "lived-in" Slack org before a customer demo — then clean it all up
in one step afterward. You drive it in plain English through your AI coding
agent (Claude Code); it turns each request into the right API calls.

Once set up, you can:

- **Post messages, threads, and DMs as real personas** (an AE, a CSM, a
  customer contact) using each person's own token — so content carries their
  real name and avatar, not a bot's.
- **Share files** (draft contracts, decks, PDFs) in-channel as a persona.
- **Post app-style notification cards** — a PagerDuty alert, a Salesforce
  "deal won," a Jira update — as the third-party app, via Block Kit.
- **Create and manage channels** (create / rename / set topic / archive).
- **Ground content in real data** by pulling from Salesforce, Jira, or any
  other system through an MCP server, so the story stays internally consistent.
- **Clean it all up** from a manifest of everything you posted.

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

## What's in here

| Area | Files |
|---|---|
| Setup & auth | `auth_user.py`, `save_bot_token.py`, `check_bot_token.py`, `verify_setup.py`, `config.py`, `preflight.py`, `tokens.example.json` |
| Posting content | `examples/send_dms_as_users.py`, `examples/send_thread.py`, `examples/delete_dms.py` |
| Channels | `channel_admin.py`, `archive_channel.py` |
| App notifications | `send_app_notification.py`, `blockkit/*.json`, `logos/*.png`, `push_logos.py`, `push_blockkit.py` |

See the **File reference** and **How it fits together** sections in
[SETUP.md](SETUP.md) for the full picture.

---

*Originally forked from
[scastaneda-eng/slack-dm-generator](https://github.com/scastaneda-eng/slack-dm-generator)
and broadened from a DM-seeding script into a general demo-asset builder.*
