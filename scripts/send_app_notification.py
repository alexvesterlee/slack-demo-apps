#!/usr/bin/env python
"""Post a fictitious third-party *app notification* into a Slack channel.

Uses the bot token's `chat:write.customize` scope to post a Block Kit card under
a custom `username` + icon, so the message renders as if it came from the named
app (Datadog, PagerDuty, GitHub, Salesforce, ...). The Block Kit card structures
come from the bob-the-builder library:
  https://github.com/evanbrosen/bob-the-builder/tree/main/blockkit

Each `blockkit/<app>.json` file has: {app, fake_bot_id, notes, examples:[{name, when, blocks}]}.
This script pulls one example's `blocks` array and posts it via chat.postMessage.

IMPORTANT (sender-identity policy): this is for APP / SYSTEM notifications only.
Anything that should come from a *person* must be sent as that persona via their
own xoxp token (send_dms_as_users.py / send_thread.py), never faked through the bot.

Examples:
  # List the apps/examples available in the library
  .venv/bin/python send_app_notification.py --list

  # Post Datadog's "monitor_triggered" card into a channel (dry-run first)
  .venv/bin/python send_app_notification.py --app datadog --example monitor_triggered \\
      --channel C0123456789 --icon-emoji :dog: --dry-run

  # Actually send it (pass a channel id C... or a #channel-name)
  .venv/bin/python send_app_notification.py --app datadog --example monitor_triggered \\
      --channel "#critical-incidents" --icon-emoji :dog:
"""
import argparse
import json
import os
import re
import sys
import urllib.request

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

# YOUR public assets repo ("owner/repo"), where logos + blockkit templates live.
# Slack needs a public image URL for a custom app icon, so these are served over
# raw.githubusercontent. Set DEMO_ASSETS_REPO to your own repo (it defaults to a
# placeholder). push_logos.py / push_blockkit.py publish into the same repo.
_ASSETS_REPO = os.environ.get("DEMO_ASSETS_REPO", "your-github-username/slack-demo-apps")
_ASSETS_BRANCH = os.environ.get("DEMO_ASSETS_BRANCH", "main")
_ASSETS_RAW = f"https://raw.githubusercontent.com/{_ASSETS_REPO}/{_ASSETS_BRANCH}"

# Where to fetch a blockkit/<key>.json when it isn't present locally, so a fresh
# clone with no local blockkit/ dir still works. Override via DEMO_BLOCKKIT_BASE.
RAW_BASE = os.environ.get("DEMO_BLOCKKIT_BASE", f"{_ASSETS_RAW}/blockkit").rstrip("/")
# Repo root is one level up from this file (scripts/); blockkit/ lives there.
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOCAL_DIR = os.path.join(_REPO_ROOT, "blockkit")

# Base URL of the hosted logo folder. Each app posts with
#   icon_url = f"{LOGO_BASE}/<key>.png"
# so notifications render with the real app logo (only if that <key>.png actually
# exists in the repo — Slack silently falls back if the URL 404s). Override via
# env DEMO_LOGO_BASE or --logo-base.
LOGO_BASE = os.environ.get("DEMO_LOGO_BASE", f"{_ASSETS_RAW}/logos").rstrip("/")

# Sensible default icon_emoji per app when no --icon-url/--icon-emoji is given.
# Override with a real logo via --icon-url for the most convincing impersonation.
DEFAULT_EMOJI = {
    "azure pipelines": ":azure:",
    "crm analytics": ":bar_chart:",
    "datadog": ":dog:",
    "deploy wizard": ":rocket:",
    "docusign": ":pencil:",
    "github": ":github:",
    "google calendar": ":calendar:",
    "jira cloud": ":jira:",
    "outreach": ":round_pushpin:",
    "pagerduty": ":rotating_light:",
    "polly": ":ballot_box_with_ballot:",
    "salesforce": ":salesforce:",
    "service cloud for slack": ":cloud:",
    "servicenow": ":gear:",
    "workday": ":briefcase:",
}


