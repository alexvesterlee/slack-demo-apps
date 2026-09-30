"""Archive a Slack channel using the stored bot token (tokens.json -> app_token).

Two modes:
  --channel C0XXXX      Archive one channel by ID (verifies it first).
  --match "substring"   Find channel(s) whose name contains the (case-insensitive)
                        substring and archive them. Used by the demo-refresh skill
                        to clean up orphaned Salesforce deal channels.

Requires a bot token with scopes: channels:read, groups:read (to find/verify),
channels:manage, groups:write (to archive). For a PRIVATE channel the bot must
also be a member; the script reports clearly if it is not.

Exit codes: 0 = archived (or nothing matched with --allow-empty), 1 = error.
"""
from __future__ import annotations

import argparse
import sys

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from config import audit_log, load_tokens


def _client() -> WebClient:
    token = load_tokens().get("app_token")
    if not token:
        print(
            "No bot token in tokens.json (app_token is empty). "
            "Run `python save_bot_token.py` first.",
            file=sys.stderr,
        )
        raise SystemExit(1)
    return WebClient(token=token)


def _workspace_team_id() -> str | None:
    """Discover the real workspace team id (T...) for Grid conversations.list.

    On this enterprise-install org a persona's auth.test returns the *enterprise*
    id (E...), not a workspace id — passing that to conversations.list fails with
    `team_access_not_granted`. Ask the bot token for its workspace via
    auth.teams.list and return the first T... id; only fall back to a persona
    auth.test that yields a workspace (T...) id.
    """
    # Preferred: the bot's own workspace list (returns the T... workspace id).
    try:
        resp = _client().api_call("auth.teams.list")
        for t in resp.get("teams") or []:
            tid = t.get("id", "")
            if tid.startswith("T"):
                return tid
    except SlackApiError:
        pass

    # Fallback: persona auth.test, accepting only a workspace (T...) id.
    users = load_tokens().get("users", {})
    for email, tok in users.items():
        if email.startswith("_"):
            continue
        try:
            tid = WebClient(token=tok).auth_test().get("team_id", "")
            if tid.startswith("T"):
                return tid
        except SlackApiError:
            continue
    return None


def _find_by_match(client: WebClient, needle: str) -> list[dict]:
    needle = needle.lower()
    found: list[dict] = []
    cursor = None
    team_id = _workspace_team_id()  # required on Enterprise Grid; None elsewhere
    while True:
        kwargs = dict(
            types="public_channel,private_channel",
            exclude_archived=True,
            limit=200,
            cursor=cursor,
        )
        if team_id:
            kwargs["team_id"] = team_id
        resp = client.conversations_list(**kwargs)
        for c in resp.get("channels", []):
            if needle in c.get("name", "").lower():
                found.append(c)
        cursor = resp.get("response_metadata", {}).get("next_cursor")
        if not cursor:
            break
    return found


def _archive_one(
    client: WebClient, channel_id: str, name: str | None = None, is_private: bool | None = None
) -> bool:
    label = f"{channel_id}" + (f" (#{name})" if name else "")

    def _do_archive() -> bool:
        client.conversations_archive(channel=channel_id)
        print(f"[archived] {label}")
        audit_log(f":wastebasket: Archived channel {label}")
        return True

    try:
        return _do_archive()
    except SlackApiError as e:
        err = e.response.get("error")
        if err == "already_archived":
            print(f"[skip] {label} already archived")
            return True
        # archive requires membership even for PUBLIC channels. For public,
        # the bot can add itself (needs channels:join); for private it must be
        # /invite'd manually.
        if err == "not_in_channel" and is_private is False:
            try:
                client.conversations_join(channel=channel_id)
            except SlackApiError as je:
                print(f"[fail] {label}: could not join to archive "
                      f"({je.response.get('error')})", file=sys.stderr)
                return False
            try:
                return _do_archive()
            except SlackApiError as e2:
                err = e2.response.get("error")
        if err in ("not_in_channel", "channel_not_found") and is_private:
            print(f"[fail] {label}: {err} — private channel; /invite the bot to it, "
                  f"then re-run.", file=sys.stderr)
        else:
            print(f"[fail] {label}: {err}", file=sys.stderr)
        return False


def main() -> int:
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--channel", help="Channel ID to archive")
    g.add_argument("--match", help="Archive channels whose name contains this substring")
    ap.add_argument(
        "--allow-empty",
        action="store_true",
        help="With --match, exit 0 (not 1) when nothing matches. Use in refresh automation.",
    )
    args = ap.parse_args()
    client = _client()

    if args.channel:
        # Verify + capture the name/visibility before archiving so the log is
        # meaningful and we know whether the bot can self-join.
        name = None
        is_private = None
        try:
            info = client.conversations_info(channel=args.channel)
            name = info["channel"]["name"]
            is_private = info["channel"].get("is_private")
            if info["channel"].get("is_archived"):
                print(f"[skip] {args.channel} (#{name}) already archived")
                return 0
        except SlackApiError as e:
            print(f"[warn] could not read {args.channel}: {e.response.get('error')} "
                  f"(attempting archive anyway)", file=sys.stderr)
        return 0 if _archive_one(client, args.channel, name, is_private) else 1

    # --match
    matches = _find_by_match(client, args.match)
    if not matches:
        msg = f"No channels matched {args.match!r}"
        print(f"[skip] {msg}")
        return 0 if args.allow_empty else 1
    ok = True
    for c in matches:
        ok = _archive_one(client, c["id"], c.get("name"), c.get("is_private")) and ok
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
