# slack-demo-generator — Setup

This toolkit lets you **stage realistic, lived-in content in a Slack demo org**
— as the real people, apps, and channels a customer would expect to see. You
drive it in plain English through Claude Code; it turns each request into the
right Slack (and, optionally, third-party) API calls.

Once it's set up you can, for example:

- **Post messages, threads, and DMs as real personas** (an AE, a CSM, a
  customer contact) using each person's own token — so the messages carry
  their real name and avatar, not a bot's.
- **Share files** (draft contracts, decks, PDFs) in-channel as a persona.
- **Post app-style notification cards** — a PagerDuty alert, a Salesforce
  "deal won," a Jira update — as the third-party app, using Block Kit.
- **Create and manage channels** (create / rename / set topic / archive).
- **Ground the content in real data** by pulling from Salesforce, Jira, or any
  other system through an MCP server, so the story stays internally consistent.
- **Clean it all up afterward** from a manifest of everything you posted.

Setup is one-time, ~15–20 minutes. You can do the minimum (personas + messages)
first and add the optional pieces (app notifications, channel admin, MCP data)
whenever you need them.

> **Already set up?** [USING_CLAUDE.md](USING_CLAUDE.md) is the next guide: how
> to build demos with Claude in plain English, package repeat flows into a
> reusable skill, and run that skill on a schedule (e.g. a Monday refresh).