def load_app(app: str) -> dict:
    """Load a blockkit/<app>.json — prefer a local copy, else fetch from GitHub."""
    key = app.lower().replace(" ", "_").removesuffix(".json")
    local = os.path.join(LOCAL_DIR, f"{key}.json")
    if os.path.exists(local):
        with open(local) as f:
            return json.load(f)
    url = f"{RAW_BASE}/{key}.json"
    try:
        with urllib.request.urlopen(url, timeout=15) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        sys.exit(f"[error] could not load block kit for {app!r} "
                 f"(tried {local} and {url}): {e}")


def fallback_text(blocks: list) -> str:
    """Notification/preview text (blocks alone show blank in notifications)."""
    for b in blocks:
        if b.get("type") == "header":
            return b["text"]["text"]
    for b in blocks:
        if b.get("type") == "section" and isinstance(b.get("text"), dict):
            return b["text"]["text"][:150]
    return "App notification"


def inject_ticket_url(blocks: list, url: str) -> list:
    """Point the card's title link at a REAL Jira issue URL.

    The first `section` block is the card title, rendered as a bold mrkdwn link
    `*<url|KEY-# Summary>*`. We swap the href for the real issue URL and, if the
    URL contains a `/browse/KEY-#`, swap the leading key too so the card matches
    the work item Slack will unfurl. The summary text (if any) is preserved.
    """
    m = re.search(r"/browse/([A-Za-z][A-Za-z0-9]+-\d+)", url)
    new_key = m.group(1) if m else None
    for b in blocks:
        if b.get("type") == "section" and isinstance(b.get("text"), dict):
            lm = re.match(r"\s*\*<[^|>]+\|([^>]+)>\*", b["text"]["text"])
            if lm:
                label = lm.group(1)
                if new_key:
                    parts = label.split(" ", 1)
                    summary = parts[1] if len(parts) > 1 else ""
                    label = f"{new_key} {summary}".strip()
                b["text"]["text"] = f"*<{url}|{label}>*"
            # only the first section (the title) carries the issue link
            return blocks
    return blocks


