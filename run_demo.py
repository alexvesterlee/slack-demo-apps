#!/usr/bin/env python3
"""One-shot demo reset: send Slack messages + update Salesforce opportunity dates.

Usage:
    .venv/bin/python run_demo.py [--skip-slack] [--skip-sf]

Options:
    --skip-slack   Skip Slack message sending
    --skip-sf      Skip Salesforce opportunity date updates
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VENV_PYTHON = ROOT / ".venv" / "bin" / "python"


def run(script: Path, *extra_args: str) -> int:
    cmd = [str(VENV_PYTHON), str(script), *extra_args]
    result = subprocess.run(cmd)
    return result.returncode


def main() -> int:
    parser = argparse.ArgumentParser(description="Run full demo setup")
    parser.add_argument("--skip-slack", action="store_true", help="Skip Slack messages")
    parser.add_argument("--skip-sf", action="store_true", help="Skip Salesforce updates")
    args = parser.parse_args()

    overall = 0
    manifest = ROOT / "sent.json"

    # ── Slack ──────────────────────────────────────────────────────────────
    if not args.skip_slack:
        print("=" * 60)
        print("STEP 1: Sending Slack messages")
        print("=" * 60)

        # Delete previously sent messages before sending new ones
        if manifest.exists():
            print("Deleting previous messages...")
            rc = run(ROOT / "examples" / "delete_dms.py", "--manifest", str(manifest))
            if rc != 0:
                print("[warn] Some previous messages could not be deleted — continuing\n")
            else:
                print("[ok] Previous messages deleted\n")
            manifest.unlink(missing_ok=True)

        rc = run(
            ROOT / "examples" / "send_dms_as_users.py",
            "--config", str(ROOT / "my_demo.json"),
            "--manifest", str(manifest),
        )
        if rc != 0:
            print("[warn] Slack step finished with errors — continuing\n")
            overall = 1
        else:
            print("[ok] Slack messages sent\n")
    else:
        print("[skip] Slack messages\n")

    # ── Salesforce ─────────────────────────────────────────────────────────
    if not args.skip_sf:
        print("=" * 60)
        print("STEP 2: Updating Salesforce opportunity close dates")
        print("=" * 60)
        rc = run(ROOT / "update_opportunities.py")
        if rc != 0:
            print("[warn] Salesforce step finished with errors\n")
            overall = 1
        else:
            print("[ok] Salesforce opportunities updated\n")
    else:
        print("[skip] Salesforce updates\n")

    print("=" * 60)
    print("Demo setup complete." if overall == 0 else "Demo setup done (some steps had errors).")
    return overall


if __name__ == "__main__":
    raise SystemExit(main())
