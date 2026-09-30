# Claude Code orientation

This toolkit lets a Slack admin send and delete DMs as real users in their
demo Slack org via per-user OAuth tokens. The user may or may not be an
experienced coder — assume they are using Terminal commands and Claude Code
for the first time, and will need clear explanations and more context on
how to install and implement this project.

## What you should do

- **Setup help** — walk the user through `SETUP.md` one step at a time. Don't
  paste long blocks of commands; pause after each step and confirm before
  moving on.
- **Beyond setup, point at `USING_CLAUDE.md`.** It's the end-to-end guide for
  driving demos: building content in plain English, packaging repeat flows into
  a reusable skill (`~/.claude/skills/<name>/SKILL.md`), and scheduling that
  skill for a recurring refresh (see "Scheduling a skill" below; that guide
  deliberately leaves the mechanics to you). A sanitized skill template lives at
  `skills/demo-refresh/SKILL.md` — offer to copy it into
  `~/.claude/skills/` and fill in the user's org specifics when they want a
  repeatable or scheduled refresh.
- **Respect the [Claude Code] vs [Terminal] tags in SETUP.md.** For
  `[Claude Code]` steps, just run the command yourself via the Bash tool
  and show the user the result. For `[Terminal]` steps, **don't run them
  yourself** — instead, tell the user: "please open a Terminal window, make
  sure you're in the project folder, and run this:" followed by the
  command. These steps block on interactive input (`getpass`, an OAuth
  callback, `y/N` confirms) that the Bash tool can't drive.
- **Venv in Claude Code sessions.** Each Bash tool call runs in a fresh
  shell, so `source .venv/bin/activate` doesn't persist. Always invoke the
  project's Python as `.venv/bin/python <script>` (macOS/Linux) or
  `.venv\Scripts\python.exe <script>` (Windows) instead of activating.
- **Ask Mac or Windows first.** Before Step 4, ask which OS they're on. The
  doc is Mac-first; for Windows users, substitute from the
  `## Windows commands` table at the bottom of `SETUP.md` whenever a command
  starts with `source`, `cp`, or `python3.12`. Everything else is identical.
- **After token capture** — always run `python scripts/verify_setup.py` and read the
  output before declaring setup done.
- **Sending DMs** — copy `examples/send_messages.example.json` to a new file,
  edit it for the user's demo, then run
  `python scripts/send_dms_as_users.py --config <file> --manifest sent.json`.
  Keep the manifest — it's how `scripts/delete_dms.py` knows what to remove later.
  When the user just asks in plain English ("send a DM from X to Y"), do all
  of this for them. They shouldn't have to edit configs or run commands.
- **App notifications always come from this repo's Block Kit library.** When
  the user asks for an app notification in plain English ("post a PagerDuty
  alert in #incidents"), use `scripts/send_app_notification.py`. It reads the
  layout from `blockkit/<app>.json` and the logo from `logos/<app>.png` (served
  from the public repo). Run `--list` to see apps/examples, pick the closest
  example, adapt the text in its blocks to the user's story, and `--dry-run`
  first if unsure. Never hand-build Block Kit or post app notifications any
  other way. If the app or layout they want isn't in the library, say so and
  tell them to contact Alex Lee, who maintains the library, to get it added.
  Post Jira notifications with `--ticket-url` pointing at a real ticket.
- **Thread openers start with 🧵.** Any parent message that kicks off a thread
  begins with the 🧵 emoji so it's easy to spot. Replies don't.

## What you must NOT do

- **Never ask the user to paste a token into the chat.** Always route them
  through `scripts/auth_user.py` (browser OAuth) for `xoxp-` user tokens or
  `scripts/save_bot_token.py` (getpass) for the optional `xoxb-` bot token (channel
  admin, strict verification, app notifications).
  Re-pasting tokens in chat re-leaks them into transcripts/logs.
- **Don't fabricate features.** This toolkit does NOT include AI agents. If
  asked for those, say so.
  - **Channel management IS now in scope** (as of the 2026-07 expansion). The
    bot token carries channel scopes and the repo provides `scripts/channel_admin.py`
    (resolve/ensure/create/rename/topic/archive), `scripts/preflight.py`, and
    `scripts/check_bot_token.py`. The goal is a **demo-asset builder** with read/write
    access to channels (and, as scopes are added, users/apps/content) so demos
    can be staged easily in Slack. See "Channel admin toolbox" and the
    Enterprise+ notes below.

## Channel admin & Enterprise+ orgs

**Every demo org is an Enterprise+ organization** (formerly called Enterprise
Grid): one or more workspaces (`T...`) nested under an enterprise (`E...`).
There are no standalone workspaces on lower tiers, so always assume the quirks
below apply. The bot token (`app_token`) carries channel
scopes: `channels:read`, `groups:read`, `channels:manage`, `groups:write`,
`channels:join`. Hard-won quirks — don't rediscover them:

- **Enterprise+ needs `team_id`** on `conversations.list` and `conversations.create`
  (else `missing_argument`). `scripts/channel_admin.py` auto-discovers it from a
  persona token; reuse that helper rather than hard-coding.
- **Archive/invite require bot membership**, even for PUBLIC channels
  (`not_in_channel` otherwise). Bot self-joins public via `channels:join`;
  PRIVATE channels need a manual `/invite` of the bot.
- **Older bot installs may lack `users:read.email`** — resolve persona
  email→id via each persona's own token `auth.test` (see
  `channel_admin.persona_user_id`).
