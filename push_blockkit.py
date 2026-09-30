#!/usr/bin/env python3
"""Publish the local Block Kit notification templates (blockkit/*.json) to the
public alexvesterlee/slack-demo-apps repo (under a `blockkit/` folder) via the
GitHub Contents API — no local clone. This makes the customized card layouts
(e.g. the real-Jira-ticket examples) available to anyone, not just this machine.

Reuses the SAME GitHub PAT as push_logos.py. Token is read from env GHT, then the
macOS Keychain — never typed into chat:

    read -rs "GHT?GitHub PAT (Contents: read/write on slack-demo-apps): "; echo
    GHT="$GHT" python3 push_blockkit.py

Add/update a template later: edit a blockkit/<key>.json next to this script and
re-run — every *.json in ./blockkit is uploaded.

The paired reader, send_app_notification.py, falls back to
  https://raw.githubusercontent.com/alexvesterlee/slack-demo-apps/main/blockkit/<key>.json
when a template isn't present locally, so a fresh clone with no blockkit/ dir
still works.
"""
import base64
import glob
import json
import os
import subprocess
import sys
import urllib.request
import urllib.error

OWNER = "alexvesterlee"
REPO = "slack-demo-apps"
BRANCH = "main"
API = f"https://api.github.com/repos/{OWNER}/{REPO}/contents"

# Same Keychain item as push_logos.py (Contents: read/write on slack-demo-apps).
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
LOCAL_BLOCKKIT_DIR = os.path.join(HERE, "blockkit")

README = """# slack-demo-apps · blockkit

Public **Block Kit card layouts** for the fictitious third-party app notifications posted
into the demo Slack org by `send_app_notification.py`.

One JSON file per app, named by its block-kit key (`salesforce.json`, `jira_cloud.json`, …).
Each file:

```json
{
  "app":         "Salesforce",      // display / logo family
  "fake_bot_id": "Salesforce",      // username the message posts under
  "notes":       "how/when to use it (for humans, not sent to Slack)",
  "examples": [
    { "name": "opportunity_won", "when": "…", "blocks": [ /* Slack Block Kit */ ] }
  ]
}
```

`send_app_notification.py --app <key> --example <name>` posts `examples[].blocks` via
`chat.postMessage`, under `fake_bot_id` as the username and the matching logo from
`../logos/<key>.png` as the avatar. When a template isn't present locally the helper
fetches it from:

    https://raw.githubusercontent.com/alexvesterlee/slack-demo-apps/main/blockkit/<key>.json

Structures originate from the bob-the-builder library
(https://github.com/evanbrosen/bob-the-builder/tree/main/blockkit) and are customized here
(e.g. real Jira ticket links in `jira_cloud.json`). Add a template: drop a `<key>.json` in
`blockkit/` and push — no code change, the helper picks it up by filename.
"""


def api(method, path, payload):
    req = urllib.request.Request(
        f"{API}/{path}", method=method, data=json.dumps(payload).encode(),
        headers={"Authorization": f"Bearer {TOKEN}",
                 "Accept": "application/vnd.github+json",
                 "X-GitHub-Api-Version": "2022-11-28",
                 "User-Agent": "demo-refresh-blockkit-uploader"})
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read().decode())


def get_sha(path):
    """Existing file sha (needed to update), or None if the file is new."""
    req = urllib.request.Request(
        f"{API}/{path}?ref={BRANCH}",
        headers={"Authorization": f"Bearer {TOKEN}",
                 "Accept": "application/vnd.github+json",
                 "User-Agent": "demo-refresh-blockkit-uploader"})
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
    put_file("blockkit/README.md", README.encode(),
             "Add blockkit README (template format)")

    if not os.path.isdir(LOCAL_BLOCKKIT_DIR):
        sys.exit(f"[error] no local blockkit/ dir at {LOCAL_BLOCKKIT_DIR}")

    files = sorted(glob.glob(os.path.join(LOCAL_BLOCKKIT_DIR, "*.json")))
    if not files:
        print("[note] no *.json found in ./blockkit — README only")
    for src in files:
        name = os.path.basename(src)
        # Validate it's parseable JSON before publishing (fail loud, not silent).
        with open(src, "rb") as f:
            raw = f.read()
        try:
            json.loads(raw)
        except json.JSONDecodeError as e:
            sys.exit(f"[error] {name} is not valid JSON ({e}); fix before publishing")
        put_file(f"blockkit/{name}", raw, f"Add/update block kit {name}")

    print("\nDone. Raw URL base:")
    print(f"  https://raw.githubusercontent.com/{OWNER}/{REPO}/{BRANCH}/blockkit")


if __name__ == "__main__":
    main()
