"""Bot-token channel administration for the demo org (Enterprise Grid aware).

Enabled by the bot token (tokens.json -> app_token) carrying channel scopes:
  channels:read, groups:read, channels:manage, groups:write, channels:join

Provides a small, tested set of primitives the demo-refresh skill relies on:
  - resolve_channel(name)            name -> id (caches the org channel list)
  - persona_user_id(email)           persona email -> Slack user id (via auth.test)
  - ensure_member(channel, users)    bot joins (public) + invites personas
  - create_channel / rename_channel / set_topic
  - archive by id or name-match      (see also the thin archive_channel.py CLI)

Grid notes learned the hard way:
  - conversations.list / .create need an explicit team_id on Grid. We discover it
    from a persona token (personas live in the target workspace) so nothing is
    hard-coded.
  - archive and invite require the bot to be a MEMBER, even for public channels.
    ensure_member/_join_public handle public; private channels need a manual
    /invite of the bot (reported clearly).

CLI:
  python channel_admin.py resolve   --name "sales-leadership"
  python channel_admin.py ensure    --channel "sales-leadership" --emails a@x,b@y
  python channel_admin.py create    --name "new-room" [--private] [--invite a@x,b@y]
  python channel_admin.py rename    --channel C0XXXX --to "new-name"
  python channel_admin.py archive   --channel C0XXXX
  python channel_admin.py archive   --match "Platform Expansion" [--allow-empty]
"""
from __future__ import annotations

import argparse
import sys
from functools import lru_cache

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from config import audit_log, load_tokens


# --------------------------------------------------------------------------- #
# Clients / Grid plumbing
# --------------------------------------------------------------------------- #
def bot_client() -> WebClient:
    token = load_tokens().get("app_token")
    if not token:
        print("No bot token in tokens.json (app_token empty). Run save_bot_token.py.",
              file=sys.stderr)
        raise SystemExit(1)
    return WebClient(token=token)


@lru_cache(maxsize=1)
def workspace_team_id() -> str | None:
    """Real workspace team id (T...) required by Grid conversations.list/create.

    IMPORTANT: on this enterprise-install org, a persona's auth.test returns the
    *enterprise* id (E...), NOT a workspace id — passing that to
    conversations.list/create fails with `team_access_not_granted`. So we ask the
    bot token for its workspace(s) via auth.teams.list and return the first T...
    id. Persona auth.test is only a fallback, and enterprise (E...) ids are
    rejected there too.
    """
    # Preferred: the bot's own workspace list (returns the T... workspace id).
    try:
        r = bot_client().api_call("auth.teams.list")
        teams = r.get("teams") or []
        for t in teams:
            tid = t.get("id", "")
            if tid.startswith("T"):
                return tid
    except SlackApiError:
        pass

    # Fallback: persona auth.test — but only accept a workspace (T...) id.
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


def user_id_for_email(email: str) -> str | None:
    """Resolve ANY org member's email -> Slack user id.

    Uses the bot's users:read.email scope (works for all 198 org users). Falls
    back to a persona's own auth.test if the email happens to be a persona and
    the lookup scope is ever unavailable.
    """
    try:
        r = bot_client().users_lookupByEmail(email=email)
        if r.get("ok"):
            return r["user"]["id"]
    except SlackApiError:
        pass
    # Fallback: persona token (pre-users-scope behavior)
    tok = load_tokens().get("users", {}).get(email)
    if tok:
        try:
            return WebClient(token=tok).auth_test().get("user_id")
        except SlackApiError:
            return None
    return None


# Backwards-compatible alias (older callers/skill docs use persona_user_id).
persona_user_id = user_id_for_email


@lru_cache(maxsize=1)
def _user_index() -> dict:
    """display_name/real_name/name (lowercased) -> user id, for all active users."""
    client = bot_client()
    team_id = workspace_team_id()
    index: dict[str, str] = {}
    cursor = None
    while True:
        kwargs = dict(limit=200, cursor=cursor)
        if team_id:
            kwargs["team_id"] = team_id
        resp = client.users_list(**kwargs)
        for u in resp.get("members", []):
            if u.get("deleted") or u.get("is_bot") or u["id"] == "USLACKBOT":
                continue
            p = u.get("profile", {})
            for key in (p.get("display_name"), p.get("real_name"), u.get("name")):
                if key:
                    index.setdefault(key.lower(), u["id"])
        cursor = resp.get("response_metadata", {}).get("next_cursor")
        if not cursor:
            break
    return index


def user_id_for_name(name: str) -> str | None:
    """Resolve a display/real/user name (case-insensitive) -> user id, or None."""
    return _user_index().get(name.lower())