def resolve_channel(ref: str) -> str:
    """Accept a channel id (C.../G...) as-is, else resolve a name via channel_admin."""
    if ref[:1] in "CG" and ref[1:2].isalnum() and " " not in ref:
        return ref
    try:
        import channel_admin
        meta = channel_admin.resolve_channel(ref)
        if meta:
            return meta["id"]
    except Exception:
        pass
    sys.exit(f"[error] could not resolve channel {ref!r} — pass a channel id (C...)")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--app", help="app key or name, e.g. 'datadog' / 'PagerDuty'")
    ap.add_argument("--example", help="example name (default: first in the file)")
    ap.add_argument("--channel", help="channel id (C...) or name")
    ap.add_argument("--username", help="override the sender name (default: the app's name)")
    ap.add_argument("--icon-emoji", help="e.g. :dog: (default: per-app guess)")
    ap.add_argument("--icon-url", help="logo URL — most convincing; wins over everything")
    ap.add_argument("--logo-base", help="base URL of hosted logo folder; overrides "
                    "LOGO_BASE / $DEMO_LOGO_BASE. icon becomes <base>/<app>.png")
    ap.add_argument("--ticket-url", help="real Jira issue URL (e.g. "
                    "https://site.atlassian.net/browse/KEY-1). Points the card's "
                    "title at it and appends the bare URL so Slack unfurls the "
                    "work item beneath the card. Enables unfurl_links.")
    ap.add_argument("--thread-ts", help="post as a reply in this thread")
    ap.add_argument("--list", action="store_true", help="list available apps/examples and exit")
    ap.add_argument("--dry-run", action="store_true", help="print the payload, don't send")
    a = ap.parse_args()

    tokens = json.load(open(os.path.join(_REPO_ROOT, "tokens.json")))
    bot = tokens.get("app_token")
    if not bot:
        sys.exit("[error] no bot token (app_token) in tokens.json — chat:write.customize "
                 "lives on the bot token")

    if a.list:
        # Best-effort listing from local dir; falls back to a hint if absent.
        if os.path.isdir(LOCAL_DIR):
            names = sorted(f[:-5] for f in os.listdir(LOCAL_DIR) if f.endswith(".json"))
        else:
            names = []
        if not names:
            print("No local blockkit/ dir. Apps live at:\n  " + RAW_BASE)
            print("Known keys: azure_pipelines, crm_analytics, datadog, deal_won, "
                  "deploy_wizard, docusign, github, google_calendar, jira_cloud, "
                  "new_opportunity, pagerduty, polly, salesforce, service_cloud, "
                  "servicenow, stage_changed, workday")
            return
        for key in names:
            d = load_app(key)
            exs = ", ".join(e["name"] for e in d.get("examples", []))
            print(f"{key:20} ({d.get('app')}): {exs}")
        return

    if not (a.app and a.channel):
        ap.error("--app and --channel are required (unless --list)")

    key = a.app.lower().replace(" ", "_").removesuffix(".json")
    data = load_app(a.app)
    examples = data.get("examples", [])
    if not examples:
        sys.exit(f"[error] no examples in block kit for {a.app!r}")
    if a.example:
        ex = next((e for e in examples if e["name"] == a.example), None)
        if not ex:
            avail = ", ".join(e["name"] for e in examples)
            sys.exit(f"[error] example {a.example!r} not found. Available: {avail}")
    else:
        ex = examples[0]

    blocks = ex["blocks"]
    username = a.username or data.get("fake_bot_id") or data.get("app")
    channel = resolve_channel(a.channel)

    # A real Jira issue link lets Slack unfurl the actual work item below the
    # card. Slack only unfurls BARE urls in the message `text` (the `<url|label>`
    # links inside blocks never unfurl), so we retarget the title link AND append
    # the raw url to the fallback text, then turn on unfurl_links.
    is_jira = key.startswith("jira")
    if a.ticket_url:
        blocks = inject_ticket_url(blocks, a.ticket_url)
    text = fallback_text(blocks)
    if a.ticket_url:
        text = f"{text}\n{a.ticket_url}"

    kwargs = dict(channel=channel, text=text, blocks=blocks, username=username)
    if a.ticket_url or is_jira:
        kwargs["unfurl_links"] = True
        kwargs["unfurl_media"] = True
    logo_base = (a.logo_base or LOGO_BASE).rstrip("/")
    if a.icon_url:                       # explicit URL wins
        kwargs["icon_url"] = a.icon_url
    elif a.icon_emoji:                   # explicit emoji next
        kwargs["icon_emoji"] = a.icon_emoji
    elif logo_base:                      # hosted real logo: <base>/<key>.png
        kwargs["icon_url"] = f"{logo_base}/{key}.png"
    else:                                # per-app emoji fallback
        kwargs["icon_emoji"] = DEFAULT_EMOJI.get(
            (data.get("app") or "").lower(), ":robot_face:")
    if a.thread_ts:
        kwargs["thread_ts"] = a.thread_ts

    if a.dry_run:
        print(f"[dry-run] would post as {username!r} to {channel} "
              f"(example={ex['name']}):")
        print(json.dumps(kwargs, indent=2))
        return

    client = WebClient(token=bot)
    try:
        resp = client.chat_postMessage(**kwargs)
    except SlackApiError as e:
        err = e.response.get("error")
        if err == "not_in_channel":
            # public channels: self-join then retry; private needs a manual /invite
            try:
                client.conversations_join(channel=channel)
                resp = client.chat_postMessage(**kwargs)
            except SlackApiError as e2:
                sys.exit(f"[error] {e2.response.get('error')} — if the channel is private, "
                         f"/invite the bot first")
        else:
            sys.exit(f"[error] chat.postMessage failed: {err}")
    print(f"[sent] {username} -> {channel} ts={resp['ts']} (example={ex['name']})")


if __name__ == "__main__":
    main()