- After the user saves the bot token (SETUP Side Quest 1) or rotates it, run `.venv/bin/python scripts/check_bot_token.py` to
  confirm the token installed to the RIGHT org (a reinstall can silently land
  in the wrong Enterprise+ org → `team_access_not_granted`). To make that check
  assert a specific org, set `EXPECTED_ENTERPRISE_ID` (and optionally
  `CHECK_CHANNEL`) in the environment first; without them the script just
  reports what it sees.

Toolbox: `scripts/channel_admin.py` (CLI + library), `scripts/preflight.py` (validate configs
+ heal membership before sending), `scripts/archive_channel.py`, `scripts/check_bot_token.py`.

## Connecting Salesforce, Jira & other MCP servers

When the user wants to connect tools (SETUP Side Quest 2), do it for them:

- **Salesforce CLI:** install it (`brew install sf` on macOS; needs Node). The
  user runs `sf org login web --alias demo --set-default` themselves in
  Terminal (browser login). Scripts need `/opt/homebrew/bin` on `PATH`, and
  `sf --json` output can include ANSI codes, so set `NO_COLOR=1` when parsing.
- **Salesforce MCP:** `claude mcp add salesforce -- npx -y @salesforce/mcp --orgs DEFAULT_TARGET_ORG --toolsets all`
  (uses the CLI login).
- **Atlassian MCP:** `claude mcp add --transport http atlassian https://mcp.atlassian.com/v1/mcp`,
  then the user runs `/mcp` → atlassian to sign in.
- After adding a server, tell the user to restart Claude Code and check `/mcp`.
- **Use them together with Slack.** Salesforce record changes (new case, new
  opportunity, date changes) can fire the org's real Salesforce-to-Slack
  workflow notifications, so prefer updating Salesforce over faking those.
  For Jira app notifications, create a real ticket via the Atlassian MCP first
  and pass its URL with `--ticket-url`.

## Scheduling a skill

When the user asks to schedule a skill (e.g. "run my demo refresh every Monday
at 7am"), you set it up. Don't hand them plist/cron files to write. Use the OS's
built-in scheduler, so nothing needs to be installed.

1. **Confirm the skill works by hand first.** If it hasn't been run
   successfully, run it (or ask them to) before scheduling.
2. **Build the headless command** and run it once yourself to prove it works
   in a fresh shell:
   ```bash
   cd /abs/path/to/slack-demo-generator && \
     /abs/path/to/claude -p "<trigger phrase>" --allowedTools "Bash" >> "$HOME/demo-refresh.log" 2>&1
   ```
   `--allowedTools "Bash"` is required: headless runs can't answer permission
   prompts, so without it every script call is denied and the run silently
   does nothing. (`--permission-mode acceptEdits` is NOT enough; it only
   covers file edits.) Use absolute paths (`which claude`).
3. **macOS: create a launchd agent** at
   `~/Library/LaunchAgents/com.<user>.demo-refresh.plist` that runs
   `/bin/zsh -lc "<command above>"` with a `StartCalendarInterval`
   (Weekday 1 = Monday, Hour, Minute), then `launchctl load` it. Prefer launchd
   over cron on macOS: it runs a missed job once the Mac wakes.
   **Linux:** add a `crontab` line (e.g. `0 7 * * 1 <command>`).
4. **PATH is minimal** under launchd/cron. If the skill runs `sf`, it needs
   `export PATH="/opt/homebrew/bin:$PATH"` (Homebrew) so `sf` finds `node`.
5. Tell the user in plain language what you set up, when it runs, where the
   log is, and how to turn it off (ask you, or
   `launchctl unload <plist>` / remove the crontab line). If they ask
   "did it work?", read the log.

## Critical OAuth gotcha

When `scripts/auth_user.py` opens the OAuth URL, it goes to the user's **default**
browser. If they're logged in to Slack there as a different user (e.g., their
admin account), Slack silently grants THAT user's token. The script's
post-capture check (`auth.test` + `users.lookupByEmail`) catches this and
refuses to save — but to avoid the round trip, **tell the user upfront** to
copy the printed URL into an **incognito** window logged in as the target
persona. Incognito shortcut: `Cmd+Shift+N` (Chrome/Edge on Mac),
`Ctrl+Shift+N` (Chrome/Edge on Windows), or `Ctrl+Shift+P` /
`Cmd+Shift+P` (Firefox).

If the user has `app_token` configured in `tokens.json`, verification is
strict (lookupByEmail). If not, verification falls back to a heuristic
name-match. Recommend they set up `app_token` for strict verification when
working with multiple personas.

## Token rotation

If the user needs to rotate tokens:
1. Rotate via Slack app UI (Basic Information page for client secret;
   reinstall app for new bot/user tokens).
2. For the bot token: `python scripts/save_bot_token.py` (getpass).
3. For user tokens: re-run `scripts/auth_user.py --email <email>` per persona.
4. Reinstalling the app does NOT invalidate already-captured `xoxp-` tokens,
   so you usually only need to re-capture the bot token.
