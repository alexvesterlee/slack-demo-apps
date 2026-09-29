# slack-demo-apps · blockkit

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
