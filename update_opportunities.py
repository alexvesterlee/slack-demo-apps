#!/usr/bin/env python3
"""Roll Salesforce opportunity close dates forward so a demo org looks current.

By default this spreads every OPEN opportunity (not Closed Won/Lost) evenly
across the next several weeks, starting a few days out — so the pipeline looks
freshly active whenever you demo. Optionally, you can pin specific "priority"
opportunities to exact dates via a local `priority_opps.json` (see below).

This is the SCRIPTED Salesforce path — it shells out to the `sf` CLI (install
separately: `brew install --cask sf`, then `sf org login web`). Interactive,
one-off reads are better done by asking Claude through the Salesforce MCP server.

Config (nothing org-specific is hardcoded):
    SF_ORG env var   — your `sf` org username or alias (required), e.g.
                       `export SF_ORG=me@example.com` or `SF_ORG=demo-org`
    --org <alias>    — overrides SF_ORG for one run
    --start-days N   — first close date is N days from today (default 5)
    --window-days N  — spread opps across this many days (default 45)

Priority pinning (optional): create a `priority_opps.json` (gitignored) like:
    [
      {"id": "006XXXXXXXXXXXXXXX", "close_date": "2026-06-05"},
      {"id": "006XXXXXXXXXXXXXXX", "close_date": "2026-06-12"}
    ]
Those ids are set to the exact dates given and excluded from the auto-spread.

Usage:
    SF_ORG=me@example.com .venv/bin/python update_opportunities.py
    .venv/bin/python update_opportunities.py --org demo-org --window-days 60
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PRIORITY_FILE = ROOT / "priority_opps.json"  # optional, gitignored

# The `sf` CLI emits ANSI color escapes even with --json unless color is
# disabled, which breaks json.loads ("Expecting value: line 1 column 1").
# Force color off in the subprocess env and strip any escapes defensively.
_NO_COLOR_ENV = dict(os.environ, NO_COLOR="1", FORCE_COLOR="0")
_ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


def _parse_sf_json(raw: str) -> dict:
    return json.loads(_ANSI_RE.sub("", raw))


def sf_bin() -> str:
    found = shutil.which("sf") or shutil.which("sf", path="/opt/homebrew/bin")
    if not found:
        sys.exit("Error: 'sf' CLI not found. Install it: brew install --cask sf")
    return found


def sf_query(org: str, soql: str) -> list[dict]:
    result = subprocess.run(
        [sf_bin(), "data", "query", "-o", org, "--query", soql, "--json"],
        capture_output=True, text=True, env=_NO_COLOR_ENV,
    )
    data = _parse_sf_json(result.stdout)
    if data.get("status") != 0:
        raise RuntimeError(f"Query failed: {data.get('message', result.stdout)}")
    return data["result"]["records"]


def sf_update(org: str, record_id: str, close_date: str) -> bool:
    result = subprocess.run(
        [sf_bin(), "data", "update", "record", "-o", org,
         "--sobject", "Opportunity",
         "--record-id", record_id,
         "--values", f"CloseDate={close_date}",
         "--json"],
        capture_output=True, text=True, env=_NO_COLOR_ENV,
    )
    data = _parse_sf_json(result.stdout)
    return data.get("status") == 0


def load_priority() -> list[dict]:
    if not PRIORITY_FILE.exists():
        return []
    try:
        return json.loads(PRIORITY_FILE.read_text())
    except json.JSONDecodeError as e:
        sys.exit(f"Error: {PRIORITY_FILE.name} is not valid JSON ({e})")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--org", default=os.environ.get("SF_ORG", ""),
                    help="sf org username or alias (or set SF_ORG)")
    ap.add_argument("--start-days", type=int, default=5,
                    help="first close date is N days from today (default 5)")
    ap.add_argument("--window-days", type=int, default=45,
                    help="spread open opps across this many days (default 45)")
    args = ap.parse_args()

    if not args.org:
        sys.exit("Error: no Salesforce org. Set SF_ORG or pass --org <alias>.")

    failures = 0
    priority = load_priority()
    priority_ids = {p["id"] for p in priority}

    # --- Priority opportunities (optional, exact dates) ---
    if priority:
        print(f"Pinning {len(priority)} priority opportunit(ies) to exact dates...")
        for p in priority:
            ok = sf_update(args.org, p["id"], p["close_date"])
            print(f"  {'OK ' if ok else 'ERR'} {p['id']}  ->  {p['close_date']}")
            failures += 0 if ok else 1

    # --- All other open opportunities: spread across the window ---
    print("\nQuerying open opportunities...")
    exclude = ""
    if priority_ids:
        joined = "','".join(priority_ids)
        exclude = f"AND Id NOT IN ('{joined}') "
    records = sf_query(
        args.org,
        f"SELECT Id, Name FROM Opportunity "
        f"WHERE StageName NOT IN ('Closed Won', 'Closed Lost') "
        f"{exclude}"
        f"ORDER BY CloseDate ASC"
    )

    if records:
        print(f"Spreading {len(records)} open opportunit(ies) across the next "
              f"{args.window_days} days...")
        start = date.today() + timedelta(days=args.start_days)
        step = max(1, args.window_days // max(1, len(records)))
        for i, rec in enumerate(records):
            target = (start + timedelta(days=i * step)).isoformat()
            ok = sf_update(args.org, rec["Id"], target)
            name = rec["Name"][:55]
            print(f"  {'OK ' if ok else 'ERR'} {name:<55}  ->  {target}")
            failures += 0 if ok else 1
    else:
        print("  No other open opportunities found.")

    print(f"\n{'All updates successful.' if not failures else f'{failures} update(s) failed.'}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
