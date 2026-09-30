---
name: demo-refresh
description: One-shot reset of a Slack + Salesforce demo environment — delete stale messages, send fresh DMs and channel messages (including an app-style incident card), refresh Salesforce opportunity close dates, and keep a key renewal opportunity open. EXAMPLE TEMPLATE — copy to ~/.claude/skills/ and fill in your own org's specifics.
triggers:
  - "refresh the demo"
  - "reset the demo"
  - "demo refresh"
  - "set up for demo"
  - "prepare for demo"
---

# Demo Refresh Skill (example template)

> **This is a sanitized example.** It shows the *shape* of a scheduled/one-shot
> demo-refresh skill built on this toolkit. Everything in `ALL_CAPS` or angle
> brackets (`<...>`) is a placeholder you replace with your own org's values:
> channel IDs (`C0XXXXXXXXX`), account/opportunity IDs (`001XXXXXXXXXXXXXXX`,
> `006XXXXXXXXXXXXXXX`), persona emails, account names, and your Salesforce org
> alias (referenced here as the `SF_ORG` env var). To use it, copy this folder
> to `~/.claude/skills/demo-refresh/` and edit it for your demo story.

Resets the full demo environment in one shot. A typical flow:

1. **Delete** any previously sent Slack messages (from `sent.json`).
1b. **Preflight** — validate channel ids are live and heal sender membership (needs bot token).
2. **Send** fresh DMs and channel messages (from `my_demo.json`), e.g. a P0 incident
   post in `#critical-incidents` from an on-call persona.
3. **Send** any threaded conversations (`*_thread.json`) into the relevant account channels.
4. **Refresh** Salesforce opportunity close dates (`scripts/update_opportunities.py`).
5. **Create / update** any Salesforce records the story needs (new opportunity, a
   support case), and keep a key renewal opportunity open (not Closed Won).

Adjust the steps to your own narrative — this is a recipe, not a fixed script.

## Message formatting conventions

Apply these when authoring any Slack message config (`my_demo.json`,
`*_thread.json`, ad-hoc threads) so the demo reads consistently.

- **Thread-opener messages must start with 🧵.** Any message that announces a
  thread is about to happen — e.g. "starting a thread here for our call with
  the customer" — must begin with the 🧵 emoji. It's a visual cue that a thread
  is coming and makes the parent message scannable. Put it at the very start of
  the `text`:

  ```json
  { "sender_email": "persona@yourorg.com", "text": "🧵 starting a thread here for our call — dropping context below" }
  ```

  This applies to the **parent** message of a thread, not the replies.

### Sender identity — who sends what

- **Anything from a person must be sent as that persona**, using the persona's
  own `xoxp-` token (the `sender_email` path in `scripts/send_dms_as_users.py` /
  `scripts/send_thread.py`). These render as genuine user messages with the person's
  real name and avatar and **no APP badge** — this is what keeps the demo
  believable. Never fake a human message through the bot.
- **`chat:write.customize` (bot token only) is reserved for app / system
  notifications** — a named bot such as a deploy notifier, incident bot, or
  integration alert. It posts under a custom `username` + icon but still carries
  an **APP** badge and is owned by the bot user, so never use it to impersonate
  a person.

## Prerequisites

- Tokens set up (`tokens.json` present and passing `scripts/verify_setup.py`).
- If your refresh touches Salesforce: the `sf` CLI authenticated to your org,
  and its dependencies on `PATH` (see the PATH callout in Execution).
- `.venv` present in the project root. Install packages with
  `.venv/bin/python -m pip install <pkg>`.
- For channel archiving / management steps: a bot token in `tokens.json`
  (`app_token`) with `channels:read`, `groups:read`, `channels:manage`,
  `groups:write`, `channels:join`. Verify with `.venv/bin/python scripts/check_bot_token.py`.

## Demo org reference

Record the facts about *your* live org that aren't obvious from the scripts, so
the skill (and ad-hoc prep) can run confidently. Fill these in for your org:

**Salesforce anchors:** set the `SF_ORG` env var to your org alias/username
(e.g. `export SF_ORG=you@example.com`); key account id `001XXXXXXXXXXXXXXX`;
key renewal opportunity id `006XXXXXXXXXXXXXXX`. The `sf` CLI emits ANSI color
codes even with `--json`, so any script that parses `sf` output must set
`NO_COLOR=1` and strip `\x1b\[[0-9;]*m` before `json.loads`.
`scripts/update_opportunities.py` already does this.

