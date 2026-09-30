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
- **(Optional) MCP servers** — only if you want to ground content in real data
  (Salesforce, Jira/Atlassian, ServiceNow, …). Configured in Claude Code, not
  here. See [Side Quest 2](#side-quest-2-connect-salesforce--other-tools).

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
> the persona who authorizes it is an org admin or owner, and because demo
> orgs are Enterprise+ organizations, an org admin may need to approve the app
> before it installs. `auth_user.py`
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

## Step 6 — Capture user tokens (~5 users recommended)

> ## ⭐ I recommend repeating this for at least ~5 users
>
> Every user you capture here is someone Claude can post as. Demo
> conversations usually need several people, so I recommend capturing
> **at least ~5 users** before moving on. You'll decide who they are (names, titles, roles) later, demo
> by demo. Right now you just need the tokens.

**[Terminal]** — **open a new Terminal window**, separate from the one where
you're talking to Claude. The script prints a link and then waits for you to
approve it in your browser, so it needs its own window that stays open.

Repeat these three steps for each user:

**1. First, sign in as that user.** Open an **incognito** browser window, go
to **DemoZone**, and sign in to your demo org as one of its fictitious users.
Stay signed in. When you approve the link in step 3, Slack gives the token to
whoever is signed in, so this makes sure it belongs to that user and not to
you.

Demo org users have email addresses in this format:

```
demoeng+jennifer_hynes_12345@slack-corp.com
```

**2. Run the script with that user's email:**

```bash
python -u scripts/auth_user.py --email demoeng+jennifer_hynes_12345@slack-corp.com
```

> ⚠ Use `python -u` (unbuffered) so the link prints **before** the script
> starts waiting.

**3. Paste the link into the same incognito window** where you're signed in as
that user, then click **Allow**.

> ⚠ **Critical:** do NOT approve it in your normal browser if you're signed in
> there as someone else (e.g., your own admin account). Slack will silently
> give *your* token instead of the demo user's.

> ℹ The script also tries to open your default browser as a convenience —
> ignore that tab if it goes to the wrong account.

> ℹ Your browser will warn about the self-signed cert. Click
> **advanced → proceed** to continue.

After you click Allow, the script checks that the token belongs to the email
you entered and **refuses to save it if they don't match**. If that happens,
retry in incognito. Each token is saved under `users` in `tokens.json`, keyed
by email.

> ℹ You can rename users or change their titles anytime later. Just ask
> Claude. Their tokens keep working.

> ℹ **What a user can do depends on the scopes their token was captured with.**
> A token captured with only `chat:write` can post messages but *not* upload
> a file — you'll get `missing_scope needed=files:write:user`. Re-run
> `scripts/auth_user.py` for that user after widening `USER_SCOPES`.

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

## Step 8 — Post your first message

Test it out by asking Claude to send a message as one of the users you
captured. In your Claude window, say something like:

> "Send a message as Jennifer Hynes in #general introducing herself and tagging
> Amy Weaver asking for an update on the Welo Guard implementation."

Just use people's names. Claude figures out which user is which from their
email addresses, and can @-mention anyone in the org.

Claude sends it as that user, so it shows up in Slack with their name and
photo. Check Slack to confirm it arrived.

From here you can ask for anything: channel messages, threads with replies from
several users, back-and-forth DMs. See [USING_CLAUDE.md](USING_CLAUDE.md) for
more examples.

> ℹ **Cleaning up is easy.** Claude keeps a list of everything it sends. When
> you're done, say *"delete everything we posted"* and it removes it all.

---

## ✅ Checkpoint: the core setup is done

Nice work. Take a quick pause here. Right now you can:

- ✅ **Send messages, threads, and DMs as your demo users**

You **can't** yet:

- ❌ Create or manage channels (add users, set topics, rename, archive)
- ❌ Post app notifications (PagerDuty, Jira, Salesforce cards, etc.)
- ❌ Pull from or update third-party tools like Salesforce

The two side quests below unlock those. Do them now or come back later when a
demo needs them.

---

## Side Quest 1: Channel Management & App Notifications

### Save the bot token

> ⚠️ **Super important:** the bot token is what lets Claude **build out your demo org**, not just post
> a few messages. With it, the app can:
>
> - **create new channels** and rename or archive old ones,
> - **add users into channels**,
> - **set channel topics**,
> - **post app notifications** (below),
> - and double-check that each user token belongs to the right person.
>
> Without it, you're limited to posting messages in channels that already
> exist. For bigger demo builds across many channels and users, you need this.

Installing the app in Step 2 created the bot token, but the toolkit doesn't
have a copy of it yet. (Your user tokens were saved automatically when you
clicked Allow. The bot token has to be copied over once by hand.)

1. In your app's settings, go to **Install App** and copy the **Bot User OAuth
   Token** (starts with `xoxb-`).
2. **[Terminal]** In your separate Terminal window (not the Claude one), run:
   ```bash
   python scripts/save_bot_token.py
   ```
   Paste the token and press Enter. **Nothing will appear on screen as you
   paste. That's intentional, to keep it hidden.** Then type `y` to confirm.

That's it. Now you can just ask Claude, for example:

> "Create a private channel called #welo-guard-implementation and add
> Jennifer Hynes and Amy Weaver."

> ℹ **Private channels:** the app can only see private channels it's been
> added to. If Claude says it can't find one, type `/invite @Demo Content
> Helper` (or whatever you named the app) in that channel.

### Post app notifications

An **app notification** is a message that looks like it came from another app
connected to Slack, like a PagerDuty incident alert, a Jira ticket update, or a
Salesforce "deal won" message. It shows the app's name, logo, and an `APP` badge,
just like the real thing.

Just ask Claude in plain English:

> "Post a PagerDuty incident alert in #critical-incidents about the checkout
> service being down."

Claude uses the app notification layouts and logos that come with this repo.
Nothing else to set up.

**Apps included:** PagerDuty, Datadog, Jira, Salesforce (deal won, new
opportunity, stage changed), ServiceNow, GitHub, Azure Pipelines, DocuSign,
Google Calendar, Zoom, Workday, Outreach, Polly, and more. Ask Claude *"which
app notifications can you post?"* for the full list.

#### 💬 Missing an app? Reach out to Alex Lee

> **I maintain the app notification layouts (Block Kit) and logos in this
> repo, and I'm happy to add more.**
>
> - Need an app that isn't on the list?
> - A layout doesn't look right or isn't working?
> - Want a different kind of notification from an app that's already here?
>
> **Reach out to Alex Lee** and I'll update the repo so it works for your
> demos. Everyone using the toolkit gets the update.

> ℹ App notifications aren't on the cleanup list from Step 8. To remove one,
> ask Claude to delete it.

---

## Side Quest 2: Connect Salesforce & other tools

Connecting Salesforce and Jira lets Claude **read and update real data** in
those tools, not just post in Slack. That makes demos much more convincing:

- **Salesforce changes trigger real workflow notifications.** If your demo org
  has Salesforce-to-Slack workflows set up, Claude can update Salesforce and
  let the workflow do the rest. For example:
  - *Create a case for Omega, Inc.* → a **"Critical Case"** workflow
    notification appears in the Omega account channel.
  - *Create a new opportunity* → a **new opportunity** notification fires.
  - *Push out close dates* → date-change notifications, and a pipeline that
    always looks current.
- **App notifications can link to real Jira tickets.** Claude creates a real
  ticket in Jira, then posts the Jira app notification linked to it. Anyone
  watching the demo can click through to a ticket that actually exists.

### Connect Salesforce

This takes two pieces. The **Salesforce CLI** lets the toolkit's scripts (and
scheduled refreshes) update Salesforce. The **Salesforce MCP server** lets
Claude work with Salesforce when you ask in plain English. The MCP server uses
the CLI's login, so you only sign in once.

1. **Install the CLI.** Ask Claude: *"Install the Salesforce CLI for me."*
2. **[Terminal] Sign in to your demo Salesforce org.** In your separate
   Terminal window, run:
   ```bash
   sf org login web --alias demo --set-default
   ```
   A browser opens. Sign in to your demo Salesforce org.
3. **Add the MCP server.** Ask Claude: *"Connect the Salesforce MCP server to
   my default org."* (Under the hood it runs
   `claude mcp add salesforce -- npx -y @salesforce/mcp --orgs DEFAULT_TARGET_ORG --toolsets all`.)
4. **Restart Claude** (type `/exit`, then `claude` again), then type `/mcp` to
   check that `salesforce` shows as connected.

### Connect Jira (Atlassian)

1. Ask Claude: *"Connect the Atlassian MCP server."* (It runs
   `claude mcp add --transport http atlassian https://mcp.atlassian.com/v1/mcp`.)
2. Restart Claude, type `/mcp`, choose **atlassian**, and sign in to your
   Atlassian site in the browser.

### Other tools

Many tools (ServiceNow, Google Drive, and more) have MCP servers. Ask Claude
*"help me connect the <tool> MCP server"* and it will find the setup steps, or
check that tool's documentation.

### Try it

> "Create a high-priority case in Salesforce for Omega, Inc. about their
> integration being down."

> "Create a Jira ticket for the Welo Guard onboarding bug, then post a Jira app
> notification about it in #welo-guard-implementation linked to the real
> ticket."

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

**Bot channel calls return `missing_argument`** — Enterprise+ orgs require a `team_id` on `conversations.list`/`create`. Use `scripts/channel_admin.py`,
which auto-discovers it.

**`scripts/check_bot_token.py` / bot calls return `team_access_not_granted`** — A
reinstall landed the bot token in the wrong Enterprise+ org. Reinstall to the correct
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
