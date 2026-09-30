#!/usr/bin/env python3
"""Commit logo assets + README into YOUR public assets repo via the GitHub
Contents API — no local clone. Slack needs a publicly reachable image URL for a
custom app icon, so app-notification logos live in a public GitHub repo you own.

Point this at your own repo with the DEMO_ASSETS_REPO env var ("owner/repo");
it defaults to a placeholder you MUST change. Token is read from env GHT (set it
via an interactive prompt so it never lands in shell history):

    export DEMO_ASSETS_REPO="your-github-username/slack-demo-apps"
    read -rs -p "GitHub PAT (Contents: read/write on that repo): " GHT; echo
    GHT="$GHT" python3 push_logos.py

Add more logos later: drop <blockkit-key>.png files into a local `logos/` dir next
to this script and re-run — every *.png in ./logos is uploaded.
"""
import base64
import glob
import json
import os
import subprocess
import sys
import urllib.request
import urllib.error

# Your PUBLIC assets repo, as "owner/repo". Override via DEMO_ASSETS_REPO.
_REPO = os.environ.get("DEMO_ASSETS_REPO", "your-github-username/slack-demo-apps")
OWNER, _, REPO = _REPO.partition("/")
BRANCH = os.environ.get("DEMO_ASSETS_BRANCH", "main")
API = f"https://api.github.com/repos/{OWNER}/{REPO}/contents"

# macOS Keychain item that stores the GitHub PAT, so this script (and Claude, on
# the user's behalf) can push without a token ever being typed into the chat.
# Store it once, interactively (the -w prompt keeps it out of shell history):
#   security add-generic-password -a "$USER" -s demo-app-logos-pat \
#       -T /usr/bin/security -U -w
KEYCHAIN_SERVICE = "demo-app-logos-pat"


def _token_from_keychain():
    try:
        r = subprocess.run(
            ["security", "find-generic-password", "-s", KEYCHAIN_SERVICE, "-w"],
            capture_output=True, text=True)
        return r.stdout.strip() if r.returncode == 0 else ""
    except Exception:
        return ""


# Token precedence: env GHT (one-off interactive push) → macOS Keychain (persistent).
TOKEN = os.environ.get("GHT", "").strip() or _token_from_keychain()
if not TOKEN:
    sys.exit("[error] no GitHub token found. Either export GHT=<pat> for this run, "
             f"or store one once in the Keychain:\n"
             f"  security add-generic-password -a \"$USER\" -s {KEYCHAIN_SERVICE} "
             f"-T /usr/bin/security -U -w")

HERE = os.path.dirname(os.path.abspath(__file__))
LOCAL_LOGO_DIR = os.path.join(HERE, "logos")

README = f"""# {REPO}

Public logo assets for **fictitious third-party app notifications** posted into a
Slack demo org by `send_app_notification.py`.

Slack's `icon_url` needs a publicly reachable image URL, so logos live here and are served
over `raw.githubusercontent.com`. The helper builds each avatar as:

    icon_url = <LOGO_BASE>/<blockkit-key>.png

with `LOGO_BASE = https://raw.githubusercontent.com/{OWNER}/{REPO}/{BRANCH}/logos`.

## Naming convention

One square PNG per app (>=192x192 renders best), named **exactly** by its block-kit file key
(from bob-the-builder/blockkit). To add or update a logo: drop `<key>.png` in `logos/` and
push — no code change, the helper picks it up automatically.

Expected keys: datadog, pagerduty, github, salesforce, service_cloud, servicenow, jira_cloud,
azure_pipelines, deploy_wizard, docusign, google_calendar, crm_analytics, workday, polly,
new_opportunity, deal_won, stage_changed.
"""


def api(method, path, payload):
    req = urllib.request.Request(
        f"{API}/{path}", method=method, data=json.dumps(payload).encode(),
        headers={"Authorization": f"Bearer {TOKEN}",
                 "Accept": "application/vnd.github+json",
                 "X-GitHub-Api-Version": "2022-11-28",
                 "User-Agent": "demo-refresh-logo-uploader"})
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read().decode())


def get_sha(path):
    """Existing file sha (needed to update), or None if the file is new."""
    req = urllib.request.Request(
        f"{API}/{path}?ref={BRANCH}",
        headers={"Authorization": f"Bearer {TOKEN}",
                 "Accept": "application/vnd.github+json",
                 "User-Agent": "demo-refresh-logo-uploader"})
    try:
        with urllib.request.urlopen(req) as r:
            return json.loads(r.read().decode()).get("sha")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise


def put_file(path, raw_bytes, message):
    payload = {"message": message, "branch": BRANCH,
               "content": base64.b64encode(raw_bytes).decode()}
    sha = get_sha(path)
    if sha:
        payload["sha"] = sha
    try:
        res = api("PUT", path, payload)
        commit = res.get("commit", {}).get("sha", "")[:7]
        print(f"[{'updated' if sha else 'created'}] {path}  commit={commit}")
    except urllib.error.HTTPError as e:
        sys.exit(f"[error] {path}: HTTP {e.code} {e.read().decode()[:300]}")


def main():
    # README first (also bootstraps the default branch on an empty repo)
    put_file("README.md", README.encode(), "Add README (logo naming convention)")

    # Collect logos: any ./logos/*.png
    files = {}
    if os.path.isdir(LOCAL_LOGO_DIR):
        for p in glob.glob(os.path.join(LOCAL_LOGO_DIR, "*.png")):
            files[os.path.basename(p)] = p

    if not files:
        print("[note] no PNGs found in ./logos — README only")
    for name, src in sorted(files.items()):
        with open(src, "rb") as f:
            put_file(f"logos/{name}", f.read(), f"Add/update logo {name}")

    print("\nDone. Raw URL base:")
    print(f"  https://raw.githubusercontent.com/{OWNER}/{REPO}/{BRANCH}/logos")


if __name__ == "__main__":
    main()
