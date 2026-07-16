#!/usr/bin/env python3
"""Update Salesforce opportunity close dates for demo readiness.

Priority accounts (Omega, Verde Group, Stellar Media) land in the next
few weeks; all other open opportunities are spread across the following
1-2 months.

Usage:
    .venv/bin/python update_opportunities.py
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from datetime import date, timedelta

SF_ORG = "alexsdo1@salesforce.com"

# Open opportunities for priority accounts — Closed Won/Lost excluded.
# Dates are relative to late May 2026 (today ~2026-05-29).
PRIORITY_UPDATES = [
    # Omega, Inc. — week-by-week across June/July
    ("006Hu00001giGfXIAU", "2026-06-05"),   # Omega Insurance - Services 23K  (Discovery)
    ("006Hu00001giGdUIAU", "2026-06-12"),   # Omega Add-On 55K               (Discovery)
    ("006Hu000022bkqmIAA", "2026-06-26"),   # Omega Core Renewal             (Negotiation)
    ("006Hu00001giGc0IAE", "2026-07-03"),   # Omega New Business 317K        (Proposal/Quote)
    ("006Hu00001giGeyIAE", "2026-07-10"),   # Omega New Business 44K         (Discovery)
    ("006Hu00001gNGPSIA4", "2026-07-17"),   # Omega Enterprise Expansion     (Prospecting)
    # Stellar Media
    ("006Hu0000207W8AIAU", "2026-06-16"),   # Stellar Media                  (Qualification)
    # Verde Group — week-by-week across June
    ("006Hu0000206FflIAE", "2026-06-06"),   # Verde New Business 80K         (Qualification)
    ("006Hu00001gN1oMIAS", "2026-06-13"),   # Verde Add-On 75K               (Qualification)
    ("006Hu00001gN1o2IAC", "2026-06-20"),   # Verde Add-On 19K               (Qualification)
    ("006Hu0000205ursIAA", "2026-06-27"),   # Verde Welo Guard 120K          (Proposal/Quote)
]

PRIORITY_IDS = {opp_id for opp_id, _ in PRIORITY_UPDATES}


def sf_bin() -> str:
    found = shutil.which("sf") or shutil.which("sf", path="/opt/homebrew/bin")
    if not found:
        sys.exit("Error: 'sf' CLI not found. Run: brew install sf")
    return found


def sf_query(soql: str) -> list[dict]:
    result = subprocess.run(
        [sf_bin(), "data", "query", "-o", SF_ORG, "--query", soql, "--json"],
        capture_output=True, text=True,
    )
    data = json.loads(result.stdout)
    if data.get("status") != 0:
        raise RuntimeError(f"Query failed: {data.get('message', result.stdout)}")
    return data["result"]["records"]


def sf_update(record_id: str, close_date: str) -> bool:
    result = subprocess.run(
        [sf_bin(), "data", "update", "record", "-o", SF_ORG,
         "--sobject", "Opportunity",
         "--record-id", record_id,
         "--values", f"CloseDate={close_date}",
         "--json"],
        capture_output=True, text=True,
    )
    data = json.loads(result.stdout)
    return data.get("status") == 0


def main() -> int:
    failures = 0

    # --- Priority accounts ---
    print("Updating priority accounts (Omega, Verde Group, Stellar Media)...")
    for opp_id, close_date in PRIORITY_UPDATES:
        ok = sf_update(opp_id, close_date)
        print(f"  {'✓' if ok else '✗'} {opp_id}  →  {close_date}")
        if not ok:
            failures += 1

    # --- All other open opportunities ---
    print("\nQuerying other open opportunities...")
    excluded = "','".join(PRIORITY_IDS)
    records = sf_query(
        f"SELECT Id, Name FROM Opportunity "
        f"WHERE StageName NOT IN ('Closed Won', 'Closed Lost') "
        f"AND Id NOT IN ('{excluded}') "
        f"ORDER BY CloseDate ASC"
    )

    if records:
        print(f"Spreading {len(records)} other open opportunities across July–August 2026...")
        start = date(2026, 7, 1)
        # Aim to spread evenly across ~62 days; minimum 3-day gaps to keep it readable
        step = max(3, 62 // len(records))
        for i, rec in enumerate(records):
            target = (start + timedelta(days=i * step)).isoformat()
            ok = sf_update(rec["Id"], target)
            name = rec["Name"][:55]
            print(f"  {'✓' if ok else '✗'} {name:<55}  →  {target}")
            if not ok:
                failures += 1
    else:
        print("  No other open opportunities found.")

    print(f"\n{'All updates successful.' if not failures else f'{failures} update(s) failed.'}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