**Slack org type.** Demo orgs are **Enterprise+ organizations** (formerly
Enterprise Grid): workspaces nested under an enterprise `E...` id. Keep these
gotchas in mind:
- `conversations.list`/`create`/`archive` require an explicit **`team_id`**, and
  it must be the **workspace** id (`T...`), never the enterprise id (`E...`).
  `scripts/channel_admin.py` discovers the right `T...` automatically.
- If your enterprise has **multiple workspaces**, `scripts/channel_admin.py create`
  picks the first `T...` from the bot's `auth.teams.list` — which may not be the
  one you want. To force a channel into a specific workspace, call
  `conversations_create(name=..., team_id="T...")` with the bot token directly,
  then invite. When posting to an *existing* channel, resolve/use its channel ID
  directly (persona `chat:write` works without `channels:read`).
- Archive/invite need the bot to be a **member**; it self-joins **public**
  channels but must be `/invite`d into **private** ones. Private channels the
  bot isn't in are invisible to it.

**Personas.** List the personas you've captured tokens for (keyed by email in
`tokens.json`), e.g. `ae@yourorg.com`, `csm@yourorg.com`,
`customer@example.com`. Note which scope tier each holds — a token captured with
only `chat:write` can post messages but can't upload files or add reactions.
Adding a scope means editing `USER_SCOPES` in `scripts/auth_user.py` **and** re-authing
each persona; already-issued tokens never gain scopes. Note too which personas
belong to which workspace — a persona not in the target
workspace can't be invited there (`org_user_not_in_team`).

## Fictitious third-party app notifications (Block Kit)

Post notifications that look like they came from a third-party app — Datadog,
PagerDuty, GitHub, Salesforce, ServiceNow, etc. — using the bot's
`chat:write.customize` scope to set a per-message `username` + icon so the
message renders **as that app**, with a Block Kit card body. Great for making
channels feel alive (incident alerts in `#critical-incidents`, deploy/PR
notifications in dev channels, deal alerts in account channels).

> **Sender-identity policy applies:** app/system notifications only. Human
> messages always go through a persona's `xoxp-` token.

**Easiest path — the `scripts/send_app_notification.py` helper.** It fetches the app's
card from the library (or a local `blockkit/` copy), sets `username` to the
app's name and a sensible icon, and posts via the bot token. The bot must be a
member of the target channel (self-joins public; `/invite` into private).

```bash
cd <path-to-toolkit>

# See everything available
.venv/bin/python scripts/send_app_notification.py --list

# Preview before sending (prints the exact payload)
.venv/bin/python scripts/send_app_notification.py --app pagerduty --example incident_triggered \
  --channel C0XXXXXXXXX --icon-emoji :rotating_light: --dry-run

# Send it
.venv/bin/python scripts/send_app_notification.py --app pagerduty --example incident_triggered \
  --channel "#critical-incidents" --icon-emoji :rotating_light:
```

App logos need a **publicly reachable image URL**, so they're hosted in a public
GitHub repo you own and served via `raw.githubusercontent.com`. Set
`DEMO_ASSETS_REPO` to your repo (`owner/repo`) and publish assets with
`scripts/push_logos.py` / `scripts/push_blockkit.py`. Logo filenames must match the block-kit
file key (`datadog.png`, `pagerduty.png`, …); square PNG ≥192×192.

Note: bot posts are **not** written to `sent.json`, so Step 1 won't auto-clean
them. Delete them manually with `chat.delete` if a refresh needs a clean slate.

## Execution

Run each step with the Bash tool. Always use `.venv/bin/python` — never `python`
or `python3` directly (the venv doesn't persist between shell calls in Claude
Code).

> **⚠️ Steps that run `sf`** — directly or via a script that shells out to it
> (e.g. `scripts/update_opportunities.py`) — may need the `sf` CLI's dependencies on
> `PATH`. On macOS with Homebrew that's `export PATH="/opt/homebrew/bin:$PATH"`
> so `sf` can find `node`; without it `sf` fails with `env: node: not found` and
> any script parsing its output crashes on `json.loads`. Prepend the export in
> those steps.

---

### STEP 1 — Delete previous Slack messages

Check if `sent.json` exists first; skip gracefully if not.

```bash
cd <path-to-toolkit>
if [ -f sent.json ]; then
  .venv/bin/python scripts/delete_dms.py --manifest sent.json && rm -f sent.json
else
  echo "[skip] No sent.json found — nothing to delete"
fi
```

---

### STEP 1b — Preflight: validate channels & heal membership

Verifies every channel referenced in the configs is live and that each sender
persona is a member (the bot auto-joins public channels and invites personas).
Prevents the two most common send failures: a stale `channel_id`
(`channel_not_found`) and a sender who isn't in the channel (`not_in_channel`).
If no bot token is set, preflight prints a notice and exits 0.