# --------------------------------------------------------------------------- #
# Read / resolve
# --------------------------------------------------------------------------- #
@lru_cache(maxsize=1)
def _channel_index() -> dict:
    """Map of name -> {'id','is_private','is_archived'} for all org channels.

    Cached per process. Includes archived so callers can detect stale/archived
    references; filter on is_archived where needed.
    """
    client = bot_client()
    team_id = workspace_team_id()
    index: dict[str, dict] = {}
    cursor = None
    while True:
        kwargs = dict(types="public_channel,private_channel", exclude_archived=False,
                      limit=200, cursor=cursor)
        if team_id:
            kwargs["team_id"] = team_id
        resp = client.conversations_list(**kwargs)
        for c in resp.get("channels", []):
            index[c["name"]] = {"id": c["id"], "is_private": c.get("is_private"),
                                "is_archived": c.get("is_archived")}
        cursor = resp.get("response_metadata", {}).get("next_cursor")
        if not cursor:
            break
    return index


def resolve_channel(name: str) -> dict | None:
    """Resolve an exact channel name to {'id','is_private','is_archived'} or None."""
    return _channel_index().get(name.lstrip("#"))


def find_channels(substr: str, include_archived: bool = False) -> list[dict]:
    """All channels whose name contains substr (case-insensitive)."""
    s = substr.lower()
    out = []
    for name, meta in _channel_index().items():
        if s in name.lower() and (include_archived or not meta["is_archived"]):
            out.append({"name": name, **meta})
    return out


# --------------------------------------------------------------------------- #
# Membership
# --------------------------------------------------------------------------- #
def _join_public(client: WebClient, channel_id: str) -> bool:
    try:
        client.conversations_join(channel=channel_id)
        return True
    except SlackApiError as e:
        print(f"[warn] bot could not join {channel_id}: {e.response.get('error')}",
              file=sys.stderr)
        return False


def resolve_user(who: str) -> str | None:
    """Resolve a user reference -> id. Accepts a raw id (U...), an email, or a
    display/real name. Works for ANY org member, not just personas."""
    if who.startswith("U") and len(who) >= 9 and who[1:].isalnum():
        return who  # already a user id (e.g. U0123456789)
    if "@" in who:
        return user_id_for_email(who)
    return user_id_for_name(who)


def ensure_member(channel: str, members: list[str]) -> bool:
    """Ensure each user is a member of `channel` (id or name).

    `members` may be emails, display/real names, or raw user ids — resolved via
    the org directory (any of the 198 users). Bot self-joins public channels so
    it can invite. Returns True if all named users end up in the channel.
    """
    meta = resolve_channel(channel) if not channel.startswith("C") else None
    channel_id = meta["id"] if meta else channel
    is_private = meta["is_private"] if meta else None

    client = bot_client()
    # Bot must be a member to invite others.
    try:
        info = client.conversations_info(channel=channel_id)
        if not info["channel"].get("is_member"):
            if is_private or info["channel"].get("is_private"):
                print(f"[fail] bot not in private #{channel_id}; /invite the bot first.",
                      file=sys.stderr)
                return False
            if not _join_public(client, channel_id):
                return False
    except SlackApiError as e:
        print(f"[warn] conversations.info {channel_id}: {e.response.get('error')}",
              file=sys.stderr)

    ok = True
    for who in members:
        uid = resolve_user(who)
        if not uid:
            print(f"[warn] could not resolve user {who!r}; skipping invite", file=sys.stderr)
            ok = False
            continue
        try:
            client.conversations_invite(channel=channel_id, users=uid)
            print(f"[invited] {who} ({uid}) -> {channel_id}")
        except SlackApiError as e:
            err = e.response.get("error")
            if err in ("already_in_channel", "cant_invite_self"):
                continue  # already good
            print(f"[warn] invite {who} -> {channel_id}: {err}", file=sys.stderr)
            ok = False
    return ok


# --------------------------------------------------------------------------- #
# Lifecycle
# --------------------------------------------------------------------------- #
def create_channel(name: str, private: bool = False, invite_emails: list[str] | None = None) -> str | None:
    client = bot_client()
    try:
        resp = client.conversations_create(
            name=name, is_private=private, team_id=workspace_team_id()
        )
    except SlackApiError as e:
        if e.response.get("error") == "name_taken":
            existing = resolve_channel(name)
            print(f"[skip] #{name} already exists ({existing['id'] if existing else '?'})")
            return existing["id"] if existing else None
        print(f"[fail] create #{name}: {e.response.get('error')}", file=sys.stderr)
        return None
    cid = resp["channel"]["id"]
    print(f"[created] #{name} ({cid})")
    audit_log(f":heavy_plus_sign: Created channel #{name} ({cid})")
    if invite_emails:
        ensure_member(cid, invite_emails)
    return cid


