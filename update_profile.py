#!/usr/bin/env python3
"""Update a Slack persona's profile fields for a demo flow.

Usage:
    .venv/bin/python update_profile.py --email <persona_email> --profile <profile_name>

Available profiles are defined in DEMO_PROFILES below.

Example:
    .venv/bin/python update_profile.py \
        --email demoeng+elliot_edwards_13583@slack-corp.com \
        --profile vp_sales
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import user_client  # noqa: E402

# ── Define demo profiles here ────────────────────────────────────────────────
# Keys match Slack's users.profile.set fields:
#   display_name, real_name, title, phone, status_text, status_emoji
DEMO_PROFILES: dict[str, dict] = {
    "vp_sales": {
        "title": "VP of Sales",
        "status_text": "Closing Q2",
        "status_emoji": ":bar_chart:",
    },
    "ae": {
        "title": "Account Executive",
        "status_text": "In demos this week",
        "status_emoji": ":handshake:",
    },
    "customer": {
        "title": "Director of Operations",
        "status_text": "Evaluating vendors",
        "status_emoji": ":mag:",
    },
    # Add more profiles here as your demo flows evolve
}


def main() -> int:
    parser = argparse.ArgumentParser(description="Update a Slack persona's profile")
    parser.add_argument("--email", required=True, help="Persona email (must be in tokens.json)")
    parser.add_argument(
        "--profile", required=True,
        choices=list(DEMO_PROFILES.keys()),
        help="Profile preset to apply",
    )
    parser.add_argument("--list", action="store_true", help="List available profiles and exit")
    args = parser.parse_args()

    if args.list:
        for name, fields in DEMO_PROFILES.items():
            print(f"  {name}: {fields}")
        return 0

    profile = DEMO_PROFILES[args.profile]
    client = user_client(args.email)

    # Split status fields (separate API call) from core profile fields
    status_text = profile.pop("status_text", None)
    status_emoji = profile.pop("status_emoji", None)

    if profile:
        resp = client.users_profile_set(profile=profile)
        if not resp["ok"]:
            print(f"[fail] Profile update: {resp.get('error')}", file=sys.stderr)
            return 1
        print(f"[ok] Core profile updated for {args.email}")

    if status_text is not None or status_emoji is not None:
        resp = client.users_profile_set(profile={
            "status_text": status_text or "",
            "status_emoji": status_emoji or "",
        })
        if not resp["ok"]:
            print(f"[fail] Status update: {resp.get('error')}", file=sys.stderr)
            return 1
        print(f"[ok] Status updated → {status_emoji} {status_text}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