```bash
cd <path-to-toolkit>
.venv/bin/python scripts/preflight.py
```

If preflight reports `[STALE] <id>`, resolve the correct id by name and fix the
config before sending:

```bash
.venv/bin/python scripts/channel_admin.py resolve --name "<channel-name>"
```

---

### STEP 2 — Send fresh Slack messages

```bash
cd <path-to-toolkit>
.venv/bin/python scripts/send_dms_as_users.py --config my_demo.json --manifest sent.json
```

Expected: one `[sent]` line per message in `my_demo.json`.

---

### STEP 3 — Send threaded conversations

Send any threaded conversations into their account channels. Each appends to
`sent.json` so Step 1 cleans it up on the next refresh.

```bash
cd <path-to-toolkit>
.venv/bin/python scripts/send_thread.py --config <account>_thread.json --manifest sent.json
```

---

### STEP 4 — Refresh Salesforce opportunity close dates

Spreads open opportunities' close dates forward so the pipeline always looks
current. `scripts/update_opportunities.py` reads `SF_ORG` (or `--org`) and takes
`--start-days` / `--window-days`; an optional `priority_opps.json` (gitignored)
pins exact dates for specific opp ids.

```bash
cd <path-to-toolkit>
export PATH="/opt/homebrew/bin:$PATH"
export SF_ORG="you@example.com"
.venv/bin/python scripts/update_opportunities.py
```

> Runtime note: this iterates over all open opportunities one `sf` call at a
> time (~2–4s each), so it can run for several minutes and exceed the 120s Bash
> timeout — let it finish rather than assuming it hung.

---

### STEP 5 — Create / update Salesforce records for the story

Create or update whatever records the narrative needs. Examples (replace ids and
field values with your own):

```bash
export PATH="/opt/homebrew/bin:$PATH"

# Create a new opportunity for a key account
sf data create record -o "$SF_ORG" -s Opportunity \
  -v "Name='<Account> - Platform Expansion' AccountId=001XXXXXXXXXXXXXXX StageName=Prospecting CloseDate=2026-12-31 Amount=180000" \
  --json

# Keep a key renewal OPEN (in Negotiation), close date = upcoming Friday.
# Never move this to Closed Won if the demo needs an in-flight renewal.
sf data update record -o "$SF_ORG" -s Opportunity \
  --record-id 006XXXXXXXXXXXXXXX \
  --values "StageName='Negotiation' CloseDate=$(date -v+Fri +%Y-%m-%d)" \
  --json
```

> `date -v+Fri +%Y-%m-%d` (macOS) resolves to the next Friday (today if Friday).

---

## Error handling

- **Step 1 failures**: warn and continue — stale messages aren't fatal.
- **Step 1b (preflight) failures**: if it reports `[STALE]`, stop and fix the
  `channel_id` before sending. Membership `[warn]`s for private channels mean
  the bot needs a manual `/invite`.
- **Step 2/3 failures**: stop and report — the demo content won't look right.
- **Step 4/5 failures**: report the specific record that failed with the error
  JSON; the `sf` CLI returns `"status": 1` with a `message` field on failure.

## Full reset (re-run)

To run the refresh again, re-execute all steps top to bottom. Step 1 deletes
whatever Step 2/3 wrote last time, keeping the inbox clean.

## Channel admin toolbox (`scripts/channel_admin.py`)

Unlocked by the bot token's channel scopes. Enterprise+-aware (team_id auto-discovered)
and idempotent where it makes sense.

```bash
# Resolve a channel name -> id
.venv/bin/python scripts/channel_admin.py resolve --name "<channel-name>"

# Resolve ANY org user (email, display/real name, or id) -> user id
.venv/bin/python scripts/channel_admin.py whois --who "Firstname Lastname"

# Ensure users are members (bot joins public channels, then invites)
.venv/bin/python scripts/channel_admin.py ensure --channel "<channel-name>" \
  --members "Firstname Lastname,persona@yourorg.com"

# Create a channel (optionally private, optionally pre-invite anyone)
.venv/bin/python scripts/channel_admin.py create --name "<new-channel>" --invite "persona@yourorg.com"

# Rename / set topic
.venv/bin/python scripts/channel_admin.py rename --channel C0XXXXXXXXX --to "<new-name>"
.venv/bin/python scripts/channel_admin.py topic  --channel "<channel-name>" --text "<topic>"

# Archive by id or by name-match
.venv/bin/python scripts/channel_admin.py archive --channel C0XXXXXXXXX
.venv/bin/python scripts/channel_admin.py archive --match "<name substring>" --allow-empty
```
