"""Preflight validation + self-heal for the demo-refresh Slack sends.

Run BEFORE Step 2. For every channel referenced across the message/thread configs
it: (1) verifies the channel id is live (not stale/archived), and (2) ensures each
sender persona is a member (bot joins public channels + invites personas). This
prevents the two failure modes seen in practice:
  - a stale hard-coded channel id (channel_not_found on every send), and
  - a sender who isn't in the channel (not_in_channel).

Requires the bot token with channel scopes (see channel_admin.py). If no bot token
is configured, this exits 0 with a notice — the refresh can still proceed, just
without the safety net.

Usage:
  python preflight.py --configs my_demo.json omega_thread.json assoc_supply_thread1.json ...
  python preflight.py            # defaults to the standard demo-refresh config set
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from config import load_tokens

DEFAULT_CONFIGS = [
    "my_demo.json",
    "omega_thread.json",
    "assoc_supply_thread1.json",
    "assoc_supply_thread2.json",
    "assoc_supply_thread3.json",
]


def _collect(configs: list[str]) -> dict[str, set[str]]:
    """channel_id -> set of sender emails that post to it, across all configs.

    Handles both formats:
      - flat DM/channel config: {messages:[{channel_id|recipient_user_id, sender_email}]}
      - thread config: {channel_id: "...", messages:[{sender_email, text}]}
        (channel_id is top-level; messages inherit it)
    """
    by_channel: dict[str, set[str]] = {}
    for path in configs:
        p = Path(path)
        if not p.exists():
            print(f"[warn] config not found: {path}", file=sys.stderr)
            continue
        cfg = json.loads(p.read_text())
        top_channel = cfg.get("channel_id")  # set for thread configs
        for m in cfg.get("messages", []):
            ch = m.get("channel_id") or top_channel
            if not ch:
                continue  # DMs (recipient_user_id) need no channel membership
            by_channel.setdefault(ch, set())
            if m.get("sender_email"):
                by_channel[ch].add(m["sender_email"])
    return by_channel


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--configs", nargs="*", default=DEFAULT_CONFIGS)
    ap.add_argument("--heal", action="store_true", default=True,
                    help="Invite missing senders (default on)")
    ap.add_argument("--no-heal", dest="heal", action="store_false",
                    help="Report only, don't invite")
    args = ap.parse_args()

    if not load_tokens().get("app_token"):
        print("[skip] No bot token (app_token) — preflight needs channel scopes. "
              "Proceeding without validation.")
        return 0

    # Imported lazily so the no-token path above doesn't require the module to init.
    from channel_admin import _channel_index, ensure_member

    by_channel = _collect(args.configs)
    if not by_channel:
        print("[preflight] no channel references found in configs")
        return 0

    # Build id -> meta from the org index (resolve_channel is name-keyed; we have ids).
    id_index = {m["id"]: {"name": n, **m} for n, m in _channel_index().items()}

    problems = 0
    for ch, senders in sorted(by_channel.items()):
        meta = id_index.get(ch)
        if not meta:
            print(f"[STALE] {ch}: not found in org — fix the channel_id in the config "
                  f"(senders: {', '.join(sorted(senders)) or 'n/a'})", file=sys.stderr)
            problems += 1
            continue
        if meta["is_archived"]:
            print(f"[STALE] {ch} (#{meta['name']}): channel is ARCHIVED — pick a live one",
                  file=sys.stderr)
            problems += 1
            continue
        print(f"[ok] {ch} (#{meta['name']}) — {len(senders)} sender(s)")
        if args.heal and senders:
            if not ensure_member(ch, sorted(senders)):
                problems += 1

    if problems:
        print(f"\n[preflight] {problems} issue(s) — resolve stale channel_ids above "
              f"before sending.", file=sys.stderr)
        return 1
    print("\n[preflight] all channels live and senders are members.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
