"""Read-only sanity check for the saved bot token (tokens.json -> app_token).

Prints which workspace/org the bot token is installed in, so you can confirm it
landed in the SAME org as your persona tokens before relying on channel_admin.py
or send_app_notification.py. Nothing is modified.

On Enterprise Grid, a reinstall can silently land the token in the wrong org.
Set the env var EXPECTED_ENTERPRISE_ID to your Grid enterprise id (starts with
`E...`) to have this script assert the bot is in the right org and exit non-zero
if not. Leave it unset to just print what it finds.

    .venv/bin/python check_bot_token.py
    EXPECTED_ENTERPRISE_ID=E0XXXXXXXXX .venv/bin/python check_bot_token.py

Exit 0 if the token works (and matches EXPECTED_ENTERPRISE_ID when set), 1 otherwise.
"""
from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request

from config import load_tokens

# Optional: your Enterprise Grid enterprise id (e.g. "E0XXXXXXXXX"). When set,
# the bot must be installed in this org or the check fails. Unset = just report.
EXPECTED_ENTERPRISE_ID = os.environ.get("EXPECTED_ENTERPRISE_ID", "").strip()

# Optional: a channel id to confirm the bot can read (e.g. one you plan to manage).
CHECK_CHANNEL = os.environ.get("CHECK_CHANNEL", "").strip()


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

    if EXPECTED_ENTERPRISE_ID and ent != EXPECTED_ENTERPRISE_ID:
        print()
        print(f"WRONG ORG. Bot is in {ent}, but you expected "
              f"{EXPECTED_ENTERPRISE_ID}.")
        print("Reinstall the app targeting the correct workspace, then re-save the token.")
        return 1

    print("\nOK — bot token works"
          + (f" and is in the expected org ({EXPECTED_ENTERPRISE_ID})." if EXPECTED_ENTERPRISE_ID else "."))

    if CHECK_CHANNEL:
        info = _call("conversations.info", tok, channel=CHECK_CHANNEL)
        if info.get("ok"):
            c = info["channel"]
            print(f"channel {CHECK_CHANNEL}: #{c.get('name')} "
                  f"(private={c.get('is_private')}, archived={c.get('is_archived')})")
        else:
            print(f"note: conversations.info on {CHECK_CHANNEL} returned "
                  f"{info.get('error')!r} — check scopes (channels:read/groups:read) "
                  f"or invite the bot to the channel.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