def rename_channel(channel: str, new_name: str) -> bool:
    meta = resolve_channel(channel) if not channel.startswith("C") else None
    cid = meta["id"] if meta else channel
    try:
        bot_client().conversations_rename(channel=cid, name=new_name)
    except SlackApiError as e:
        print(f"[fail] rename {cid} -> {new_name}: {e.response.get('error')}", file=sys.stderr)
        return False
    print(f"[renamed] {cid} -> #{new_name}")
    audit_log(f":pencil2: Renamed channel {cid} -> #{new_name}")
    return True


def set_topic(channel: str, topic: str) -> bool:
    meta = resolve_channel(channel) if not channel.startswith("C") else None
    cid = meta["id"] if meta else channel
    try:
        bot_client().conversations_setTopic(channel=cid, topic=topic)
    except SlackApiError as e:
        print(f"[fail] setTopic {cid}: {e.response.get('error')}", file=sys.stderr)
        return False
    print(f"[topic] {cid}: {topic}")
    return True


def archive_channel(channel: str) -> bool:
    """Archive by id or name. Auto-joins public channels first (archive needs membership)."""
    meta = resolve_channel(channel) if not channel.startswith("C") else None
    cid = meta["id"] if meta else channel
    is_private = meta["is_private"] if meta else None
    name = meta and next((n for n, m in _channel_index().items() if m["id"] == cid), None)
    label = cid + (f" (#{name})" if name else "")
    client = bot_client()

    def _do():
        client.conversations_archive(channel=cid)
        print(f"[archived] {label}")
        audit_log(f":wastebasket: Archived channel {label}")
        return True

    try:
        return _do()
    except SlackApiError as e:
        err = e.response.get("error")
        if err == "already_archived":
            print(f"[skip] {label} already archived")
            return True
        if err == "not_in_channel" and is_private is not True:
            if _join_public(client, cid):
                try:
                    return _do()
                except SlackApiError as e2:
                    err = e2.response.get("error")
        if err in ("not_in_channel", "channel_not_found") and is_private:
            print(f"[fail] {label}: {err} — private; /invite the bot, then re-run.",
                  file=sys.stderr)
        else:
            print(f"[fail] {label}: {err}", file=sys.stderr)
        return False


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def _list(s: str | None) -> list[str]:
    return [e.strip() for e in s.split(",") if e.strip()] if s else []


def main() -> int:
    ap = argparse.ArgumentParser(description="Demo org channel & user administration")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("resolve"); p.add_argument("--name", required=True)
    p = sub.add_parser("whois"); p.add_argument("--who", required=True,
        help="email, display/real name, or user id — resolves against the whole org")
    p = sub.add_parser("ensure"); p.add_argument("--channel", required=True)
    p.add_argument("--members", "--emails", dest="members", required=True,
        help="comma-separated emails / names / user ids (any org member)")
    p = sub.add_parser("create"); p.add_argument("--name", required=True); p.add_argument("--private", action="store_true")
    p.add_argument("--invite", help="comma-separated emails / names / user ids to invite")
    p = sub.add_parser("rename"); p.add_argument("--channel", required=True); p.add_argument("--to", required=True)
    p = sub.add_parser("topic"); p.add_argument("--channel", required=True); p.add_argument("--text", required=True)
    p = sub.add_parser("archive")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--channel"); g.add_argument("--match")
    p.add_argument("--allow-empty", action="store_true")

    a = ap.parse_args()
    if a.cmd == "resolve":
        m = resolve_channel(a.name)
        if not m:
            print(f"[not found] {a.name}"); return 1
        print(f"{a.name} -> {m['id']} (private={m['is_private']}, archived={m['is_archived']})")
        return 0
    if a.cmd == "whois":
        uid = resolve_user(a.who)
        if not uid:
            print(f"[not found] {a.who}"); return 1
        print(f"{a.who} -> {uid}")
        return 0
    if a.cmd == "ensure":
        return 0 if ensure_member(a.channel, _list(a.members)) else 1
    if a.cmd == "create":
        return 0 if create_channel(a.name, a.private, _list(a.invite)) else 1
    if a.cmd == "rename":
        return 0 if rename_channel(a.channel, a.to) else 1
    if a.cmd == "topic":
        return 0 if set_topic(a.channel, a.text) else 1
    if a.cmd == "archive":
        if a.channel:
            return 0 if archive_channel(a.channel) else 1
        matches = find_channels(a.match)
        if not matches:
            print(f"[skip] No channels matched {a.match!r}")
            return 0 if a.allow_empty else 1
        ok = all(archive_channel(c["id"]) for c in matches)
        return 0 if ok else 1
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
