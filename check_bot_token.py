"""Read-only sanity check for the saved bot token (tokens.json -> app_token).

Confirms the bot is installed in the SAME org as the persona tokens, and that it
can actually read the orphaned deal channel. Run this after reinstalling the app
and saving the token, BEFORE relying on archive_channel.py.

Nothing is modified. Exit 0 if the token is in the right org, 1 otherwise.
"""
from __future__ import annotations

import json
import sys
import urllib.parse
import urllib.request

from config import load_tokens

TARGET_CHANNEL = "C0BGD9T95EV"  # the orphaned Omega deal channel to archive
# The org the personas (and the deal channel) live in — bot must match this.
EXPECTED_ENTERPRISE_ID = "E081F1M8TAN"  # demo-13583 / "Global"


def _call(method: str, token: str, **params):
    req = urllib.request.Request(
        "https://slack.com/api/" + method,
        data=urllib.parse.urlencode(params).encode() if params else None,
        headers={"Authorization": f"Bearer {token}"},
    )
    try:
        return json.load(urllib.request.urlopen(req))
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": f"http:{e}"}


def main() -> int:
    tok = load_tokens().get("app_token")
    if not tok:
        print("No bot token saved (app_token empty). Run save_bot_token.py first.")
        return 1

    a = _call("auth.test", tok)
    if not a.get("ok"):
        print(f"auth.test failed: {a.get('error')}")
        return 1

    ent = a.get("enterprise_id")
    print(f"bot:            {a.get('user')}")
    print(f"team / url:     {a.get('team')} / {a.get('url')}")
    print(f"enterprise_id:  {ent}")

    if ent != EXPECTED_ENTERPRISE_ID:
        print()
        print(f"WRONG ORG. Bot is in {ent}, but the deal channel lives in "
              f"{EXPECTED_ENTERPRISE_ID} (demo-13583 / Global).")
        print("Reinstall the app targeting the demo-13583 workspace, then re-save.")
        return 1

    print(f"\nOK — bot is in the expected org ({EXPECTED_ENTERPRISE_ID}).")

    info = _call("conversations.info", tok, channel=TARGET_CHANNEL)
    if info.get("ok"):
        c = info["channel"]
        print(f"channel {TARGET_CHANNEL}: #{c.get('name')} "
              f"(private={c.get('is_private')}, archived={c.get('is_archived')})")
        print("Ready to archive.")
    else:
        print(f"note: can read the org but conversations.info on {TARGET_CHANNEL} "
              f"returned {info.get('error')!r} — check scopes (channels:read/groups:read).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
