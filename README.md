# slack-demo-apps

Public logo assets for **fictitious third-party app notifications** posted into the demo
Slack org by the `demo-refresh` skill's `send_app_notification.py` helper.

Slack's `icon_url` needs a publicly reachable image URL, so logos live here and are served
over `raw.githubusercontent.com`. The helper builds each avatar as:

    icon_url = <LOGO_BASE>/<blockkit-key>.png

with `LOGO_BASE = https://raw.githubusercontent.com/alexvesterlee/slack-demo-apps/main/logos`.

## Naming convention

One square PNG per app (>=192x192 renders best), named **exactly** by its block-kit file key
(from bob-the-builder/blockkit). To add or update a logo: drop `<key>.png` in `logos/` and
push — no code change, the helper picks it up automatically.

Expected keys: datadog, pagerduty, github, salesforce, service_cloud, servicenow, jira_cloud,
azure_pipelines, deploy_wizard, docusign, google_calendar, crm_analytics, workday, polly,
new_opportunity, deal_won, stage_changed.