> **New to this? Read the [architecture 101](#how-it-fits-together) at the
> bottom first** — one diagram of how Claude, this folder, and Slack connect.

---

## Before you start — if this is your first time with a terminal

This guide assumes you may never have used Terminal, Python, or Claude Code
before. That's fine — read this short primer and you'll be oriented.

**Claude Code** is an AI assistant that runs inside a folder on your
computer. You type a request in plain English and it can read your files
and run commands for you. If you're reading this because Claude Code told
you to, you already have it installed — you just type into the prompt.

**Terminal** is the Mac/Linux app that lets you type commands directly to
your computer (on Windows, the equivalent is **PowerShell**). You can open
it from Spotlight: press `Cmd+Space`, type `Terminal`, hit Enter.

**Every command below is tagged with where to run it:**

- **[Claude Code]** — paste the command into your Claude Code prompt (or
  just ask Claude to run it). Claude handles the typing for you.
- **[Terminal]** — open a dedicated Terminal / PowerShell window and type
  the command there. Use these for anything that takes over your screen
  with prompts or hidden input.

**About the working directory.** All the commands below assume you're
"inside" the toolkit folder. In Claude Code that's automatic if you opened
this folder. In a fresh Terminal window, you get there once with:

```bash
cd path/to/slack-demo-generator
```

Replace `path/to/` with wherever you cloned/downloaded it (e.g.
`cd ~/claude-projects/slack-demo-generator`).

**About `.venv` (Python virtual environment).** Step 4 creates a folder
called `.venv` inside the project. It's a private, sandboxed copy of Python
just for this toolkit — that way installing packages here won't affect the
rest of your system. You'll see the `.venv/` folder appear; that's
expected. `source .venv/bin/activate` (Step 4) tells *your current Terminal
window* to use that sandbox. It only lasts for that window — open a new
Terminal and you'd re-activate it. When running from Claude Code, each
command runs in a fresh shell, so Claude will call `.venv/bin/python`
directly instead of activating.

---

## Prerequisites

- **Slack admin** in your demo org (you need to install an app there).
- **Python 3.12** — the macOS system Python (3.9) is too old.
  **[Terminal]** (one-time system install):
  ```bash
  brew install python@3.12
  ```
  > **Don't have Homebrew?** Homebrew is the standard Mac package manager.
  > Install it once from https://brew.sh (a single command to paste into
  > Terminal), then run `brew install python@3.12` above.
  >
  > **On Windows?** Download the Python 3.12 installer from
  > https://www.python.org/downloads/ and **check "Add python.exe to PATH"**
  > on the first installer screen. When you hit a step below whose command
  > starts with `source`, `cp`, or `python3.12`, swap it for the Windows
  > equivalent in the [Windows commands](#windows-commands) table at the
  > bottom of this file. Every other command is identical.
- **macOS, Linux, or Windows** — the toolkit generates its own OAuth cert
  using a pure-Python library, so you don't need `openssl` installed.
- **(Optional) A GitHub account + a fine-grained PAT** — *not* needed to post
  app-style notification cards (the layouts and logos ship in this repo). Only
  needed if you want to host your **own** custom app logos as message avatars,
  since Slack requires a public URL for a custom icon. See
  [Step 10](#step-10-optional--app-style-notifications).
- **(Optional) MCP servers** — only if you want to ground content in real data
  (Salesforce, Jira/Atlassian, ServiceNow, …). Configured in Claude Code, not
  here. See [Step 11](#step-11-optional--ground-content-in-real-data-mcp).

---

## Step 1 — Create the Slack app (from a manifest)

A manifest creates the app with every setting the toolkit needs already filled
in: the redirect URL plus a broad set of user and bot scopes (including ones
for future demos). You don't toggle anything by hand.

1. Go to https://api.slack.com/apps → **Create New App** → **From a manifest**.
2. Pick your demo workspace → **Next**.
3. Choose the **JSON** tab, delete the sample, and paste this:

   ```json
   {
     "display_information": {
       "name": "Demo Content Helper"
     },
     "features": {
       "bot_user": {
         "display_name": "Demo Content Helper",
         "always_online": false
       }
     },
     "oauth_config": {
       "redirect_urls": [
         "https://localhost:3000/oauth/callback"
       ],
       "scopes": {
         "user": [
           "chat:write",
           "users.profile:read",
           "users.profile:write",
           "files:write",
           "reactions:write",
           "channels:write",
           "groups:write",
           "im:write",
           "mpim:write",
           "users:write",
           "admin.dlp:write",
           "admin",
           "admin.analytics:read",
           "admin.app_activities:read",
           "admin.apps:read",
           "admin.apps:write",
           "admin.barriers:write",
           "admin.conversations:read",
           "admin.conversations:write",
           "admin.users:write",
           "admin.workflows:read",
           "admin.workflows:write",
           "workflows.templates:write"
         ],
         "bot": [
           "chat:write",
           "chat:write.customize",
           "chat:write.public",
           "users:read",
           "users:read.email",
           "users.profile:read",
           "channels:read",
           "groups:read",
           "channels:manage",
           "groups:write",
           "channels:join",
           "channels:write.invites",
           "groups:write.invites",
           "channels:history",
           "groups:history",
           "im:write",
           "mpim:write",
           "files:read",
           "files:write",
           "reactions:write",
           "pins:write",
           "bookmarks:write",
           "canvases:read",
           "canvases:write",
           "lists:write",
           "team:read",
           "emoji:read",
           "links:write",
           "assistant:write",
           "calls:write",
           "im:read",
           "im:write.topic",
           "mcp:connect",
           "metadata.message:read",
           "mpim:history",
           "reactions:read",
           "search:read.public",
           "search:read.users",
           "triggers:read",
           "triggers:write",
           "users:write",
           "workflow.steps:execute",
           "workflows.templates:read",
           "workflows.templates:write",
           "remote_files:write"
         ]
       }
     },
     "settings": {
       "org_deploy_enabled": false,
       "socket_mode_enabled": false,
       "token_rotation_enabled": false
     }
   }
   ```

   > ✏️ **The only thing you might edit:** `name` (under `display_information`)
   > and `display_name` (under `bot_user`). This is what the app is called in
   > your workspace. Change both to whatever you like. Leave everything else
   > as-is.

4. **Next** → review the summary → **Create**.

> One app carries **both** kinds of token you'll use: **User tokens**
> (`xoxp-`, one per persona — these post as real people) and a single **Bot
> token** (`xoxb-` — this posts app notifications, manages channels, and does
> strict verification). The manifest grants the scopes for both.

---

## Step 2 — Install the app

In the app settings, go to **OAuth & Permissions** (or **Install App**) →
**Install to Workspace** → **Allow**. That's it. Scopes and the redirect URL
came from the manifest.

<details>
<summary>What the manifest's scopes do (reference)</summary>

The redirect URL `https://localhost:3000/oauth/callback` must be `https://`.
Slack rejects `http://localhost`, and the toolkit generates a self-signed cert
for it on first run.

**User Token Scopes.** These are what `scripts/auth_user.py` requests when it
captures a persona token (see `USER_SCOPES` in that file; keep it in sync with
the manifest):

| Scope | Enables |
|---|---|
| `chat:write` | Post & delete messages/DMs/threads as the persona (**required**) |
| `users.profile:read` | Read the persona's profile (used in verification) |
| `users.profile:write` | Set the persona's display name / status |
| `files:write` | Upload files (contracts, decks, PDFs) as the persona |
| `reactions:write` | Add emoji reactions as the persona |
| `channels:write`, `groups:write` | Persona-level channel actions |
| `im:write`, `mpim:write` | Open DMs / group DMs as the persona |
| `users:write` | Set the persona's presence (show as active during a demo) |
| `workflows.templates:write` | Create Workflow Builder templates as the persona |
| `admin`, `admin.*` | Org admin APIs: users, conversations, apps, workflows, barriers, DLP, analytics. Only work for a persona who is an org admin/owner |

**Bot Token Scopes** (app notifications, channel admin, strict verification):

| Scope | Enables |
|---|---|
| `chat:write` | Bot posts (app notification cards) |
| `chat:write.customize` | Post those cards under a **custom name + icon** (e.g. "PagerDuty") |
| `chat:write.public` | Post to public channels the bot hasn't joined |
| `users:read`, `users:read.email` | Strict persona verification (email → user ID); `users:read.email` requires `users:read` |
| `users.profile:read` | Read profiles (names, titles) when building content |
| `channels:read`, `groups:read` | List/resolve channels |
| `channels:manage`, `groups:write` | Create / rename / set topic / archive channels |
| `channels:join` | Bot self-joins public channels (needed before archiving/inviting) |
| `channels:write.invites`, `groups:write.invites` | Invite personas into channels |
| `channels:history`, `groups:history` | Read existing channel messages (check content, clean up bot posts) |
| `im:write`, `mpim:write` | Send app notifications in DMs / group DMs |
| `files:read`, `files:write` | Upload files as the app (reports, exports) |
| `reactions:write`, `pins:write`, `bookmarks:write` | Add reactions, pin messages, add channel bookmarks |
| `canvases:read`, `canvases:write`, `lists:write` | Create and edit channel canvases and Lists |
| `team:read`, `emoji:read` | Read workspace info and custom emoji |
| `im:read`, `im:write.topic`, `mpim:history` | Read DMs, set DM topics, read group DM history |
| `reactions:read`, `metadata.message:read` | Read reactions and message metadata |
| `search:read.public`, `search:read.users` | Search public messages and users |
| `users:write` | Set the bot's presence |
| `links:write` | Custom link unfurls (needs unfurl domains configured) |
| `assistant:write` | Agents & Assistants (needs that feature turned on) |
| `workflow.steps:execute`, `triggers:read`, `triggers:write`, `workflows.templates:read`, `workflows.templates:write` | Workflow Builder steps, triggers and templates |
| `calls:write`, `remote_files:write`, `mcp:connect` | Calls, remote files, MCP connections |

Not every scope has a ready-made script. Most are there so Claude can do those
things on request without you having to reinstall the app first.

> ⚠ **About the `admin` scopes:** a user token only gets real admin power if
> the persona who authorizes it is an org admin or owner, and on Enterprise
> Grid an admin may need to approve the app before it installs. `auth_user.py`
> doesn't request them by default. To use them for a persona, add them to
> `USER_SCOPES` (see below). Treat any token that has them like an admin
> password.

</details>

> ℹ **You can add more scopes later.** This manifest covers what the toolkit
> uses plus a broad set of extras. If a specific demo needs something that
> isn't listed, add it anytime:
> 1. In the app settings, open **App Manifest** (or **OAuth & Permissions**)
>    and add the scope.
> 2. **Reinstall** the app so the bot token picks it up.
> 3. For a **user** (persona) scope, also add it to `USER_SCOPES` in
>    `scripts/auth_user.py` and re-run `scripts/auth_user.py` for each persona.
>    Scopes are baked into a token when it's captured.


---

## Step 3 — Get the OAuth credentials

1. In the app settings, go to **Basic Information**.
2. Under **App Credentials**, copy:
   - **Client ID**
   - **Client Secret** (click "Show")

You'll paste these into `tokens.json` in Step 5.

---

## Step 4 — Set up Python

**[Claude Code]** Ask Claude to run these, or paste them into the prompt.
If you're using Terminal instead, run them there — just make sure you've
`cd`'d into the toolkit folder first (see "Before you start" above).

```bash
python3.12 -m venv .venv
pip install -r requirements.txt
```

You'll see a new `.venv/` folder appear in the project — that's the
sandboxed Python install. It's gitignored, so it won't be committed.

**If you're working in a dedicated Terminal window (not Claude Code),**
also run this once per new Terminal window, so your shell uses the sandbox:

```bash
source .venv/bin/activate
```

You'll know it worked when your prompt gains a `(.venv)` prefix. You do
**not** need to run `source ...` inside Claude Code — Claude calls
`.venv/bin/python` directly.

---

## Step 5 — Create `tokens.json`

**[Claude Code]** Ask Claude to run this, or do it yourself in Terminal:

```bash
cp tokens.example.json tokens.json
```

Open `tokens.json` and fill in `oauth.client_id` and `oauth.client_secret`
from Step 3. Leave everything else as-is for now. (If you're in Claude
Code, you can ask Claude to open the file and help you edit it — just
paste the client ID/secret from the Slack web UI; don't paste other
tokens.)

> ⚠ **Never paste tokens into a chat with Claude Code.** Always use the
> local scripts (`scripts/auth_user.py` for user tokens, `scripts/save_bot_token.py` for the
> bot token). Pasting tokens into chat re-leaks them.

---

## Step 6 — Capture per-persona tokens

**[Terminal]** — run this in a dedicated Terminal window, not Claude Code.
(The script prints a URL, then waits for your browser to complete OAuth.
You need to watch it live and have the window stay open.)

For each user you want to impersonate (e.g., an AE persona, a customer
persona, a deal-desk persona):

```bash
python -u scripts/auth_user.py --email persona@yourorg.com
```

> ⚠ Use `python -u` (unbuffered) so the OAuth URL prints **before** the
> script blocks waiting for the callback.

The script will print an OAuth URL. **STOP** — read this carefully:

> ⚠ **Critical: open the URL in an INCOGNITO window** logged in as the
> target persona. Do NOT use your default browser if you're logged in there
> as a different user (e.g., your admin account). If you do, Slack will
> silently grant the wrong user's token.

> ℹ The script also tries to open your default browser as a convenience —
> ignore that tab if it goes to the wrong account.

> ℹ Your browser will warn about the self-signed cert. Click
> **advanced → proceed** to continue.

After you authorize, the script:
1. Captures the `xoxp-` token from the OAuth callback.
2. Calls `auth.test` on the new token to find out which user it actually
   belongs to.
3. (If `app_token` is configured) calls `users.lookupByEmail(email)` to get
   the user ID for the email you passed.
4. **Refuses to save** if those don't match — and tells you to retry in
   incognito.

Repeat for every persona. Each is stored under `users` in `tokens.json`,
keyed by email.

> ℹ **Which persona can do what depends on the scopes it was captured with.**
> A persona captured with only `chat:write` can post messages but *not* upload
> a file — you'll get `missing_scope needed=files:write:user`. Re-run
> `scripts/auth_user.py` for that persona after widening `USER_SCOPES`, or pick a
> persona that already has the scope for that role.

---

## Step 7 — Verify

**[Claude Code]** (or Terminal, either works):

```bash
python scripts/verify_setup.py
```

Should print every persona email + matching user ID and end with
`READY — all checks passed.` If anything is flagged, fix it before moving on.
In Claude Code, Claude can run this and read the output back to you.

---

## Step 8 — Post your first content (as a persona)

The simplest content is a message or DM sent as one of your personas. Every
human message goes out through that **persona's own token** — never the bot.

1. Copy the example config:
   ```bash
   cp examples/send_messages.example.json my_demo.json
   ```
2. Edit `my_demo.json` — set `sender_email` (one of your captured personas)
   and the recipient / channel. In Claude Code, ask Claude to open and edit it.
3. Send:
   ```bash
   python scripts/send_dms_as_users.py --config my_demo.json --manifest sent.json
   ```
4. Confirm it appears in Slack.

**Threads** work the same way — see `scripts/send_thread.py` for a parent
message plus threaded replies from different personas.

> ℹ **Manifest = your undo button.** Everything sent as a persona is appended
> to `sent.json`. To clean up:
> ```bash
> python scripts/delete_dms.py --manifest sent.json
> ```
> (User tokens can only delete their *own* messages, so the manifest records
> which persona sent each one.)

> ℹ **Convention:** thread-opener messages start with a 🧵 emoji so it's
> obvious at a glance which message roots a thread.

---

## Step 9 (optional) — Channel management

The **bot token** unlocks channel administration — creating, renaming,
setting topics on, and archiving channels. (The same bot token also backs
strict verification in Step 7 and app notifications in Step 10 — one bot token
serves all of them.)

1. Make sure the app is installed ([Step 2](#step-2-install-the-app)). The
   manifest from Step 1 already includes the bot scopes.
2. Copy the **Bot User OAuth Token** (`xoxb-...`) from the app's **Install
   App** page.
   > ℹ Reinstalling the app does **not** invalidate already-captured
   > `xoxp-` user tokens.
3. **[Terminal]** — save it (hidden paste prompt + `y/N` confirm, which Claude
   Code's runner can't drive):
   ```bash
   python scripts/save_bot_token.py
   ```
   Paste the `xoxb-` when prompted. **Your keystrokes won't appear on
   screen — that's intentional (`getpass` hides them). Just paste and Enter.**
4. **[Claude Code]** Confirm the token landed in the right workspace:
   ```bash
   python scripts/check_bot_token.py
   ```
5. With the bot token saved, `scripts/channel_admin.py` can resolve / create / rename /
   set-topic / archive channels:
   ```bash
   python scripts/channel_admin.py --help
   ```
   Use `scripts/preflight.py` before a big send to validate a config and heal channel
   membership (invite the bot / personas where needed).

> ⚠ **Enterprise Grid quirks** (if your demo org is Grid): channel `list`/
> `create` calls need a `team_id` (auto-discovered by `scripts/channel_admin.py`);
> archiving or inviting requires the bot to be a *member* of the channel even
> when it's public; and the bot can only *see* public channels — a private
> channel it hasn't been invited to reads as "not found," which is not the
> same as missing. Don't create a duplicate.

---

## Step 10 (optional) — App-style notifications

Post cards that look like they came from a third-party app — PagerDuty,
Salesforce, Jira, Docusign, etc. These go out via the **bot token** using
`chat:write.customize` (custom username + icon), so they carry the app's name
and an `APP` badge. (They are *not* recorded in `sent.json`; delete them
manually with `chat.delete` if needed.)

**No GitHub account is required.** Both ingredients already ship in this repo,
so a fresh clone can post cards out of the box:

- `blockkit/<app>.json` — the card layout(s) for each app (Block Kit). Read
  straight from the local folder; nothing to fetch.
- `logos/<app>.png` — the app icons, bundled here too.

Post a card:

```bash
python scripts/send_app_notification.py --app pagerduty --example <example_name> --channel <C...>
```

(`scripts/send_app_notification.py --help` lists the apps and examples.) The card text
can be grounded in real data — see Step 11.

### About the app logo (the avatar)

The one thing Slack won't accept from a local file is the **custom icon**: an
`icon_url` must be a **publicly reachable URL**, not a file on disk. You have
three choices, easiest first:

1. **Use an emoji avatar (zero setup).** Pass `--icon-emoji :rotating_light:`
   (or let the per-app default apply). The card posts fine — it just shows an
   emoji instead of the real logo. Good enough for most demos.
2. **Point at an already-public logo URL (no account, no PAT).** If the logos
   are hosted somewhere public — including this repo's own `logos/` folder once
   it's on GitHub — set `DEMO_LOGO_BASE` to that raw base and the helper builds
   `icon_url = <base>/<app>.png` for you:
   ```bash
   export DEMO_LOGO_BASE="https://raw.githubusercontent.com/<owner>/<repo>/<branch>/logos"
   ```
3. **Host your own logos (needs a GitHub account + PAT).** Only if you want to
   add or customize logos: set `DEMO_ASSETS_REPO="<your-username>/<your-repo>"`
   and publish with `scripts/push_logos.py` / `scripts/push_blockkit.py` (these upload via the
   GitHub Contents API). Provide the token via the `GHT` env var or the macOS
   Keychain — **never paste it into chat.**

Icon precedence in the helper: `--icon-url` → `--icon-emoji` →
`DEMO_LOGO_BASE`/`<app>.png` → per-app emoji fallback. So if you set nothing,
you still get a recognizable emoji avatar.

---

## Step 11 (optional) — Ground content in real data (MCP or CLI)

The most convincing demos reference data that actually exists, so names,
amounts, stages, and dates all line up. There are **two ways** the toolkit
reaches that data — you'll use both, for different jobs:

**A. Live, interactive reads — via an MCP server.** When you ask Claude Code in
plain English — e.g. *"pull the open renewal opportunity for <account> and write
a thread about it in that account's channel"* — Claude queries the connected
**MCP server**, then uses the persona / app-notification scripts above to post
the result. MCP servers are configured in **Claude Code itself** (not in this
repo).

- **Salesforce** — read an opportunity's name, amount, stage, close date, then
  seed a matching deal-team thread.
- **Jira / Atlassian, ServiceNow, or any other MCP server** — reference a real
  ticket or record so a notification card links to something that exists.

**B. Scripted reads/writes — via a vendor CLI.** The repo's own automation talks
to Salesforce through the **`sf` CLI**, not MCP. For example
`scripts/update_opportunities.py` shells out to it:

```python
subprocess.run([sf_bin(), "data", "query", "-o", SF_ORG, "--query", soql, "--json"])
```

So anything a *committed script* reads or writes in Salesforce uses the CLI
(install it separately; on macOS it's `brew install --cask sf`, and it must be
on your `PATH`). The live/interactive path (A) uses MCP.

> ℹ Either way, the point is the same: the Slack story and the CRM/ticketing
> data tell the *same* story because one was generated from the other.
> **Rule of thumb:** *you asking Claude* → MCP; *a script running on its own* →
> the vendor CLI.

---

## Token rotation

If you need to rotate (e.g., a token leaked):

| Token | How to rotate |
|---|---|
| `client_secret` | Slack app → Basic Information → Regenerate. Update `tokens.json`. |
| Bot `xoxb-` | Reinstall app → copy new token → `python scripts/save_bot_token.py` → `python scripts/check_bot_token.py`. |
| Persona `xoxp-` | Re-run `python -u scripts/auth_user.py --email persona@yourorg.com`. |
| GitHub PAT (logos) | Regenerate in GitHub → update `GHT` env var / Keychain entry. |

Reinstalling the app does **not** invalidate existing user (`xoxp-`) tokens.

> ⚠ Never paste rotated tokens into a chat with Claude Code. Always use
> the local scripts / environment.

---

## File reference

**Core setup & auth**

| File | Purpose |
|---|---|
| `scripts/auth_user.py` | OAuth flow — captures one persona's `xoxp-` per run (scopes = `USER_SCOPES`) |
| `scripts/save_bot_token.py` | Hidden paste path for the bot `xoxb-` token |
| `scripts/check_bot_token.py` | Confirms the bot token installed to the right workspace/org |
| `scripts/verify_setup.py` | Diagnostic — confirms `tokens.json` is wired up correctly |
| `scripts/config.py` | Shared helpers: `user_client(email)`, bot client, `audit_log()` |
| `scripts/preflight.py` | Validate a send config + heal channel membership before sending |
| `tokens.example.json` | Template — copy to `tokens.json` and fill in |
| `tokens.json` | Your real tokens (gitignored, never committed) |

**Posting content**

| File | Purpose |
|---|---|
| `scripts/send_dms_as_users.py` | Send a list of messages/DMs from different personas |
| `scripts/send_thread.py` | Post a parent message + threaded replies as personas |
| `scripts/delete_dms.py` | Delete previously-sent persona messages (from the manifest) |
| `scripts/channel_admin.py` | Resolve / create / rename / set-topic / archive channels (bot token) |
| `scripts/archive_channel.py` | Convenience wrapper to archive a channel |
| `scripts/send_app_notification.py` | Post an app-style Block Kit card as a third-party app (bot token) |
| `blockkit/*.json` | Block Kit card layouts, one file per app |
| `logos/*.png` | App icons for the cards |
| `scripts/push_logos.py`, `scripts/push_blockkit.py` | Publish logos/templates to the public assets repo |
| `scripts/update_opportunities.py` | Example: read/update Salesforce opps via the `sf` CLI (scripted data path) |

> The various `seed_*.py`, `case_channels.py`, `*_thread.py`, and `*.json`
> content files in the repo root are **example demo scenarios**, not part of
> the toolkit — read them as recipes for building your own.

---

## Troubleshooting

**`scripts/auth_user.py` exits with "Missing or unset oauth.client_id"** — You
haven't filled in `tokens.json`. See Step 5.

**Browser shows "Your connection is not private"** — Expected. The toolkit
uses a self-signed cert for the OAuth callback. Click **advanced → proceed**.

**`scripts/auth_user.py` says "VERIFICATION FAILED — token NOT saved"** — You
authorized in a browser logged in as the wrong user. Re-run in incognito as
the target persona.

**`scripts/auth_user.py` blocks before printing the URL** — You forgot the `-u`
flag. Hit `Ctrl+C` and re-run as `python -u scripts/auth_user.py ...`.

**`missing_scope needed=files:write:user`** (or another `:user` scope) — The
persona's token was captured before that scope existed in `USER_SCOPES`. Add
the scope in the Slack app, then re-run `scripts/auth_user.py` for that persona.

**`chat.delete` returns `cant_delete_message`** — User tokens can only
delete their own messages. Make sure the `sender_email` in the manifest
matches the user that originally sent the message.

**`chat.postMessage` / `conversations.archive` returns `not_in_channel`** —
The bot isn't a member of that channel. It self-joins public channels via
`channels:join`; for a private channel, `/invite` the bot manually first.

**Bot channel calls return `missing_argument` (Enterprise Grid)** — Grid
requires a `team_id` on `conversations.list`/`create`. Use `scripts/channel_admin.py`,
which auto-discovers it.

**`scripts/check_bot_token.py` / bot calls return `team_access_not_granted`** — A
reinstall landed the bot token in the wrong Grid org. Reinstall to the correct
org and re-save the token.

**A private channel reads as "not found"** — The bot only sees public channels
plus private ones it's been invited to. "Not found" ≠ "doesn't exist." Don't
create a duplicate; invite the bot instead.

**`'source' is not recognized as an internal or external command`** — You're
on Windows. Use `.venv\Scripts\Activate.ps1` instead of
`source .venv/bin/activate`. See [Windows commands](#windows-commands) below.

**`.venv\Scripts\Activate.ps1 cannot be loaded because running scripts is
disabled on this system`** — PowerShell's default execution policy blocks
the activation script. Run this once, then retry:
```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

**`'python' is not recognized`** (Windows) — Python wasn't added to PATH
during install. Easiest fix: reinstall from python.org and check **"Add
python.exe to PATH"** on the first screen. Or use the Python launcher:
replace `python` with `py` and `python3.12` with `py -3.12`.

---

## How it fits together

The whole system is three parts, in one direction:

```
YOU  →  Claude Code (in your terminal)  →  the toolkit folder  →  Slack (+ optional data sources)
```

1. **You** type a plain-English request.
2. **Claude Code** is the brain and the hands — it decides what to do, writes
   and runs the small Python scripts in this folder, reads results, and fixes
   things when a call fails.
3. **The toolkit folder** (this repo) holds the scripts, your keys
   (`tokens.json`), and the Block Kit templates. The scripts just translate a
   request into API calls.
4. Those calls go out two ways:
   - **Direct API calls** (using your saved keys) to **Slack** — messages,
     files, channel admin, app-notification cards — and to **GitHub**, which
     hosts the logos + templates.
   - **To data sources** — **Salesforce, Jira, ServiceNow,** etc. — to read
     real data so the content stays authentic. Two ways: an **MCP server** for
     live/interactive reads (you asking Claude), or a **vendor CLI** like `sf`
     for what the committed scripts do on their own.

That's why this runs in a **terminal / Claude Code**, not the Claude desktop
app: it needs to run local scripts and hold local files (your tokens, the
`.venv`). The desktop app can talk to MCP servers but can't run this folder's
code or reach your local keys.

---

## Windows commands

Windows users: Steps 1–3 are in the Slack web UI and work as written.
Everything from Step 4 onward runs in **PowerShell** (search "PowerShell" in
the Start menu). Only the commands in this table differ from the main flow
above — anything that starts with `python` (e.g.,
`python -u scripts/auth_user.py ...`, `python scripts/verify_setup.py`,
`python scripts/send_dms_as_users.py ...`) runs identically.

| Step | Mac/Linux (main flow) | Windows (PowerShell) |
|---|---|---|
| 4 — create venv | `python3.12 -m venv .venv` | `py -3.12 -m venv .venv` |
| 4 — activate venv | `source .venv/bin/activate` | `.venv\Scripts\Activate.ps1` |
| 5 — copy tokens file | `cp tokens.example.json tokens.json` | `Copy-Item tokens.example.json tokens.json` |
| 8 — copy example config | `cp examples/send_messages.example.json my_demo.json` | `Copy-Item examples\send_messages.example.json my_demo.json` |

**First-time PowerShell note:** If activating the venv fails with
"running scripts is disabled on this system," run
`Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once and retry. This
is a one-time per-user setting.

**Incognito windows on Windows:** For the OAuth step, open a private
browsing window — **Ctrl+Shift+N** in Chrome/Edge, **Ctrl+Shift+P** in
Firefox. (On Mac, it's `Cmd` instead of `Ctrl`.)
