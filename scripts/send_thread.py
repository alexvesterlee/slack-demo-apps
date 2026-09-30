"""Send a thread to a channel — first message is the parent, rest are replies.

Config format:
  {
    "channel_id": "C...",
    "messages": [
      {"sender_email": "...", "text": "..."},  <- parent
      {"sender_email": "...", "text": "..."},  <- reply
      ...
    ]
  }

Appends to --manifest (same format as send_dms_as_users.py) for cleanup.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from slack_sdk.errors import SlackApiError

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import audit_log, user_client


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--manifest", required=True)
    args = parser.parse_args()

    with open(args.config) as f:
        config = json.load(f)

    channel_id = config["channel_id"]
    messages = config["messages"]
    if not messages:
        print("No messages in config.")
        return 0

    # Load existing manifest if present
    manifest_path = Path(args.manifest)
    if manifest_path.exists():
        with open(manifest_path) as f:
            manifest = json.load(f)
    else:
        manifest = {"sent": []}

    sent = manifest["sent"]
    failures = 0
    thread_ts = None

    for i, msg in enumerate(messages):
        sender = msg["sender_email"]
        text = msg["text"]
        client = user_client(sender)
        try:
            kwargs = {"channel": channel_id, "text": text}
            if thread_ts:
                kwargs["thread_ts"] = thread_ts
            resp = client.chat_postMessage(**kwargs)
            ts = resp["ts"]
            if i == 0:
                thread_ts = ts
            entry = {"sender_email": sender, "channel_id": channel_id, "ts": ts}
            sent.append(entry)
            label = "parent" if i == 0 else f"reply {i}"
            print(f"[sent] {label} {sender} -> #{channel_id} ts={ts}")
            audit_log(f":thread: thread msg seeded — {sender} -> <#{channel_id}> (`ts={ts}`)")
        except (SlackApiError, RuntimeError) as e:
            err = e.response.get("error") if isinstance(e, SlackApiError) else str(e)
            print(f"[fail] {sender} -> #{channel_id}: {err}", file=sys.stderr)
            failures += 1

    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"\nManifest updated at {manifest_path}")

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
